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
    """Setup Chrome driver for real scraping"""
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

def extract_agentblazer_badge(profile_url, driver):
    """
    Extract the EXACT agentblazer badge image from salesforce.com/trailblazer/ profiles
    Looking for: <img src="https://trailhead.salesforce.com/agentblazer/banner-level-X.png" alt="Agentblazer ...">
    """
    try:
        st.write(f"🔍 Loading: {profile_url}")
        
        # Load the profile page
        driver.get(profile_url)
        
        # Wait for page to load completely
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content (badges load via JS)
        time.sleep(10)  # Increased wait time for JS to load badges
        
        # Get page source after JS execution
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Method 1: Find EXACT agentblazer banner images
        all_images = soup.find_all('img')
        
        st.write(f"📊 Found {len(all_images)} total images on page")
        
        # Look specifically for agentblazer banner images
        for img in all_images:
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            # Debug: Show first few images
            if 'agentblazer' in src.lower() or 'agentblazer' in alt.lower():
                st.write(f"🎯 **Agentblazer image found:**")
                st.write(f"- **src:** `{src}`")
                st.write(f"- **alt:** `{alt}`")
                
                # Extract badge level from the EXACT pattern you provided
                if 'banner-level-3.png' in src:
                    return {
                        'badge_level': 'Legend',
                        'badge_image_url': src,
                        'alt_text': alt,
                        'detection_method': 'Agentblazer Banner Level 3',
                        'status': 'Success'
                    }
                elif 'banner-level-2.png' in src:
                    return {
                        'badge_level': 'Innovator', 
                        'badge_image_url': src,
                        'alt_text': alt,
                        'detection_method': 'Agentblazer Banner Level 2',
                        'status': 'Success'
                    }
                elif 'banner-level-1.png' in src:
                    return {
                        'badge_level': 'Champion',
                        'badge_image_url': src, 
                        'alt_text': alt,
                        'detection_method': 'Agentblazer Banner Level 1',
                        'status': 'Success'
                    }
                
                # Also check alt text as backup
                alt_lower = alt.lower()
                if 'legend' in alt_lower:
                    return {'badge_level': 'Legend', 'badge_image_url': src, 'alt_text': alt, 'detection_method': 'Alt Text - Legend', 'status': 'Success'}
                elif 'innovator' in alt_lower:
                    return {'badge_level': 'Innovator', 'badge_image_url': src, 'alt_text': alt, 'detection_method': 'Alt Text - Innovator', 'status': 'Success'}
                elif 'champion' in alt_lower:
                    return {'badge_level': 'Champion', 'badge_image_url': src, 'alt_text': alt, 'detection_method': 'Alt Text - Champion', 'status': 'Success'}
        
        # Debug: Show all image sources for troubleshooting
        st.write("🔍 **Debug - All image sources:**")
        agentblazer_related = []
        for i, img in enumerate(all_images[:10]):  # Show first 10 images
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            if src:  # Only show images with src
                st.write(f"**Image {i+1}:** `{src[:100]}...` | Alt: `{alt[:50]}...`")
                
                # Check for any agentblazer related content
                if 'agentblazer' in src.lower() or 'agentblazer' in alt.lower() or 'banner' in src.lower():
                    agentblazer_related.append(f"Image {i+1}: {src}")
        
        if agentblazer_related:
            st.write("🎯 **Potential agentblazer images:**")
            for img_info in agentblazer_related:
                st.write(f"- {img_info}")
        
        # No agentblazer badge found
        return {
            'badge_level': 'None',
            'badge_image_url': '',
            'alt_text': '',
            'detection_method': 'No Agentblazer Badge Found',
            'status': 'No Badge Found'
        }
        
    except Exception as e:
        return {
            'badge_level': 'Error',
            'badge_image_url': '',
            'alt_text': '',
            'detection_method': 'Request Failed',
            'status': f'Error: {str(e)}'
        }

