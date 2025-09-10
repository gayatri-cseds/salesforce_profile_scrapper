import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from io import StringIO
import json

# Set page config
st.set_page_config(
    page_title="Salesforce Badge Extractor",
    page_icon="🏆",
    layout="wide"
)

def extract_badges_from_url(profile_url):
    """Extract badges from Salesforce Trailhead profile URL"""
    try:
        # Add headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request to the profile URL
        response = requests.get(profile_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        badges = []
        
        # Look for different badge patterns
        # Method 1: Look for badge titles in various selectors
        badge_selectors = [
            '.badge-title',
            '.th-badge-title', 
            '[data-badge-name]',
            '.badge-name',
            '.achievement-title',
            '.superbadge-title'
        ]
        
        for selector in badge_selectors:
            badge_elements = soup.select(selector)
            for element in badge_elements:
                badge_text = element.get_text(strip=True)
                if badge_text and badge_text not in badges:
                    badges.append(badge_text)
        
        # Method 2: Look for specific badge types in text content
        page_text = soup.get_text().lower()
        badge_keywords = ['champion', 'innovator', 'legend', 'ranger', 'architect', 'superbadge']
        
        for keyword in badge_keywords:
            if keyword in page_text:
                # Try to extract the full badge name around the keyword
                pattern = rf'\b[\w\s]*{keyword}[\w\s]*\b'
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_match = match.strip().title()
                    if clean_match and len(clean_match) < 100:  # Reasonable length
                        badges.append(clean_match)
        
        # Method 3: Look in JSON-LD structured data
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'achievement' in str(data).lower():
                    # Extract achievement names
                    achievements = extract_achievements_from_json(data)
                    badges.extend(achievements)
            except:
                pass
        
        # Remove duplicates and clean up
        unique_badges = list(set(badges))
        cleaned_badges = [badge for badge in unique_badges if len(badge.strip()) > 2]
        
        return cleaned_badges if cleaned_badges else ["No badges found"]
        
    except requests.exceptions.RequestException as e:
        return [f"Error: Unable to fetch URL - {str(e)}"]
    except Exception as e:
        return [f"Error: {str(e)}"]

def extract_achievements_from_json(data):
    """Recursively extract achievements from JSON data"""
    achievements = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if 'achievement' in key.lower() or 'badge' in key.lower():
                if isinstance(value, str):
                    achievements.append(value)
                elif isinstance(value, list):
                    achievements.extend([str(item) for item in value if isinstance(item, str)])
            else:
                achievements.extend(extract_achievements_from_json(value))
    elif isinstance(data, list):
        for item in data:
            achievements.extend(extract_achievements_from_json(item))
    
    return achievements

def process_csv(df):
    """Process the CSV file and extract badges for each profile"""
    results = []
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in df.iterrows():
        try:
            roll_number = row.get('roll_number', row.get('Roll Number', ''))
            name = row.get('name', row.get('Name', ''))
            url = row.get('salesforce_url', row.get('Salesforce URL', row.get('url', row.get('URL', ''))))
            
            status_text.text(f"Processing: {name} ({index + 1}/{len(df)})")
            
            # Extract badges
            badges = extract_badges_from_url(url)
            
            # Create result entry
            result = {
                'Roll Number': roll_number,
                'Name': name,
                'Salesforce URL': url,
                'Badges': ', '.join(badges),
                'Badge Count': len([b for b in badges if not b.startswith('Error') and b != "No badges found"])
            }
            
            results.append(result)
            
            # Update progress
            progress_bar.progress((index + 1) / len(df))
            
            # Add delay to avoid overwhelming the server
            time.sleep(1)
            
        except Exception as e:
            results.append({
                'Roll Number': row.get('roll_number', ''),
                'Name': row.get('name', ''),
                'Salesforce URL': row.get('salesforce_url', ''),
                'Badges': f"Processing Error: {str(e)}",
                'Badge Count': 0
            })
    
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

# Streamlit App Layout
st.title("🏆 Salesforce Badge Extractor")
st.markdown("**Extract badges from Salesforce Trailhead profiles using CSV input**")

# Sidebar with instructions
st.sidebar.header("📋 Instructions")
st.sidebar.markdown("""
1. **Prepare your CSV file** with columns:
   - `roll_number` or `Roll Number`
   - `name` or `Name`  
   - `salesforce_url` or `Salesforce URL`

2. **Upload the CSV file** using the uploader

3. **Preview** your data before processing

4. **Click Process** to extract badges

5. **Download** the results as CSV
""")

st.sidebar.header("🎯 Badge Types Detected")
st.sidebar.markdown("""
- **Champions**
- **Innovators** 
- **Legends**
- **Rangers**
- **Architects**
- **Superbadges**
- And more...
""")

# File uploader
uploaded_file = st.file_uploader(
    "Upload CSV file with Salesforce profile URLs",
    type=['csv'],
    help="CSV should contain: roll_number, name, salesforce_url columns"
)

if uploaded_file is not None:
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! Found {len(df)} records.")
        
        # Display preview
        st.subheader("📊 Data Preview")
        st.dataframe(df.head(10))
        
        # Show column information
        st.subheader("📋 Column Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Available columns:**")
            for col in df.columns:
                st.write(f"- {col}")
        
        with col2:
            st.write("**Expected columns:**")
            st.write("- roll_number (or Roll Number)")
            st.write("- name (or Name)")
            st.write("- salesforce_url (or Salesforce URL)")
        
        # Validation
        required_cols = ['roll_number', 'name', 'salesforce_url']
        alt_cols = ['Roll Number', 'Name', 'Salesforce URL', 'url', 'URL']
        
        has_required = any(col in df.columns for col in required_cols + alt_cols)
        
        if has_required:
            st.success("✅ Required columns found!")
            
            # Process button
            if st.button("🚀 Start Badge Extraction", type="primary"):
                st.subheader("⚙️ Processing...")
                
                with st.spinner("Extracting badges from profiles..."):
                    results_df = process_csv(df)
                
                st.success(f"✅ Processing completed! Extracted badges for {len(results_df)} profiles.")
                
                # Display results
                st.subheader("📈 Results")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Profiles", len(results_df))
                
                with col2:
                    profiles_with_badges = len(results_df[results_df['Badge Count'] > 0])
                    st.metric("Profiles with Badges", profiles_with_badges)
                
                with col3:
                    total_badges = results_df['Badge Count'].sum()
                    st.metric("Total Badges", total_badges)
                
                with col4:
                    avg_badges = results_df['Badge Count'].mean()
                    st.metric("Avg Badges per Profile", f"{avg_badges:.1f}")
                
                # Results table
                st.dataframe(results_df, use_container_width=True)
                
                # Download button
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_data,
                    file_name="salesforce_badges_results.csv",
                    mime="text/csv",
                    type="primary"
                )
                
                # Badge analysis
                st.subheader("🏆 Badge Analysis")
                
                # Extract individual badges for analysis
                all_badges = []
                for badges_str in results_df['Badges']:
                    if badges_str and not badges_str.startswith('Error') and badges_str != "No badges found":
                        badges_list = [badge.strip() for badge in badges_str.split(',')]
                        all_badges.extend(badges_list)
                
                if all_badges:
                    badge_counts = pd.Series(all_badges).value_counts().head(10)
                    st.bar_chart(badge_counts)
                    
                    st.write("**Most Common Badges:**")
                    for badge, count in badge_counts.items():
                        st.write(f"- {badge}: {count} people")
        
        else:
            st.error("❌ Required columns not found. Please ensure your CSV has the required columns.")
    
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {str(e)}")

else:
    # Show sample CSV format
    st.subheader("📝 Sample CSV Format")
    sample_data = {
        'roll_number': ['001', '002', '003'],
        'name': ['John Doe', 'Jane Smith', 'Alex Johnson'],
        'salesforce_url': [
            'https://trailblazer.salesforce.com/profile/johndoe',
            'https://trailblazer.salesforce.com/profile/janesmith', 
            'https://trailblazer.salesforce.com/profile/alexjohnson'
        ]
    }
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df)
    
    # Download sample CSV
    sample_csv = sample_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Sample CSV",
        data=sample_csv,
        file_name="sample_salesforce_profiles.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("**Note:** This tool extracts publicly available badge information from Salesforce Trailhead profiles. Processing may take time depending on the number of profiles.")
