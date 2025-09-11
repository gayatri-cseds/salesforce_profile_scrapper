import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import os

class WorkingSalesforceLogin:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome with persistent user profile for session management"""
        options = Options()
        
        # CRITICAL: Use persistent user profile to save session
        profile_path = os.path.abspath("chrome_user_profile")
        options.add_argument(f"--user-data-dir={profile_path}")
        
        # DON'T use headless mode - it gets detected
        # options.add_argument("--headless")  # COMMENTED OUT
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Reduce automation detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Use webdriver-manager for compatibility
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def manual_login_with_mfa(self, username, password):
        """Interactive login that handles MFA manually"""
        try:
            # Navigate to Salesforce login
            self.driver.get("https://login.salesforce.com")
            time.sleep(3)
            
            # Check if already logged in
            if self.check_already_logged_in():
                return True
            
            # Fill credentials
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login
            login_button = self.driver.find_element(By.ID, "Login")
            login_button.click()
            
            # Wait and provide instructions for manual MFA
            st.info("🔐 **Complete MFA/2FA manually in the browser window that opened**")
            st.info("⏳ **After completing MFA, click 'Check Login Status' below**")
            
            return "MFA_REQUIRED"
            
        except Exception as e:
            st.error(f"Login failed: {str(e)}")
            return False
    
    def check_already_logged_in(self):
        """Check if already logged in to Salesforce"""
        current_url = self.driver.current_url
        return any(keyword in current_url for keyword in ["lightning", "setup", "one.app", "salesforce.com/"])
    
    def check_login_success(self):
        """Check if login was successful after MFA"""
        time.sleep(5)  # Wait for page to load
        
        if self.check_already_logged_in():
            st.success("✅ **Successfully logged in to Salesforce!**")
            st.success("🎉 **Session saved - future runs won't require MFA**")
            return True
        else:
            st.warning("⚠️ **Still on login page - please complete MFA and try again**")
            return False
    
    def navigate_to_profile(self, profile_url):
        """Navigate to a profile page using authenticated session"""
        try:
            if not self.check_already_logged_in():
                st.error("❌ Not logged in - please login first")
                return False
            
            self.driver.get(profile_url)
            time.sleep(10)  # Wait for page load
            
            return True
            
        except Exception as e:
            st.error(f"Navigation failed: {str(e)}")
            return False
    
    def cleanup(self):
        """Cleanup driver"""
        if self.driver:
            self.driver.quit()

def main():
    st.set_page_config(
        page_title="Working Salesforce Login",
        page_icon="🔐",
        layout="wide"
    )
    
    st.title("🔐 Working Salesforce Login Solution")
    
    # Important instructions
    with st.expander("📋 How This Works", expanded=True):
        st.markdown("""
        **This solution handles Salesforce's security requirements:**
        
        1. **Manual MFA Completion** - You complete 2FA manually once
        2. **Session Persistence** - Browser saves your login session
        3. **No Re-authentication** - Future runs use saved session
        4. **Visible Browser** - Reduces automation detection
        
        **Steps:**
        1. Enter credentials and click "Login with Manual MFA"
        2. Complete MFA in the browser window that opens
        3. Click "Check Login Status" after completing MFA
        4. Use "Test Profile Navigation" to verify it works
        """)
    
    # Initialize session manager
    if 'login_manager' not in st.session_state:
        st.session_state.login_manager = None
    
    # Login Section
    st.subheader("🔑 Salesforce Authentication")
    
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input(
            "Salesforce Username:",
            help="Your Salesforce login email"
        )
        password = st.text_input(
            "Salesforce Password:",
            type="password"
        )
    
    with col2:
        if st.button("🔐 Login with Manual MFA", type="primary"):
            if username and password:
                try:
                    with st.spinner("Setting up browser session..."):
                        login_manager = WorkingSalesforceLogin()
                        st.session_state.login_manager = login_manager
                    
                    with st.spinner("Navigating to login page..."):
                        result = login_manager.manual_login_with_mfa(username, password)
                    
                    if result == "MFA_REQUIRED":
                        st.info("👆 **Browser window opened - complete MFA there**")
                    elif result:
                        st.success("✅ Login successful!")
                    
                except Exception as e:
                    st.error(f"Setup failed: {str(e)}")
            else:
                st.error("Please enter username and password")
        
        # Check login status after MFA
        if st.session_state.login_manager and st.button("✅ Check Login Status"):
            if st.session_state.login_manager.check_login_success():
                st.balloons()
    
    # Test navigation
    if st.session_state.login_manager:
        st.divider()
        st.subheader("🧪 Test Profile Navigation")
        
        test_url = st.text_input(
            "Test Profile URL:",
            value="https://trailhead.salesforce.com/profile/aarathisreeballa",
            help="Enter a Salesforce profile URL to test navigation"
        )
        
        if st.button("🌐 Navigate to Profile"):
            if test_url:
                with st.spinner("Navigating to profile..."):
                    success = st.session_state.login_manager.navigate_to_profile(test_url)
                
                if success:
                    st.success("✅ **Navigation successful!**")
                    st.info("📸 You can now take screenshots or extract data")
                else:
                    st.error("❌ Navigation failed")
    
    # Cleanup section
    if st.session_state.login_manager:
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reset Session"):
                st.session_state.login_manager.cleanup()
                st.session_state.login_manager = None
                st.success("✅ Session reset - you can login again")
                st.rerun()
        
        with col2:
            st.info("**Session Status:** Active and ready for profile navigation")

if __name__ == "__main__":
    main()
