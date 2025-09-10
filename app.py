import streamlit as st
import pandas as pd
import requests
import re
import time

def extract_label_badge_only(profile_url):
    """Enhanced badge extraction with privacy detection"""
    try:
        if not profile_url.startswith('http'):
            profile_url = f"https://{profile_url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(profile_url, headers=headers, timeout=15)
        
        # Check response status
        if response.status_code == 404:
            return {'label_badge': 'Profile Not Found', 'status': 'URL Not Found'}
        elif response.status_code != 200:
            return {'label_badge': 'Access Error', 'status': f'HTTP Error: {response.status_code}'}
        
        page_content = response.text.lower()
        
        # Check if profile is private or requires authentication
        privacy_indicators = [
            'profile is private',
            'this profile is not visible',
            'sign in to view',
            'login required',
            'access denied',
            'profile not found'
        ]
        
        for indicator in privacy_indicators:
            if indicator in page_content:
                return {'label_badge': 'Private Profile', 'status': 'Profile Set to Private'}
        
        # Enhanced badge detection with multiple patterns
        badge_patterns = [
            # Legend patterns (highest priority)
            (r'\bagentblazer\s+legend\b', 'Legend'),
            (r'\blegend\b.*\bagentblazer\b', 'Legend'),
            (r'\blegend\b', 'Legend'),
            
            # Champion patterns  
            (r'\bagentblazer\s+champion\b', 'Champion'),
            (r'\bchampion\b.*\bagentblazer\b', 'Champion'),
            (r'\bchampion\b', 'Champion'),
            
            # Innovator patterns (lowest priority)
            (r'\bagentblazer\s+innovator\b', 'Innovator'),
            (r'\binnovator\b.*\bagentblazer\b', 'Innovator'),
            (r'\binnovator\b', 'Innovator')
        ]
        
        # Check patterns in priority order
        for pattern, badge_name in badge_patterns:
            if re.search(pattern, page_content):
                return {'label_badge': badge_name, 'status': 'Success'}
        
        # Check if profile has content but no badges
        if any(keyword in page_content for keyword in ['badges', 'points', 'trails', 'trailblazer']):
            return {'label_badge': 'None', 'status': 'No Agentblazer Badge Found'}
        else:
            return {'label_badge': 'No Data', 'status': 'Limited Profile Content'}
            
    except requests.exceptions.Timeout:
        return {'label_badge': 'Timeout', 'status': 'Request Timeout'}
    except requests.exceptions.RequestException as e:
        return {'label_badge': 'Network Error', 'status': f'Network Error: {str(e)}'}
    except Exception as e:
        return {'label_badge': 'Error', 'status': f'Unexpected Error: {str(e)}'}

def process_csv_for_labels(df):
    """Process CSV with enhanced error handling and progress tracking"""
    result_df = df.copy()
    result_df['label_badge'] = ''
    result_df['status'] = ''
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, row in result_df.iterrows():
        status_text.text(f'Processing {index + 1} of {len(result_df)}: {row.get("name", "Unknown")}')
        
        profile_url = row.get('salesforce_url', '') or row.get('url', '') or row.get('profile_url', '')
        
        if profile_url:
            badge_data = extract_label_badge_only(profile_url)
            result_df.at[index, 'label_badge'] = badge_data['label_badge']
            result_df.at[index, 'status'] = badge_data['status']
        else:
            result_df.at[index, 'label_badge'] = 'No URL'
            result_df.at[index, 'status'] = 'URL Not Provided'
        
        progress_bar.progress((index + 1) / len(result_df))
        time.sleep(2)  # Rate limiting
    
    status_text.text('Badge extraction complete!')
    return result_df

def display_results_with_colors(df):
    """Display results with color coding and statistics"""
    
    # Create color mapping function
    def color_badges(val):
        color_map = {
            'Legend': 'background-color: #FFD700; color: black; font-weight: bold',  # Gold
            'Champion': 'background-color: #C0C0C0; color: black; font-weight: bold',  # Silver
            'Innovator': 'background-color: #CD7F32; color: white; font-weight: bold',  # Bronze
            'None': 'background-color: #f0f0f0; color: gray',
            'Private Profile': 'background-color: #ffcccc; color: red',
            'No URL': 'background-color: #ffe6cc; color: orange'
        }
        return color_map.get(val, '')
    
    # Apply styling
    styled_df = df.style.applymap(color_badges, subset=['label_badge'])
    st.dataframe(styled_df, use_container_width=True)

