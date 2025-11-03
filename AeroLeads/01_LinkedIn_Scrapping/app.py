"""
LinkedIn Profile Scraper - Streamlit Frontend (Local MacBook Version)
WARNING: This application is for educational purposes only.
Using automated scraping violates LinkedIn's Terms of Service.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from config import Config
from scraper import run_scraper

# Page configuration
st.set_page_config(
    page_title="LinkedIn Profile Scraper",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and warning
st.title("🔍 LinkedIn Profile Scraper")
st.warning("⚠️ **Important**: This is for testing purpose only. LinkedIn does not allown automated scraping. Your accout may get suspended. Use a dummy account.")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# Check credentials
is_valid, cred_message = Config.validate_credentials()

if not is_valid:
    st.sidebar.error(cred_message)
    st.info("""
    ### Setup Instructions:
    
    1. Create a `.env` file in the project root
    2. Add your LinkedIn credentials:
       ```
       LINKEDIN_EMAIL=your.email@example.com
       LINKEDIN_PASSWORD=your_password
       ```
    3. Restart the application
    """)
    st.stop()
else:
    st.sidebar.success("✅ Credentials configured")

# Browser visibility option
st.sidebar.subheader("🌐 Browser Settings")
visible_browser = st.sidebar.checkbox(
    "Show Browser Window",
    value=True,
    help="Visible browser is more reliable and lets you solve CAPTCHAs manually"
)

if visible_browser:
    st.sidebar.info("✅ Browser will be visible - you can watch the scraping process and solve CAPTCHAs if needed")
else:
    st.sidebar.warning("⚠️ Headless mode - may trigger more security challenges")

# Filters
st.sidebar.subheader("🔍 Search Filters")

# Location filter
location_options = [
    "",  # No filter
    "United States",
    "United Kingdom",
    "India",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "Singapore",
    "Netherlands",
    "Custom"
]
location = st.sidebar.selectbox("📍 Location", location_options)

if location == "Custom":
    location = st.sidebar.text_input("Enter custom location", "")

# Industry/Domain filter
industry_options = [
    "",  # No filter
    "Technology",
    "Software Development",
    "Finance",
    "Healthcare",
    "Marketing",
    "Sales",
    "Education",
    "Consulting",
    "Manufacturing",
    "Retail",
    "Custom"
]
industry = st.sidebar.selectbox("💼 Industry/Domain", industry_options)

if industry == "Custom":
    industry = st.sidebar.text_input("Enter custom industry", "")

# Number of profiles
num_profiles = st.sidebar.slider(
    "📊 Number of Profiles",
    min_value=1,
    max_value=Config.MAX_PROFILES_LIMIT,
    value=Config.DEFAULT_PROFILES_TO_SCRAPE,
    help=f"Maximum {Config.MAX_PROFILES_LIMIT} profiles recommended"
)

# Initialize session state
if 'scraping' not in st.session_state:
    st.session_state.scraping = False
if 'profiles_data' not in st.session_state:
    st.session_state.profiles_data = None

# Progress tracking
def update_progress(current, total, message):
    """Update progress in Streamlit"""
    if total > 0:
        progress = current / total
        st.session_state.progress_bar.progress(progress)
    st.session_state.status_text.text(message)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Scraping Configuration")
    
    # Display current settings
    settings_df = pd.DataFrame({
        "Setting": ["Location", "Industry", "Number of Profiles", "Browser Mode"],
        "Value": [
            location if location else "Any",
            industry if industry else "Any",
            str(num_profiles),
            "Visible" if visible_browser else "Headless"
        ]
    })
    st.table(settings_df)

with col2:
    st.subheader("ℹ️ Information")
    st.info("""
    **Data Fields Collected:**
    - Name
    - Headline
    - Location
    - Current Company
    - Current Position
    """)

# Scraping section
st.markdown("---")
st.subheader("🚀 Start Scraping")

if visible_browser:
    st.info("💡 **Tip**: A Chrome browser window will open. If you see a CAPTCHA, solve it manually and the scraper will continue automatically.")

# Start scraping button
start_button = st.button(
    "▶️ Start Scraping",
    disabled=st.session_state.scraping,
    type="primary",
    use_container_width=True
)

if start_button:
    st.session_state.scraping = True
    st.session_state.profiles_data = None
    
    # Create progress elements
    st.session_state.progress_bar = st.progress(0)
    st.session_state.status_text = st.empty()
    
    # Run scraper
    try:
        with st.spinner("Initializing browser..."):
            success, message, profiles_data = run_scraper(
                email=Config.LINKEDIN_EMAIL,
                password=Config.LINKEDIN_PASSWORD,
                location=location,
                industry=industry,
                max_profiles=num_profiles,
                progress_callback=update_progress,
                visible=visible_browser
            )
        
        st.session_state.scraping = False
        
        if success:
            st.success(message)
            st.session_state.profiles_data = profiles_data
            
            # Display results
            st.subheader("📊 Scraped Profiles")
            df = pd.DataFrame(profiles_data)
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"linkedin_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
            
            # Statistics
            st.subheader("📈 Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Profiles", len(profiles_data))
            with col2:
                profiles_with_company = sum(1 for p in profiles_data if p.get('current_company'))
                st.metric("With Company Info", profiles_with_company)
            with col3:
                profiles_with_location = sum(1 for p in profiles_data if p.get('location'))
                st.metric("With Location Info", profiles_with_location)
        else:
            st.error(f"❌ {message}")
            
    except Exception as e:
        st.session_state.scraping = False
        st.error(f"❌ An error occurred: {str(e)}")

# Display previously scraped data if available
elif st.session_state.profiles_data:
    st.subheader("📊 Previously Scraped Profiles")
    df = pd.DataFrame(st.session_state.profiles_data)
    st.dataframe(df, use_container_width=True)
    
    # Download button
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_data,
        file_name=f"linkedin_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>
        <strong>Running on your MacBook - Chrome browser will open visibly for more reliable scraping.</strong>
    </small>
</div>
""", unsafe_allow_html=True)
