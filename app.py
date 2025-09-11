import streamlit as st
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Chrome setup failed: {e}")
        return None

def extract_badge_comprehensive(profile_url, driver):
    """
    Comprehensive badge extraction using multiple methods
    """
    badge_info = {'found': False, 'method': None, 'details': {}}
    
    try:
        # Method 1: Try trailblazer.me profile
        st.info("🔍 Checking trailblazer.me profile...")
        result1 = check_trailblazer_me_profile(profile_url, driver)
        
        # Method 2: Try converting to trailhead.salesforce.com format
        st.info("🔍 Checking trailhead.salesforce.com profile...")
        username = extract_username_from_url(profile_url)
        if username:
            trailhead_url = f"https://trailhead.salesforce.com/en/me/{username}"
            result2 = check_trailhead_profile(trailhead_url, driver)
            
            if result2['found']:
                return result2
        
        # Method 3: Try agentblazer specific page
        st.info("🔍 Checking agentblazer specific page...")
        if username:
            agentblazer_url = f"https://trailhead.salesforce.com/agentblazer/{username}"
            result3 = check_agentblazer_page(agentblazer_url, driver)
            
            if result3['found']:
                return result3
        
        return result1 if result1['found'] else {'found': False}
        
    except Exception as e:
        return {'found': False, 'error': str(e)}

def extract_username_from_url(profile_url):
    """Extract username from profile URL"""
    try:
        if '/id/' in profile_url:
            return profile_url.split('/id/')[-1].strip('/')
        elif '/me/' in profile_url:
            return profile_url.split('/me/')[-1].strip('/')
        return None
    except:
        return None

