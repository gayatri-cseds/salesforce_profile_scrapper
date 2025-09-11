import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class BulkBadgeProcessor:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers
        
    def setup_driver(self):
        """Setup optimized Chrome driver"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-web-security")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Performance optimizations
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,  # Block images
                "plugins": 2,
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
            }
        }
        options.add_experimental_option("prefs", prefs)
        
        return webdriver.Chrome(options=options)
    
    def extract_badge_with_js_wait(self, url, retries=3):
        """Enhanced badge extraction with JavaScript wait"""
        driver = None
        
        for attempt in range(retries):
            try:
                driver = self.setup_driver()
                
                # Load page
                driver.get(url)
                
                # Wait for initial content
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Execute JavaScript to wait for dynamic content
                driver.execute_script("""
                    return new Promise((resolve) => {
                        // Wait for agentblazer content to load
                        let attempts = 0;
                        const checkForBadges = () => {
                            const agentblazerElements = document.querySelectorAll('[src*="agentblazer"], [alt*="agentblazer"]');
                            if (agentblazerElements.length > 0 || attempts > 20) {
                                resolve();
                            } else {
                                attempts++;
                                setTimeout(checkForBadges, 500);
                            }
                        };
                        checkForBadges();
                    });
                """)
                
                # Get page source after JS execution
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Look for agentblazer badge images
                agentblazer_images = soup.find_all('img')
                
                for img in agentblazer_images:
                    src = str(img.get('src', ''))
                    alt = str(img.get('alt', ''))
                    
                    if 'agentblazer' in src.lower() or 'agentblazer' in alt.lower():
                        # Exact pattern matching
                        if 'banner-level-3.png' in src:
                            return {'badge': 'Legend', 'image_url': src, 'method': 'Image URL'}
                        elif 'banner-level-2.png' in src:
                            return {'badge': 'Innovator', 'image_url': src, 'method': 'Image URL'}
                        elif 'banner-level-1.png' in src:
                            return {'badge': 'Champion', 'image_url': src, 'method': 'Image URL'}
                        
                        # Alt text fallback
                        alt_lower = alt.lower()
                        if 'legend' in alt_lower:
                            return {'badge': 'Legend', 'image_url': src, 'method': 'Alt Text'}
                        elif 'innovator' in alt_lower:
                            return {'badge': 'Innovator', 'image_url': src, 'method': 'Alt Text'}
                        elif 'champion' in alt_lower:
                            return {'badge': 'Champion', 'image_url': src, 'method': 'Alt Text'}
                
                return {'badge': 'None', 'image_url': '', 'method': 'No Badge Found'}
                
            except Exception as e:
                if attempt == retries - 1:
                    return {'badge': 'Error', 'image_url': '', 'method': f'Error: {str(e)}'}
                time.sleep(2)  # Wait before retry
                
            finally:
                if driver:
                    driver.quit()
    
    def process_bulk_profiles(self, profiles, progress_callback=None):
        """Process multiple profiles concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_profile = {
                executor.submit(self.extract_badge_with_js_wait, profile['Salesforce URL']): profile 
                for profile in profiles
            }
            
            completed = 0
            total = len(profiles)
            
            # Process results as they complete
            for future in as_completed(future_to_profile):
                profile = future_to_profile[future]
                
                try:
                    badge_result = future.result(timeout=60)  # 60 second timeout per profile
                    
                    result = {
                        'Roll Number': profile.get('Roll Number', ''),
                        'Name': profile.get('Name', ''),
                        'Salesforce URL': profile.get('Salesforce URL', ''),
                        'Badge Level': badge_result['badge'],
                        'Badge Image URL': badge_result['image_url'],
                        'Detection Method': badge_result['method'],
                        'Status': 'Success' if badge_result['badge'] != 'Error' else 'Failed'
                    }
                    
                except Exception as e:
                    result = {
                        'Roll Number': profile.get('Roll Number', ''),
                        'Name': profile.get('Name', ''),
                        'Salesforce URL': profile.get('Salesforce URL', ''),
                        'Badge Level': 'Error',
                        'Badge Image URL': '',
                        'Detection Method': f'Processing Error: {str(e)}',
                        'Status': 'Failed'
                    }
                
                results.append(result)
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, total, result)
        
        return results