def main():
    st.set_page_config(
        page_title="Agentblazer Badge Image Extractor",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Agentblazer Badge Image Extractor")
    st.success("✅ Extracts badge images from salesforce.com/trailblazer/ profiles!")
    
    st.info("""
    **Targeting the EXACT pattern you found:**
    ```
    <img src="https://trailhead.salesforce.com/agentblazer/banner-level-2.png" alt="Agentblazer Innovator">
    ```
    
    **Expected URL format:** `https://www.salesforce.com/trailblazer/username`
    """)
    
    # Single profile test
    st.subheader("🧪 Test Single Profile")
    
    test_url = st.text_input(
        "Salesforce Profile URL:",
        value="https://www.salesforce.com/trailblazer/aarathisreeballa",
        placeholder="https://www.salesforce.com/trailblazer/username"
    )
    
    if st.button("🔍 Extract Badge Image"):
        if test_url:
            driver = setup_driver()
            if driver:
                try:
                    with st.spinner("Extracting agentblazer badge..."):
                        result = extract_agentblazer_badge(test_url, driver)
                        
                        if result['status'] == 'Success':
                            st.success(f"🎉 **Badge Found: {result['badge_level']}**")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📋 Badge Details")
                                st.write(f"**Badge Level:** {result['badge_level']}")
                                st.write(f"**Detection Method:** {result['detection_method']}")
                                st.write(f"**Image URL:** `{result['badge_image_url']}`")
                                st.write(f"**Alt Text:** `{result['alt_text']}`")
                            
                            with col2:
                                st.subheader("📷 Badge Image")
                                if result['badge_image_url']:
                                    try:
                                        st.image(result['badge_image_url'], caption=f"Agentblazer {result['badge_level']} Badge", width=300)
                                    except Exception as e:
                                        st.error(f"Could not load image: {e}")
                        
                        elif result['badge_level'] == 'None':
                            st.warning("❌ No agentblazer badge found on this profile")
                            st.info("The profile might not have an agentblazer badge or it may not be publicly visible")
                        
                        else:
                            st.error(f"❌ {result['status']}")
                        
                finally:
                    driver.quit()
    
    # Batch processing
    st.divider()
    st.subheader("📂 Batch Processing")
    
    uploaded_file = st.file_uploader("Upload CSV with Salesforce URLs", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} profiles")
            st.dataframe(df.head())
            
            # Configuration
            col1, col2 = st.columns(2)
            with col1:
                delay = st.slider("Delay between requests (seconds)", 3, 15, 8)
            with col2:
                max_profiles = st.number_input("Max profiles to process", 1, len(df), min(5, len(df)))
            
            if st.button("🚀 Extract All Badge Images"):
                
                profiles_to_process = df.head(max_profiles)
                
                driver = setup_driver()
                if driver:
                    try:
                        results = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, (_, row) in enumerate(profiles_to_process.iterrows()):
                            progress = (i + 1) / len(profiles_to_process)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing {i+1}/{len(profiles_to_process)}: {row['Name']}")
                            
                            result = extract_agentblazer_badge(row['Salesforce URL'], driver)
                            
                            results.append({
                                'Roll Number': row['Roll Number'],
                                'Name': row['Name'],
                                'Salesforce URL': row['Salesforce URL'],
                                'Badge Level': result['badge_level'],
                                'Badge Image URL': result['badge_image_url'],
                                'Alt Text': result['alt_text'],
                                'Detection Method': result['detection_method'],
                                'Status': result['status']
                            })
                            
                            # Delay between requests
                            if i < len(profiles_to_process) - 1:
                                time.sleep(delay)
                        
                        # Display results
                        results_df = pd.DataFrame(results)
                        
                        st.success("🎉 Batch processing completed!")
                        
                        # Summary
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total", len(results_df))
                        with col2:
                            badges_found = len(results_df[results_df['Badge Level'].isin(['Champion', 'Innovator', 'Legend'])])
                            st.metric("Badges Found", badges_found)
                        with col3:
                            innovators = len(results_df[results_df['Badge Level'] == 'Innovator'])
                            st.metric("Innovators", innovators)
                        with col4:
                            champions = len(results_df[results_df['Badge Level'] == 'Champion'])
                            st.metric("Champions", champions)
                        
                        # Results table
                        st.dataframe(results_df)
                        
                        # Download
                        csv_data = results_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Results",
                            csv_data,
                            f"agentblazer_badges_{int(time.time())}.csv",
                            "text/csv"
                        )
                        
                    finally:
                        driver.quit()
        else:
            st.error("❌ CSV must have columns: Roll Number, Name, Salesforce URL")

if __name__ == "__main__":
    main()
