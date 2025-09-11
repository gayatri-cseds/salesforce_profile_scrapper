import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        st.error(f"Failed to setup Chrome driver: {e}")
        return None

def extract_badge_level_selenium(url, driver):
    """
    Enhanced badge extraction using Selenium for dynamic content
    """
    try:
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Get page source after JavaScript execution
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Enhanced badge detection patterns
        badge_patterns = [
            # Agentblazer specific patterns
            (r'agentblazer.*banner-level-1', 'Champion'),
            (r'agentblazer.*banner-level-2', 'Innovator'),
            (r'agentblazer.*banner-level-3', 'Legend'),
            # General badge patterns
            (r'champion', 'Champion'),
            (r'innovator', 'Innovator'),
            (r'legend', 'Legend'),
            # Rank-based patterns
            (r'rank.*1', 'Champion'),
            (r'rank.*2', 'Innovator'),
            (r'rank.*3', 'Legend')
        ]
        
        # Check all images
        for img in soup.find_all('img'):
            src = str(img.get('src', '')).lower()
            alt = str(img.get('alt', '')).lower()
            classes = ' '.join(img.get('class', [])).lower()
            
            for pattern, level in badge_patterns:
                if re.search(pattern, src) or re.search(pattern, alt) or re.search(pattern, classes):
                    return level
        
        # Check div elements with classes
        for div in soup.find_all('div'):
            classes = ' '.join(div.get('class', [])).lower()
            text = div.get_text().lower()
            
            for pattern, level in badge_patterns:
                if re.search(pattern, classes) or re.search(pattern, text):
                    return level
        
        # Check for rank information in JSON-like structures
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                content = script.string.lower()
                for pattern, level in badge_patterns:
                    if re.search(pattern, content):
                        return level
        
        return "None"
        
    except Exception as e:
        st.error(f"Error processing {url}: {str(e)}")
        return "Error"

def check_profile_accessibility(url, driver):
    """
    Check if profile is accessible and public
    """
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        page_text = driver.page_source.lower()
        
        # Check for privacy indicators
        if "profile is private" in page_text or "not found" in page_text:
            return "Private/Not Found"
        elif "badges" in page_text or "trailhead" in page_text:
            return "Public"
        else:
            return "Unknown"
            
    except Exception as e:
        return "Error"