def main():
    st.set_page_config(
        page_title="Bulk Badge Processor",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Bulk Salesforce Badge Processor")
    st.success("✅ Professional bulk processing for faculty - handles hundreds of profiles!")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Student Data CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} student profiles")
            st.dataframe(df.head())
            
            # Configuration
            st.subheader("⚙️ Bulk Processing Configuration")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max_workers = st.slider("Concurrent browsers", 1, 10, 5)
                st.info("More browsers = faster processing")
            
            with col2:
                batch_size = st.number_input("Batch size", 10, len(df), min(50, len(df)))
                st.info("Process in smaller batches for reliability")
            
            with col3:
                delay = st.slider("Delay between batches (seconds)", 0, 30, 10)
                st.info("Prevents overwhelming servers")
            
            # Processing
            if st.button("🚀 Start Bulk Processing", type="primary"):
                
                processor = BulkBadgeProcessor(max_workers=max_workers)
                
                # Convert to list of dictionaries
                profiles = df.to_dict('records')
                
                # Process in batches
                all_results = []
                total_batches = (len(profiles) + batch_size - 1) // batch_size
                
                # Progress containers
                main_progress = st.progress(0)
                batch_progress = st.progress(0)
                status_text = st.empty()
                results_container = st.empty()
                
                for batch_idx in range(0, len(profiles), batch_size):
                    batch_profiles = profiles[batch_idx:batch_idx + batch_size]
                    current_batch = (batch_idx // batch_size) + 1
                    
                    status_text.text(f"Processing batch {current_batch}/{total_batches} ({len(batch_profiles)} profiles)")
                    
                    # Progress callback for this batch
                    def update_progress(completed, total, result):
                        batch_progress.progress(completed / total)
                        # Show latest result
                        with results_container.container():
                            st.write(f"✅ {result['Name']}: {result['Badge Level']}")
                    
                    # Process batch
                    batch_results = processor.process_bulk_profiles(
                        batch_profiles, 
                        progress_callback=update_progress
                    )
                    
                    all_results.extend(batch_results)
                    
                    # Update main progress
                    main_progress.progress(len(all_results) / len(profiles))
                    
                    # Delay between batches (except last)
                    if current_batch < total_batches and delay > 0:
                        status_text.text(f"Waiting {delay}s before next batch...")
                        time.sleep(delay)
                
                # Final results
                results_df = pd.DataFrame(all_results)
                
                st.success("🎉 Bulk processing completed!")
                
                # Comprehensive statistics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Processed", len(results_df))
                
                with col2:
                    successful = len(results_df[results_df['Status'] == 'Success'])
                    st.metric("Successful", successful)
                
                with col3:
                    champions = len(results_df[results_df['Badge Level'] == 'Champion'])
                    st.metric("Champions", champions)
                
                with col4:
                    innovators = len(results_df[results_df['Badge Level'] == 'Innovator'])
                    st.metric("Innovators", innovators)
                
                with col5:
                    legends = len(results_df[results_df['Badge Level'] == 'Legend'])
                    st.metric("Legends", legends)
                
                # Additional metrics
                col6, col7, col8 = st.columns(3)
                
                with col6:
                    no_badges = len(results_df[results_df['Badge Level'] == 'None'])
                    st.metric("No Badge", no_badges)
                
                with col7:
                    errors = len(results_df[results_df['Badge Level'] == 'Error'])
                    st.metric("Errors", errors)
                
                with col8:
                    success_rate = (successful / len(results_df)) * 100 if len(results_df) > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Detailed results
                st.subheader("📊 Detailed Results")
                st.dataframe(results_df, use_container_width=True)
                
                # Badge distribution chart
                if not results_df.empty:
                    badge_counts = results_df['Badge Level'].value_counts()
                    st.subheader("📈 Badge Distribution")
                    st.bar_chart(badge_counts)
                
                # Download options
                st.subheader("📥 Download Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Full results
                    csv_data = results_df.to_csv(index=False)
                    st.download_button(
                        "📊 Download Full Results",
                        csv_data,
                        f"bulk_badge_results_{int(time.time())}.csv",
                        "text/csv",
                        type="primary"
                    )
                
                with col2:
                    # Summary report
                    summary_data = {
                        'Metric': ['Total Students', 'Champions', 'Innovators', 'Legends', 'No Badge', 'Errors', 'Success Rate'],
                        'Count': [len(results_df), champions, innovators, legends, no_badges, errors, f"{success_rate:.1f}%"]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_csv = summary_df.to_csv(index=False)
                    st.download_button(
                        "📋 Download Summary Report", 
                        summary_csv,
                        f"badge_summary_{int(time.time())}.csv",
                        "text/csv"
                    )

if __name__ == "__main__":
    main()