def check_trailblazer_me_profile(profile_url, driver):
    """Check trailblazer.me profile for badges"""
    try:
        driver.get(profile_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for any agentblazer-related content
        agentblazer_elements = soup.find_all(string=re.compile(r'agentblazer|agent.*blazer', re.I))
        
        if agentblazer_elements:
            st.success("✅ Found agentblazer content in trailblazer.me profile!")
            return analyze_agentblazer_content(soup, 'trailblazer.me')
        
        return {'found': False, 'method': 'trailblazer.me'}
        
    except Exception as e:
        return {'found': False, 'error': str(e)}

def check_trailhead_profile(trailhead_url, driver):
    """Check trailhead.salesforce.com profile"""
    try:
        driver.get(trailhead_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for agentblazer badges
        images = soup.find_all('img')
        
        for img in images:
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            if ('agentblazer' in src.lower() or 'agentblazer' in alt.lower()):
                return analyze_badge_image(src, alt, 'trailhead.salesforce.com')
        
        return {'found': False, 'method': 'trailhead.salesforce.com'}
        
    except Exception as e:
        return {'found': False, 'error': str(e)}

def check_agentblazer_page(agentblazer_url, driver):
    """Check dedicated agentblazer page"""
    try:
        driver.get(agentblazer_url)
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for badge level indicators
        level_indicators = soup.find_all(string=re.compile(r'champion|innovator|legend', re.I))
        
        if level_indicators:
            return analyze_level_indicators(level_indicators, 'agentblazer page')
        
        return {'found': False, 'method': 'agentblazer page'}
        
    except Exception as e:
        return {'found': False, 'error': str(e)}

def analyze_badge_image(src, alt, method):
    """Analyze badge image to determine level"""
    level = 'Unknown'
    
    if 'level-3' in src or 'legend' in alt.lower():
        level = 'Legend'
    elif 'level-2' in src or 'innovator' in alt.lower():
        level = 'Innovator'
    elif 'level-1' in src or 'champion' in alt.lower():
        level = 'Champion'
    
    return {
        'found': True,
        'method': method,
        'badge_level': level,
        'badge_url': src,
        'alt_text': alt
    }

def analyze_agentblazer_content(soup, method):
    """Analyze general agentblazer content"""
    content = soup.get_text().lower()
    
    if 'legend' in content:
        level = 'Legend'
    elif 'innovator' in content:
        level = 'Innovator'
    elif 'champion' in content:
        level = 'Champion'
    else:
        level = 'Found but level unclear'
    
    return {
        'found': True,
        'method': method,
        'badge_level': level
    }

def analyze_level_indicators(indicators, method):
    """Analyze level indicators from text"""
    for indicator in indicators:
        if 'legend' in indicator.lower():
            return {'found': True, 'method': method, 'badge_level': 'Legend'}
        elif 'innovator' in indicator.lower():
            return {'found': True, 'method': method, 'badge_level': 'Innovator'}
        elif 'champion' in indicator.lower():
            return {'found': True, 'method': method, 'badge_level': 'Champion'}
    
    return {'found': False, 'method': method}

def main():
    st.set_page_config(
        page_title="Comprehensive Badge Detector",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Comprehensive Agentblazer Badge Detector")
    st.success("✅ Tries multiple methods to find your badge!")
    
    st.info("""
    **This detector tries multiple approaches:**
    1. 🔍 Checks your trailblazer.me profile
    2. 🔍 Converts to trailhead.salesforce.com format
    3. 🔍 Checks dedicated agentblazer pages
    4. 🔍 Looks for text content and images
    """)
    
    # Single profile test
    st.subheader("🧪 Test Your Profile")
    
    profile_url = st.text_input(
        "Profile URL:",
        placeholder="https://trailblazer.me/id/aarathisreeballa",
        value="https://trailblazer.me/id/aarathisreeballa"
    )
    
    if st.button("🔍 Comprehensive Badge Search"):
        if profile_url:
            driver = setup_driver()
            if driver:
                try:
                    with st.spinner("Searching for your badge using multiple methods..."):
                        result = extract_badge_comprehensive(profile_url, driver)
                        
                        if result.get('found'):
                            st.success(f"🎉 **Badge Found using {result['method']}!**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.subheader("📋 Badge Details")
                                st.write(f"**Level:** {result.get('badge_level', 'Unknown')}")
                                st.write(f"**Detection Method:** {result['method']}")
                                
                                if 'badge_url' in result:
                                    st.write(f"**Badge URL:** `{result['badge_url']}`")
                                if 'alt_text' in result:
                                    st.write(f"**Alt Text:** `{result['alt_text']}`")
                            
                            with col2:
                                if 'badge_url' in result and result['badge_url']:
                                    st.subheader("📷 Badge Image")
                                    try:
                                        st.image(result['badge_url'], caption="Your Agentblazer Badge", width=300)
                                    except:
                                        st.info("Badge image could not be displayed")
                        else:
                            st.warning("❌ No agentblazer badge found using any method")
                            st.info("""
                            **Possible reasons:**
                            1. You might not have an Agentblazer badge yet
                            2. Your badge might not be publicly visible
                            3. The badge might be on a different profile page
                            4. Manual verification might be needed
                            """)
                            
                            # Suggest manual check
                            username = extract_username_from_url(profile_url)
                            if username:
                                st.subheader("🔗 Manual Check Links")
                                st.write("Try checking these URLs manually:")
                                st.write(f"1. [Trailhead Profile](https://trailhead.salesforce.com/en/me/{username})")
                                st.write(f"2. [Agentblazer Page](https://trailhead.salesforce.com/agentblazer)")
                                
                finally:
                    driver.quit()
    
    st.divider()
    
    # Manual entry as backup
    st.subheader("📝 Manual Badge Entry (Backup Method)")
    st.write("If automated detection fails, you can manually enter badge levels:")
    
    with st.form("manual_entry"):
        name = st.text_input("Your Name")
        roll_number = st.text_input("Roll Number") 
        badge_level = st.selectbox(
            "Your Badge Level",
            ["None", "Champion", "Innovator", "Legend"],
            index=2  # Default to Innovator since you mentioned you have it
        )
        
        if st.form_submit_button("✅ Confirm Badge Level"):
            st.success(f"**Confirmed: {name} has {badge_level} badge level!**")
            
            result_data = {
                'Name': name,
                'Roll Number': roll_number, 
                'Badge Status': badge_level,
                'Level': {
                    'Champion': 'Level 1',
                    'Innovator': 'Level 2',
                    'Legend': 'Level 3',
                    'None': 'None'
                }[badge_level],
                'Method': 'Manual Entry'
            }
            
            st.json(result_data)

if __name__ == "__main__":
    main()
s
