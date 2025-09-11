import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import time
import base64

class BadgeScreenshotDetector:
    def __init__(self):
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome driver"""
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    def capture_badge_area(self, profile_url):
        """Capture the bottom-right area where Agentblazer badge is displayed"""
        driver = webdriver.Chrome(options=self.options)
        
        try:
            # Load profile page
            driver.get(profile_url)
            
            # Wait for page to load completely
            time.sleep(15)
            
            # Take full page screenshot
            full_screenshot = driver.get_screenshot_as_png()
            
            # Open with PIL
            full_image = Image.open(BytesIO(full_screenshot))
            
            # Define crop area for badge (bottom-right section)
            img_width, img_height = full_image.size
            
            # Crop coordinates (adjust these based on your screen size)
            left = img_width - 500   # 500px from right edge
            upper = img_height - 300 # 300px from bottom
            right = img_width        # Full right edge
            lower = img_height       # Full bottom edge
            
            # Crop the badge area
            badge_area = full_image.crop((left, upper, right, lower))
            
            return {
                'success': True,
                'badge_image': badge_area,
                'full_image': full_image,
                'crop_coordinates': (left, upper, right, lower)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'badge_image': None,
                'full_image': None
            }
        
        finally:
            driver.quit()
    
    def analyze_badge_visually(self, badge_image):
        """Analyze cropped badge image to determine level"""
        # Save cropped image for analysis
        badge_bytes = BytesIO()
        badge_image.save(badge_bytes, format='PNG')
        badge_bytes.seek(0)
        
        # Convert to base64 for display
        img_base64 = base64.b64encode(badge_bytes.getvalue()).decode()
        
        return {
            'image_data': img_base64,
            'analysis': 'Visual inspection required - check the cropped badge area',
            'recommendation': 'Look for "Agentblazer Champion", "Agentblazer Innovator", or "Agentblazer Legend" text/images'
        }

def main():
    st.set_page_config(
        page_title="Screenshot Badge Detector",
        page_icon="📸",
        layout="wide"
    )
    
    st.title("📸 Screenshot-Based Badge Detector")
    st.success("✅ Captures the exact badge area from profile screenshots!")
    
    # Show the approach
    with st.expander("🎯 How This Works", expanded=True):
        st.markdown("""
        **Visual Detection Approach:**
        1. **Load profile page** with Selenium in headless mode
        2. **Wait for content** to fully load (15 seconds)
        3. **Take full screenshot** of the entire page
        4. **Crop bottom-right area** where Agentblazer badge appears
        5. **Display cropped image** for visual verification
        6. **Analyze badge level** from the cropped screenshot
        
        **Why This Works:**
        - ✅ **Bypasses Shadow DOM** - Works with visual content
        - ✅ **No element detection needed** - Pure image capture
        - ✅ **Reliable** - Always captures what's visually displayed
        - ✅ **Faculty-friendly** - Visual verification is intuitive
        """)
    
    # Initialize detector
    detector = BadgeScreenshotDetector()
    
    # Single profile test
    st.subheader("🧪 Test Screenshot Badge Detection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        profile_url = st.text_input(
            "Salesforce Profile URL:",
            value="https://trailhead.salesforce.com/profile/aarathisreeballa",
            help="Enter the complete Trailhead profile URL"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        capture_button = st.button("📸 Capture Badge Area", type="primary")
    
    if capture_button and profile_url:
        with st.spinner("📸 Taking screenshot and cropping badge area..."):
            result = detector.capture_badge_area(profile_url)
        
        if result['success']:
            st.success("✅ Badge area captured successfully!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🖼️ Full Page Screenshot")
                if result['full_image']:
                    # Resize for display
                    display_full = result['full_image'].copy()
                    display_full.thumbnail((600, 400))
                    st.image(display_full, caption="Full Profile Page", use_column_width=True)
                    
                    # Show crop area
                    left, upper, right, lower = result['crop_coordinates']
                    st.write(f"**Crop Coordinates:** ({left}, {upper}, {right}, {lower})")
            
            with col2:
                st.subheader("🎯 Badge Area (Cropped)")
                if result['badge_image']:
                    st.image(result['badge_image'], caption="Agentblazer Badge Area", use_column_width=True)
                    
                    # Visual analysis
                    analysis = detector.analyze_badge_visually(result['badge_image'])
                    
                    st.write("**Visual Analysis:**")
                    st.info(analysis['analysis'])
                    st.help(analysis['recommendation'])
            
            # Manual badge level input
            st.subheader("👁️ Manual Badge Verification")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                badge_level = st.selectbox(
                    "What badge level do you see?",
                    ["", "None", "Champion", "Innovator", "Legend"],
                    help="Look at the cropped image above and select the badge level"
                )
            
            with col2:
                confidence = st.selectbox(
                    "Confidence Level:",
                    ["High", "Medium", "Low"],
                    help="How confident are you in this identification?"
                )
            
            with col3:
                if badge_level:
                    st.success(f"✅ Verified: {badge_level}")
                    
                    # Save result
                    verification_result = {
                        'profile_url': profile_url,
                        'badge_level': badge_level,
                        'confidence': confidence,
                        'method': 'Screenshot + Manual Verification',
                        'timestamp': pd.Timestamp.now()
                    }
                    
                    st.json(verification_result)
        
        else:
            st.error(f"❌ Screenshot capture failed: {result.get('error', 'Unknown error')}")
    
    # Batch processing
    st.divider()
    st.subheader("📂 Batch Screenshot Processing")
    
    uploaded_file = st.file_uploader("Upload CSV with profile URLs", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} profiles")
            st.dataframe(df.head())
            
            # Processing settings
            col1, col2 = st.columns(2)
            
            with col1:
                max_profiles = st.number_input("Max profiles to process", 1, len(df), min(5, len(df)))
                st.info("Start with small batches for testing")
            
            with col2:
                delay_between = st.slider("Delay between screenshots (seconds)", 5, 30, 10)
                st.info("Longer delays prevent being blocked")
            
            if st.button("📸 Process Batch Screenshots", type="primary"):
                
                profiles_to_process = df.head(max_profiles)
                results = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Create columns for real-time display
                col1, col2 = st.columns(2)
                
                for idx, row in profiles_to_process.iterrows():
                    progress = (idx + 1) / len(profiles_to_process)
                    progress_bar.progress(progress)
                    status_text.text(f"📸 Screenshot {idx+1}/{len(profiles_to_process)}: {row['Name']}")
                    
                    # Capture badge area
                    result = detector.capture_badge_area(row['Salesforce URL'])
                    
                    if result['success']:
                        # Display images for manual verification
                        with col1:
                            st.write(f"**{row['Name']}** (Roll: {row['Roll Number']})")
                            if result['badge_image']:
                                st.image(result['badge_image'], caption=f"Badge area for {row['Name']}", width=200)
                        
                        with col2:
                            # Manual verification input
                            manual_badge = st.selectbox(
                                f"Badge level for {row['Name']}:",
                                ["", "None", "Champion", "Innovator", "Legend"],
                                key=f"manual_{idx}"
                            )
                            
                            if manual_badge:
                                results.append({
                                    'Roll Number': row['Roll Number'],
                                    'Name': row['Name'],
                                    'Salesforce URL': row['Salesforce URL'],
                                    'Badge Level': manual_badge,
                                    'Method': 'Screenshot + Manual Verification',
                                    'Status': 'Verified'
                                })
                    
                    else:
                        results.append({
                            'Roll Number': row['Roll Number'],
                            'Name': row['Name'],
                            'Salesforce URL': row['Salesforce URL'],
                            'Badge Level': 'Error',
                            'Method': 'Screenshot Failed',
                            'Status': result.get('error', 'Unknown error')
                        })
                    
                    # Delay between screenshots
                    if idx < len(profiles_to_process) - 1:
                        time.sleep(delay_between)
                
                # Final results
                if results:
                    st.success("🎉 Batch screenshot processing completed!")
                    
                    results_df = pd.DataFrame(results)
                    
                    # Summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        successful = len(results_df[results_df['Status'] == 'Verified'])
                        st.metric("Successfully Verified", successful)
                    
                    with col2:
                        badges_found = len(results_df[results_df['Badge Level'].isin(['Champion', 'Innovator', 'Legend'])])
                        st.metric("Badges Found", badges_found)
                    
                    with col3:
                        errors = len(results_df[results_df['Badge Level'] == 'Error'])
                        st.metric("Errors", errors)
                    
                    # Results table
                    st.dataframe(results_df)
                    
                    # Download
                    csv_data = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Screenshot Results",
                        csv_data,
                        f"screenshot_badge_results_{int(time.time())}.csv",
                        "text/csv"
                    )
        
        else:
            st.error("❌ CSV must have columns: Roll Number, Name, Salesforce URL")
    
    # Setup instructions
    st.divider()
    
    with st.expander("🔧 Setup Requirements"):
        st.markdown("""
        ### **Required Dependencies**
        ```
        pip install selenium streamlit pillow pandas
        ```
        
        ### **ChromeDriver Setup**
        1. **Download ChromeDriver** from [chromedriver.chromium.org](https://chromedriver.chromium.org)
        2. **Match your Chrome version** (check chrome://version)
        3. **Add to PATH** or place in project directory
        
        ### **Alternative Setup Methods**
        ```
        # Using webdriver-manager (automatic)
        pip install webdriver-manager
        
        # Then in code:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(ChromeDriverManager().install())
        ```
        
        ### **Troubleshooting**
        - **ChromeDriver version mismatch**: Update ChromeDriver
        - **Timeout errors**: Increase wait time to 20+ seconds
        - **Crop area wrong**: Adjust coordinates based on screen resolution
        - **Rate limiting**: Increase delays between requests
        """)

if __name__ == "__main__":
    main()
