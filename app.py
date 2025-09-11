import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse
import time
import json

class TrailheadBadgeAPI:
    """Class to interact with Trailhead badge APIs"""
    
    def __init__(self):
        # Multiple API endpoints to try
        self.api_endpoints = [
            "https://trailheadbadges-api.herokuapp.com",
            "https://api.trailhead.com/v1",
            "https://trailhead.salesforce.com/api/v1"
        ]
        
    def extract_username_from_url(self, profile_url):
        """Extract username from Salesforce profile URL"""
        try:
            if '/trailblazer/' in profile_url:
                return profile_url.split('/trailblazer/')[-1].strip('/')
            elif '/id/' in profile_url:
                return profile_url.split('/id/')[-1].strip('/')
            return None
        except:
            return None
    
    def check_trailhead_api_v1(self, username):
        """Try the unofficial Trailhead Badges API"""
        try:
            url = f"{self.api_endpoints[0]}/users/search/findByTrailheadId"
            params = {"trailheadId": username}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                badges = data.get('badges', [])
                
                # Look for agentblazer badges
                agentblazer_badges = []
                for badge in badges:
                    badge_info = badge.get('badge', {})
                    href = badge_info.get('href', '').lower()
                    title = badge_info.get('title', '').lower()
                    
                    if 'agentblazer' in href or 'agentblazer' in title:
                        agentblazer_badges.append({
                            'href': href,
                            'title': title,
                            'badge': badge_info
                        })
                
                # Determine highest badge level
                if agentblazer_badges:
                    for badge in agentblazer_badges:
                        href = badge['href']
                        title = badge['title']
                        
                        if 'legend' in href or 'legend' in title:
                            return {'badge_level': 'Legend', 'method': 'API v1', 'status': 'Success'}
                        elif 'innovator' in href or 'innovator' in title:
                            return {'badge_level': 'Innovator', 'method': 'API v1', 'status': 'Success'}
                        elif 'champion' in href or 'champion' in title:
                            return {'badge_level': 'Champion', 'method': 'API v1', 'status': 'Success'}
                
                return {'badge_level': 'None', 'method': 'API v1', 'status': 'No Agentblazer Badge'}
                
            else:
                return {'badge_level': 'Error', 'method': 'API v1', 'status': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'badge_level': 'Error', 'method': 'API v1', 'status': f'Exception: {str(e)}'}
    
    def check_profile_direct_api(self, username):
        """Try direct profile API approach"""
        try:
            # Try different profile API patterns
            api_patterns = [
                f"https://trailhead.salesforce.com/en/me/{username}",
                f"https://api.trailhead.com/users/{username}/badges",
                f"https://trailhead.salesforce.com/api/users/{username}"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            for api_url in api_patterns:
                try:
                    response = requests.get(api_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Try to parse as JSON
                        try:
                            data = response.json()
                            
                            # Look for badge information in response
                            if isinstance(data, dict):
                                badges = data.get('badges', [])
                                achievements = data.get('achievements', [])
                                
                                # Check badges array
                                for badge in badges:
                                    if isinstance(badge, dict):
                                        name = badge.get('name', '').lower()
                                        type_field = badge.get('type', '').lower()
                                        
                                        if 'agentblazer' in name or 'agentblazer' in type_field:
                                            if 'legend' in name:
                                                return {'badge_level': 'Legend', 'method': 'Direct API', 'status': 'Success'}
                                            elif 'innovator' in name:
                                                return {'badge_level': 'Innovator', 'method': 'Direct API', 'status': 'Success'}
                                            elif 'champion' in name:
                                                return {'badge_level': 'Champion', 'method': 'Direct API', 'status': 'Success'}
                        
                        except json.JSONDecodeError:
                            # If not JSON, check HTML content for badge references
                            content = response.text.lower()
                            if 'agentblazer' in content:
                                if 'banner-level-3' in content or 'agentblazer legend' in content:
                                    return {'badge_level': 'Legend', 'method': 'HTML Content', 'status': 'Success'}
                                elif 'banner-level-2' in content or 'agentblazer innovator' in content:
                                    return {'badge_level': 'Innovator', 'method': 'HTML Content', 'status': 'Success'}
                                elif 'banner-level-1' in content or 'agentblazer champion' in content:
                                    return {'badge_level': 'Champion', 'method': 'HTML Content', 'status': 'Success'}
                
                except requests.RequestException:
                    continue
            
            return {'badge_level': 'None', 'method': 'Direct API', 'status': 'No API access'}
            
        except Exception as e:
            return {'badge_level': 'Error', 'method': 'Direct API', 'status': f'Exception: {str(e)}'}
    
    def get_badge_status(self, profile_url):
        """Main method to get badge status using multiple API approaches"""
        username = self.extract_username_from_url(profile_url)
        
        if not username:
            return {'badge_level': 'Error', 'method': 'URL parsing', 'status': 'Invalid URL format'}
        
        # Try Method 1: Unofficial API
        result1 = self.check_trailhead_api_v1(username)
        if result1['status'] == 'Success':
            return result1
        
        # Try Method 2: Direct API
        result2 = self.check_profile_direct_api(username)
        if result2['status'] == 'Success':
            return result2
        
        # Return best available result
        if result1['badge_level'] != 'Error':
            return result1
        else:
            return result2

def main():
    st.set_page_config(
        page_title="Salesforce API Badge Detector",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 Salesforce API Badge Detector")
    st.success("✅ Using Salesforce APIs for badge detection!")
    
    # Initialize API client
    api_client = TrailheadBadgeAPI()
    
    # Display API endpoints being used
    with st.expander("🔍 API Endpoints"):
        st.write("**Trying these API endpoints:**")
        for i, endpoint in enumerate(api_client.api_endpoints, 1):
            st.write(f"{i}. `{endpoint}`")
    
    # Single profile test
    st.subheader("🧪 Test API Badge Detection")
    
    profile_url = st.text_input(
        "Salesforce Profile URL:",
        value="https://www.salesforce.com/trailblazer/aarathisreeballa",
        placeholder="https://www.salesforce.com/trailblazer/username"
    )
    
    if st.button("🔗 Check Badge via API", type="primary"):
        if profile_url:
            with st.spinner("Querying Salesforce APIs..."):
                result = api_client.get_badge_status(profile_url)
            
            if result['status'] == 'Success':
                st.success(f"🎉 **Badge Detected: {result['badge_level']}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 API Response")
                    st.write(f"**Badge Level:** {result['badge_level']}")
                    st.write(f"**Detection Method:** {result['method']}")
                    st.write(f"**Status:** {result['status']}")
                
                with col2:
                    st.subheader("✅ Verification")
                    st.info("Badge detected successfully via API!")
                    
                    # Show badge image if possible
                    badge_images = {
                        'Champion': 'https://trailhead.salesforce.com/agentblazer/banner-level-1.png',
                        'Innovator': 'https://trailhead.salesforce.com/agentblazer/banner-level-2.png',
                        'Legend': 'https://trailhead.salesforce.com/agentblazer/banner-level-3.png'
                    }
                    
                    if result['badge_level'] in badge_images:
                        try:
                            st.image(badge_images[result['badge_level']], 
                                   caption=f"Agentblazer {result['badge_level']}", 
                                   width=250)
                        except:
                            pass
            
            else:
                st.warning(f"⚠️ {result['status']}")
                st.write(f"**Badge Level:** {result['badge_level']}")
                st.write(f"**Method:** {result['method']}")
                
                if result['badge_level'] == 'None':
                    st.info("✅ API worked, but no Agentblazer badge found for this profile")
                elif result['badge_level'] == 'Error':
                    st.error("❌ API request failed - check profile URL or API availability")
    
    # Batch processing
    st.divider()
    st.subheader("📂 Bulk API Processing")
    
    uploaded_file = st.file_uploader("Upload CSV with profiles", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} profiles")
            st.dataframe(df.head())
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                max_profiles = st.number_input("Max profiles to process", 1, len(df), min(10, len(df)))
            
            with col2:
                delay = st.slider("Delay between API calls (seconds)", 1, 10, 2)
            
            if st.button("🚀 Process All via API", type="primary"):
                
                profiles_to_process = df.head(max_profiles)
                
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, row in profiles_to_process.iterrows():
                    progress = (idx + 1) / len(profiles_to_process)
                    progress_bar.progress(progress)
                    status_text.text(f"API processing {idx+1}/{len(profiles_to_process)}: {row['Name']}")
                    
                    # Get badge via API
                    result = api_client.get_badge_status(row['Salesforce URL'])
                    
                    results.append({
                        'Roll Number': row['Roll Number'],
                        'Name': row['Name'],
                        'Salesforce URL': row['Salesforce URL'],
                        'Badge Level': result['badge_level'],
                        'Detection Method': result['method'],
                        'API Status': result['status']
                    })
                    
                    # Delay between API calls
                    if idx < len(profiles_to_process) - 1:
                        time.sleep(delay)
                
                # Display results
                results_df = pd.DataFrame(results)
                
                st.success("🎉 API processing completed!")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Processed", len(results_df))
                
                with col2:
                    successful = len(results_df[results_df['API Status'] == 'Success'])
                    st.metric("API Success", successful)
                
                with col3:
                    badges_found = len(results_df[results_df['Badge Level'].isin(['Champion', 'Innovator', 'Legend'])])
                    st.metric("Badges Found", badges_found)
                
                with col4:
                    api_success_rate = (successful / len(results_df)) * 100 if len(results_df) > 0 else 0
                    st.metric("Success Rate", f"{api_success_rate:.1f}%")
                
                # Results table
                st.subheader("📊 API Results")
                st.dataframe(results_df, use_container_width=True)
                
                # Badge distribution
                badge_counts = results_df['Badge Level'].value_counts()
                if not badge_counts.empty:
                    st.subheader("📈 Badge Distribution")
                    st.bar_chart(badge_counts)
                
                # Download results
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📥 Download API Results",
                    csv_data,
                    f"api_badge_results_{int(time.time())}.csv",
                    "text/csv",
                    type="primary"
                )
        
        else:
            st.error("❌ CSV must have columns: Roll Number, Name, Salesforce URL")
    
    # API Status & Information
    st.divider()
    
    with st.expander("ℹ️ API Information & Troubleshooting"):
        st.markdown("""
        ### **API Endpoints Used:**
        1. **Unofficial Trailhead API**: `trailheadbadges-api.herokuapp.com`
        2. **Direct Profile APIs**: Various Salesforce endpoints
        3. **HTML Content Analysis**: Fallback parsing
        
        ### **Expected Results:**
        - **Success**: Badge level detected via API
        - **None**: API worked, no Agentblazer badge found
        - **Error**: API unavailable or profile inaccessible
        
        ### **Troubleshooting:**
        - **High error rate**: APIs may be down or rate-limited
        - **"None" results**: Profile may be private or no badge earned
        - **Slow processing**: APIs may have rate limits
        
        ### **Advantages of API Approach:**
        - ✅ **No browser automation** required
        - ✅ **Faster processing** than scraping
        - ✅ **More reliable** than Shadow DOM extraction
        - ✅ **Less likely to be blocked** than scraping
        """)

if __name__ == "__main__":
    main()
