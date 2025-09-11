import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO
import time
import pickle
import os

class SalesforceSessionManager:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with session persistence"""
        options = Options()
        
        # Use persistent user data directory to save session
        options.add_argument("--user-data-dir=./chrome_profile")
        
        # Don't use headless to avoid detection
        # options.add_argument("--headless")  # Commented out
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def login_salesforce(self, username, password):
        """Login to Salesforce and maintain session"""
        try:
            self.driver.get("https://login.salesforce.com")
            time.sleep(3)
            
            # Check if already logged in
            if "lightning" in self.driver.current_url or "setup" in self.driver.current_url:
                st.success("✅ Already logged in to Salesforce!")
                return True
            
            # Perform login
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.ID, "Login")
            login_button.click()
            
            # Wait for login to complete (handle 2FA manually if needed)
            time.sleep(15)
            
            # Check if login successful
            if "lightning" in self.driver.current_url or "setup" in self.driver.current_url:
                st.success("✅ Successfully logged in to Salesforce!")
                return True
            else:
                st.error("❌ Login failed - check credentials or complete 2FA manually")
                return False
                
        except Exception as e:
            st.error(f"Login error: {str(e)}")
            return False
    
    def save_session(self):
        """Save session cookies for reuse"""
        cookies = self.driver.get_cookies()
        with open("session_cookies.pkl", "wb") as file:
            pickle.dump(cookies, file)
        st.info("💾 Session saved")
    
    def load_session(self):
        """Load saved session cookies"""
        try:
            if os.path.exists("session_cookies.pkl"):
                with open("session_cookies.pkl", "rb") as file:
                    cookies = pickle.load(file)
                
                self.driver.get("https://salesforce.com")
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass  # Skip invalid cookies
                
                st.info("🔄 Session loaded from cookies")
                return True
        except Exception as e:
            st.warning(f"Could not load session: {str(e)}")
        
        return False
    
    def capture_profile_badge(self, profile_url):
        """Navigate to profile and capture badge area"""
        try:
            # Navigate to profile
            self.driver.get(profile_url)
            time.sleep(10)  # Wait for page load
            
            # Check for access denied
            if "access denied" in self.driver.page_source.lower():
                return {
                    'success': False,
                    'error': 'Access Denied - Profile may be private or requires different permissions'
                }
            
            # Take full screenshot
            screenshot_png = self.driver.get_screenshot_as_png()
            full_image = Image.open(BytesIO(screenshot_png))
            
            # Crop badge area (bottom-right corner)
            img_width, img_height = full_image.size
            
            left = img_width - 500   # 500px from right
            upper = img_height - 300 # 300px from bottom
            right = img_width
            lower = img_height
            
            badge_area = full_image.crop((left, upper, right, lower))
            
            return {
                'success': True,
                'full_image': full_image,
                'badge_image': badge_area,
                'crop_coordinates': (left, upper, right, lower)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_multiple_profiles(self, profile_urls, progress_callback=None):
        """Process multiple profiles maintaining the same session"""
        results = []
        
        for idx, url in enumerate(profile_urls):
            if progress_callback:
                progress_callback(idx + 1, len(profile_urls), url)
            
            result = self.capture_profile_badge(url)
            
            profile_result = {
                'profile_url': url,
                'success': result['success'],
                'error': result.get('error', ''),
                'badge_image': result.get('badge_image'),
                'full_image': result.get('full_image')
            }
            
            results.append(profile_result)
            
            # Small delay between profiles
            time.sleep(3)
        
        return results
    
    def cleanup(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()

def main():
    st.set_page_config(
        page_title="Authenticated Badge Detector",
        page_icon="🔐",
        layout="wide"
    )
    
    st.title("🔐 Authenticated Salesforce Badge Detector")
    st.success("✅ Login once, then process multiple profiles with maintained session!")
    
    # Initialize session manager
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = None
    
    # Login Section
    st.subheader("🔑 Salesforce Authentication")
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Salesforce Username:", help="Your Salesforce login email")
        password = st.text_input("Salesforce Password:", type="password")
    
    with col2:
        if st.button("🔐 Login to Salesforce"):
            if username and password:
                with st.spinner("Logging into Salesforce..."):
                    session_manager = SalesforceSessionManager()
                    
                    if session_manager.login_salesforce(username, password):
                        st.session_state.session_manager = session_manager
                        session_manager.save_session()
                    else:
                        session_manager.cleanup()
        
        if st.button("🔄 Load Saved Session"):
            session_manager = SalesforceSessionManager()
            if session_manager.load_session():
                st.session_state.session_manager = session_manager
            else:
                session_manager.cleanup()
    
    # Display login status
    if st.session_state.session_manager:
        st.success("✅ Authenticated session active!")
        
        # Single profile test
        st.subheader("🧪 Test Single Profile")
        
        test_url = st.text_input(
            "Test Profile URL:",
            value="https://trailhead.salesforce.com/profile/aarathisreeballa",
            help="Enter a Salesforce Trailblazer profile URL"
        )
        
        if st.button("📸 Capture Badge Area"):
            if test_url:
                with st.spinner("Capturing badge area..."):
                    result = st.session_state.session_manager.capture_profile_badge(test_url)
                
                if result['success']:
                    st.success("✅ Badge area captured!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🖼️ Full Screenshot")
                        display_full = result['full_image'].copy()
                        display_full.thumbnail((600, 400))
                        st.image(display_full, caption="Full Profile Page")
                    
                    with col2:
                        st.subheader("🎯 Badge Area")
                        st.image(result['badge_image'], caption="Agentblazer Badge Area")
                        
                        # Manual verification
                        badge_level = st.selectbox(
                            "What badge do you see?",
                            ["", "None", "Champion", "Innovator", "Legend"]
                        )
                        
                        if badge_level:
                            st.success(f"✅ Verified: {badge_level}")
                
                else:
                    st.error(f"❌ Failed: {result['error']}")
        
        # Batch processing
        st.divider()
        st.subheader("📂 Batch Profile Processing")
        
        uploaded_file = st.file_uploader("Upload CSV with profile URLs", type="csv")
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            required_cols = ['Roll Number', 'Name', 'Salesforce URL']
            if all(col in df.columns for col in required_cols):
                
                st.success(f"✅ Loaded {len(df)} profiles")
                st.dataframe(df.head())
                
                # Processing options
                col1, col2 = st.columns(2)
                
                with col1:
                    max_profiles = st.number_input("Profiles to process", 1, len(df), min(5, len(df)))
                
                with col2:
                    delay_seconds = st.slider("Delay between profiles (seconds)", 2, 10, 3)
                
                if st.button("🚀 Process All Profiles", type="primary"):
                    
                    profiles_to_process = df.head(max_profiles)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Progress callback
                    def update_progress(current, total, url):
                        progress_bar.progress(current / total)
                        status_text.text(f"Processing {current}/{total}: {url}")
                    
                    with st.spinner("Processing profiles with authenticated session..."):
                        results = st.session_state.session_manager.process_multiple_profiles(
                            profiles_to_process['Salesforce URL'].tolist(),
                            progress_callback=update_progress
                        )
                    
                    # Display results
                    st.success("🎉 Batch processing completed!")
                    
                    final_results = []
                    
                    for idx, result in enumerate(results):
                        row = profiles_to_process.iloc[idx]
                        
                        if result['success']:
                            col1, col2, col3 = st.columns([2, 2, 1])
                            
                            with col1:
                                st.write(f"**{row['Name']}** (Roll: {row['Roll Number']})")
                            
                            with col2:
                                if result['badge_image']:
                                    st.image(result['badge_image'], caption=f"Badge - {row['Name']}", width=200)
                            
                            with col3:
                                manual_badge = st.selectbox(
                                    "Badge:",
                                    ["", "None", "Champion", "Innovator", "Legend"],
                                    key=f"batch_badge_{idx}"
                                )
                                
                                if manual_badge:
                                    final_results.append({
                                        'Roll Number': row['Roll Number'],
                                        'Name': row['Name'],
                                        'Salesforce URL': row['Salesforce URL'],
                                        'Badge Level': manual_badge,
                                        'Status': 'Verified'
                                    })
                        else:
                            final_results.append({
                                'Roll Number': row['Roll Number'],
                                'Name': row['Name'],
                                'Salesforce URL': row['Salesforce URL'],
                                'Badge Level': 'Error',
                                'Status': result['error']
                            })
                    
                    # Export results
                    if final_results:
                        results_df = pd.DataFrame(final_results)
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            successful = len(results_df[results_df['Status'] == 'Verified'])
                            st.metric("Successfully Processed", successful)
                        
                        with col2:
                            badges_found = len(results_df[results_df['Badge Level'].isin(['Champion', 'Innovator', 'Legend'])])
                            st.metric("Badges Found", badges_found)
                        
                        with col3:
                            errors = len(results_df[results_df['Badge Level'] == 'Error'])
                            st.metric("Errors", errors)
                        
                        st.dataframe(results_df)
                        
                        # Download
                        csv_data = results_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Results",
                            csv_data,
                            f"authenticated_badge_results_{int(time.time())}.csv",
                            "text/csv"
                        )
            
            else:
                st.error("❌ CSV must have: Roll Number, Name, Salesforce URL")
    
    else:
        st.info("👆 Please login to Salesforce to start processing profiles")
    
    # Instructions
    st.divider()
    
    with st.expander("🔧 Setup Instructions"):
        st.markdown("""
        ### **Key Advantages of This Approach:**
        
        ✅ **Single Login** - Authenticate once, process multiple profiles  
        ✅ **Session Persistence** - Maintain login across profile visits  
        ✅ **No Access Denied** - Authenticated access to profile pages  
        ✅ **Batch Processing** - Handle entire class rosters efficiently  
        ✅ **Visual Verification** - See actual badge screenshots for confirmation  
        
        ### **How It Works:**
        
        1. **Login Once** - Enter your Salesforce credentials
        2. **Maintain Session** - Browser keeps authentication cookies
        3. **Navigate Profiles** - Visit each profile URL without re-login
        4. **Capture Screenshots** - Take badge area screenshots
        5. **Manual Verification** - Faculty verifies badges from screenshots
        6. **Export Results** - Download complete badge report
        
        ### **Requirements:**
        
        - **Salesforce Account** with access to view student profiles
        - **Chrome Browser** with matching ChromeDriver
        - **2FA Handling** - Complete manually during first login
        
        ### **Troubleshooting:**
        
        - **Login Issues**: Check credentials and complete 2FA manually
        - **Access Denied**: Ensure your account has permission to view profiles  
        - **Session Expires**: Re-login if you get logged out
        - **Rate Limiting**: Increase delays between profile requests
        """)
    
    # Cleanup on app close
    if st.session_state.session_manager and st.button("🔄 Logout & Cleanup"):
        st.session_state.session_manager.cleanup()
        st.session_state.session_manager = None
        st.success("✅ Session cleaned up")

if __name__ == "__main__":
    main()
