# Club Directory Web Application

A customizable web application for discovering and exploring student clubs and organizations. Originally designed for CS/EECS clubs at UC Berkeley, this project can be easily adapted for any type of club data at any institution.

## 🌟 Features

- **Interactive Club Directory**: Browse clubs with detailed information cards
- **Advanced Search & Filtering**: Search by name, acronym, focus area, and filter by various criteria
- **Analytics Dashboard**: Visual insights into club distributions and statistics
- **Responsive Design**: Beautiful, mobile-friendly interface with UC Berkeley branding
- **Database Integration**: MongoDB backend for scalable data storage
- **Easy Customization**: Adaptable for any club type or institution

## 📊 Data Format

The application expects a CSV file with the following columns (customize as needed):

| Column Name | Description | Required |
|-------------|-------------|----------|
| `Club Name` | Full name of the club | ✅ |
| `Acronym` | Short abbreviation | ❌ |
| `Website` | Club website URL | ❌ |
| `Primary Focus` | Main purpose/focus area | ❌ |
| `Typical Recruitment` | How members join | ❌ |
| `Freshman Friendliness (General Vibe)` | Beginner-friendliness level | ❌ |
| `Typical Activities` | What the club does | ❌ |
| `How to Join/Learn More` | Contact/application info | ❌ |
| `Notes for EECS Freshmen` | Special notes (customize field name) | ❌ |

### Sample CSV Format
```csv
Club Name,Acronym,Website,Primary Focus,Typical Recruitment,Freshman Friendliness (General Vibe),Typical Activities,How to Join/Learn More,Notes for EECS Freshmen
Computer Science Mentors,CSM,https://csmentors.berkeley.edu/,Academic support,Open to all,Very High,Tutoring sessions,Sign up online,Great for getting help
Hackathon Club,HC,https://hackathon.club,Programming competitions,Application-based,High,Coding events,Apply each semester,Build cool projects
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- MongoDB (local or cloud instance)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd club-directory
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB**
   - Install MongoDB locally OR use MongoDB Atlas (cloud)
   - Update `.env` file with your connection string

4. **Prepare your data**
   - Replace `data/clubs.csv` with your club data
   - Ensure column names match expected format (or customize the code)

5. **Load data into database**
   ```bash
   python load_data.py
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Open your browser** to `http://localhost:8501`


*This project was originally created for CS/EECS clubs at UC Berkeley but is designed to be easily adaptable for any organization's club directory needs.*