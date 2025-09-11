import streamlit as st
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from bs4 import BeautifulSoup

def setup_selenium():
    """Setup Selenium with proper configuration for Salesforce"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        st.error(f"Selenium setup failed: {e}")
        return None

def extract_badges_selenium(url, driver):
    """Extract badges using Selenium with comprehensive detection"""
    try:
        st.info(f"🔍 Processing: {url}")
        
        # Load the page
        driver.get(url)
        
        # Wait for the page to load completely
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Scroll to load dynamic content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Try to find badge information in multiple ways
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Method 1: Look for rank information
        rank_info = extract_rank_info(soup, driver)
        if rank_info != "None":
            return rank_info
        
        # Method 2: Look for badge counts/points
        badge_info = extract_badge_count_info(soup, driver)
        if badge_info != "None":
            return badge_info
        
        # Method 3: Look for specific badge images
        image_info = extract_image_badges(soup, driver)
        if image_info != "None":
            return image_info
        
        return "None"
        
    except Exception as e:
        st.error(f"Error processing {url}: {str(e)}")
        return "Error"

def extract_rank_info(soup, driver):
    """Extract rank information from various page elements"""
    
    # Look for rank text patterns
    rank_patterns = [
        (r'ranger', 'Legend'),
        (r'expeditioner', 'Legend'), 
        (r'mountaineer', 'Innovator'),
        (r'adventurer', 'Champion'),
        (r'explorer', 'Champion'),
        (r'hiker', 'Novice')
    ]
    
    # Search in text content
    page_text = soup.get_text().lower()
    for pattern, level in rank_patterns:
        if re.search(pattern, page_text):
            return level
    
    # Search in specific elements
    try:
        # Look for rank elements by common class patterns
        rank_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='rank'], [class*='level'], [class*='badge']")
        
        for element in rank_elements:
            text = element.text.lower()
            for pattern, level in rank_patterns:
                if pattern in text:
                    return level
    except:
        pass
    
    return "None"

def extract_badge_count_info(soup, driver):
    """Extract information based on badge counts"""
    try:
        # Look for numerical indicators
        numbers = re.findall(r'\b\d+\b', soup.get_text())
        
        # Convert to integers and look for typical badge counts
        badge_counts = [int(n) for n in numbers if n.isdigit() and 1 <= int(n) <= 1000]
        
        if badge_counts:
            max_badges = max(badge_counts)
            
            # Estimate level based on badge count
            if max_badges >= 100:
                return "Legend"
            elif max_badges >= 50:
                return "Innovator" 
            elif max_badges >= 20:
                return "Champion"
            elif max_badges >= 5:
                return "Explorer"
        
    except:
        pass
    
    return "None"

def extract_image_badges(soup, driver):
    """Extract badges from image sources"""
    
    try:
        # Look for all images
        images = soup.find_all('img')
        
        badge_patterns = [
            (r'ranger|legend|level.*3', 'Legend'),
            (r'mountaineer|innovator|level.*2', 'Innovator'),
            (r'adventurer|champion|level.*1', 'Champion')
        ]
        
        for img in images:
            src = str(img.get('src', '')).lower()
            alt = str(img.get('alt', '')).lower()
            
            for pattern, level in badge_patterns:
                if re.search(pattern, src) or re.search(pattern, alt):
                    return level
                    
    except:
        pass
    
    return "None"

def main():
    st.set_page_config(
        page_title="Salesforce Badge Extractor - Enhanced",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Enhanced Salesforce Badge Extractor")
    st.success("✅ This version uses browser automation to handle dynamic content!")
    
    # Single profile testing
    st.subheader("🧪 Test Single Profile")
    
    test_url = st.text_input(
        "Test Profile URL:",
        placeholder="https://www.salesforce.com/trailblazer/username"
    )
    
    if st.button("🔍 Test Profile"):
        if test_url:
            driver = setup_selenium()
            if driver:
                try:
                    with st.spinner("Processing profile..."):
                        result = extract_badges_selenium(test_url, driver)
                        
                        st.subheader("Results:")
                        if result == "None":
                            st.warning("❌ No badges detected or profile may be private")
                        elif result == "Error":
                            st.error("❌ Error processing profile")
                        else:
                            st.success(f"🎉 Badge Level Detected: **{result}**")
                            
                finally:
                    driver.quit()
    
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
                
                driver = setup_selenium()
                if not driver:
                    st.error("❌ Failed to setup browser automation")
                    return
                
                try:
                    progress_bar = st.progress(0)
                    results = []
                    
                    for idx, row in df.iterrows():
                        progress = (idx + 1) / len(df)
                        progress_bar.progress(progress)
                        
                        st.write(f"Processing {idx + 1}/{len(df)}: {row['Name']}")
                        
                        badge_level = extract_badges_selenium(row['Salesforce URL'], driver)
                        
                        # Map to standardized levels
                        level_mapping = {
                            'Legend': 'Level 3',
                            'Innovator': 'Level 2',
                            'Champion': 'Level 1',
                            'Explorer': 'Level 0',
                            'None': 'None',
                            'Error': 'Error'
                        }
                        
                        results.append({
                            'Roll Number': row['Roll Number'],
                            'Name': row['Name'],
                            'Salesforce URL': row['Salesforce URL'],
                            'Badge Status': badge_level,
                            'Level': level_mapping.get(badge_level, 'Unknown')
                        })
                        
                        # Small delay to avoid overloading
                        time.sleep(2)
                    
                    # Display results
                    results_df = pd.DataFrame(results)
                    
                    st.subheader("📊 Final Results")
                    st.dataframe(results_df)
                    
                    # Summary
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
                    
                    # Download
                    csv_data = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results",
                        csv_data,
                        "badge_extraction_results.csv",
                        "text/csv"
                    )
                    
                finally:
                    driver.quit()
        else:
            st.error(f"❌ Missing required columns: {required_cols}")

if __name__ == "__main__":
    main()
