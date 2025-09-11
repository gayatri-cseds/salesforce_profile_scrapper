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
    """Setup Chrome driver with debugging enabled"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Chrome driver setup failed: {e}")
        return None

def debug_badge_detection(profile_url, driver):
    """
    Debug version that shows exactly what's found on the page
    """
    try:
        st.info(f"🔍 Loading: {profile_url}")
        driver.get(profile_url)
        
        # Wait for page load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(8)  # Increased wait time
        
        # Get page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Debug: Show all images found
        st.subheader("🖼️ All Images Found on Page:")
        images = soup.find_all('img')
        st.write(f"Total images found: {len(images)}")
        
        agentblazer_images = []
        for idx, img in enumerate(images):
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            # Show first 10 images for debugging
            if idx < 10:
                st.write(f"**Image {idx + 1}:**")
                st.write(f"- src: `{src}`")
                st.write(f"- alt: `{alt}`")
                
            # Check for agentblazer patterns
            if 'agentblazer' in src.lower() or 'agentblazer' in alt.lower():
                agentblazer_images.append({'src': src, 'alt': alt})
        
        st.subheader("🤖 Agentblazer Images Found:")
        if agentblazer_images:
            for img in agentblazer_images:
                st.write(f"- **src:** `{img['src']}`")
                st.write(f"- **alt:** `{img['alt']}`")
        else:
            st.warning("❌ No agentblazer images found")
        
        # Debug: Search for any "level" or "banner" text
        st.subheader("🔍 Text Content Analysis:")
        page_text = soup.get_text().lower()
        
        level_keywords = ['level-1', 'level-2', 'level-3', 'banner-level', 'innovator', 'champion', 'legend', 'agentblazer']
        found_keywords = []
        
        for keyword in level_keywords:
            if keyword in page_text:
                found_keywords.append(keyword)
        
        if found_keywords:
            st.success(f"✅ Found keywords: {', '.join(found_keywords)}")
        else:
            st.warning("❌ No relevant keywords found in page text")
        
        # Debug: Check for specific div/span elements
        st.subheader("🏷️ Badge-related Elements:")
        badge_elements = soup.find_all(['div', 'span', 'section'], 
                                     class_=re.compile(r'badge|level|agentblazer|innovator|champion|legend', re.I))
        
        if badge_elements:
            for idx, elem in enumerate(badge_elements[:5]):  # Show first 5
                st.write(f"**Element {idx + 1}:**")
                st.write(f"- Tag: `{elem.name}`")
                st.write(f"- Classes: `{elem.get('class', [])}`")
                st.write(f"- Text: `{elem.get_text().strip()[:100]}...`")
        else:
            st.warning("❌ No badge-related elements found")
        
        # Enhanced badge detection
        badge_level = enhanced_badge_detection(soup)
        
        return badge_level
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "Error"

def enhanced_badge_detection(soup):
    """Enhanced detection with multiple fallback methods"""
    
    # Method 1: Direct image src matching
    images = soup.find_all('img')
    for img in images:
        src = str(img.get('src', ''))
        alt = str(img.get('alt', ''))
        
        # Check for exact patterns
        if re.search(r'banner-level-3|level.*3', src, re.IGNORECASE):
            return "Legend"
        elif re.search(r'banner-level-2|level.*2', src, re.IGNORECASE):
            return "Innovator"
        elif re.search(r'banner-level-1|level.*1', src, re.IGNORECASE):
            return "Champion"
        
        # Check alt text
        if 'innovator' in alt.lower():
            return "Innovator"
        elif 'champion' in alt.lower():
            return "Champion"
        elif 'legend' in alt.lower():
            return "Legend"
    
    # Method 2: Text-based detection
    page_text = soup.get_text().lower()
    
    if any(word in page_text for word in ['agentblazer legend', 'banner-level-3']):
        return "Legend"
    elif any(word in page_text for word in ['agentblazer innovator', 'banner-level-2']):
        return "Innovator"
    elif any(word in page_text for word in ['agentblazer champion', 'banner-level-1']):
        return "Champion"
    
    # Method 3: CSS class detection
    badge_elements = soup.find_all(attrs={'class': re.compile(r'agentblazer|badge|level', re.I)})
    
    for elem in badge_elements:
        text = elem.get_text().lower()
        classes = ' '.join(elem.get('class', [])).lower()
        
        if any(word in text or word in classes for word in ['innovator', 'level-2', 'level 2']):
            return "Innovator"
        elif any(word in text or word in classes for word in ['champion', 'level-1', 'level 1']):
            return "Champion"
        elif any(word in text or word in classes for word in ['legend', 'level-3', 'level 3']):
            return "Legend"
    
    return "None"

def main():
    st.title("🐛 Enhanced Badge Detector with Debugging")
    st.success("This version shows exactly what's being detected on your profile")
    
    # Test URL input
    test_url = st.text_input(
        "Your Profile URL:", 
        placeholder="Enter your trailblazer profile URL"
    )
    
    if st.button("🔍 Debug Badge Detection"):
        if test_url:
            driver = setup_driver()
            if driver:
                try:
                    with st.spinner("Analyzing your profile..."):
                        result = debug_badge_detection(test_url, driver)
                        
                        st.subheader("🎯 Final Result:")
                        if result == "Innovator":
                            st.success("🎉 **Badge Level: Innovator** ✅")
                        elif result == "Champion":
                            st.success("🎉 **Badge Level: Champion** ✅")
                        elif result == "Legend":
                            st.success("🎉 **Badge Level: Legend** ✅")
                        elif result == "None":
                            st.warning("❌ No badge detected - Check the debug info above")
                        else:
                            st.error(f"❌ Error: {result}")
                            
                finally:
                    driver.quit()
            else:
                st.error("❌ Browser setup failed")

    # Alternative: Manual URL Analysis
    st.divider()
    st.subheader("🔧 Alternative: Direct URL Test")
    
    if st.button("Test Innovator Badge Image"):
        # Test if the innovator badge image loads
        test_img_url = "https://trailhead.salesforce.com/agentblazer/banner-level-2.png"
        
        try:
            response = requests.get(test_img_url, timeout=10)
            if response.status_code == 200:
                st.success("✅ Innovator badge image URL is accessible")
                st.image(test_img_url, caption="Agentblazer Innovator Badge")
            else:
                st.error(f"❌ Badge image not accessible: {response.status_code}")
        except Exception as e:
            st.error(f"❌ Error accessing badge image: {e}")
    
    # Quick fix suggestion
    st.divider()
    st.subheader("💡 Possible Issues & Solutions:")
    
    st.write("""
    **Common reasons why badge detection fails:**
    
    1. **Badge not yet updated on profile** - Sometimes it takes time for badges to appear[79]
    2. **Profile privacy settings** - Ensure your profile is public
    3. **Different badge format** - Your badge might use a different image URL pattern
    4. **Dynamic loading delay** - Badge images load slowly via JavaScript
    
    **Try this:**
    - Wait 24-48 hours after earning the badge
    - Check your profile visibility settings  
    - Verify the badge appears when you visit your profile manually
    """)

if __name__ == "__main__":
    main()
