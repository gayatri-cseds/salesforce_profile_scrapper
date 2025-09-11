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
import pytesseract
import io
import cv2
import numpy as np

def setup_driver():
    """Setup Chrome driver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        st.error(f"Chrome setup failed: {e}")
        return None

def extract_text_from_image_url(image_url):
    """
    Download image from URL and extract text using OCR
    """
    try:
        # Download the image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(image)
        
        # Convert RGB to BGR for OpenCV
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Enhance image for better OCR
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_array
            
        # Apply image processing for better OCR
        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
        
        # Apply threshold to get black text on white background
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(thresh)
        
        # Extract text using Tesseract
        extracted_text = pytesseract.image_to_string(processed_image, config='--psm 8').strip()
        
        return extracted_text.lower()
        
    except Exception as e:
        st.error(f"Error extracting text from image: {e}")
        return ""

def detect_badge_from_images(profile_url, driver):
    """
    Find agentblazer images and extract text to determine badge level
    """
    try:
        # Load profile page
        driver.get(profile_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)
        
        # Get all images
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        images = soup.find_all('img')
        
        # Look for agentblazer banner images
        agentblazer_images = []
        
        for img in images:
            src = str(img.get('src', ''))
            alt = str(img.get('alt', ''))
            
            # Check if it's an agentblazer banner image
            if ('agentblazer' in src.lower() and 'banner' in src.lower()) or \
               ('agentblazer' in alt.lower()):
                
                # Convert relative URLs to absolute
                if src.startswith('/'):
                    src = 'https://trailhead.salesforce.com' + src
                elif not src.startswith('http'):
                    src = 'https://trailhead.salesforce.com/' + src
                    
                agentblazer_images.append({
                    'src': src,
                    'alt': alt
                })
        
        st.info(f"Found {len(agentblazer_images)} agentblazer images")
        
        # Process each agentblazer image
        for img_info in agentblazer_images:
            st.write(f"Processing image: {img_info['src']}")
            
            # Extract text from the image
            extracted_text = extract_text_from_image_url(img_info['src'])
            
            st.write(f"Extracted text: '{extracted_text}'")
            
            # Determine badge level from extracted text
            if any(word in extracted_text for word in ['legend', 'level 3', 'level3']):
                return 'Legend'
            elif any(word in extracted_text for word in ['innovator', 'level 2', 'level2']):
                return 'Innovator'
            elif any(word in extracted_text for word in ['champion', 'level 1', 'level1']):
                return 'Champion'
            
            # Also check alt text as backup
            alt_lower = img_info['alt'].lower()
            if 'legend' in alt_lower:
                return 'Legend'
            elif 'innovator' in alt_lower:
                return 'Innovator'
            elif 'champion' in alt_lower:
                return 'Champion'
        
        return 'None'
        
    except Exception as e:
        st.error(f"Error detecting badge: {e}")
        return 'Error'

def test_direct_image_ocr():
    """
    Test OCR on the known innovator badge image
    """
    st.subheader("🧪 Test Direct Image OCR")
    
    # Test with the known innovator badge URL
    test_image_url = "https://trailhead.salesforce.com/agentblazer/banner-level-2.png"
    
    if st.button("Test OCR on Innovator Badge Image"):
        with st.spinner("Extracting text from badge image..."):
            extracted_text = extract_text_from_image_url(test_image_url)
            
            st.success(f"✅ Extracted text: '{extracted_text}'")
            
            # Show the image for reference
            try:
                st.image(test_image_url, caption="Agentblazer Innovator Badge", width=300)
            except:
                pass
            
            # Determine badge level
            if 'innovator' in extracted_text.lower() or 'level 2' in extracted_text.lower():
                st.success("🎉 **Detected: Innovator Badge!**")
            else:
                st.warning("⚠️ Badge level unclear from OCR text")

def main():
    st.title("🔍 OCR-Based Badge Detector")
    st.success("✅ Uses OCR to extract text directly from badge images!")
    
    # Test direct OCR first
    test_direct_image_ocr()
    
    st.divider()
    
    # Profile testing
    st.subheader("👤 Test Your Profile")
    
    profile_url = st.text_input(
        "Your Profile URL:",
        placeholder="https://trailblazer.me/id/username"
    )
    
    if st.button("🔍 Detect Badge with OCR"):
        if profile_url:
            driver = setup_driver()
            if driver:
                try:
                    with st.spinner("Analyzing profile with OCR..."):
                        result = detect_badge_from_images(profile_url, driver)
                        
                        if result in ['Champion', 'Innovator', 'Legend']:
                            st.success(f"🎉 **Badge Detected: {result}**")
                        elif result == 'None':
                            st.warning("❌ No badge detected")
                        else:
                            st.error(f"❌ Error: {result}")
                            
                finally:
                    driver.quit()
    
    st.divider()
    
    # Batch processing
    st.subheader("📂 Batch Processing with OCR")
    
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        if all(col in df.columns for col in ['Roll Number', 'Name', 'Salesforce URL']):
            st.dataframe(df.head())
            
            if st.button("🚀 Process All with OCR"):
                driver = setup_driver()
                if driver:
                    try:
                        results = []
                        progress = st.progress(0)
                        
                        for idx, row in df.iterrows():
                            progress.progress((idx + 1) / len(df))
                            
                            badge_level = detect_badge_from_images(row['Salesforce URL'], driver)
                            
                            results.append({
                                'Roll Number': row['Roll Number'],
                                'Name': row['Name'],
                                'Badge Status': badge_level,
                                'Level': {
                                    'Champion': 'Level 1',
                                    'Innovator': 'Level 2',
                                    'Legend': 'Level 3',
                                    'None': 'None'
                                }.get(badge_level, 'Unknown')
                            })
                            
                            time.sleep(2)  # Be respectful to servers
                        
                        results_df = pd.DataFrame(results)
                        st.dataframe(results_df)
                        
                        # Download results
                        csv_data = results_df.to_csv(index=False)
                        st.download_button("📥 Download Results", csv_data, "ocr_badge_results.csv")
                        
                    finally:
                        driver.quit()

if __name__ == "__main__":
    main()
