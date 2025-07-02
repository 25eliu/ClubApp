import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import CSClubsDatabase
from resume_manager import ResumeDatabase
import os

# Page configuration
st.set_page_config(
    page_title="CS Clubs @ UC Berkeley",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS 
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #003262;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.2rem;
        color: #FDB515;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    .club-card {
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #003262;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .club-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .club-name {
        font-size: 1.8rem;
        font-weight: bold;
        color: #003262;
        margin-bottom: 0.5rem;
    }
    .club-acronym {
        font-size: 1.2rem;
        color: #666;
        font-style: italic;
        margin-bottom: 1rem;
        background-color: #FDB515;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        display: inline-block;
    }
    .field-label {
        font-weight: bold;
        color: #003262;
        margin-top: 1rem;
        font-size: 1.1rem;
    }
    .friendliness-very-high {
        background-color: #d4edda;
        color: #155724;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
    }
    .friendliness-high {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
    }
    .friendliness-medium {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
    }
    .friendliness-low {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
    }
    .website-link {
        background-color: #FDB515;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .stats-card {
        background: linear-gradient(145deg, #003262, #004080);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_data():
    """Load data from MongoDB with caching"""
    try:
        db = CSClubsDatabase()
        clubs = db.get_all_clubs()
        stats = db.get_database_stats()
        db.close_connection()
        
        # Clean up freshman-friendliness data
        for club in clubs:
            if 'Freshman Friendliness (General Vibe)' in club:
                value = club['Freshman Friendliness (General Vibe)'].lower()
                if 'high' in value:
                    club['Freshman Friendliness (General Vibe)'] = 'High'
                elif 'medium' in value:
                    club['Freshman Friendliness (General Vibe)'] = 'Medium'
                elif 'low' in value:
                    club['Freshman Friendliness (General Vibe)'] = 'Low'
                # If none match, leave as is or set to a default value
        
        return clubs, stats
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return [], {}

def get_friendliness_color_class(friendliness):
    """Get CSS class for friendliness level"""
    if not friendliness:
        return "friendliness-medium"
    friendliness_lower = friendliness.lower()
    if "very high" in friendliness_lower:
        return "friendliness-very-high"
    elif "high" in friendliness_lower:
        return "friendliness-high"
    elif "medium" in friendliness_lower:
        return "friendliness-medium"
    else:
        return "friendliness-low"

def display_club_card(club):
    """Display a single club in a beautiful card format"""
    st.markdown(f"""
    <div class="club-card">
        <div class="club-name">{club.get("Club Name", "Unknown Club")}</div>
        {f'<div class="club-acronym">{club.get("Acronym", "")}</div>' if club.get("Acronym") else ""}
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Primary focus
        st.markdown(f'<div class="field-label">🎯 Primary Focus</div>', unsafe_allow_html=True)
        st.write(club.get("Primary Focus", "N/A"))
        
        # Typical activities
        st.markdown(f'<div class="field-label">🚀 Typical Activities</div>', unsafe_allow_html=True)
        st.write(club.get("Typical Activities", "N/A"))
        
        # How to join
        st.markdown(f'<div class="field-label">📝 How to Join/Learn More</div>', unsafe_allow_html=True)
        st.write(club.get("How to Join/Learn More", "N/A"))
        
        # Recruitment info
        st.markdown(f'<div class="field-label">👥 Typical Recruitment</div>', unsafe_allow_html=True)
        st.write(club.get("Typical Recruitment", "N/A"))
    
    with col2:
        # Website link
        if club.get("Website"):
            st.markdown(f'[🔗 Visit Website]({club["Website"]})')
        if club.get("ApplicationLink"):
            st.markdown(f'[📝 Application Link]({club["ApplicationLink"]})')
            
        # Application Time
        st.markdown(f'<div class="field-label">📅 Application Time</div>', unsafe_allow_html=True)
        st.write(club.get("Fall Application Time", "N/A"))
        # Freshman friendliness
        friendliness = club.get("Freshman Friendliness (General Vibe)", "N/A")
        color_class = get_friendliness_color_class(friendliness)
        st.markdown(f'<div class="field-label">🎓 Freshman Friendliness</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="{color_class}">{friendliness}</span>', unsafe_allow_html=True)
    
    # Notes for EECS freshmen (full width)
    if club.get("Notes for EECS Freshmen"):
        st.markdown(f'<div class="field-label">💡 Notes for EECS Freshmen</div>', unsafe_allow_html=True)
        st.info(club["Notes for EECS Freshmen"])
    
    st.markdown("---")

def create_analytics_charts(clubs_data):
    """Create analytics charts"""
    df = pd.DataFrame(clubs_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Freshman friendliness distribution
        if 'Freshman Friendliness (General Vibe)' in df.columns:
            friendliness_counts = df['Freshman Friendliness (General Vibe)'].value_counts()
            
            fig = px.pie(
                values=friendliness_counts.values,
                names=friendliness_counts.index,
                title="📊 Freshman Friendliness Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                title_font_size=16,
                title_x=0.5,
                font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Recruitment type analysis
        if 'Typical Recruitment' in df.columns:
            # Categorize recruitment types
            recruitment_categories = []
            for recruitment in df['Typical Recruitment'].dropna():
                if 'open' in recruitment.lower():
                    recruitment_categories.append('Open Membership')
                elif 'application' in recruitment.lower():
                    recruitment_categories.append('Application-Based')
                elif 'invitation' in recruitment.lower():
                    recruitment_categories.append('Invitation Only')
                else:
                    recruitment_categories.append('Other')
            
            if recruitment_categories:
                recruitment_counts = pd.Series(recruitment_categories).value_counts()
                
                fig = px.bar(
                    x=recruitment_counts.index,
                    y=recruitment_counts.values,
                    title="📋 Recruitment Types",
                    color=recruitment_counts.values,
                    color_continuous_scale="Blues"
                )
                fig.update_layout(
                    title_font_size=16,
                    title_x=0.5,
                    xaxis_title="Recruitment Type",
                    yaxis_title="Number of Clubs",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

def create_resume_section():
    """Create the resume upload and management section"""
    st.markdown("### 📄 Resume Management")
    st.markdown("Upload and manage your resumes for club applications")
    
    # Initialize database
    resume_db = ResumeDatabase()
    
    # Create tabs for upload and view
    upload_tab, view_tab = st.tabs(["📤 Upload Resume", "📋 View Resumes"])
    
    with upload_tab:
        st.markdown("#### Upload Your Resume")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose your resume file",
            type=['pdf'],
            help="Currently supports PDF files only"
        )
        
        if uploaded_file is not None:
            # Display file info
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Filename:** {uploaded_file.name}")
                st.info(f"**File size:** {uploaded_file.size / 1024:.1f} KB")
            
            with col2:
                st.info(f"**File type:** {uploaded_file.type}")
            
            # Upload button
            if st.button("📤 Upload Resume", type="primary"):
                with st.spinner("Processing resume..."):
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    # Save to database
                    resume_id = resume_db.save_resume(
                        filename=uploaded_file.name,
                        file_content=uploaded_file,
                        file_type="pdf"
                    )
                    
                    if resume_id:
                        st.success(f"✅ Resume uploaded successfully!")
                        st.balloons()
                        
                        # Show preview
                        resume = resume_db.get_resume_by_id(resume_id)
                        if resume:
                            st.markdown("#### Preview")
                            preview_text = resume["text_content"][:500] + "..." if len(resume["text_content"]) > 500 else resume["text_content"]
                            st.text_area("Resume Content Preview", preview_text, height=150)
                    else:
                        st.error("❌ Failed to upload resume. Please try again.")
    
    with view_tab:
        st.markdown("#### Your Uploaded Resumes")
        
        # Get all resumes
        resumes = resume_db.get_all_resumes()
        
        if not resumes:
            st.info("📝 No resumes uploaded yet. Upload your first resume in the Upload tab!")
        else:
            # Display statistics
            stats = resume_db.get_resume_stats()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Resumes", stats["total_resumes"])
            with col2:
                st.metric("Avg Word Count", f"{stats['avg_word_count']:.0f}")
            
            st.markdown("---")
            
            # Display each resume
            for resume in resumes:
                with st.expander(f"📄 {resume['filename']} - {resume['upload_timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Word Count:** {resume.get('word_count', 'N/A')}")
                        st.write(f"**Character Count:** {resume.get('character_count', 'N/A')}")
                        st.write(f"**Upload Date:** {resume['upload_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    with col2:
                        if st.button(f"👁️ View", key=f"view_{resume['_id']}"):
                            st.text_area(
                                "Resume Content",
                                resume["text_content"],
                                height=300,
                                key=f"content_{resume['_id']}"
                            )
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{resume['_id']}", type="secondary"):
                            if resume_db.delete_resume(resume['_id']):
                                st.success("Resume deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete resume")
    
    # Close database connection
    resume_db.close_connection()

def main():
    # Header
    st.markdown('<h1 class="main-header">🎓 CS Clubs @ UC Berkeley</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover the perfect Computer Science club for your journey!</p>', unsafe_allow_html=True)
    
    # Load data
    clubs_data, db_stats = load_data()
    
    if not clubs_data:
        st.error("🚨 No data available. Please check your database connection.")
        st.info("""
        **To fix this:**
        1. Make sure MongoDB is running
        2. Run `python load_data.py` to load your CSV data
        3. Refresh this page
        """)
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Search & Filter")
    st.sidebar.markdown("---")
    
    # Search functionality
    search_term = st.sidebar.text_input(
        "🔎 Search clubs:", 
        placeholder="Enter club name, acronym, or focus area..."
    )
    
    # Freshman friendliness filter
    friendliness_options = ["All Levels"] + sorted(list(set([
        club.get("Freshman Friendliness (General Vibe)", "N/A") 
        for club in clubs_data if club.get("Freshman Friendliness (General Vibe)")
    ])))
    selected_friendliness = st.sidebar.selectbox("🎓 Freshman Friendliness:", friendliness_options)
    
    # Recruitment type filter
    recruitment_types = ["All Types"] + sorted(list(set([
        "Open Membership" if "open" in club.get("Typical Recruitment", "").lower()
        else "Application-Based" if "application" in club.get("Typical Recruitment", "").lower()
        else "Invitation Only" if "invitation" in club.get("Typical Recruitment", "").lower()
        else "Other"
        for club in clubs_data if club.get("Typical Recruitment")
    ])))
    selected_recruitment = st.sidebar.selectbox("📝 Recruitment Type:", recruitment_types)
    
    # Filter clubs based on search and filters
    filtered_clubs = clubs_data.copy()
    
    if search_term:
        filtered_clubs = [
            club for club in filtered_clubs 
            if (search_term.lower() in club.get("Club Name", "").lower() or
                search_term.lower() in club.get("Acronym", "").lower() or
                search_term.lower() in club.get("Primary Focus", "").lower() or
                search_term.lower() in club.get("Typical Recruitment", "").lower())
        ]
    
    if selected_friendliness != "All Levels":
        filtered_clubs = [
            club for club in filtered_clubs 
            if club.get("Freshman Friendliness (General Vibe)", "N/A") == selected_friendliness
        ]
    
    if selected_recruitment != "All Types":
        filtered_clubs = [
            club for club in filtered_clubs 
            if ((selected_recruitment == "Open Membership" and "open" in club.get("Typical Recruitment", "").lower()) or
                (selected_recruitment == "Application-Based" and "application" in club.get("Typical Recruitment", "").lower()) or
                (selected_recruitment == "Invitation Only" and "invitation" in club.get("Typical Recruitment", "").lower()))
        ]
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Clubs", len(clubs_data))
    with col2:
        st.metric("🔍 Filtered Results", len(filtered_clubs))
    with col3:
        high_friendliness = len([
            c for c in clubs_data 
            if "high" in c.get("Freshman Friendliness (General Vibe)", "").lower()
        ])
        st.metric("🎓 Freshman-Friendly", high_friendliness)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Club Directory", "📊 Analytics", "📄 Resume Manager"])

    with tab1:
        st.markdown("### Club Directory")
        
        if filtered_clubs:
            for club in filtered_clubs:
                display_club_card(club)
        else:
            st.info("🔍 No clubs match your current filters. Try adjusting your search criteria.")
    
    with tab2:
        st.markdown("### Analytics Dashboard")
        create_analytics_charts(clubs_data)
        
        # Additional stats
        st.markdown("### 📈 Quick Stats")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            open_clubs = len([c for c in clubs_data if "open" in c.get("Typical Recruitment", "").lower()])
            st.metric("Open Membership Clubs", open_clubs)
        
        with col2:
            app_clubs = len([c for c in clubs_data if "application" in c.get("Typical Recruitment", "").lower()])
            st.metric("Application-Based Clubs", app_clubs)
        
        with col3:
            clubs_with_websites = len([c for c in clubs_data if c.get("Website")])
            st.metric("Clubs with Websites", clubs_with_websites)
    with tab3:
        create_resume_section()
if __name__ == "__main__":
    main()