import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

def extract_trailblazer_badges(profile_url):
    """
    Extract badge information from trailblazer.me profiles
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(profile_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Method 1: Extract from tally counts (proven to work)
        badge_count = extract_badge_count(soup)
        points_count = extract_points_count(soup) 
        
        # Method 2: Look for rank information
        rank_info = extract_rank_from_profile(soup)
        
        # Method 3: Look for specific badge level indicators
        level_info = extract_level_indicators(soup)
        
        # Determine badge level based on extracted data
        badge_level = determine_badge_level(badge_count, points_count, rank_info, level_info)
        
        return {
            'badge_count': badge_count,
            'points': points_count,
            'rank': rank_info,
            'level': badge_level,
            'status': 'Success'
        }
        
    except requests.RequestException as e:
        return {'status': 'Connection Error', 'level': 'Error', 'error': str(e)}
    except Exception as e:
        return {'status': 'Parse Error', 'level': 'Error', 'error': str(e)}

def extract_badge_count(soup):
    """Extract badge count using known CSS classes"""
    try:
        # Look for tally count elements (from StackOverflow examples)
        tally_elements = soup.find_all(['span', 'div'], 
                                     class_=re.compile(r'tds-tally__count|count|badge'))
        
        for element in tally_elements:
            text = element.get_text().strip()
            if text.isdigit():
                count = int(text)
                if 1 <= count <= 1000:  # Reasonable badge count range
                    return count
        
        # Alternative: look for numbers near "badge" text
        badge_sections = soup.find_all(string=re.compile(r'badge', re.I))
        for section in badge_sections:
            parent = section.parent
            if parent:
                numbers = re.findall(r'\b(\d+)\b', parent.get_text())
                for num in numbers:
                    if 1 <= int(num) <= 1000:
                        return int(num)
        
        return 0
        
    except Exception:
        return 0

def extract_points_count(soup):
    """Extract points count"""
    try:
        # Look for points indicators
        points_elements = soup.find_all(['span', 'div'], 
                                      class_=re.compile(r'point|tally'))
        
        for element in points_elements:
            text = element.get_text().strip().replace(',', '')
            # Look for larger numbers that could be points
            numbers = re.findall(r'\b(\d+)\b', text)
            for num in numbers:
                if int(num) >= 100:  # Points are usually higher than badge counts
                    return int(num)
        
        return 0
        
    except Exception:
        return 0

def extract_rank_from_profile(soup):
    """Extract rank information from profile"""
    try:
        # Common rank patterns from the research
        rank_patterns = [
            'ranger', 'expeditioner', 'mountaineer', 
            'adventurer', 'explorer', 'hiker'
        ]
        
        page_text = soup.get_text().lower()
        
        for rank in rank_patterns:
            if rank in page_text:
                return rank.title()
        
        # Look in specific elements
        rank_elements = soup.find_all(['h1', 'h2', 'h3', 'span', 'div'], 
                                    class_=re.compile(r'rank|title|level'))
        
        for element in rank_elements:
            text = element.get_text().lower()
            for rank in rank_patterns:
                if rank in text:
                    return rank.title()
        
        return "Unknown"
        
    except Exception:
        return "Unknown"

def extract_level_indicators(soup):
    """Look for specific level indicators"""
    try:
        # Look for level-specific images or text
        images = soup.find_all('img')
        
        level_patterns = [
            (r'level.*3|legend|ranger', 'Legend'),
            (r'level.*2|innovator|mountaineer', 'Innovator'),
            (r'level.*1|champion|adventurer', 'Champion')
        ]
        
        for img in images:
            src = str(img.get('src', '')).lower()
            alt = str(img.get('alt', '')).lower()
            
            for pattern, level in level_patterns:
                if re.search(pattern, src) or re.search(pattern, alt):
                    return level
        
        return "None"
        
    except Exception:
        return "None"

def determine_badge_level(badge_count, points, rank, level_indicator):
    """Determine final badge level based on all available data"""
    
    # Priority 1: Direct level indicators
    if level_indicator and level_indicator != "None":
        return level_indicator
    
    # Priority 2: Rank-based mapping (from research)
    rank_mapping = {
        'Ranger': 'Legend',        # 50,000+ points
        'Expeditioner': 'Legend',  # 35,000+ points  
        'Mountaineer': 'Innovator', # 18,000+ points
        'Adventurer': 'Champion',   # 9,000+ points
        'Explorer': 'Champion',     # 3,000+ points
        'Hiker': 'Novice'          # 500+ points
    }
    
    if rank in rank_mapping:
        return rank_mapping[rank]
    
    # Priority 3: Points-based estimation
    if points >= 35000:
        return 'Legend'
    elif points >= 18000:
        return 'Innovator'
    elif points >= 9000:
        return 'Champion'
    elif points >= 3000:
        return 'Explorer'
    
    # Priority 4: Badge count estimation
    if badge_count >= 100:
        return 'Legend'
    elif badge_count >= 50:
        return 'Innovator'
    elif badge_count >= 20:
        return 'Champion'
    elif badge_count >= 5:
        return 'Explorer'
    
    return 'None'

def main():
    st.set_page_config(
        page_title="Trailblazer.me Badge Extractor",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Trailblazer.me Badge Extractor")
    st.success("✅ Optimized for trailblazer.me profiles!")
    
    # URL format info
    st.info("""
    **Expected URL Format**: `https://trailblazer.me/id/username`
    
    **Example**: `https://trailblazer.me/id/aarathisreeballa`
    """)
    
    # Single profile test
    st.subheader("🧪 Test Single Profile")
    
    test_url = st.text_input(
        "Test Profile URL:",
        placeholder="https://trailblazer.me/id/username",
        value="https://trailblazer.me/id/aarathisreeballa"
    )
    
    if st.button("🔍 Test Profile"):
        if test_url:
            with st.spinner("Extracting badge data..."):
                result = extract_trailblazer_badges(test_url)
                
                st.subheader("🎯 Extraction Results:")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Badge Count", result.get('badge_count', 0))
                with col2:
                    st.metric("Points", result.get('points', 0))
                with col3:
                    st.metric("Rank", result.get('rank', 'Unknown'))
                with col4:
                    st.metric("Level", result.get('level', 'None'))
                
                if result.get('status') == 'Success':
                    st.success(f"✅ **Final Badge Level: {result['level']}**")
                else:
                    st.error(f"❌ {result['status']}: {result.get('error', 'Unknown error')}")
                
                st.json(result)
    
    st.divider()
    
    # Batch processing
    st.subheader("📂 Batch Processing")
    
    uploaded_file = st.file_uploader(
        "Upload CSV with trailblazer.me URLs", 
        type="csv",
        help="CSV should have columns: Roll Number, Name, Salesforce URL (using trailblazer.me format)"
    )
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        # Validate columns
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} records")
            st.dataframe(df.head())
            
            # Validate URL format
            sample_urls = df['Salesforce URL'].head(3).tolist()
            trailblazer_me_count = sum(1 for url in sample_urls if 'trailblazer.me' in url)
            
            if trailblazer_me_count == 0:
                st.warning("⚠️ URLs don't seem to be in trailblazer.me format. Please ensure URLs are like: https://trailblazer.me/id/username")
            
            if st.button("🚀 Process All Profiles"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results = []
                
                for idx, row in df.iterrows():
                    progress = (idx + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {idx + 1}/{len(df)}: {row['Name']}")
                    
                    result = extract_trailblazer_badges(row['Salesforce URL'])
                    
                    results.append({
                        'Roll Number': row['Roll Number'],
                        'Name': row['Name'],
                        'Salesforce URL': row['Salesforce URL'],
                        'Badge Count': result.get('badge_count', 0),
                        'Points': result.get('points', 0),
                        'Rank': result.get('rank', 'Unknown'),
                        'Badge Status': result.get('level', 'None'),
                        'Status': result.get('status', 'Unknown')
                    })
                    
                    # Small delay to be respectful
                    time.sleep(1)
                
                # Display results
                results_df = pd.DataFrame(results)
                
                st.subheader("📊 Final Results")
                st.dataframe(results_df)
                
                # Summary stats
                st.subheader("📈 Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Processed", len(results_df))
                with col2:
                    champions = len(results_df[results_df['Badge Status'] == 'Champion'])
                    st.metric("Champions", champions)
                with col3:
                    innovators = len(results_df[results_df['Badge Status'] == 'Innovator'])
                    st.metric("Innovators", innovators)
                with col4:
                    legends = len(results_df[results_df['Badge Status'] == 'Legend'])
                    st.metric("Legends", legends)
                
                # Success rate
                successful = len(results_df[results_df['Status'] == 'Success'])
                success_rate = (successful / len(results_df)) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Download results
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Results",
                    csv_data,
                    "trailblazer_badge_results.csv",
                    "text/csv"
                )
        else:
            st.error(f"❌ Missing required columns: {required_cols}")

if __name__ == "__main__":
    main()
