import streamlit as st
import pandas as pd
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

def extract_trailblazer_data(profile_url):
    """
    Extract trailblazer data using API endpoints instead of HTML scraping
    """
    try:
        # Extract username from URL
        if '/trailblazer/' in profile_url:
            username = profile_url.split('/trailblazer/')[-1].strip('/')
        else:
            return {"status": "Invalid URL", "badges": [], "rank": "None"}
        
        # Try different API endpoints that Salesforce uses internally
        api_endpoints = [
            f"https://trailhead.salesforce.com/api/trailblazer/{username}",
            f"https://trailhead.salesforce.com/api/public/trailblazers/{username}",
            f"https://trailhead.salesforce.com/services/apexrest/trailhead-leaderboard/api/trailblazer/{username}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://trailhead.salesforce.com/'
        }
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return parse_api_response(data)
            except:
                continue
        
        # Fallback: Try to get basic profile info
        return get_basic_profile_info(profile_url)
        
    except Exception as e:
        return {"status": f"Error: {str(e)}", "badges": [], "rank": "Error"}

def parse_api_response(data):
    """Parse API response to extract badge information"""
    try:
        # This will vary based on the actual API structure
        badges = data.get('badges', [])
        rank = data.get('rank', {}).get('title', 'None')
        
        # Map ranks to levels
        rank_mapping = {
            'Hiker': 'Level 1',
            'Explorer': 'Level 2', 
            'Adventurer': 'Level 3',
            'Mountaineer': 'Level 4',
            'Expeditioner': 'Level 5'
        }
        
        return {
            "status": "Success",
            "badges": badges,
            "rank": rank,
            "level": rank_mapping.get(rank, "None")
        }
    except:
        return {"status": "Parse Error", "badges": [], "rank": "None"}

def get_basic_profile_info(url):
    """
    Simplified approach - just check if profile exists and is public
    """
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return {"status": "Profile Not Found", "rank": "None"}
        elif "This profile is private" in response.text:
            return {"status": "Private Profile", "rank": "None"}
        elif response.status_code == 200:
            # Profile exists and is public, but we can't determine badges
            return {"status": "Public Profile - Manual Verification Needed", "rank": "Unknown"}
        else:
            return {"status": f"HTTP {response.status_code}", "rank": "Error"}
            
    except Exception as e:
        return {"status": f"Connection Error: {str(e)}", "rank": "Error"}

def main():
    st.set_page_config(
        page_title="Salesforce Badge Checker - Fixed Version",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Salesforce Badge Checker - Working Version")
    
    st.warning("""
    **Important Notice**: Due to Salesforce's anti-scraping measures, automated badge detection is extremely limited. 
    This tool will:
    1. Verify if profiles exist and are public
    2. Attempt to extract basic information
    3. Provide manual verification suggestions
    """)
    
    # Sample working approach
    st.subheader("🧪 Test Single Profile First")
    
    test_url = st.text_input(
        "Test URL", 
        placeholder="https://www.salesforce.com/trailblazer/username",
        help="Test a single profile first to see what data is available"
    )
    
    if st.button("🔍 Test Single Profile") and test_url:
        with st.spinner("Testing profile..."):
            result = extract_trailblazer_data(test_url)
            st.json(result)
    
    st.divider()
    
    # File upload section
    st.subheader("📂 Batch Processing")
    
    uploaded_file = st.file_uploader("Choose CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Validate columns
        required_columns = ['Roll Number', 'Name', 'Salesforce URL']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing columns: {', '.join(missing_columns)}")
            return
        
        st.success(f"Loaded {len(df)} records")
        st.dataframe(df.head())
        
        if st.button("🚀 Process All Profiles"):
            progress_bar = st.progress(0)
            results = []
            
            for idx, row in df.iterrows():
                progress_bar.progress((idx + 1) / len(df))
                
                result = extract_trailblazer_data(row['Salesforce URL'])
                
                results.append({
                    'Roll Number': row['Roll Number'],
                    'Name': row['Name'],
                    'Salesforce URL': row['Salesforce URL'],
                    'Status': result['status'],
                    'Rank': result['rank'],
                    'Badge Status': result.get('level', 'Unknown')
                })
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            results_df = pd.DataFrame(results)
            
            st.subheader("📊 Results")
            st.dataframe(results_df)
            
            # Summary
            status_counts = results_df['Status'].value_counts()
            st.subheader("📈 Summary")
            for status, count in status_counts.items():
                st.metric(status, count)
            
            # Download
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                "📥 Download Results",
                csv_data,
                "badge_check_results.csv",
                "text/csv"
            )

if __name__ == "__main__":
    main()
