import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import CSClubsDatabase
from resume_manager import ResumeDatabase
from analysis_manager import AnalysisManager
from llm_analyzer import LLMAnalyzer
import os
import time

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
    .favorite-club-card {
        background: linear-gradient(145deg, #fff8e1, #fff3c4);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FDB515;
        border-right: 3px solid #FDB515;
        margin-bottom: 1.5rem;
        box-shadow: 0 6px 12px rgba(253, 181, 21, 0.2);
        transition: transform 0.2s;
        position: relative;
    }
    .favorite-club-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(253, 181, 21, 0.3);
    }
    .favorite-star {
        position: absolute;
        top: 15px;
        right: 15px;
        font-size: 1.5rem;
        color: #FDB515;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .favorite-star:hover {
        transform: scale(1.2);
    }
    .non-favorite-star {
        position: absolute;
        top: 15px;
        right: 15px;
        font-size: 1.5rem;
        color: #ccc;
        cursor: pointer;
        transition: all 0.2s;
    }
    .non-favorite-star:hover {
        color: #FDB515;
        transform: scale(1.2);
    }
    .favorites-separator {
        margin: 2rem 0;
        text-align: center;
        position: relative;
    }
    .favorites-separator:before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(to right, transparent, #FDB515, transparent);
    }
    .favorites-separator span {
        background: white;
        padding: 0 1rem;
        color: #003262;
        font-weight: bold;
        font-size: 1.1rem;
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

def get_user_favorites():
    """Get user favorites with caching"""
    try:
        current_time = time.time()
        
        # Check if cache is still valid (refresh every 5 minutes for persistent favorites)
        if (current_time - st.session_state.last_favorites_update > 300):
            db = CSClubsDatabase()
            st.session_state.favorites_cache = db.get_user_favorites(st.session_state.user_id)
            st.session_state.last_favorites_update = current_time
            db.close_connection()
        
        return st.session_state.favorites_cache
    except Exception as e:
        st.error(f"Error loading favorites: {str(e)}")
        return []

def toggle_favorite(club_name):
    """Toggle favorite status of a club"""
    try:
        db = CSClubsDatabase()
        
        if db.is_club_favorited(st.session_state.user_id, club_name):
            success = db.remove_favorite_club(st.session_state.user_id, club_name)
            if success and club_name in st.session_state.favorites_cache:
                st.session_state.favorites_cache.remove(club_name)
        else:
            success = db.save_favorite_club(st.session_state.user_id, club_name)
            if success and club_name not in st.session_state.favorites_cache:
                st.session_state.favorites_cache.append(club_name)
        
        db.close_connection()
        
        # Force cache refresh
        st.session_state.last_favorites_update = 0
        
        return success
    except Exception as e:
        st.error(f"Error toggling favorite: {str(e)}")
        return False

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
    club_name = club.get("Club Name", "Unknown Club")
    user_favorites = get_user_favorites()
    is_favorited = club_name in user_favorites
    
    # Use different CSS class for favorited clubs
    card_class = "favorite-club-card" if is_favorited else "club-card"
    star_icon = "⭐" if is_favorited else "☆"
    star_class = "favorite-star" if is_favorited else "non-favorite-star"
    
    # Create unique key for the button
    button_key = f"fav_btn_{club_name.replace(' ', '_')}"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="club-name">{club_name}</div>
        {f'<div class="club-acronym">{club.get("Acronym", "")}</div>' if club.get("Acronym") else ""}
    </div>
    """, unsafe_allow_html=True)
    
    # Create a column layout for the favorite button
    col_fav, col_content = st.columns([1, 9])
    
    with col_fav:
        # Favorite toggle button
        if st.button(star_icon, key=button_key, help=f"{'Remove from' if is_favorited else 'Add to'} favorites"):
            if toggle_favorite(club_name):
                st.rerun()
    
    with col_content:
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
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**Word Count:** {resume.get('word_count', 'N/A')}")
                        st.write(f"**Character Count:** {resume.get('character_count', 'N/A')}")
                        st.write(f"**Upload Date:** {resume['upload_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # Show analysis summary if available
                        try:
                            from analysis_manager import AnalysisManager
                            temp_analysis_manager = AnalysisManager()
                            analysis_summary = temp_analysis_manager.get_resume_analysis_summary(str(resume['_id']))
                            if analysis_summary["count"] > 0:
                                st.write(f"**Analyses:** {analysis_summary['count']}")
                                st.write(f"**Top Match:** {analysis_summary['top_club']} ({analysis_summary['top_score']})")
                            temp_analysis_manager.close_connection()
                        except Exception:
                            pass  # Ignore if analysis manager is not available
                    
                    with col2:
                        if st.button(f"👁️ View", key=f"view_{resume['_id']}"):
                            st.text_area(
                                "Resume Content",
                                resume["text_content"],
                                height=300,
                                key=f"content_{resume['_id']}"
                            )
                    
                    with col3:
                        if st.button(f"🤖 Quick Analysis", key=f"analyze_{resume['_id']}", type="primary"):
                            st.session_state[f"show_analysis_{resume['_id']}"] = True
                    
                    with col4:
                        if st.button(f"🗑️ Delete", key=f"delete_{resume['_id']}", type="secondary"):
                            if resume_db.delete_resume(resume['_id']):
                                st.success("Resume deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete resume")
                    
                    # Show quick analysis interface if requested
                    if st.session_state.get(f"show_analysis_{resume['_id']}", False):
                        st.markdown("---")
                        st.markdown("##### Quick Analysis")
                        
                        # Get clubs data for selection
                        try:
                            db = CSClubsDatabase()
                            clubs_data = db.get_all_clubs()
                            db.close_connection()
                            
                            if clubs_data:
                                club_options = {club.get("Club Name", "Unknown"): club for club in clubs_data}
                                selected_club_name = st.selectbox(
                                    "Select Club for Analysis:", 
                                    list(club_options.keys()), 
                                    key=f"club_select_{resume['_id']}"
                                )
                                
                                quick_col1, quick_col2 = st.columns(2)
                                with quick_col1:
                                    if st.button(f"🔍 Analyze", key=f"run_analysis_{resume['_id']}", type="primary"):
                                        selected_club = club_options[selected_club_name]
                                        
                                        # Initialize analysis manager
                                        analysis_manager = AnalysisManager()
                                        
                                        if analysis_manager.analyzer.is_configured():
                                            with st.spinner("Analyzing resume..."):
                                                analysis_result = analysis_manager.analyze_resume_for_club(
                                                    resume_id=str(resume["_id"]),
                                                    resume_text=resume["text_content"],
                                                    club_data=selected_club,
                                                    force_refresh=False
                                                )
                                                
                                                if analysis_result:
                                                    st.success(f"Analysis completed! Match Score: {analysis_result.match_score}/100")
                                                    st.info("View full analysis in the Resume Analysis tab.")
                                                else:
                                                    st.error("Analysis failed. Please try again.")
                                        else:
                                            st.warning("LLM not configured. Please set up API keys in .env file.")
                                        
                                        analysis_manager.close_connection()
                                
                                with quick_col2:
                                    if st.button(f"❌ Cancel", key=f"cancel_analysis_{resume['_id']}"):
                                        st.session_state[f"show_analysis_{resume['_id']}"] = False
                                        st.rerun()
                            else:
                                st.warning("No clubs data available for analysis.")
                        except Exception as e:
                            st.error(f"Error loading clubs data: {str(e)}")
    
    # Close database connection
    resume_db.close_connection()

def create_resume_analysis_section(clubs_data):
    """Create the resume analysis section with LLM-powered insights"""
    st.markdown("### 🤖 Resume Analysis")
    st.markdown("Get AI-powered insights on how well your resume matches specific clubs")
    
    # Initialize analysis manager
    analysis_manager = AnalysisManager()
    
    # Check if LLM is configured
    if not analysis_manager.analyzer.is_configured():
        st.error("🔧 LLM Analysis not configured. Please set up your API keys in the .env file.")
        st.info("""
        **To enable LLM analysis:**
        1. Add your OpenAI or Anthropic API key to the .env file
        2. Set LLM_PROVIDER to 'openai' or 'anthropic'
        3. Restart the application
        """)
        return
    
    # Get available resumes
    resume_db = ResumeDatabase()
    resumes = resume_db.get_all_resumes()
    
    if not resumes:
        st.info("📝 No resumes found. Please upload a resume in the Resume Manager tab first.")
        resume_db.close_connection()
        return
    
    # Create analysis interface
    analysis_tab, comparison_tab, history_tab = st.tabs(["🔍 Single Analysis", "📊 Compare Clubs", "📈 Analysis History"])
    
    with analysis_tab:
        st.markdown("#### Analyze Resume for Specific Club")
        
        # Resume selection
        resume_options = {f"{resume['filename']} ({resume['upload_timestamp'].strftime('%Y-%m-%d')})": resume for resume in resumes}
        selected_resume_key = st.selectbox("Select Resume:", list(resume_options.keys()))
        selected_resume = resume_options[selected_resume_key]
        
        # Club selection
        club_options = {club.get("Club Name", "Unknown"): club for club in clubs_data}
        selected_club_name = st.selectbox("Select Club:", list(club_options.keys()))
        selected_club = club_options[selected_club_name]
        
        # Analysis options
        col1, col2 = st.columns(2)
        with col1:
            force_refresh = st.checkbox("Force new analysis (ignore cache)", value=False)
        with col2:
            if st.button("🔍 Analyze Resume", type="primary"):
                with st.spinner("Analyzing resume..."):
                    analysis_result = analysis_manager.analyze_resume_for_club(
                        resume_id=str(selected_resume["_id"]),
                        resume_text=selected_resume["text_content"],
                        club_data=selected_club,
                        force_refresh=force_refresh
                    )
                    
                    if analysis_result:
                        display_analysis_result(analysis_result, selected_club_name)
                    else:
                        st.error("Analysis failed. Please try again.")
    
    with comparison_tab:
        st.markdown("#### Compare Resume Against Multiple Clubs")
        
        # Resume selection
        selected_resume_key = st.selectbox("Select Resume:", list(resume_options.keys()), key="compare_resume")
        selected_resume = resume_options[selected_resume_key]
        
        # Club selection
        club_names = [club.get("Club Name", "Unknown") for club in clubs_data]
        
        # Get user favorites for default selection
        user_favorites_for_comparison = get_user_favorites()
        available_favorites = [name for name in user_favorites_for_comparison if name in club_names]
        
        # Determine default selection: favorites if available, otherwise first 3 clubs
        if available_favorites:
            default_clubs = available_favorites[:10]  # Limit to max_selections
            help_text = f"Your {len(available_favorites)} favorite club{'s are' if len(available_favorites) != 1 else ' is'} pre-selected"
        else:
            default_clubs = club_names[:3] if len(club_names) >= 3 else club_names
            help_text = "No favorites set - showing first 3 clubs"
        
        selected_club_names = st.multiselect(
            "Select Clubs to Compare:", 
            club_names, 
            default=default_clubs,
            max_selections=10,
            help=help_text
        )
        
        if selected_club_names:
            selected_clubs = [club for club in clubs_data if club.get("Club Name") in selected_club_names]
            
            col1, col2 = st.columns(2)
            with col1:
                force_refresh = st.checkbox("Force new analysis (ignore cache)", value=False, key="compare_force")
            with col2:
                if st.button("📊 Compare Clubs", type="primary"):
                    with st.spinner("Analyzing resume against multiple clubs..."):
                        comparison_result = analysis_manager.analyze_resume_for_multiple_clubs(
                            resume_id=str(selected_resume["_id"]),
                            resume_text=selected_resume["text_content"],
                            clubs_data=selected_clubs,
                            force_refresh=force_refresh
                        )
                        
                        if comparison_result["analyses"]:
                            display_comparison_results(comparison_result)
                        else:
                            st.error("Comparison analysis failed. Please try again.")
    
    with history_tab:
        st.markdown("#### Analysis History")
        
        # Resume selection for history
        selected_resume_key = st.selectbox("Select Resume:", list(resume_options.keys()), key="history_resume")
        selected_resume = resume_options[selected_resume_key]
        
        # Get analysis history
        analyses = analysis_manager.db.get_analyses_for_resume(str(selected_resume["_id"]))
        
        if analyses:
            st.success(f"Found {len(analyses)} previous analyses")
            
            # Display summary statistics
            summary = analysis_manager.get_resume_analysis_summary(str(selected_resume["_id"]))
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Analyses", summary["count"])
            with col2:
                st.metric("Average Match Score", f"{summary['average_score']:.1f}")
            with col3:
                st.metric("Top Match", f"{summary['top_club']} ({summary['top_score']})")
            
            # Display individual analyses
            for analysis in analyses:
                display_historical_analysis(analysis)
                
            # Export option
            if st.button("📥 Export Analysis History"):
                export_data = analysis_manager.export_resume_analyses(str(selected_resume["_id"]))
                st.download_button(
                    label="Download Analysis History (JSON)",
                    data=export_data,
                    file_name=f"resume_analysis_{selected_resume['filename']}_{selected_resume['upload_timestamp'].strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
        else:
            st.info("No analysis history found for this resume.")
    
    # Close database connections
    resume_db.close_connection()
    analysis_manager.close_connection()

def display_analysis_result(analysis_result, club_name):
    """Display a single analysis result"""
    st.markdown(f"#### Analysis Results for {club_name}")
    
    # Match score with color coding
    score = analysis_result.match_score
    if score >= 80:
        score_color = "green"
    elif score >= 60:
        score_color = "orange"
    else:
        score_color = "red"
    
    st.markdown(f"**Match Score:** <span style='color:{score_color}; font-size:24px; font-weight:bold'>{score}/100</span>", unsafe_allow_html=True)
    
    # Strategy summary
    if analysis_result.strategy_summary:
        st.info(f"**Strategy Overview:** {analysis_result.strategy_summary}")
    
    # Create columns for different sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤝 Networking Strategy")
        for strategy in analysis_result.networking_strategy:
            st.markdown(f"• {strategy}")
        
        st.markdown("#### 🏫 Campus Resources")
        for resource in analysis_result.campus_resources:
            st.markdown(f"• {resource}")
    
    with col2:
        st.markdown("#### 📅 Application Timeline")
        for timeline in analysis_result.application_timeline:
            st.markdown(f"• {timeline}")
        
        st.markdown("#### 🎯 Preparation Steps")
        for step in analysis_result.preparation_steps:
            st.markdown(f"• {step}")
    
    # Resume improvements section (full width)
    st.markdown("#### 📈 Resume Improvements")
    for improvement in analysis_result.improvements:
        st.markdown(f"• {improvement}")

def display_comparison_results(comparison_result):
    """Display comparison results for multiple clubs"""
    st.markdown("#### 📊 Club Comparison Results")
    
    analyses = comparison_result["analyses"]
    
    # Create a summary chart
    club_names = [analysis[0] for analysis in analyses]
    match_scores = [analysis[1].match_score for analysis in analyses]
    
    # Bar chart of match scores
    import plotly.graph_objects as go
    fig = go.Figure(data=[
        go.Bar(
            x=club_names,
            y=match_scores,
            text=match_scores,
            textposition='auto',
            marker_color=['green' if score >= 80 else 'orange' if score >= 60 else 'red' for score in match_scores]
        )
    ])
    
    fig.update_layout(
        title="Match Scores by Club",
        xaxis_title="Club",
        yaxis_title="Match Score",
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display top matches
    st.markdown("#### 🏆 Top Matches")
    for i, (club_name, analysis) in enumerate(analyses[:3]):
        with st.expander(f"#{i+1} {club_name} (Score: {analysis.match_score})"):
            display_analysis_result(analysis, club_name)

def display_historical_analysis(analysis):
    """Display a historical analysis in an expandable format"""
    club_name = analysis["club_name"]
    match_score = analysis["match_score"]
    timestamp = analysis["analysis_timestamp"].strftime("%Y-%m-%d %H:%M")
    
    with st.expander(f"{club_name} - Score: {match_score} ({timestamp})"):
        # Strategy summary
        if "strategy_summary" in analysis:
            st.info(f"**Strategy:** {analysis['strategy_summary']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "networking_strategy" in analysis:
                st.markdown("**🤝 Networking Strategy:**")
                for strategy in analysis["networking_strategy"]:
                    st.markdown(f"• {strategy}")
            
            if "campus_resources" in analysis:
                st.markdown("**🏫 Campus Resources:**")
                for resource in analysis["campus_resources"]:
                    st.markdown(f"• {resource}")
        
        with col2:
            if "application_timeline" in analysis:
                st.markdown("**📅 Application Timeline:**")
                for timeline in analysis["application_timeline"]:
                    st.markdown(f"• {timeline}")
            
            if "preparation_steps" in analysis:
                st.markdown("**🎯 Preparation Steps:**")
                for step in analysis["preparation_steps"]:
                    st.markdown(f"• {step}")
        
        # Resume improvements (full width)
        if "improvements" in analysis:
            st.markdown("**📈 Resume Improvements:**")
            for improvement in analysis["improvements"]:
                st.markdown(f"• {improvement}")
        
        # Backward compatibility for old analyses
        if "strengths" in analysis:
            st.markdown("**✅ Strengths (Legacy):**")
            for strength in analysis["strengths"]:
                st.markdown(f"• {strength}")
        if "key_experiences" in analysis:
            st.markdown("**🔧 Key Experiences (Legacy):**")
            for experience in analysis["key_experiences"]:
                st.markdown(f"• {experience}")
        if "tailoring_suggestions" in analysis:
            st.markdown("**🎯 Tailoring Suggestions (Legacy):**")
            for suggestion in analysis["tailoring_suggestions"]:
                st.markdown(f"• {suggestion}")

def main():
    # Initialize session state for favorites using a persistent user ID
    if 'user_id' not in st.session_state:
        # Use a simple persistent identifier - could be enhanced with actual user authentication
        st.session_state.user_id = "default_user"
    
    if 'favorites_cache' not in st.session_state:
        st.session_state.favorites_cache = []
    
    if 'last_favorites_update' not in st.session_state:
        st.session_state.last_favorites_update = 0
    
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
    
    # Display favorites count
    user_favorites = get_user_favorites()
    favorites_count = len(user_favorites)
    if favorites_count > 0:
        st.sidebar.success(f"⭐ {favorites_count} favorite{'s' if favorites_count != 1 else ''}")
    
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
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Club Directory", "📊 Analytics", "📄 Resume Manager", "🤖 Resume Analysis"])

    with tab1:
        st.markdown("### Club Directory")
        
        if filtered_clubs:
            # Sort clubs: favorited clubs first, then alphabetical
            favorited_clubs = []
            non_favorited_clubs = []
            
            for club in filtered_clubs:
                club_name = club.get("Club Name", "Unknown Club")
                if club_name in user_favorites:
                    favorited_clubs.append(club)
                else:
                    non_favorited_clubs.append(club)
            
            # Sort each group alphabetically
            favorited_clubs.sort(key=lambda x: x.get("Club Name", ""))
            non_favorited_clubs.sort(key=lambda x: x.get("Club Name", ""))
            
            # Display favorited clubs first
            if favorited_clubs:
                st.markdown("### ⭐ Your Favorite Clubs")
                for club in favorited_clubs:
                    display_club_card(club)
                
                if non_favorited_clubs:
                    st.markdown('<div class="favorites-separator"><span>Other Clubs</span></div>', unsafe_allow_html=True)
            
            # Display non-favorited clubs
            for club in non_favorited_clubs:
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
    
    with tab4:
        create_resume_analysis_section(clubs_data)

if __name__ == "__main__":
    main()