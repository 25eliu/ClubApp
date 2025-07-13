import os
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

@dataclass
class AnalysisResult:
    """Structured result from LLM club application strategy analysis"""
    networking_strategy: List[str]
    campus_resources: List[str]
    application_timeline: List[str]
    preparation_steps: List[str]
    improvements: List[str]
    match_score: int
    strategy_summary: str

class LLMAnalyzer:
    def __init__(self):
        self.provider = LLMProvider(os.getenv("LLM_PROVIDER", "openai"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("ANALYSIS_TEMPERATURE", "0.3"))
        
        # Initialize the appropriate client
        if self.provider == LLMProvider.OPENAI:
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                st.error("OpenAI package not installed. Please install it with: pip install openai")
                self.client = None
        elif self.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except ImportError:
                st.error("Anthropic package not installed. Please install it with: pip install anthropic")
                self.client = None

    def create_analysis_prompt(self, resume_text: str, club_data: Dict[str, Any]) -> str:
        """Create a comprehensive club application strategy prompt"""
        
        # Extract club information
        club_name = club_data.get("Club Name", "Unknown Club")
        primary_focus = club_data.get("Primary Focus", "Not specified")
        typical_activities = club_data.get("Typical Activities", "Not specified")
        typical_recruitment = club_data.get("Typical Recruitment", "Not specified")
        freshman_friendliness = club_data.get("Freshman Friendliness (General Vibe)", "Not specified")
        notes_for_freshmen = club_data.get("Notes for EECS Freshmen", "Not specified")
        how_to_join = club_data.get("How to Join/Learn More", "Not specified")
        website = club_data.get("Website", "Not specified")
        application_link = club_data.get("ApplicationLink", "Not specified")
        
        prompt = f"""
You are an expert student advisor specializing in UC Berkeley club applications and networking strategies. 
Create a comprehensive, step-by-step guide for successfully getting into this specific club.

CLUB INFORMATION:
- Club Name: {club_name}
- Primary Focus: {primary_focus}
- Typical Activities: {typical_activities}
- Recruitment Process: {typical_recruitment}
- Freshman Friendliness: {freshman_friendliness}
- Special Notes: {notes_for_freshmen}
- How to Join: {how_to_join}
- Website: {website}
- Application Link: {application_link}

STUDENT'S BACKGROUND (from resume):
{resume_text}

STRATEGY REQUIREMENTS:
Create a structured action plan in the following JSON format:

{{
    "networking_strategy": [
        "Specific steps for coffee chats (who to reach out to, how to find contacts)",
        "LinkedIn connection strategies for club members/alumni",
        "Campus events or meetings to attend to meet current members",
        "Informational interview tactics with club officers or advisors"
    ],
    "campus_resources": [
        "Specific UC Berkeley offices, programs, or services to leverage",
        "Academic courses or workshops that align with club's focus",
        "Campus groups or activities that complement this club",
        "Faculty connections or research opportunities relevant to the club"
    ],
    "application_timeline": [
        "Month-by-month action plan leading up to application",
        "Key deadlines and milestones to track",
        "When to start networking vs. when to apply",
        "Follow-up strategies and timeline after application"
    ],
    "preparation_steps": [
        "Specific skills or experiences to develop before applying",
        "Projects or initiatives to undertake that demonstrate fit",
        "Ways to show genuine interest and commitment to the club's mission",
        "How to research and understand the club's culture and values"
    ],
    "improvements": [
        "2-3 specific resume/application improvements for this club",
        "Ways to better highlight relevant experiences for this opportunity"
    ],
    "match_score": 85,
    "strategy_summary": "2-3 sentence overview of the recommended approach and likelihood of success"
}}

STRATEGY GUIDELINES:
1. Be specific to UC Berkeley's campus culture and resources
2. Tailor networking advice to the club's recruitment style and culture
3. Include realistic timelines based on typical academic calendars
4. Focus on genuine relationship building, not just transactional networking
5. Consider the student's current background and how to bridge any gaps
6. Provide actionable steps that can be started immediately
7. Include both short-term and long-term preparation strategies
8. Factor in the club's freshman friendliness and competitiveness

Research publicly available information about this club when possible and incorporate specific details about their culture, recent activities, or leadership structure into your recommendations.

Provide only the JSON response with no additional text.
"""
        return prompt

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def call_llm(self, prompt: str) -> str:
        """Make LLM API call with retry logic"""
        try:
            if self.provider == LLMProvider.OPENAI:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                return response.choices[0].message.content
            
            elif self.provider == LLMProvider.ANTHROPIC:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            st.error(f"LLM API call failed: {str(e)}")
            raise

    def parse_llm_response(self, response: str) -> AnalysisResult:
        """Parse LLM response into structured format"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            data = json.loads(response)
            
            return AnalysisResult(
                networking_strategy=data.get("networking_strategy", []),
                campus_resources=data.get("campus_resources", []),
                application_timeline=data.get("application_timeline", []),
                preparation_steps=data.get("preparation_steps", []),
                improvements=data.get("improvements", []),
                match_score=int(data.get("match_score", 0)),
                strategy_summary=data.get("strategy_summary", "")
            )
            
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse LLM response as JSON: {str(e)}")
            # Return a fallback result
            return AnalysisResult(
                networking_strategy=["Unable to parse strategy - please try again"],
                campus_resources=["Analysis parsing failed"],
                application_timeline=["Please retry the analysis"],
                preparation_steps=["Try again with a different approach"],
                improvements=["Analysis parsing failed"],
                match_score=0,
                strategy_summary="Analysis parsing failed due to JSON format issues"
            )
        except Exception as e:
            st.error(f"Unexpected error parsing response: {str(e)}")
            return AnalysisResult(
                networking_strategy=["Error in analysis"],
                campus_resources=["Please try again"],
                application_timeline=["Analysis failed"],
                preparation_steps=["Retry recommended"],
                improvements=["Please try again"],
                match_score=0,
                strategy_summary=f"Error: {str(e)}"
            )

    def analyze_resume_for_club(self, resume_text: str, club_data: Dict[str, Any]) -> AnalysisResult:
        """Complete analysis workflow for a resume-club pair"""
        if not self.client:
            st.error("LLM client not initialized. Please check your API keys and dependencies.")
            return AnalysisResult(
                networking_strategy=["LLM client not available"],
                campus_resources=["Please configure LLM settings"],
                application_timeline=["Check API keys"],
                preparation_steps=["Verify LLM configuration"],
                improvements=["Please configure LLM settings"],
                match_score=0,
                strategy_summary="LLM client initialization failed"
            )
        
        try:
            # Create the analysis prompt
            prompt = self.create_analysis_prompt(resume_text, club_data)
            
            # Call LLM
            with st.spinner(f"Analyzing resume for {club_data.get('Club Name', 'Unknown Club')}..."):
                response = self.call_llm(prompt)
            
            # Parse response
            result = self.parse_llm_response(response)
            
            return result
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            return AnalysisResult(
                networking_strategy=["Analysis failed"],
                campus_resources=["Please try again"],
                application_timeline=["Error occurred"],
                preparation_steps=["Retry recommended"],
                improvements=["Please try again"],
                match_score=0,
                strategy_summary=f"Analysis failed: {str(e)}"
            )

    def analyze_resume_for_multiple_clubs(self, resume_text: str, clubs_data: List[Dict[str, Any]]) -> List[Tuple[str, AnalysisResult]]:
        """Analyze resume against multiple clubs"""
        results = []
        
        for club_data in clubs_data:
            club_name = club_data.get("Club Name", "Unknown Club")
            
            try:
                result = self.analyze_resume_for_club(resume_text, club_data)
                results.append((club_name, result))
            except Exception as e:
                st.error(f"Failed to analyze for {club_name}: {str(e)}")
                # Add a failed result
                failed_result = AnalysisResult(
                    networking_strategy=[f"Analysis failed for {club_name}"],
                    campus_resources=["Please try again"],
                    application_timeline=["Error occurred"],
                    preparation_steps=["Retry recommended"],
                    improvements=["Please try again"],
                    match_score=0,
                    strategy_summary=f"Analysis failed: {str(e)}"
                )
                results.append((club_name, failed_result))
        
        return results

    def get_comparative_analysis(self, resume_text: str, clubs_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comparative analysis across multiple clubs"""
        if not clubs_data:
            return {}
        
        # Analyze each club
        club_analyses = self.analyze_resume_for_multiple_clubs(resume_text, clubs_data)
        
        # Sort by match score
        sorted_analyses = sorted(club_analyses, key=lambda x: x[1].match_score, reverse=True)
        
        # Generate summary statistics
        match_scores = [analysis[1].match_score for analysis in club_analyses]
        avg_match_score = sum(match_scores) / len(match_scores) if match_scores else 0
        
        return {
            "club_analyses": sorted_analyses,
            "top_match": sorted_analyses[0] if sorted_analyses else None,
            "average_match_score": avg_match_score,
            "total_clubs_analyzed": len(club_analyses),
            "recommendation": self._generate_application_strategy(sorted_analyses)
        }

    def _generate_application_strategy(self, sorted_analyses: List[Tuple[str, AnalysisResult]]) -> str:
        """Generate application strategy based on match scores"""
        if not sorted_analyses:
            return "No clubs analyzed."
        
        high_match = [club for club, analysis in sorted_analyses if analysis.match_score >= 80]
        medium_match = [club for club, analysis in sorted_analyses if 60 <= analysis.match_score < 80]
        low_match = [club for club, analysis in sorted_analyses if analysis.match_score < 60]
        
        strategy = "Application Strategy:\n"
        
        if high_match:
            strategy += f"🎯 High Priority ({len(high_match)} clubs): {', '.join(high_match[:3])}"
            if len(high_match) > 3:
                strategy += f" and {len(high_match) - 3} more"
            strategy += " - Apply early, these are excellent matches.\n"
        
        if medium_match:
            strategy += f"📝 Medium Priority ({len(medium_match)} clubs): {', '.join(medium_match[:3])}"
            if len(medium_match) > 3:
                strategy += f" and {len(medium_match) - 3} more"
            strategy += " - Good options with some resume improvements.\n"
        
        if low_match:
            strategy += f"🔄 Growth Opportunities ({len(low_match)} clubs): {', '.join(low_match[:3])}"
            if len(low_match) > 3:
                strategy += f" and {len(low_match) - 3} more"
            strategy += " - Consider for skill development after building experience.\n"
        
        return strategy

    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        if self.provider == LLMProvider.OPENAI:
            return os.getenv("OPENAI_API_KEY") is not None and self.client is not None
        elif self.provider == LLMProvider.ANTHROPIC:
            return os.getenv("ANTHROPIC_API_KEY") is not None and self.client is not None
        return False