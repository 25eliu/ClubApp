import pandas as pd
import pymongo
from pymongo import MongoClient
import csv
import os

class CSClubsDatabase:
    def __init__(self, connection_string="mongodb://localhost:27017/", database_name="cs_clubs_db", collection_name="clubs"):
        """
        Initialize the MongoDB connection
        """
        self.client = MongoClient(connection_string)
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]
        
    def load_csv_to_mongodb(self, csv_file_path):
        """
        Load CSV data into MongoDB
        """
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            # Convert DataFrame to dictionary records
            records = df.to_dict('records')
            
            # Clear existing data
            self.collection.delete_many({})
            
            # Insert new data
            result = self.collection.insert_many(records)
            
            print(f"Successfully inserted {len(result.inserted_ids)} records into MongoDB")
            return True
            
        except Exception as e:
            print(f"Error loading CSV to MongoDB: {str(e)}")
            return False
    
    def get_all_clubs(self):
        """
        Retrieve all clubs from MongoDB
        """
        try:
            clubs = list(self.collection.find({}, {'_id': 0}))  # Exclude MongoDB's _id field
            return clubs
        except Exception as e:
            print(f"Error retrieving clubs: {str(e)}")
            return []
    
    def get_club_by_name(self, club_name):
        """
        Get a specific club by name
        """
        try:
            club = self.collection.find_one({"Club Name": club_name}, {'_id': 0})
            return club
        except Exception as e:
            print(f"Error retrieving club: {str(e)}")
            return None
    
    def search_clubs(self, search_term):
        """
        Search clubs by name, acronym, or primary focus
        """
        try:
            query = {
                "$or": [
                    {"Club Name": {"$regex": search_term, "$options": "i"}},
                    {"Acronym": {"$regex": search_term, "$options": "i"}},
                    {"Primary Focus": {"$regex": search_term, "$options": "i"}}
                ]
            }
            clubs = list(self.collection.find(query, {'_id': 0}))
            return clubs
        except Exception as e:
            print(f"Error searching clubs: {str(e)}")
            return []
    
    def get_clubs_by_freshman_friendliness(self, friendliness_level):
        """
        Filter clubs by freshman friendliness level
        """
        try:
            query = {"Freshman Friendliness (General Vibe)": {"$regex": friendliness_level, "$options": "i"}}
            clubs = list(self.collection.find(query, {'_id': 0}))
            return clubs
        except Exception as e:
            print(f"Error filtering clubs: {str(e)}")
            return []
    def get_database_stats(self):
        """
        Get statistics about the database
        Returns:
            dict: Database statistics
        """
        if self.collection is None: 
            return {}
        
        try:
            total_clubs = self.collection.count_documents({})
            
            # Count by freshman friendliness
            high_friendly = self.collection.count_documents({
                "Freshman Friendliness (General Vibe)": {"$regex": "high", "$options": "i"}
            })
            
            return {
                "total_clubs": total_clubs,
                "high_freshman_friendly": high_friendly
            }
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return {}
    def close_connection(self):
        """
        Close MongoDB connection
        """
        self.client.close()

if __name__ == "__main__":
    # Initialize database
    db = CSClubsDatabase()
    
    # Load CSV data (you'll need to provide the correct path)
    csv_path = "cs_clubs.csv"  # Update this path
    if os.path.exists(csv_path):
        db.load_csv_to_mongodb(csv_path)
    else:
        print(f"CSV file not found at {csv_path}")
    
    # Test the connection
    clubs = db.get_all_clubs()
    print(f"Total clubs in database: {len(clubs)}")
