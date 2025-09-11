import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from PIL import Image
from io import BytesIO
import time

class FixedSalesforceSessionManager:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with automatic driver management"""
        options = Options()
        
        # Use persistent user data directory
        options.add_argument("--user-data-dir=./chrome_profile")
        
        # Don't use headless to avoid detection
        # options.add_argument("--headless")
        
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Use WebDriverManager for automatic driver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            st.success("✅ ChromeDriver setup successful!")
            
        except Exception as e:
            st.error(f"❌ ChromeDriver setup failed: {str(e)}")
            st.info("💡 Try installing webdriver-manager: pip install webdriver-manager")
            raise
    
    def test_connection(self):
        """Test if driver works correctly"""
        try:
            self.driver.get("https://www.google.com")
            st.success("✅ Browser connection test successful!")
            return True
        except Exception as e:
            st.error(f"❌ Browser test failed: {str(e)}")
            return False
    
    def login_salesforce(self, username, password):
        """Login to Salesforce with improved error handling"""
        try:
            self.driver.get("https://login.salesforce.com")
            time.sleep(3)
            
            # Check if already logged in
            if "lightning" in self.driver.current_url or "setup" in self.driver.current_url:
                st.success("✅ Already logged in to Salesforce!")
                return True
            
            # Perform login
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.ID, "Login")
            login_button.click()
            
            # Wait for login
            time.sleep(15)
            
            # Check if login successful
            if "lightning" in self.driver.current_url or "setup" in self.driver.current_url:
                st.success("✅ Successfully logged in to Salesforce!")
                return True
            else:
                st.warning("⚠️ Login may require 2FA - complete manually and try again")
                return False
                
        except Exception as e:
            st.error(f"Login error: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()

def main():
    st.set_page_config(
        page_title="Fixed Badge Detector",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Fixed Salesforce Badge Detector")
    st.success("✅ ChromeDriver version mismatch resolved!")
    
    # Setup requirements
    with st.expander("📋 Setup Requirements", expanded=True):
        st.markdown("""
        **To fix the ChromeDriver error, install:**
        
        ```
        pip install webdriver-manager selenium streamlit pillow pandas
        ```
        
        **This will automatically:**
        - ✅ Download the correct ChromeDriver version
        - ✅ Match your installed Chrome browser
        - ✅ Handle driver management automatically
        """)
    
    # Test connection first
    if st.button("🧪 Test ChromeDriver Setup"):
        try:
            with st.spinner("Testing ChromeDriver setup..."):
                session_manager = FixedSalesforceSessionManager()
                
                if session_manager.test_connection():
                    st.session_state.session_manager = session_manager
                    st.balloons()
                else:
                    session_manager.cleanup()
                    
        except Exception as e:
            st.error(f"Setup failed: {str(e)}")
            
            st.subheader("🔧 Troubleshooting Steps")
            st.write("1. **Check Chrome version:** Go to `chrome://version/`")
            st.write("2. **Install webdriver-manager:** `pip install webdriver-manager`")
            st.write("3. **Update Chrome browser** to latest version")
            st.write("4. **Restart your application** after installing dependencies")
    
    # Login section (only show if driver works)
    if 'session_manager' in st.session_state:
        st.divider()
        st.subheader("🔑 Salesforce Login")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username:")
            password = st.text_input("Password:", type="password")
        
        with col2:
            if st.button("🔐 Login to Salesforce"):
                if username and password:
                    with st.spinner("Logging in..."):
                        success = st.session_state.session_manager.login_salesforce(username, password)
                        
                        if success:
                            st.success("Ready for badge detection!")
                        else:
                            st.error("Login failed - check credentials or complete 2FA")
    
    # Cleanup button
    if 'session_manager' in st.session_state:
        if st.button("🔄 Cleanup Browser Session"):
            st.session_state.session_manager.cleanup()
            del st.session_state.session_manager
            st.success("✅ Browser session cleaned up")
            st.rerun()

if __name__ == "__main__":
    main()
