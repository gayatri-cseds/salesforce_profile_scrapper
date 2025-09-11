import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

def extract_badge_level(url):
    """
    Extract badge level from Salesforce trailblazer profile URL
    Returns: Champion (level1), Innovator (level2), Legend (level3), or None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for badge level images based on your inspection pattern
        badge_patterns = [
            # Agentblazer badges (Champion, Innovator, Legend)
            (r'banner-level-1\.png', 'Champion'),
            (r'banner-level-2\.png', 'Innovator'), 
            (r'banner-level-3\.png', 'Legend'),
            # Alternative patterns for different badge types
            (r'champion', 'Champion'),
            (r'innovator', 'Innovator'),
            (r'legend', 'Legend')
        ]
        
        # Search in img src attributes
        for img in soup.find_all('img'):
            src = img.get('src', '').lower()
            alt = img.get('alt', '').lower()
            
            for pattern, level in badge_patterns:
                if re.search(pattern, src) or re.search(pattern, alt):
                    return level
        
        # Search in CSS classes and other attributes
        for element in soup.find_all():
            class_attr = ' '.join(element.get('class', [])).lower()
            for pattern, level in badge_patterns:
                if re.search(pattern, class_attr):
                    return level
        
        return "None"
        
    except Exception as e:
        st.error(f"Error processing {url}: {str(e)}")
        return "Error"

def process_single_row(row):
    """Process a single row of data"""
    roll_number, name, url = row['Roll Number'], row['Name'], row['Salesforce URL']
    badge_level = extract_badge_level(url)
    
    # Map to level numbers
    level_mapping = {
        'Champion': 'Level 1',
        'Innovator': 'Level 2', 
        'Legend': 'Level 3',
        'None': 'None',
        'Error': 'Error'
    }
    
    return {
        'Roll Number': roll_number,
        'Name': name,
        'Salesforce URL': url,
        'Badge Status': badge_level,
        'Level': level_mapping.get(badge_level, 'Unknown')
    }

def main():
    st.set_page_config(
        page_title="Salesforce Badge Extractor",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Salesforce Trailblazer Badge Extractor")
    st.markdown("Upload a CSV file with Roll Number, Name, and Salesforce public URLs to extract badge levels.")
    
    # Sidebar with information
    with st.sidebar:
        st.header("Badge Levels")
        st.markdown("""
        **Agentblazer Badges:**
        - 🥉 **Champion** → Level 1
        - 🥈 **Innovator** → Level 2  
        - 🥇 **Legend** → Level 3
        - ❌ **None** → No badge found
        
        **Expected CSV Format:**
        - Roll Number
        - Name  
        - Salesforce URL
        """)
        
        st.header("Sample URL Format")
        st.code("https://www.salesforce.com/trailblazer/username")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file", 
        type="csv",
        help="Upload a CSV file with columns: Roll Number, Name, Salesforce URL"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Validate required columns
            required_columns = ['Roll Number', 'Name', 'Salesforce URL']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                st.info("Please ensure your CSV has columns: Roll Number, Name, Salesforce URL")
                return
            
            st.success(f"✅ CSV loaded successfully! Found {len(df)} records.")
            
            # Display preview
            with st.expander("📋 Data Preview", expanded=True):
                st.dataframe(df.head())
            
            # Processing options
            col1, col2 = st.columns(2)
            with col1:
                max_workers = st.slider("Concurrent requests", 1, 10, 3, 
                                      help="Number of simultaneous requests (higher = faster but may cause rate limiting)")
            with col2:
                delay = st.slider("Delay between requests (seconds)", 0.0, 5.0, 1.0, 0.5,
                                help="Delay to avoid overwhelming the server")
            
            # Process button
            if st.button("🚀 Extract Badge Levels", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.empty()
                
                results = []
                total_rows = len(df)
                
                # Process with threading for better performance
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    future_to_row = {
                        executor.submit(process_single_row, row): idx 
                        for idx, (_, row) in enumerate(df.iterrows())
                    }
                    
                    # Collect results as they complete
                    for completed, future in enumerate(as_completed(future_to_row)):
                        try:
                            result = future.result()
                            results.append(result)
                            
                            # Update progress
                            progress = (completed + 1) / total_rows
                            progress_bar.progress(progress)
                            status_text.text(f"Processed {completed + 1}/{total_rows} records...")
                            
                            # Add delay to avoid rate limiting
                            if delay > 0:
                                time.sleep(delay)
                                
                        except Exception as e:
                            st.error(f"Error processing record: {str(e)}")
                
                # Create results DataFrame
                results_df = pd.DataFrame(results)
                
                # Display results
                st.success("🎉 Processing completed!")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", len(results_df))
                with col2:
                    champions = len(results_df[results_df['Badge Status'] == 'Champion'])
                    st.metric("Champions", champions)
                with col3:
                    innovators = len(results_df[results_df['Badge Status'] == 'Innovator'])
                    st.metric("Innovators", innovators)
                with col4:
                    legends = len(results_df[results_df['Badge Status'] == 'Legend'])
                    st.metric("Legends", legends)
                
                # Results table
                st.subheader("📊 Results")
                st.dataframe(results_df, use_container_width=True)
                
                # Download button
                csv_buffer = io.StringIO()
                results_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_data,
                    file_name=f"salesforce_badges_results_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            st.info("Please check that your CSV file is properly formatted.")

if __name__ == "__main__":
    main()
