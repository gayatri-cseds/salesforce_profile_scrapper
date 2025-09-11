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
    """Setup Chrome driver for JavaScript execution"""
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

def detect_badge_level(profile_url, driver):
    """
    Detect badge level from agentblazer banner images
    """
    try:
        # Load the page
        driver.get(profile_url)
        
        # Wait for JavaScript to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(5)
        
        # Get page source after JavaScript execution
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for the specific agentblazer banner patterns
        badge_patterns = [
            (r'agentblazer/banner-level-3\.png', 'Legend'),
            (r'agentblazer/banner-level-2\.png', 'Innovator'), 
            (r'agentblazer/banner-level-1\.png', 'Champion')
        ]
        
        # Check all images in the page
        images = soup.find_all('img')
        
        for img in images:
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            # Check each pattern
            for pattern, level in badge_patterns:
                if re.search(pattern, src, re.IGNORECASE):
                    return level
                    
                # Also check alt text for additional confirmation
                if 'agentblazer' in alt.lower():
                    if 'legend' in alt.lower() or 'level 3' in alt.lower():
                        return 'Legend'
                    elif 'innovator' in alt.lower() or 'level 2' in alt.lower():
                        return 'Innovator'
                    elif 'champion' in alt.lower() or 'level 1' in alt.lower():
                        return 'Champion'
        
        return "None"
        
    except Exception as e:
        st.error(f"Error processing {profile_url}: {str(e)}")
        return "Error"

def main():
    st.set_page_config(
        page_title="Agentblazer Badge Detector",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Agentblazer Badge Level Detector")
    st.success("✅ Detects JavaScript-loaded banner images: Champion | Innovator | Legend")
    
    st.info("""
    **Detection Method**: Looks for specific agentblazer banner images:
    - `banner-level-1.png` → Champion
    - `banner-level-2.png` → Innovator  
    - `banner-level-3.png` → Legend
    """)
    
    # Single profile test
    st.subheader("🧪 Test Single Profile")
    
    test_url = st.text_input(
        "Profile URL:", 
        placeholder="https://trailblazer.me/id/username or https://www.salesforce.com/trailblazer/username"
    )
    
    if st.button("🔍 Test Badge Detection"):
        if test_url:
            driver = setup_driver()
            if driver:
                try:
                    with st.spinner("Loading profile and detecting badges..."):
                        result = detect_badge_level(test_url, driver)
                        
                        if result == "None":
                            st.warning("❌ No Agentblazer badge detected")
                        elif result == "Error":
                            st.error("❌ Error processing profile")
                        else:
                            st.success(f"🎉 **Badge Level: {result}**")
                            
                            # Show which image was detected
                            if result == "Champion":
                                st.info("📷 Detected: `banner-level-1.png`")
                            elif result == "Innovator":
                                st.info("📷 Detected: `banner-level-2.png`")
                            elif result == "Legend":
                                st.info("📷 Detected: `banner-level-3.png`")
                                
                finally:
                    driver.quit()
            else:
                st.error("❌ Could not setup browser. Install ChromeDriver first.")
    
    st.divider()
    
    # Batch processing
    st.subheader("📂 Batch Processing")
    
    uploaded_file = st.file_uploader("Upload CSV File", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} records")
            st.dataframe(df.head())
            
            if st.button("🚀 Process All Profiles"):
                
                driver = setup_driver()
                if not driver:
                    st.error("❌ Browser setup failed")
                    return
                
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results = []
                    
                    for idx, row in df.iterrows():
                        progress = (idx + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {idx + 1}/{len(df)}: {row['Name']}")
                        
                        badge_level = detect_badge_level(row['Salesforce URL'], driver)
                        
                        results.append({
                            'Roll Number': row['Roll Number'],
                            'Name': row['Name'],
                            'Salesforce URL': row['Salesforce URL'],
                            'Badge Status': badge_level,
                            'Level': {
                                'Champion': 'Level 1',
                                'Innovator': 'Level 2', 
                                'Legend': 'Level 3',
                                'None': 'None',
                                'Error': 'Error'
                            }.get(badge_level, 'Unknown')
                        })
                        
                        # Small delay between requests
                        time.sleep(2)
                    
                    # Show results
                    results_df = pd.DataFrame(results)
                    
                    st.subheader("📊 Detection Results")
                    st.dataframe(results_df)
                    
                    # Summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total", len(results_df))
                    with col2:
                        champions = len(results_df[results_df['Badge Status'] == 'Champion'])
                        st.metric("Champions", champions)
                    with col3:
                        innovators = len(results_df[results_df['Badge Status'] == 'Innovator'])
                        st.metric("Innovators", innovators)
                    with col4:
                        legends = len(results_df[results_df['Badge Status'] == 'Legend'])
                        st.metric("Legends", legends)
                    
                    # Success rate
                    successful = len(results_df[results_df['Badge Status'].isin(['Champion', 'Innovator', 'Legend'])])
                    success_rate = (successful / len(results_df)) * 100
                    st.metric("Detection Success Rate", f"{success_rate:.1f}%")
                    
                    # Download results
                    csv_data = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results CSV",
                        csv_data,
                        "agentblazer_badge_results.csv",
                        "text/csv"
                    )
                    
                finally:
                    driver.quit()
                    
        else:
            st.error(f"❌ Missing required columns: {required_cols}")

if __name__ == "__main__":
    main()