def main():
    st.set_page_config(
        page_title="Agentblazer Badge Checker - Complete",
        page_icon="🏅",
        layout="wide"
    )
    
    st.title("🏅 Agentblazer Badge Checker - Complete Solution")
    st.markdown("Extract **Champion/Innovator/Legend** badges with privacy handling")
    
    # Privacy alert
    st.error("""
    🔒 **Important: Profile Privacy Notice**
    
    Most Salesforce Trailblazer profiles are **private by default**. If results show "Private Profile":
    
    1. **Profile Owner** must go to Trailhead → Profile Settings → Change Privacy to "Public"
    2. Use **Manual Entry** tab below for private profiles
    3. **Alternative**: Check profiles manually and update results
    """)
    
    # Sidebar with instructions
    with st.sidebar:
        st.header("📋 How to Use")
        st.markdown("""
        **Step 1:** Upload CSV with columns:
        - Name
        - Roll Number  
        - Salesforce URL
        
        **Step 2:** Run automated extraction
        
        **Step 3:** Manually update private profiles
        
        **Step 4:** Download final results
        """)
        
        st.header("🔒 Making Profiles Public")
        st.info("""
        **For Profile Owners:**
        1. Login to Trailhead
        2. Click Profile Avatar → Settings
        3. Privacy → Change to "Public"
        4. Save Changes
        """)
        
        st.header("🏆 Badge Hierarchy")
        st.markdown("""
        - 🥇 **Legend** (Highest)
        - 🥈 **Champion** (Mid-level)
        - 🥉 **Innovator** (Entry-level)
        """)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Automated Extraction", "✍️ Manual Entry", "📊 Results Analysis"])
    
    with tab1:
        st.header("Automated Badge Extraction")
        
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
                    col_name = st.selectbox("Name Column:", columns, index=0)
                with col2:
                    col_roll = st.selectbox("Roll Number Column:", columns, index=1 if len(columns) > 1 else 0)
                with col3:
                    col_url = st.selectbox("URL Column:", columns, index=2 if len(columns) > 2 else 0)
                
                # Process button
                if st.button("🚀 Extract Badges", type="primary"):
                    st.header("⚡ Processing Profiles")
                    
                    # Rename columns
                    df_processed = df.rename(columns={
                        col_name: 'name',
                        col_roll: 'roll_number',
                        col_url: 'salesforce_url'
                    })
                    
                    # Store in session state for cross-tab access
                    st.session_state['results_df'] = process_csv_for_labels(df_processed)
                    
                    # Display results
                    result_df = st.session_state['results_df']
                    
                    # Summary metrics
                    st.subheader("📈 Extraction Summary")
                    
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    
                    with col1:
                        total = len(result_df)
                        st.metric("Total", total)
                    
                    with col2:
                        success = len(result_df[result_df['status'] == 'Success'])
                        st.metric("✅ Success", success)
                    
                    with col3:
                        legends = len(result_df[result_df['label_badge'] == 'Legend'])
                        st.metric("🥇 Legends", legends)
                    
                    with col4:
                        champions = len(result_df[result_df['label_badge'] == 'Champion'])
                        st.metric("🥈 Champions", champions)
                    
                    with col5:
                        innovators = len(result_df[result_df['label_badge'] == 'Innovator'])
                        st.metric("🥉 Innovators", innovators)
                    
                    with col6:
                        private = len(result_df[result_df['label_badge'] == 'Private Profile'])
                        st.metric("🔒 Private", private)
                    
                    # Results table
                    st.subheader("📋 Detailed Results")
                    display_results_with_colors(result_df)
                    
                    # Download
                    csv_output = result_df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download Results",
                        data=csv_output,
                        file_name="agentblazer_badges_complete.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
    
    with tab2:
        st.header("Manual Badge Entry for Private Profiles")
        
        if 'results_df' in st.session_state:
            result_df = st.session_state['results_df'].copy()
            
            # Filter profiles needing manual update
            needs_update = result_df[result_df['label_badge'].isin([
                'Private Profile', 'None', 'No Data', 'Access Error'
            ])]
            
            if len(needs_update) > 0:
                st.info(f"Found {len(needs_update)} profiles that may need manual verification")
                
                # Batch update interface
                st.subheader("Batch Update Interface")
                
                for idx, row in needs_update.iterrows():
                    with st.expander(f"Update: {row['name']} ({row['roll_number']})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**URL:** {row['salesforce_url']}")
                            st.write(f"**Current Status:** {row['status']}")
                        
                        with col2:
                            new_badge = st.selectbox(
                                "Badge Level:",
                                ["Keep Current", "None", "Innovator", "Champion", "Legend"],
                                key=f"badge_select_{idx}"
                            )
                            
                            if st.button(f"Update", key=f"update_btn_{idx}"):
                                if new_badge != "Keep Current":
                                    st.session_state['results_df'].at[idx, 'label_badge'] = new_badge
                                    st.session_state['results_df'].at[idx, 'status'] = 'Manually Updated'
                                    st.success(f"✅ Updated {row['name']} to {new_badge}")
                                    time.sleep(0.5)
                                    st.experimental_rerun()
                
                # Download updated results
                if st.button("💾 Download Updated Results"):
                    updated_csv = st.session_state['results_df'].to_csv(index=False)
                    st.download_button(
                        label="📥 Download Final Results",
                        data=updated_csv,
                        file_name="agentblazer_badges_final.csv",
                        mime="text/csv"
                    )
            else:
                st.success("✅ All profiles processed successfully! No manual updates needed.")
        else:
            st.info("👆 Please run the automated extraction first in the previous tab.")
    
    with tab3:
        st.header("Results Analysis")
        
        if 'results_df' in st.session_state:
            result_df = st.session_state['results_df']
            
            # Badge distribution
            badge_counts = result_df['label_badge'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Badge Distribution")
                st.bar_chart(badge_counts)
            
            with col2:
                st.subheader("📈 Status Breakdown")
                status_counts = result_df['status'].value_counts()
                st.bar_chart(status_counts)
            
            # Detailed breakdown
            st.subheader("📋 Summary Statistics")
            
            total_profiles = len(result_df)
            successful_extractions = len(result_df[result_df['status'] == 'Success'])
            private_profiles = len(result_df[result_df['label_badge'] == 'Private Profile'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Success Rate", f"{(successful_extractions/total_profiles)*100:.1f}%")
            with col2:
                st.metric("Private Profiles", f"{(private_profiles/total_profiles)*100:.1f}%")
            with col3:
                badge_holders = len(result_df[result_df['label_badge'].isin(['Legend', 'Champion', 'Innovator'])])
                st.metric("Badge Holders", f"{(badge_holders/total_profiles)*100:.1f}%")
        else:
            st.info("👆 Please run the extraction first to see analysis.")

if __name__ == "__main__":
    main()
