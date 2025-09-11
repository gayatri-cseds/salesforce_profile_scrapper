import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def setup_driver():
    """Setup Chrome driver optimized for Shadow DOM"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    return webdriver.Chrome(options=options)

def debug_page_structure(driver):
    """Debug: Show all shadow hosts on the page"""
    shadow_hosts = driver.execute_script("""
        function findAllShadowHosts(element) {
            let shadowHosts = [];
            
            function traverse(el) {
                if (el.shadowRoot) {
                    shadowHosts.push({
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id
                    });
                    
                    // Recursively check inside shadow root
                    const shadowElements = el.shadowRoot.querySelectorAll('*');
                    shadowElements.forEach(traverse);
                }
                
                // Check children
                if (el.children) {
                    Array.from(el.children).forEach(traverse);
                }
            }
            
            traverse(element);
            return shadowHosts;
        }
        
        return findAllShadowHosts(document.body);
    """)
    
    return shadow_hosts

def extract_badge_advanced_shadow_dom(driver, profile_url):
    """Advanced Shadow DOM extraction with proper nested traversal"""
    try:
        st.info(f"🔍 Loading: {profile_url}")
        driver.get(profile_url)
        
        # Wait for initial load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for Shadow DOM content
        time.sleep(15)
        
        st.info("🔍 Debugging page structure...")
        shadow_hosts = debug_page_structure(driver)
        st.write(f"Found {len(shadow_hosts)} shadow hosts: {shadow_hosts}")
        
        # Method 1: Modern Selenium 4+ Shadow Root approach
        try:
            st.info("🔍 Trying modern shadow root approach...")
            
            # Look for common shadow host patterns
            shadow_host_patterns = [
                "lwc-tbui-learner-status-level",
                "[class*='learner-status']",
                "[class*='tbui']",
                "[class*='badge']",
                "c-tbui-learner-status-level",
                "force-record-layout-item"
            ]
            
            for pattern in shadow_host_patterns:
                try:
                    shadow_hosts_elements = driver.find_elements(By.CSS_SELECTOR, pattern)
                    st.write(f"Found {len(shadow_hosts_elements)} elements with pattern: {pattern}")
                    
                    for shadow_host in shadow_hosts_elements:
                        try:
                            # Use modern shadow root property (Selenium 4+)
                            shadow_root = shadow_host.shadow_root
                            
                            if shadow_root:
                                st.success(f"✅ Accessed shadow root with pattern: {pattern}")
                                
                                # Look for nested shadow hosts or direct images
                                possible_selectors = [
                                    "img[src*='agentblazer']",
                                    "img[alt*='agentblazer']",
                                    "img[src*='banner-level']",
                                    ".container img",
                                    "div img",
                                    "*[class*='badge'] img"
                                ]
                                
                                for selector in possible_selectors:
                                    try:
                                        images = shadow_root.find_elements(By.CSS_SELECTOR, selector)
                                        st.write(f"Found {len(images)} images with selector: {selector}")
                                        
                                        for img in images:
                                            src = img.get_attribute('src')
                                            alt = img.get_attribute('alt')
                                            
                                            st.write(f"Image found - src: {src}, alt: {alt}")
                                            
                                            if src and ('agentblazer' in src.lower() or 'banner-level' in src.lower()):
                                                # Extract badge level
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
                                                    'alt_text': alt,
                                                    'detection_method': f'Modern Shadow Root - {pattern} -> {selector}',
                                                    'status': 'Success'
                                                }
                                    except Exception as e:
                                        continue
                                
                                # Check for nested shadow hosts
                                nested_hosts = shadow_root.find_elements(By.CSS_SELECTOR, "*")
                                st.write(f"Checking {len(nested_hosts)} nested elements...")
                                
                                for nested_element in nested_hosts:
                                    try:
                                        if hasattr(nested_element, 'shadow_root'):
                                            nested_shadow = nested_element.shadow_root
                                            if nested_shadow:
                                                nested_images = nested_shadow.find_elements(By.CSS_SELECTOR, "img")
                                                for img in nested_images:
                                                    src = img.get_attribute('src')
                                                    alt = img.get_attribute('alt')
                                                    
                                                    if src and 'agentblazer' in src.lower():
                                                        st.success(f"Found nested badge: {src}")
                                                        return {
                                                            'badge_level': 'Detected',
                                                            'badge_src': src,
                                                            'alt_text': alt,
                                                            'detection_method': 'Nested Shadow Root',
                                                            'status': 'Success'
                                                        }
                                    except:
                                        continue
                        
                        except Exception as e:
                            st.write(f"Error accessing shadow root: {str(e)}")
                            continue
                            
                except NoSuchElementException:
                    continue
        
        except Exception as e:
            st.error(f"Modern approach failed: {str(e)}")
        
        # Method 2: JavaScript-based comprehensive search
        st.info("🔍 Trying comprehensive JavaScript search...")
        
        badge_data = driver.execute_script("""
            function findBadgesInAllShadowRoots(element) {
                let badges = [];
                
                function searchElement(el, path = '') {
                    // Check current element for badges
                    if (el.tagName === 'IMG') {
                        const src = el.src || '';
                        const alt = el.alt || '';
                        
                        if (src.includes('agentblazer') || alt.includes('agentblazer') || src.includes('banner-level')) {
                            badges.push({
                                src: src,
                                alt: alt,
                                path: path
                            });
                        }
                    }
                    
                    // If element has shadow root, search inside
                    if (el.shadowRoot) {
                        const shadowElements = el.shadowRoot.querySelectorAll('*');
                        shadowElements.forEach((shadowEl, index) => {
                            searchElement(shadowEl, path + ` -> shadow[${index}]`);
                        });
                    }
                    
                    // Search children
                    if (el.children) {
                        Array.from(el.children).forEach((child, index) => {
                            searchElement(child, path + ` -> child[${index}]`);
                        });
                    }
                }
                
                searchElement(element, 'body');
                return badges;
            }
            
            return findBadgesInAllShadowRoots(document.body);
        """)
        
        st.write(f"JavaScript search found: {badge_data}")
        
        if badge_data:
            for badge in badge_data:
                src = badge.get('src', '')
                alt = badge.get('alt', '')
                path = badge.get('path', '')
                
                if src:
                    # Determine badge level
                    if "banner-level-3.png" in src:
                        badge_level = "Legend"
                    elif "banner-level-2.png" in src:
                        badge_level = "Innovator"
                    elif "banner-level-1.png" in src:
                        badge_level = "Champion"
                    else:
                        badge_level = "Found"
                    
                    return {
                        'badge_level': badge_level,
                        'badge_src': src,
                        'alt_text': alt,
                        'detection_method': f'JavaScript Deep Search - {path}',
                        'status': 'Success'
                    }
        
        # Method 3: Check page source as final fallback
        page_source = driver.page_source
        if 'agentblazer' in page_source.lower():
            st.info("Found 'agentblazer' in page source, but couldn't locate specific elements")
            return {
                'badge_level': 'Present in Source',
                'badge_src': '',
                'alt_text': '',
                'detection_method': 'Page Source Analysis',
                'status': 'Partial Success'
            }
        
        return {
            'badge_level': 'None',
            'badge_src': '',
            'alt_text': '',
            'detection_method': 'All methods exhausted',
            'status': 'No Badge Found'
        }
        
    except Exception as e:
        return {
            'badge_level': 'Error',
            'badge_src': '',
            'alt_text': '',
            'detection_method': 'Exception in processing',
            'status': f'Error: {str(e)}'
        }

def main():
    st.set_page_config(
        page_title="Advanced Shadow DOM Extractor",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Advanced Shadow DOM Badge Extractor")
    st.success("✅ Multi-level Shadow DOM traversal with comprehensive debugging!")
    
    # Debug mode toggle
    debug_mode = st.checkbox("🐛 Enable Debug Mode", value=True)
    
    profile_url = st.text_input(
        "Salesforce Profile URL:",
        value="https://www.salesforce.com/trailblazer/aarathisreeballa",
        placeholder="https://www.salesforce.com/trailblazer/username"
    )
    
    if st.button("🔍 Advanced Shadow DOM Extraction", type="primary"):
        if profile_url:
            driver = setup_driver()
            
            try:
                with st.spinner("Performing advanced Shadow DOM analysis..."):
                    result = extract_badge_advanced_shadow_dom(driver, profile_url)
                
                if result['status'] == 'Success':
                    st.success(f"🎉 **Badge Detected: {result['badge_level']}**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Badge Details")
                        st.write(f"**Level:** {result['badge_level']}")
                        st.write(f"**Alt Text:** {result['alt_text']}")
                        st.write(f"**Detection Method:** {result['detection_method']}")
                        st.write(f"**Status:** {result['status']}")
                    
                    with col2:
                        st.subheader("📷 Badge Image")
                        if result['badge_src']:
                            st.image(result['badge_src'], caption=f"Badge: {result['badge_level']}", width=300)
                            st.code(result['badge_src'])
                
                else:
                    st.warning(f"⚠️ {result['status']}")
                    st.write(f"**Detection Method:** {result['detection_method']}")
                    
                    if debug_mode:
                        st.subheader("🐛 Debug Information")
                        st.write("**Troubleshooting Steps:**")
                        st.write("1. Check if the profile is public")
                        st.write("2. Verify the profile has Agentblazer badges")
                        st.write("3. Try accessing the profile manually to confirm badge visibility")
                        st.write("4. The profile might be using a different Shadow DOM structure")
                
            finally:
                driver.quit()
    
    # Instructions
    with st.expander("🔧 Troubleshooting Guide"):
        st.markdown("""
        ### **Common Issues & Solutions:**
        
        1. **"No Badge Found"**: 
           - Profile might be private
           - User might not have Agentblazer badges
           - Badge might be in different Shadow DOM structure
        
        2. **"Error in processing"**: 
           - Network connectivity issues
           - Profile URL might be incorrect
           - Chrome driver compatibility
        
        3. **Empty Results**: 
           - Salesforce might have changed their DOM structure
           - Anti-bot protection might be active
           - Profile content is loading dynamically
        
        ### **Manual Verification:**
        1. Open the profile URL in a browser
        2. Look for Agentblazer badge images
        3. Use browser inspect element to verify Shadow DOM structure
        4. Check if badges are visible without JavaScript
        """)

if __name__ == "__main__":
    main()
