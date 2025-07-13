#!/usr/bin/env python3
"""
Data loading script for CS Clubs application.
This script loads club data from CSV files into MongoDB.
"""

import os
import sys
from database import CSClubsDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_clubs_data():
    """Load clubs data from CSV file into MongoDB"""
    
    # CSV file path
    csv_file_path = os.path.join("data", "cs_clubs.csv")
    
    # Check if CSV file exists
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found at: {csv_file_path}")
        print("Please ensure the CSV file exists in the data/ directory")
        return False
    
    # Initialize database
    try:
        db = CSClubsDatabase()
        print(f"📊 Loading data from: {csv_file_path}")
        
        # Load CSV data into MongoDB
        success = db.load_csv_to_mongodb(csv_file_path)
        
        if success:
            # Get statistics
            stats = db.get_database_stats()
            print(f"✅ Successfully loaded {stats.get('total_clubs', 0)} clubs into MongoDB")
            
            # Display some sample data
            clubs = db.get_all_clubs()
            if clubs:
                print(f"📋 Sample clubs loaded:")
                for i, club in enumerate(clubs[:3]):  # Show first 3 clubs
                    print(f"  {i+1}. {club.get('Club Name', 'Unknown')} - {club.get('Primary Focus', 'N/A')}")
                if len(clubs) > 3:
                    print(f"  ... and {len(clubs) - 3} more clubs")
        else:
            print("❌ Failed to load data into MongoDB")
        
        # Close database connection
        db.close_connection()
        return success
        
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return False

def verify_database_connection():
    """Verify that MongoDB connection is working"""
    try:
        db = CSClubsDatabase()
        stats = db.get_database_stats()
        db.close_connection()
        print(f"✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("Please ensure MongoDB is running and connection string is correct in .env file")
        return False

def main():
    """Main function"""
    print("🚀 CS Clubs Data Loader")
    print("=" * 50)
    
    # Check environment configuration
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    if not connection_string:
        print("❌ MongoDB connection string not found in .env file")
        print("Please create a .env file with MONGODB_CONNECTION_STRING")
        sys.exit(1)
    
    print(f"📡 Using MongoDB connection: {connection_string}")
    
    # Verify database connection
    if not verify_database_connection():
        sys.exit(1)
    
    # Load data
    success = load_clubs_data()
    
    if success:
        print("\n✅ Data loading completed successfully!")
        print("You can now run the application with: streamlit run app.py")
    else:
        print("\n❌ Data loading failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()