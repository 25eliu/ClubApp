import streamlit as st
from pymongo import MongoClient
import PyPDF2
import io
from datetime import datetime
import hashlib
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class ResumeDatabase:
    def __init__(self):
        # Get connection details from .env file
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        database_name = os.getenv("DATABASE_NAME", "cs_clubs_db")  # Default fallback
        if not connection_string:
            st.error("MongoDB connection string not found in .env file")
            return
        
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]  # Use database name from .env
        self.collection = self.db.resumes  # Create resumes collection
        # Create index on filename and timestamp
        self.collection.create_index([("filename", 1), ("timestamp", -1)])
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text content from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return None
    
    def save_resume(self, filename, file_content, file_type="pdf"):
        """Save resume to MongoDB"""
        try:
            # Extract text content
            if file_type.lower() == "pdf":
                text_content = self.extract_text_from_pdf(file_content)
            else:
                # For future: handle other file types
                text_content = "Unsupported file type"
            
            if text_content is None:
                return None
            
            # Create file hash for deduplication
            file_hash = hashlib.md5(text_content.encode()).hexdigest()
            
            # Check if similar resume already exists
            existing = self.collection.find_one({"file_hash": file_hash})
            if existing:
                st.warning("A similar resume already exists in the database.")
                return existing["_id"]
            
            # Create resume document
            resume_doc = {
                "filename": filename,
                "file_type": file_type,
                "text_content": text_content,
                "file_hash": file_hash,
                "upload_timestamp": datetime.now(),
                "character_count": len(text_content),
                "word_count": len(text_content.split())
            }
            
            # Insert into database
            result = self.collection.insert_one(resume_doc)
            return result.inserted_id
            
        except Exception as e:
            st.error(f"Error saving resume: {str(e)}")
            return None
    
    def get_all_resumes(self):
        """Get all resumes from database"""
        try:
            resumes = list(self.collection.find().sort("upload_timestamp", -1))
            return resumes
        except Exception as e:
            st.error(f"Error fetching resumes: {str(e)}")
            return []
    
    def get_resume_by_id(self, resume_id):
        """Get specific resume by ID"""
        try:
            from bson import ObjectId
            resume = self.collection.find_one({"_id": ObjectId(resume_id)})
            return resume
        except Exception as e:
            st.error(f"Error fetching resume: {str(e)}")
            return None
    
    def delete_resume(self, resume_id):
        """Delete resume from database"""
        try:
            from bson import ObjectId
            result = self.collection.delete_one({"_id": ObjectId(resume_id)})
            return result.deleted_count > 0
        except Exception as e:
            st.error(f"Error deleting resume: {str(e)}")
            return False
    
    def get_resume_stats(self):
        """Get resume database statistics"""
        try:
            total_resumes = self.collection.count_documents({})
            avg_word_count = list(self.collection.aggregate([
                {"$group": {"_id": None, "avg_words": {"$avg": "$word_count"}}}
            ]))
            
            return {
                "total_resumes": total_resumes,
                "avg_word_count": avg_word_count[0]["avg_words"] if avg_word_count else 0
            }
        except Exception as e:
            st.error(f"Error getting stats: {str(e)}")
            return {"total_resumes": 0, "avg_word_count": 0}
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()