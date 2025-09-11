import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import time

def fetch_badge_image(badge_url):
    """Fetch badge image from Salesforce CDN"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://trailhead.salesforce.com/'
        }
        
        response = requests.get(badge_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img, True
        else:
            return None, False
            
    except Exception as e:
        return None, False

def determine_badge_level_from_url(url):
    """Determine badge level from URL pattern"""
    if 'banner-level-3.png' in url:
        return 'Legend'
    elif 'banner-level-2.png' in url:
        return 'Innovator'
    elif 'banner-level-1.png' in url:
        return 'Champion'
    else:
        return 'Unknown'

def generate_badge_urls():
    """Generate all possible badge URLs"""
    base_url = "https://trailhead.salesforce.com/agentblazer/"
    badge_urls = {
        'Champion': f"{base_url}banner-level-1.png",
        'Innovator': f"{base_url}banner-level-2.png", 
        'Legend': f"{base_url}banner-level-3.png"
    }
    return badge_urls

def main():
    st.set_page_config(
        page_title="Badge Image Fetcher",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Salesforce Badge Image Detector")
    st.success("✅ Direct image fetching from Salesforce CDN!")
    
    # Show discovered image URL
    st.subheader("🔍 Discovered Badge URL")
    discovered_url = "https://trailhead.salesforce.com/agentblazer/banner-level-2.png"
    st.code(discovered_url)
    
    # Test image fetching
    st.subheader("🧪 Test Badge Image Fetching")
    
    badge_urls = generate_badge_urls()
    
    # Display all badge images
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🥉 Champion")
        img, success = fetch_badge_image(badge_urls['Champion'])
        if success:
            st.image(img, caption="Champion Badge", use_column_width=True)
            st.success("✅ Champion image loaded")
        else:
            st.error("❌ Champion image failed")
    
    with col2:
        st.subheader("🥈 Innovator")
        img, success = fetch_badge_image(badge_urls['Innovator'])
        if success:
            st.image(img, caption="Innovator Badge", use_column_width=True)
            st.success("✅ Innovator image loaded")
        else:
            st.error("❌ Innovator image failed")
    
    with col3:
        st.subheader("🥇 Legend")
        img, success = fetch_badge_image(badge_urls['Legend'])
        if success:
            st.image(img, caption="Legend Badge", use_column_width=True)
            st.success("✅ Legend image loaded")
        else:
            st.error("❌ Legend image failed")
    
    # Custom URL test
    st.subheader("🔗 Custom Badge URL Test")
    
    custom_url = st.text_input(
        "Enter Badge Image URL:",
        value=discovered_url,
        help="Enter the full URL to a Salesforce badge image"
    )
    
    if st.button("🖼️ Fetch Image"):
        if custom_url:
            with st.spinner("Fetching image..."):
                img, success = fetch_badge_image(custom_url)
                
                if success:
                    st.success("✅ Image fetched successfully!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.image(img, caption="Badge Image", use_column_width=True)
                    
                    with col2:
                        # Analyze the URL
                        badge_level = determine_badge_level_from_url(custom_url)
                        st.subheader("📊 Analysis")
                        st.write(f"**Badge Level:** {badge_level}")
                        st.write(f"**Image Size:** {img.size}")
                        st.write(f"**Image Mode:** {img.mode}")
                        
                        # Show URL pattern
                        st.write("**URL Pattern Detected:**")
                        if 'banner-level-1' in custom_url:
                            st.write("🥉 Champion Badge Pattern")
                        elif 'banner-level-2' in custom_url:
                            st.write("🥈 Innovator Badge Pattern")
                        elif 'banner-level-3' in custom_url:
                            st.write("🥇 Legend Badge Pattern")
                        else:
                            st.write("❓ Unknown Pattern")
                
                else:
                    st.error("❌ Failed to fetch image")
                    st.info("The image URL might be incorrect or protected")
    
    # Batch image verification
    st.subheader("📂 Batch Badge Image Verification")
    
    # Create sample data with badge URLs
    if st.button("🧪 Test Batch Badge Detection"):
        sample_data = [
            {
                'Name': 'Student 1',
                'Roll Number': '1001',
                'Badge URL': 'https://trailhead.salesforce.com/agentblazer/banner-level-2.png'
            },
            {
                'Name': 'Student 2', 
                'Roll Number': '1002',
                'Badge URL': 'https://trailhead.salesforce.com/agentblazer/banner-level-1.png'
            },
            {
                'Name': 'Student 3',
                'Roll Number': '1003', 
                'Badge URL': 'https://trailhead.salesforce.com/agentblazer/banner-level-3.png'
            }
        ]
        
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, student in enumerate(sample_data):
            progress = (idx + 1) / len(sample_data)
            progress_bar.progress(progress)
            status_text.text(f"Processing {student['Name']}...")
            
            # Fetch badge image
            img, success = fetch_badge_image(student['Badge URL'])
            
            if success:
                badge_level = determine_badge_level_from_url(student['Badge URL'])
                status = "Success"
            else:
                badge_level = "Error"
                status = "Failed"
            
            results.append({
                'Name': student['Name'],
                'Roll Number': student['Roll Number'],
                'Badge Level': badge_level,
                'Status': status,
                'Badge URL': student['Badge URL']
            })
            
            time.sleep(1)  # Small delay
        
        # Display results
        st.success("🎉 Batch processing completed!")
        
        results_df = pd.DataFrame(results)
        
        # Summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            successful = len(results_df[results_df['Status'] == 'Success'])
            st.metric("Successful", successful)
        
        with col2:
            innovators = len(results_df[results_df['Badge Level'] == 'Innovator'])
            st.metric("Innovators", innovators)
        
        with col3:
            champions = len(results_df[results_df['Badge Level'] == 'Champion'])
            st.metric("Champions", champions)
        
        # Results table
        st.dataframe(results_df)
    
    # Information panel
    st.divider()
    
    with st.expander("ℹ️ How This Image Detection Works"):
        st.markdown("""
        ### **🎯 Key Discovery**
        Your inspect element revealed the **exact badge image URLs**:
        - **Champion**: `banner-level-1.png`
        - **Innovator**: `banner-level-2.png` 
        - **Legend**: `banner-level-3.png`
        
        ### **✅ What Works**
        - ✅ **Direct image fetching** from Salesforce CDN
        - ✅ **URL pattern detection** for badge levels
        - ✅ **Visual verification** by displaying actual badge images
        - ✅ **Batch processing** multiple badge URLs
        
        ### **🚀 Practical Applications**
        1. **Manual Verification Aid**: Faculty can visually verify badge levels
        2. **Badge Gallery**: Show all possible badge types to students  
        3. **Quality Assurance**: Verify badge URLs are working correctly
        4. **Documentation**: Create visual guides for badge levels
        
        ### **💡 Next Steps**
        Since we can fetch the images, we can:
        1. Create a badge verification tool for faculty
        2. Build a visual badge gallery for students
        3. Use image URLs to validate badge submissions
        4. Generate visual reports with actual badge images
        """)

if __name__ == "__main__":
    main()
