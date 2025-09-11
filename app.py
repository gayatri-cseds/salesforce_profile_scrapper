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
from PIL import Image
import io

def setup_driver():
    """Setup Chrome driver"""
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

def extract_badge_image(profile_url, driver):
    """
    Extract agentblazer badge image from profile
    """
    try:
        driver.get(profile_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images = soup.find_all('img')
        
        # Look for agentblazer badge images
        for img in images:
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            # Check if it's an agentblazer badge image
            if ('agentblazer' in src.lower() or 'agentblazer' in alt.lower()) and \
               ('banner' in src.lower() or 'badge' in alt.lower()):
                
                # Convert relative URL to absolute
                if src.startswith('/'):
                    badge_url = 'https://trailhead.salesforce.com' + src
                elif not src.startswith('http'):
                    badge_url = 'https://trailhead.salesforce.com/' + src
                else:
                    badge_url = src
                
                return {
                    'badge_url': badge_url,
                    'alt_text': alt,
                    'found': True
                }
        
        return {'found': False}
        
    except Exception as e:
        return {'found': False, 'error': str(e)}

def download_and_display_image(image_url):
    """
    Download and display badge image
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Display the image
        image = Image.open(io.BytesIO(response.content))
        return image
        
    except Exception as e:
        st.error(f"Error downloading image: {e}")
        return None

def classify_badge_from_url(badge_url, alt_text):
    """
    Classify badge based on URL pattern and alt text
    """
    url_lower = badge_url.lower()
    alt_lower = alt_text.lower()
    
    # URL pattern matching
    if 'level-3' in url_lower or 'banner-level-3' in url_lower:
        return 'Legend'
    elif 'level-2' in url_lower or 'banner-level-2' in url_lower:
        return 'Innovator'
    elif 'level-1' in url_lower or 'banner-level-1' in url_lower:
        return 'Champion'
    
    # Alt text matching
    if 'legend' in alt_lower:
        return 'Legend'
    elif 'innovator' in alt_lower:
        return 'Innovator'
    elif 'champion' in alt_lower:
        return 'Champion'
    
    return 'Unknown'

def main():
    st.set_page_config(
        page_title="Badge Image Extractor",
        page_icon="🖼️",
        layout="wide"
    )
    
    st.title("🖼️ Agentblazer Badge Image Extractor")
    st.success("✅ Extracts and displays badge images from profiles!")
    
    # Single profile test
    st.subheader("🧪 Extract Badge Image")
    
    profile_url = st.text_input(
        "Profile URL:",
        placeholder="https://trailblazer.me/id/username"
    )
    
    if st.button("🖼️ Extract Badge Image"):
        if profile_url:
            driver = setup_driver()
            if driver:
                try:
                    with st.spinner("Extracting badge image..."):
                        result = extract_badge_image(profile_url, driver)
                        
                        if result.get('found'):
                            badge_url = result['badge_url']
                            alt_text = result['alt_text']
                            
                            st.success("✅ Badge image found!")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📷 Badge Image")
                                
                                # Download and display image
                                badge_image = download_and_display_image(badge_url)
                                if badge_image:
                                    st.image(badge_image, caption="Agentblazer Badge", width=300)
                                
                            with col2:
                                st.subheader("📋 Badge Details")
                                
                                st.write(f"**Badge URL:** `{badge_url}`")
                                st.write(f"**Alt Text:** `{alt_text}`")
                                
                                # Classify badge
                                badge_level = classify_badge_from_url(badge_url, alt_text)
                                
                                if badge_level != 'Unknown':
                                    st.success(f"🎉 **Badge Level: {badge_level}**")
                                else:
                                    st.warning("⚠️ Badge level unclear - manual verification needed")
                                
                                # Download button for image
                                if badge_image:
                                    img_buffer = io.BytesIO()
                                    badge_image.save(img_buffer, format='PNG')
                                    img_data = img_buffer.getvalue()
                                    
                                    st.download_button(
                                        "📥 Download Badge Image",
                                        img_data,
                                        f"agentblazer_badge.png",
                                        "image/png"
                                    )
                        else:
                            st.warning("❌ No agentblazer badge found on this profile")
                            
                finally:
                    driver.quit()
            else:
                st.error("❌ Browser setup failed")
    
    st.divider()
    
    # Batch processing
    st.subheader("📂 Batch Badge Image Extraction")
    
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        if all(col in df.columns for col in ['Roll Number', 'Name', 'Salesforce URL']):
            st.dataframe(df.head())
            
            if st.button("🚀 Extract All Badge Images"):
                driver = setup_driver()
                if driver:
                    try:
                        results = []
                        progress = st.progress(0)
                        
                        for idx, row in df.iterrows():
                            progress.progress((idx + 1) / len(df))
                            st.write(f"Processing: {row['Name']}")
                            
                            result = extract_badge_image(row['Salesforce URL'], driver)
                            
                            if result.get('found'):
                                badge_url = result['badge_url']
                                alt_text = result['alt_text']
                                badge_level = classify_badge_from_url(badge_url, alt_text)
                                
                                # Display the badge image
                                st.subheader(f"👤 {row['Name']} - Badge Found!")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    badge_image = download_and_display_image(badge_url)
                                    if badge_image:
                                        st.image(badge_image, caption=f"{row['Name']}'s Badge", width=200)
                                
                                with col2:
                                    st.write(f"**Badge Level:** {badge_level}")
                                    st.write(f"**Alt Text:** {alt_text}")
                            
                            results.append({
                                'Roll Number': row['Roll Number'],
                                'Name': row['Name'],
                                'Salesforce URL': row['Salesforce URL'],
                                'Badge Found': result.get('found', False),
                                'Badge URL': result.get('badge_url', 'N/A'),
                                'Badge Status': classify_badge_from_url(
                                    result.get('badge_url', ''), 
                                    result.get('alt_text', '')
                                ) if result.get('found') else 'None'
                            })
                            
                            time.sleep(2)  # Be respectful
                        
                        # Summary results
                        results_df = pd.DataFrame(results)
                        
                        st.subheader("📊 Summary Results")
                        st.dataframe(results_df)
                        
                        # Download results
                        csv_data = results_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Results CSV",
                            csv_data,
                            "badge_extraction_results.csv",
                            "text/csv"
                        )
                        
                    finally:
                        driver.quit()

if __name__ == "__main__":
    main()
