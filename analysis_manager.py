import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId
import json
import hashlib
from dotenv import load_dotenv
import os
from llm_analyzer import AnalysisResult, LLMAnalyzer

# Load environment variables
load_dotenv()

class AnalysisDatabase:
    def __init__(self):
        # Get connection details from .env file
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        database_name = os.getenv("DATABASE_NAME", "cs_clubs_db")
        
        if not connection_string:
            st.error("MongoDB connection string not found in .env file")
            return
        
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db.resume_analyses
        
        # Create indexes for efficient querying
        self.collection.create_index([("resume_id", 1), ("club_name", 1)], unique=True)
        self.collection.create_index([("analysis_timestamp", -1)])
        self.collection.create_index([("match_score", -1)])
        self.collection.create_index([("resume_id", 1)])

    def save_analysis(self, resume_id: str, club_name: str, analysis_result: AnalysisResult) -> Optional[str]:
        """Save analysis result to MongoDB"""
        try:
            # Create analysis document
            analysis_doc = {
                "resume_id": ObjectId(resume_id),
                "club_name": club_name,
                "analysis_timestamp": datetime.now(),
                "networking_strategy": analysis_result.networking_strategy,
                "campus_resources": analysis_result.campus_resources,
                "application_timeline": analysis_result.application_timeline,
                "preparation_steps": analysis_result.preparation_steps,
                "improvements": analysis_result.improvements,
                "match_score": analysis_result.match_score,
                "strategy_summary": analysis_result.strategy_summary
            }
            
            # Use upsert to update existing analysis or create new one
            result = self.collection.update_one(
                {"resume_id": ObjectId(resume_id), "club_name": club_name},
                {"$set": analysis_doc},
                upsert=True
            )
            
            if result.upserted_id:
                return str(result.upserted_id)
            else:
                # Find the existing document ID
                existing = self.collection.find_one({"resume_id": ObjectId(resume_id), "club_name": club_name})
                return str(existing["_id"]) if existing else None
                
        except Exception as e:
            st.error(f"Error saving analysis: {str(e)}")
            return None

    def get_analysis(self, resume_id: str, club_name: str) -> Optional[Dict[str, Any]]:
        """Get specific analysis by resume ID and club name"""
        try:
            analysis = self.collection.find_one({
                "resume_id": ObjectId(resume_id),
                "club_name": club_name
            })
            return analysis
        except Exception as e:
            st.error(f"Error retrieving analysis: {str(e)}")
            return None

    def get_analyses_for_resume(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a specific resume"""
        try:
            analyses = list(self.collection.find({
                "resume_id": ObjectId(resume_id)
            }).sort("analysis_timestamp", -1))
            return analyses
        except Exception as e:
            st.error(f"Error retrieving analyses: {str(e)}")
            return []

    def get_recent_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analyses across all resumes"""
        try:
            analyses = list(self.collection.find().sort("analysis_timestamp", -1).limit(limit))
            return analyses
        except Exception as e:
            st.error(f"Error retrieving recent analyses: {str(e)}")
            return []

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete a specific analysis"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(analysis_id)})
            return result.deleted_count > 0
        except Exception as e:
            st.error(f"Error deleting analysis: {str(e)}")
            return False

    def delete_analyses_for_resume(self, resume_id: str) -> bool:
        """Delete all analyses for a specific resume"""
        try:
            result = self.collection.delete_many({"resume_id": ObjectId(resume_id)})
            return result.deleted_count > 0
        except Exception as e:
            st.error(f"Error deleting analyses: {str(e)}")
            return False

    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get statistics about analyses"""
        try:
            total_analyses = self.collection.count_documents({})
            
            # Get average match score
            avg_score_pipeline = [
                {"$group": {"_id": None, "avg_score": {"$avg": "$match_score"}}}
            ]
            avg_score_result = list(self.collection.aggregate(avg_score_pipeline))
            avg_score = avg_score_result[0]["avg_score"] if avg_score_result else 0
            
            # Get unique resume count
            unique_resumes = len(self.collection.distinct("resume_id"))
            
            # Get unique club count
            unique_clubs = len(self.collection.distinct("club_name"))
            
            # Get analyses from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_analyses = self.collection.count_documents({
                "analysis_timestamp": {"$gte": week_ago}
            })
            
            # Get top performing clubs (highest average match scores)
            top_clubs_pipeline = [
                {"$group": {
                    "_id": "$club_name",
                    "avg_score": {"$avg": "$match_score"},
                    "analysis_count": {"$sum": 1}
                }},
                {"$sort": {"avg_score": -1}},
                {"$limit": 5}
            ]
            top_clubs = list(self.collection.aggregate(top_clubs_pipeline))
            
            return {
                "total_analyses": total_analyses,
                "average_match_score": avg_score,
                "unique_resumes": unique_resumes,
                "unique_clubs": unique_clubs,
                "recent_analyses": recent_analyses,
                "top_clubs": top_clubs
            }
            
        except Exception as e:
            st.error(f"Error getting statistics: {str(e)}")
            return {
                "total_analyses": 0,
                "average_match_score": 0,
                "unique_resumes": 0,
                "unique_clubs": 0,
                "recent_analyses": 0,
                "top_clubs": []
            }

    def get_club_analysis_summary(self, club_name: str) -> Dict[str, Any]:
        """Get summary of analyses for a specific club"""
        try:
            analyses = list(self.collection.find({"club_name": club_name}))
            
            if not analyses:
                return {"count": 0, "average_score": 0, "recent_count": 0}
            
            scores = [analysis["match_score"] for analysis in analyses]
            avg_score = sum(scores) / len(scores)
            
            # Count recent analyses (last 30 days)
            month_ago = datetime.now() - timedelta(days=30)
            recent_count = len([a for a in analyses if a["analysis_timestamp"] >= month_ago])
            
            return {
                "count": len(analyses),
                "average_score": avg_score,
                "recent_count": recent_count,
                "highest_score": max(scores),
                "lowest_score": min(scores)
            }
            
        except Exception as e:
            st.error(f"Error getting club summary: {str(e)}")
            return {"count": 0, "average_score": 0, "recent_count": 0}

    def export_analyses_to_dict(self, resume_id: str) -> Dict[str, Any]:
        """Export all analyses for a resume to a dictionary format"""
        try:
            analyses = self.get_analyses_for_resume(resume_id)
            
            export_data = {
                "resume_id": resume_id,
                "export_timestamp": datetime.now().isoformat(),
                "total_analyses": len(analyses),
                "analyses": []
            }
            
            for analysis in analyses:
                export_data["analyses"].append({
                    "club_name": analysis["club_name"],
                    "match_score": analysis["match_score"],
                    "analysis_timestamp": analysis["analysis_timestamp"].isoformat(),
                    "networking_strategy": analysis["networking_strategy"],
                    "campus_resources": analysis["campus_resources"],
                    "application_timeline": analysis["application_timeline"],
                    "preparation_steps": analysis["preparation_steps"],
                    "improvements": analysis["improvements"],
                    "strategy_summary": analysis["strategy_summary"]
                })
            
            return export_data
            
        except Exception as e:
            st.error(f"Error exporting analyses: {str(e)}")
            return {}

    def close_connection(self):
        """Close database connection"""
        self.client.close()

class AnalysisManager:
    """High-level manager for resume analysis operations"""
    
    def __init__(self):
        self.analyzer = LLMAnalyzer()
        self.db = AnalysisDatabase()
        self.cache_duration = timedelta(hours=24)  # Cache analyses for 24 hours

    def analyze_resume_for_club(self, resume_id: str, resume_text: str, club_data: Dict[str, Any], force_refresh: bool = False) -> Optional[AnalysisResult]:
        """Analyze resume for a specific club with caching"""
        club_name = club_data.get("Club Name", "Unknown Club")
        
        # Check cache first unless force refresh
        if not force_refresh:
            cached_analysis = self.db.get_analysis(resume_id, club_name)
            if cached_analysis:
                # Check if cache is still valid
                cache_age = datetime.now() - cached_analysis["analysis_timestamp"]
                if cache_age < self.cache_duration:
                    return AnalysisResult(
                        networking_strategy=cached_analysis["networking_strategy"],
                        campus_resources=cached_analysis["campus_resources"],
                        application_timeline=cached_analysis["application_timeline"],
                        preparation_steps=cached_analysis["preparation_steps"],
                        improvements=cached_analysis["improvements"],
                        match_score=cached_analysis["match_score"],
                        strategy_summary=cached_analysis["strategy_summary"]
                    )
        
        # Perform new analysis
        if not self.analyzer.is_configured():
            st.error("LLM is not properly configured. Please check your API keys.")
            return None
        
        analysis_result = self.analyzer.analyze_resume_for_club(resume_text, club_data)
        
        # Save to database
        if analysis_result:
            self.db.save_analysis(resume_id, club_name, analysis_result)
        
        return analysis_result

    def analyze_resume_for_multiple_clubs(self, resume_id: str, resume_text: str, clubs_data: List[Dict[str, Any]], force_refresh: bool = False) -> Dict[str, Any]:
        """Analyze resume for multiple clubs"""
        results = []
        
        for club_data in clubs_data:
            club_name = club_data.get("Club Name", "Unknown Club")
            analysis_result = self.analyze_resume_for_club(resume_id, resume_text, club_data, force_refresh)
            
            if analysis_result:
                results.append((club_name, analysis_result))
        
        # Generate comparative analysis
        if results:
            sorted_results = sorted(results, key=lambda x: x[1].match_score, reverse=True)
            match_scores = [result[1].match_score for result in results]
            avg_score = sum(match_scores) / len(match_scores)
            
            return {
                "analyses": sorted_results,
                "top_match": sorted_results[0] if sorted_results else None,
                "average_score": avg_score,
                "total_analyzed": len(results)
            }
        
        return {"analyses": [], "top_match": None, "average_score": 0, "total_analyzed": 0}

    def get_resume_analysis_summary(self, resume_id: str) -> Dict[str, Any]:
        """Get summary of all analyses for a resume"""
        analyses = self.db.get_analyses_for_resume(resume_id)
        
        if not analyses:
            return {"count": 0, "average_score": 0, "top_club": None}
        
        scores = [analysis["match_score"] for analysis in analyses]
        avg_score = sum(scores) / len(scores)
        
        # Find top match
        top_analysis = max(analyses, key=lambda x: x["match_score"])
        
        return {
            "count": len(analyses),
            "average_score": avg_score,
            "top_club": top_analysis["club_name"],
            "top_score": top_analysis["match_score"],
            "last_updated": max(analysis["analysis_timestamp"] for analysis in analyses)
        }

    def export_resume_analyses(self, resume_id: str) -> str:
        """Export all analyses for a resume as JSON string"""
        export_data = self.db.export_analyses_to_dict(resume_id)
        return json.dumps(export_data, indent=2, default=str)

    def cleanup_old_analyses(self, days_old: int = 30) -> int:
        """Remove analyses older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            result = self.db.collection.delete_many({
                "analysis_timestamp": {"$lt": cutoff_date}
            })
            return result.deleted_count
        except Exception as e:
            st.error(f"Error cleaning up old analyses: {str(e)}")
            return 0

    def close_connection(self):
        """Close database connection"""
        self.db.close_connection()