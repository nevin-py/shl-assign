"""
Streamlit Frontend for SHL Assessment Recommendation System
"""

import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-size: 1.1rem;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .result-card {
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)


def get_api_url():
    """Get API URL from environment or use default"""
    # For local development
    api_url = os.getenv("API_URL", "http://localhost:8000")
    return api_url


def check_api_health(api_url):
    """Check if the API is healthy"""
    try:
        st.write(f"🔍 Checking: {api_url}/health")
        response = requests.get(f"{api_url}/health", timeout=10)
        st.write(f"📡 Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy", data.get("message", "")
        return False, f"API returned {response.status_code}: {response.text[:200]}"
    except requests.exceptions.Timeout:
        return False, "Request timed out after 10 seconds"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {str(e)}"


def get_recommendations(api_url, query):
    """Get recommendations from the API"""
    try:
        st.write(f"🔍 Sending request to: {api_url}/recommend")
        response = requests.post(
            f"{api_url}/recommend",
            json={"query": query},
            timeout=90
        )
        
        st.write(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            return response.json().get("recommendations", []), None
        else:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text[:500]
            return None, f"API Error ({response.status_code}): {error_detail}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out after 90 seconds. The API may be initializing on first request."
    except requests.exceptions.ConnectionError as e:
        return None, f"Connection Error: Cannot reach API at {api_url}. {str(e)}"
    except Exception as e:
        return None, f"Request Error ({type(e).__name__}): {str(e)}"


def main():
    # Header
    st.markdown('<p class="main-header">🎯 SHL Assessment Recommendation System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Find the perfect assessments for your hiring needs</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.write("""
        This tool helps you find relevant SHL assessments based on:
        - **Natural language queries**
        - **Job description text**
        - **Job posting URLs**
        
        Simply enter your requirement and get 5-10 most relevant assessments!
        """)
        
        st.divider()
        
        # API Health Check
        st.header("🔌 API Status")
        api_url = get_api_url()
        st.code(f"API URL: {api_url}", language="text")
        
        if st.button("Check API Health"):
            with st.spinner("Checking API..."):
                is_healthy, message = check_api_health(api_url)
                if is_healthy:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ API Unhealthy: {message}")
        
        st.divider()
        
        # Sample Queries
        st.header("💡 Sample Queries")
        st.write("""
        - *I need a Java developer who can collaborate with teams*
        - *Looking for mid-level professionals proficient in Python, SQL and JavaScript*
        - *Need cognitive and personality tests for analyst role*
        """)
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("📝 Enter Your Query")
    
    # Input options
    input_type = st.radio(
        "Input Type:",
        ["Text Query / Job Description", "Job Posting URL"],
        horizontal=True
    )
    
    # Text input
    if input_type == "Text Query / Job Description":
        query = st.text_area(
            "Enter your query or paste job description:",
            height=150,
            placeholder="E.g., I am hiring for Java developers who can also collaborate effectively with my business teams."
        )
    else:
        query = st.text_input(
            "Enter job posting URL:",
            placeholder="https://example.com/job-posting"
        )
    
    # Search button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_clicked = st.button("🔍 Find Assessments", use_container_width=True)
    
    # Process query
    if search_clicked:
        if not query or len(query.strip()) == 0:
            st.error("⚠️ Please enter a query or URL")
        else:
            with st.spinner("🔄 Analyzing requirements and finding best assessments..."):
                recommendations, error = get_recommendations(api_url, query)
                
                if error:
                    st.error(f"❌ {error}")
                    st.info("💡 Make sure the API is running on the correct port")
                elif recommendations:
                    st.success(f"✅ Found {len(recommendations)} relevant assessments!")
                    
                    st.divider()
                    st.header("📊 Recommended Assessments")
                    
                    # Create DataFrame for table view
                    df = pd.DataFrame(recommendations)
                    # Rename 'name' to 'assessment_name' for consistent display
                    if 'name' in df.columns and 'assessment_name' not in df.columns:
                        df['assessment_name'] = df['name']
                        df = df.drop('name', axis=1)
                    df.index = range(1, len(df) + 1)
                    
                    # Display as interactive table
                    st.dataframe(
                        df,
                        column_config={
                            "assessment_name": st.column_config.TextColumn(
                                "Assessment Name",
                                width="medium"
                            ),
                            "url": st.column_config.LinkColumn(
                                "URL",
                                width="large",
                                display_text="View Assessment"
                            )
                        },
                        use_container_width=True,
                        hide_index=False
                    )
                    
                    st.divider()
                    
                    # Detailed view
                    st.subheader("📋 Detailed View")
                    for i, rec in enumerate(recommendations, 1):
                        # Handle both 'name' and 'assessment_name' keys for compatibility
                        assessment_name = rec.get('name') or rec.get('assessment_name', 'Unknown Assessment')
                        with st.expander(f"{i}. {assessment_name}", expanded=(i <= 3)):
                            st.markdown(f"**Assessment Name:** {assessment_name}")
                            st.markdown(f"**URL:** [{rec['url']}]({rec['url']})")
                            st.markdown("---")
                            st.markdown("Click the URL above to view full assessment details on SHL website")
                    
                    # Download results
                    st.divider()
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download Results as CSV",
                        data=csv,
                        file_name="shl_recommendations.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("⚠️ No recommendations found. Try a different query.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>Built with ❤️ using Streamlit, FastAPI, ChromaDB, and Google Gemini</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
