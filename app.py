import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def setup_driver():
    """Setup Chrome driver for Shadow DOM scraping"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    return webdriver.Chrome(options=options)

def extract_badge_from_shadow_dom(driver, profile_url):
    """Extract badge from Shadow DOM structure you found"""
    try:
        driver.get(profile_url)
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(10)
        
        # Method 1: Find the exact shadow host you discovered
        shadow_host_selectors = [
            "lwc-tbui-learner-status-level",
            "[class*='learner-status-level']",
            "[class*='tbui-learner']"
        ]
        
        for selector in shadow_host_selectors:
            try:
                # Find shadow host
                shadow_host = driver.find_element(By.CSS_SELECTOR, selector)
                
                # Get shadow root using JavaScript
                shadow_root = driver.execute_script("return arguments[0].shadowRoot", shadow_host)
                
                if shadow_root:
                    # Look for the container div inside shadow root
                    container = driver.execute_script(
                        "return arguments[0].querySelector('.container')", 
                        shadow_root
                    )
                    
                    if container:
                        # Find the badge image
                        badge_img = driver.execute_script(
                            "return arguments[0].querySelector('img')", 
                            container
                        )
                        
                        if badge_img:
                            # Extract badge information
                            src = driver.execute_script("return arguments[0].src", badge_img)
                            alt_text = driver.execute_script("return arguments[0].alt", badge_img)
                            
                            # Determine badge level from your exact pattern
                            if "banner-level-3.png" in src:
                                badge_level = "Legend"
                            elif "banner-level-2.png" in src:
                                badge_level = "Innovator"  # This matches your screenshot!
                            elif "banner-level-1.png" in src:
                                badge_level = "Champion"
                            else:
                                # Fallback to alt text analysis
                                alt_lower = alt_text.lower() if alt_text else ""
                                if "legend" in alt_lower:
                                    badge_level = "Legend"
                                elif "innovator" in alt_lower:
                                    badge_level = "Innovator"
                                elif "champion" in alt_lower:
                                    badge_level = "Champion"
                                else:
                                    badge_level = "Unknown"
                            
                            return {
                                'badge_level': badge_level,
                                'badge_src': src,
                                'alt_text': alt_text,
                                'detection_method': f'Shadow DOM - {selector}',
                                'status': 'Success'
                            }
            
            except Exception as e:
                continue  # Try next selector
        
        # Method 2: Generic shadow DOM traversal
        shadow_elements = driver.execute_script("""
            function findShadowRoots(element) {
                let shadowRoots = [];
                
                function traverse(el) {
                    if (el.shadowRoot) {
                        shadowRoots.push(el);
                        // Look inside shadow root
                        const shadowElements = el.shadowRoot.querySelectorAll('*');
                        shadowElements.forEach(traverse);
                    }
                    
                    // Also check children
                    el.children && Array.from(el.children).forEach(traverse);
                }
                
                traverse(element);
                return shadowRoots;
            }
            
            const shadowHosts = findShadowRoots(document.body);
            const results = [];
            
            shadowHosts.forEach(host => {
                const images = host.shadowRoot.querySelectorAll('img[src*="agentblazer"], img[alt*="agentblazer"]');
                images.forEach(img => {
                    results.push({
                        src: img.src,
                        alt: img.alt,
                        hostTag: host.tagName
                    });
                });
            });
            
            return results;
        """)
        
        if shadow_elements:
            for element in shadow_elements:
                src = element.get('src', '')
                alt_text = element.get('alt', '')
                
                # Determine badge level
                if "banner-level-3.png" in src:
                    badge_level = "Legend"
                elif "banner-level-2.png" in src:
                    badge_level = "Innovator"
                elif "banner-level-1.png" in src:
                    badge_level = "Champion"
                else:
                    badge_level = "Unknown"
                
                return {
                    'badge_level': badge_level,
                    'badge_src': src,
                    'alt_text': alt_text,
                    'detection_method': 'Generic Shadow DOM Search',
                    'status': 'Success'
                }
        
        return {
            'badge_level': 'None',
            'badge_src': '',
            'alt_text': '',
            'detection_method': 'No Shadow DOM badges found',
            'status': 'No Badge Found'
        }
        
    except Exception as e:
        return {
            'badge_level': 'Error',
            'badge_src': '',
            'alt_text': '',
            'detection_method': 'Exception occurred',
            'status': f'Error: {str(e)}'
        }

def main():
    st.set_page_config(
        page_title="Shadow DOM Badge Extractor",
        page_icon="👻",
        layout="wide"
    )
    
    st.title("👻 Shadow DOM Badge Extractor")
    st.success("✅ Specifically designed for Salesforce Shadow DOM structure!")
    
    # Show the discovered structure
    with st.expander("🔍 Discovered Shadow DOM Structure"):
        st.code("""
        lwc-tbui-learner-status-level
        └── #shadow-root (open)
            └── div class="container"
                └── img src="https://trailhead.salesforce.com/agentblazer/banner-level-2.png" 
                    alt="Agentblazer Innovator"
        """, language="html")
    
    # Single profile test
    st.subheader("🧪 Test Shadow DOM Extraction")
    
    profile_url = st.text_input(
        "Salesforce Profile URL:",
        value="https://www.salesforce.com/trailblazer/aarathisreeballa",
        placeholder="https://www.salesforce.com/trailblazer/username"
    )
    
    if st.button("👻 Extract from Shadow DOM", type="primary"):
        if profile_url:
            driver = setup_driver()
            
            try:
                with st.spinner("Accessing Shadow DOM..."):
                    result = extract_badge_from_shadow_dom(driver, profile_url)
                
                if result['status'] == 'Success':
                    st.success(f"🎉 **Badge Detected: {result['badge_level']}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Badge Details")
                        st.write(f"**Level:** {result['badge_level']}")
                        st.write(f"**Alt Text:** {result['alt_text']}")
                        st.write(f"**Detection Method:** {result['detection_method']}")
                    
                    with col2:
                        st.subheader("📷 Badge Image")
                        if result['badge_src']:
                            st.image(result['badge_src'], caption=f"Agentblazer {result['badge_level']}", width=300)
                            st.write(f"**Image URL:** `{result['badge_src']}`")
                
                else:
                    st.warning(f"❌ {result['status']}")
                    st.write(f"**Method:** {result['detection_method']}")
                
            finally:
                driver.quit()
    
    # Batch processing
    st.divider()
    st.subheader("📂 Batch Shadow DOM Processing")
    
    uploaded_file = st.file_uploader("Upload CSV with profiles", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} profiles")
            st.dataframe(df.head())
            
            if st.button("🚀 Process All with Shadow DOM", type="primary"):
                driver = setup_driver()
                
                try:
                    results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, row in df.iterrows():
                        progress = (idx + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {idx+1}/{len(df)}: {row['Name']}")
                        
                        result = extract_badge_from_shadow_dom(driver, row['Salesforce URL'])
                        
                        results.append({
                            'Roll Number': row['Roll Number'],
                            'Name': row['Name'],
                            'Salesforce URL': row['Salesforce URL'],
                            'Badge Level': result['badge_level'],
                            'Badge Image URL': result['badge_src'],
                            'Alt Text': result['alt_text'],
                            'Detection Method': result['detection_method'],
                            'Status': result['status']
                        })
                        
                        # Small delay between requests
                        time.sleep(3)
                    
                    # Display results
                    results_df = pd.DataFrame(results)
                    
                    st.success("🎉 Shadow DOM extraction completed!")
                    
                    # Summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total", len(results_df))
                    
                    with col2:
                        successful = len(results_df[results_df['Status'] == 'Success'])
                        st.metric("Successful", successful)
                    
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
                        "📥 Download Shadow DOM Results",
                        csv_data,
                        f"shadow_dom_badge_results_{int(time.time())}.csv",
                        "text/csv"
                    )
                
                finally:
                    driver.quit()

if __name__ == "__main__":
    main()
