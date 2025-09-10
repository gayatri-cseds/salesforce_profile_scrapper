import streamlit as st
import pandas as pd
import requests
import re
import time

def extract_label_badge_only(profile_url):
    """Fixed badge extraction with proper priority and exact matching"""
    try:
        if not profile_url.startswith('http'):
            profile_url = f"https://{profile_url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(profile_url, headers=headers, timeout=10)
        page_content = response.text.lower()
        
        # FIXED: Use regex word boundaries for exact matching
        # Priority: Legend > Champion > Innovator (highest to lowest)
        
        if re.search(r'\blegend\b', page_content) or 'agentblazer legend' in page_content:
            return {'label_badge': 'Legend', 'status': 'Success'}
        elif re.search(r'\bchampion\b', page_content) or 'agentblazer champion' in page_content:
            return {'label_badge': 'Champion', 'status': 'Success'}
        elif re.search(r'\binnovator\b', page_content) or 'agentblazer innovator' in page_content:
            return {'label_badge': 'Innovator', 'status': 'Success'}
        else:
            return {'label_badge': 'None', 'status': 'No Badge Found'}
            
    except Exception as e:
        return {'label_badge': 'Error', 'status': f'Error: {str(e)}'}

def process_csv_for_labels(df):
    """Process CSV with improved badge detection"""
    result_df = df.copy()
    result_df['label_badge'] = ''
    result_df['status'] = ''
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in result_df.iterrows():
        status_text.text(f'Checking badge {index + 1} of {len(result_df)}: {row.get("name", "Unknown")}')
        
        profile_url = row.get('salesforce_url', '') or row.get('url', '') or row.get('profile_url', '')
        
        if profile_url:
            badge_data = extract_label_badge_only(profile_url)
            result_df.at[index, 'label_badge'] = badge_data['label_badge']
            result_df.at[index, 'status'] = badge_data['status']
        else:
            result_df.at[index, 'label_badge'] = 'No URL'
            result_df.at[index, 'status'] = 'No URL provided'
        
        progress_bar.progress((index + 1) / len(result_df))
        time.sleep(2)  # Rate limiting
    
    status_text.text('Badge extraction complete!')
    return result_df

# Main Streamlit App
def main():
    st.set_page_config(
        page_title="Fixed Agentblazer Badge Checker",
        page_icon="🏅",
        layout="wide"
    )
    
    st.title("🏅 Agentblazer Badge Checker (Fixed)")
    st.markdown("Extract **Champion/Innovator/Legend** badges with improved accuracy")
    
    # Badge hierarchy explanation
    with st.expander("📋 Badge Hierarchy & Detection Logic"):
        st.markdown("""
        **Detection Priority (Highest to Lowest):**
        1. 🥇 **Legend** - Most advanced badge
        2. 🥈 **Champion** - Mid-level badge  
        3. 🥉 **Innovator** - Entry-level badge
        4. ❌ **None** - No badge detected
        
        **Fixed Logic:**
        - Uses regex word boundaries for exact matching
        - Prevents false positives from partial text matches
        - Correct priority order (Legend > Champion > Innovator)
        """)
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload CSV File", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ File uploaded! Found {len(df)} records.")
            
            # Preview
            st.subheader("📊 Data Preview")
            st.dataframe(df.head())
            
            # Column mapping
            st.subheader("🔗 Column Selection")
            columns = df.columns.tolist()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                col_roll = st.selectbox("Roll Number:", columns, index=0)
            with col2:
                col_name = st.selectbox("Name:", columns, index=1 if len(columns) > 1 else 0)
            with col3:
                col_url = st.selectbox("Salesforce URL:", columns, index=2 if len(columns) > 2 else 0)
            
            # Process button
            if st.button("🏅 Check Badges (Fixed Logic)", type="primary"):
                st.header("⚡ Processing with Fixed Logic")
                
                # Rename columns
                df_processed = df.rename(columns={
                    col_roll: 'roll_number',
                    col_name: 'name',
                    col_url: 'salesforce_url'
                })
                
                # Process with fixed logic
                result_df = process_csv_for_labels(df_processed)
                
                # Results summary
                st.header("📈 Corrected Badge Summary")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    total = len(result_df)
                    st.metric("Total Checked", total)
                
                with col2:
                    legends = len(result_df[result_df['label_badge'] == 'Legend'])
                    st.metric("🥇 Legends", legends)
                
                with col3:
                    champions = len(result_df[result_df['label_badge'] == 'Champion'])
                    st.metric("🥈 Champions", champions)
                
                with col4:
                    innovators = len(result_df[result_df['label_badge'] == 'Innovator'])
                    st.metric("🥉 Innovators", innovators)
                
                with col5:
                    none_badges = len(result_df[result_df['label_badge'] == 'None'])
                    st.metric("❌ No Badge", none_badges)
                
                # Results table with color coding
                st.subheader("📋 Detailed Results")
                
                # Color code the results
                def color_badges(val):
                    if val == 'Legend':
                        return 'background-color: gold'
                    elif val == 'Champion':
                        return 'background-color: silver'
                    elif val == 'Innovator':
                        return 'background-color: #CD7F32'  # Bronze
                    else:
                        return ''
                
                styled_df = result_df.style.applymap(color_badges, subset=['label_badge'])
                st.dataframe(styled_df)
                
                # Download
                csv_output = result_df.to_csv(index=False)
                st.download_button(
                    label="💾 Download Fixed Results",
                    data=csv_output,
                    file_name="agentblazer_badges_fixed.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
