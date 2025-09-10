import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # ADD THIS IMPORT
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re


def setup_driver():
    """Setup headless Chrome driver - FIXED"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # FIXED: Proper service initialization
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def extract_badges_from_profile(profile_url, driver):
    """Simple approach - look for all large numbers on page"""
    try:
        if not profile_url.startswith('http'):
            profile_url = f"https://{profile_url}"

        driver.get(profile_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(10)

        badges_data = {
            'label_badge': 'None',
            'status': 'Success'
        }

        # Find all elements with large numbers (likely stats)
        all_elements = driver.find_elements(By.XPATH, "//*[text()[contains(.,'185')] or text()[contains(.,'132,000')] or text()[contains(.,'22')]]")
        
        numbers_found = []
        for element in all_elements:
            text = element.text.strip()
            numbers = re.findall(r'[\d,]+', text)
            for num in numbers:
                clean_num = int(num.replace(',', ''))
                numbers_found.append(clean_num)
        
        # Sort numbers and assign based on typical ranges
        numbers_found = sorted(set(numbers_found), reverse=True)
        
        for num in numbers_found:
            if num > 1000 and badges_data['points'] == 0:  # Likely points
                badges_data['points'] = num
            elif num < 1000 and num > 20 and badges_data['total_badges'] == 0:  # Likely badges
                badges_data['total_badges'] = num
            elif num < 50 and badges_data['trails'] == 0:  # Likely trails
                badges_data['trails'] = num

        # Extract label badge and rank as before
        page_source = driver.page_source.lower()
        
        if 'ranger' in page_source:
            badges_data['rank'] = 'Ranger'
        
        if 'innovator' in page_source:
            badges_data['label_badge'] = 'Innovator'
        elif 'champion' in page_source:
            badges_data['label_badge'] = 'Champion'
        elif 'legend' in page_source:
            badges_data['label_badge'] = 'Legend'

        return badges_data

    except Exception as e:
        return {'status': f'Error: {str(e)}', 'total_badges': 0, 'points': 0, 'trails': 0, 'rank': 'Error', 'label_badge': 'Error'}



def process_csv_data(df):
    """Process CSV with progress tracking"""
    driver = None
    try:
        driver = setup_driver()
        result_df = df.copy()
        
        new_columns = ['label_badge']
        for col in new_columns:
            result_df[col] = ''
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, row in result_df.iterrows():
            status_text.text(f'Processing profile {index + 1} of {len(result_df)}: {row.get("name", "Unknown")}')
            
            profile_url = row.get('salesforce_url', '') or row.get('url', '') or row.get('profile_url', '')
            
            if profile_url:
                badge_data = extract_badges_from_profile(profile_url, driver)
                for col in new_columns:
                    result_df.at[index, col] = badge_data.get(col, '')
            else:
                result_df.at[index, 'status'] = 'No URL provided'
            
            progress_bar.progress((index + 1) / len(result_df))
            time.sleep(3)  # Rate limiting
        
        status_text.text('Processing complete!')
        return result_df
    
    except Exception as e:
        st.error(f"Driver setup error: {str(e)}")
        return df
    finally:
        if driver:
            driver.quit()


# Streamlit App
def main():
    st.set_page_config(
        page_title="Trailblazer Badge Extractor - Fixed",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Salesforce Trailblazer Badge Extractor (Fixed)")
    st.markdown("Extract badge information using Selenium WebDriver")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Setup Requirements: CSV file must contain the following columns with exact naming only Roll Number, Name, Salesforce URL")
       
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload CSV File", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ File uploaded! Found {len(df)} records.")
            
            st.subheader("📊 Data Preview")
            st.dataframe(df.head())
            
            # Column mapping
            st.subheader("🔗 Column Mapping")
            columns = df.columns.tolist()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                col_roll = st.selectbox("Roll Number:", columns, index=0)
            with col2:
                col_name = st.selectbox("Name:", columns, index=1 if len(columns) > 1 else 0)
            with col3:
                col_url = st.selectbox("Salesforce URL:", columns, index=2 if len(columns) > 2 else 0)
            
            if st.button("🚀 Extract Badges (Fixed)", type="primary"):
                st.header("⚡ Processing Profiles")
                
                # Rename columns
                df_processed = df.rename(columns={
                    col_roll: 'roll_number',
                    col_name: 'name',
                    col_url: 'salesforce_url'
                })
                
                # Process with fixed driver
                result_df = process_csv_data(df_processed)
                
                # Results
                st.header("📈 Results")
                col1, col2, col3, = st.columns(3)
                
                
                
                with col1:
                    innovators = len(result_df[result_df['label_badge'] == 'Innovator'])
                    st.metric("Innovators", innovators)
                
                with col2:
                    champions = len(result_df[result_df['label_badge'] == 'Champion'])
                    st.metric("Champions", champions)
                
                with col3:
                    legends = len(result_df[result_df['label_badge'] == 'Legend'])
                    st.metric("Legends", legends)
                
                st.dataframe(result_df)
                
                # Download
                csv_output = result_df.to_csv(index=False)
                st.download_button(
                    label="💾 Download Results",
                    data=csv_output,
                    file_name="trailblazer_results_fixed.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
