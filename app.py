import streamlit as st
import pandas as pd
import pickle
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
import time

class SalesforceAutomatedChecker:
    def __init__(self):
        self.driver = None
        self.cookies_file = "salesforce_cookies.pkl"
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with persistent session management"""
        options = Options()
        
        # CRITICAL: Use persistent user profile to maintain session
        profile_path = os.path.abspath("chrome_user_profile")
        options.add_argument(f"--user-data-dir={profile_path}")
        
        # Don't use headless mode
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Reduce automation detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def manual_login_and_save_session(self):
        """Manual login once to establish authenticated session"""
        try:
            self.driver.get("https://login.salesforce.com")
            st.info("🔐 **Complete login and MFA in the browser window that opened**")
            st.info("⏳ **After successful login, click 'Session Saved' below**")
            
            return True
            
        except Exception as e:
            st.error(f"Login setup failed: {str(e)}")
            return False
    
    def save_cookies(self):
        """Save current session cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, "wb") as file:
                pickle.dump(cookies, file)
            st.success("✅ **Session cookies saved successfully!**")
            return True
        except Exception as e:
            st.error(f"Cookie save failed: {str(e)}")
            return False
    
    def load_cookies(self):
        """Load saved session cookies"""
        try:
            if os.path.exists(self.cookies_file):
                # Must navigate to domain first before adding cookies
                self.driver.get("https://salesforce.com")
                time.sleep(3)
                
                with open(self.cookies_file, "rb") as file:
                    cookies = pickle.load(file)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception:
                        pass  # Skip invalid cookies
                
                # Refresh to apply cookies
                self.driver.refresh()
                time.sleep(5)
                
                return True
            else:
                st.warning("No saved session found - please login first")
                return False
                
        except Exception as e:
            st.error(f"Cookie load failed: {str(e)}")
            return False
    
    def check_if_logged_in(self):
        """Verify if session is authenticated"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Check for Salesforce authenticated indicators
            is_logged_in = any([
                "lightning" in current_url,
                "setup" in current_url,
                "one.app" in current_url,
                "home" in page_source,
                "my domain" in page_source
            ])
            
            return is_logged_in
            
        except Exception:
            return False
    
    def capture_profile_badge(self, profile_url):
        """Navigate to profile and capture badge area"""
        try:
            st.info(f"📸 Processing: {profile_url}")
            
            # Navigate to profile
            self.driver.get(profile_url)
            time.sleep(12)  # Wait for page load
            
            # Check for access issues
            page_source = self.driver.page_source.lower()
            if "access denied" in page_source or "login" in self.driver.current_url:
                return {
                    'success': False,
                    'error': 'Access denied or session expired',
                    'badge_image': None
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
                'badge_image': badge_area,
                'full_image': full_image,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'badge_image': None
            }
    
    def process_multiple_profiles(self, profile_data, progress_callback=None):
        """Process multiple profiles automatically"""
        results = []
        
        for idx, row in profile_data.iterrows():
            if progress_callback:
                progress_callback(idx + 1, len(profile_data), row['Name'])
            
            # Capture badge
            result = self.capture_profile_badge(row['Salesforce URL'])
            
            profile_result = {
                'Roll Number': row['Roll Number'],
                'Name': row['Name'],
                'Salesforce URL': row['Salesforce URL'],
                'success': result['success'],
                'error': result.get('error', ''),
                'badge_image': result.get('badge_image'),
                'full_image': result.get('full_image')
            }
            
            results.append(profile_result)
            
            # Delay between profiles
            time.sleep(4)
        
        return results
    
    def cleanup(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()

def main():
    st.set_page_config(
        page_title="Automated Badge Checker",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Automated Salesforce Badge Checker")
    st.success("✅ Login once, then automatically check all student profiles!")
    
    # Initialize checker
    if 'checker' not in st.session_state:
        st.session_state.checker = None
    
    # Step 1: Setup and Login
    st.subheader("🔑 Step 1: One-Time Authentication Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Setup Automated Session", type="primary"):
            try:
                with st.spinner("Setting up browser..."):
                    checker = SalesforceAutomatedChecker()
                    st.session_state.checker = checker
                
                if checker.manual_login_and_save_session():
                    st.info("👆 **Browser opened - complete login there**")
                
            except Exception as e:
                st.error(f"Setup failed: {str(e)}")
    
    with col2:
        if st.session_state.checker and st.button("💾 Save Session"):
            if st.session_state.checker.save_cookies():
                st.balloons()
                st.success("🎉 **Ready for automated processing!**")
    
    # Step 2: Automated Batch Processing
    if st.session_state.checker:
        st.divider()
        st.subheader("🤖 Step 2: Automated Batch Processing")
        
        uploaded_file = st.file_uploader("Upload Student CSV", type="csv")
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            required_cols = ['Roll Number', 'Name', 'Salesforce URL']
            if all(col in df.columns for col in required_cols):
                
                st.success(f"✅ Loaded {len(df)} student profiles")
                st.dataframe(df.head())
                
                # Processing settings
                col1, col2 = st.columns(2)
                
                with col1:
                    max_profiles = st.number_input("Profiles to process", 1, len(df), min(5, len(df)))
                
                with col2:
                    delay_seconds = st.slider("Delay between profiles (seconds)", 3, 15, 5)
                
                if st.button("🤖 Start Automated Processing", type="primary"):
                    
                    # Load saved session
                    with st.spinner("Loading saved session..."):
                        session_loaded = st.session_state.checker.load_cookies()
                    
                    if session_loaded:
                        st.success("✅ Session loaded - starting automated processing...")
                        
                        profiles_to_process = df.head(max_profiles)
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        results_container = st.empty()
                        
                        # Progress callback
                        def update_progress(current, total, name):
                            progress_bar.progress(current / total)
                            status_text.text(f"🤖 Automated processing {current}/{total}: {name}")
                        
                        # Process all profiles automatically
                        results = st.session_state.checker.process_multiple_profiles(
                            profiles_to_process,
                            progress_callback=update_progress
                        )
                        
                        # Display results
                        st.success("🎉 Automated processing completed!")
                        
                        final_results = []
                        
                        # Show results for manual verification
                        st.subheader("📊 Automated Results - Manual Verification")
                        
                        for idx, result in enumerate(results):
                            if result['success']:
                                col1, col2, col3 = st.columns([2, 2, 1])
                                
                                with col1:
                                    st.write(f"**{result['Name']}** (Roll: {result['Roll Number']})")
                                
                                with col2:
                                    if result['badge_image']:
                                        st.image(result['badge_image'], caption=f"Badge - {result['Name']}", width=200)
                                
                                with col3:
                                    manual_verification = st.selectbox(
                                        "Badge Level:",
                                        ["", "None", "Champion", "Innovator", "Legend"],
                                        key=f"verify_{idx}"
                                    )
                                    
                                    if manual_verification:
                                        final_results.append({
                                            'Roll Number': result['Roll Number'],
                                            'Name': result['Name'],
                                            'Salesforce URL': result['Salesforce URL'],
                                            'Badge Level': manual_verification,
                                            'Processing Status': 'Automated + Verified',
                                            'Method': 'Session Persistence'
                                        })
                            else:
                                final_results.append({
                                    'Roll Number': result['Roll Number'],
                                    'Name': result['Name'],
                                    'Salesforce URL': result['Salesforce URL'],
                                    'Badge Level': 'Error',
                                    'Processing Status': result['error'],
                                    'Method': 'Automated Failed'
                                })
                        
                        # Export results
                        if final_results:
                            results_df = pd.DataFrame(final_results)
                            
                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                processed = len(results_df)
                                st.metric("Total Processed", processed)
                            
                            with col2:
                                successful = len(results_df[results_df['Processing Status'] == 'Automated + Verified'])
                                st.metric("Successfully Processed", successful)
                            
                            with col3:
                                badges_found = len(results_df[results_df['Badge Level'].isin(['Champion', 'Innovator', 'Legend'])])
                                st.metric("Badges Found", badges_found)
                            
                            with col4:
                                success_rate = (successful / processed) * 100 if processed > 0 else 0
                                st.metric("Success Rate", f"{success_rate:.1f}%")
                            
                            st.dataframe(results_df)
                            
                            # Download
                            csv_data = results_df.to_csv(index=False)
                            st.download_button(
                                "📥 Download Automated Results",
                                csv_data,
                                f"automated_badge_results_{int(time.time())}.csv",
                                "text/csv"
                            )
                    
                    else:
                        st.error("❌ Session loading failed - please complete login setup first")
            
            else:
                st.error("❌ CSV must have columns: Roll Number, Name, Salesforce URL")
    
    # Cleanup section
    if st.session_state.checker:
        st.divider()
        
        if st.button("🔄 Reset and Cleanup"):
            st.session_state.checker.cleanup()
            st.session_state.checker = None
            st.success("✅ Session cleaned up")
            st.rerun()

if __name__ == "__main__":
    main()
