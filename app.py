import streamlit as st
import pandas as pd
import requests
import re
import time

def extract_badge(profile_url):
    """Fixed badge extraction with precise matching"""
    try:
        if not profile_url.startswith('http'):
            profile_url = f"https://{profile_url}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(profile_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {'label_badge': 'Error', 'status': 'Cannot Access'}
        
        content = response.text.lower()
        
        # FIXED: More specific patterns to avoid false matches
        # Look for specific badge contexts, not just isolated words
        
        # Priority order: Legend > Champion > Innovator
        if any(pattern in content for pattern in [
            'agentblazer legend',
            'agentblazer-legend', 
            'become an agentblazer legend'
        ]):
            return {'label_badge': 'Legend', 'status': 'Success'}
            
        elif any(pattern in content for pattern in [
            'agentblazer champion',
            'agentblazer-champion',
            'become an agentblazer champion'
        ]):
            return {'label_badge': 'Champion', 'status': 'Success'}
            
        elif any(pattern in content for pattern in [
            'agentblazer innovator',
            'agentblazer-innovator',
            'become an agentblazer innovator'
        ]):
            return {'label_badge': 'Innovator', 'status': 'Success'}
        
        # If no specific Agentblazer badge found
        return {'label_badge': 'None', 'status': 'No Badge Found'}
            
    except Exception as e:
        return {'label_badge': 'Error', 'status': 'Failed'}

def main():
    st.title("🏅 Agentblazer Badge Checker - Fixed")
    st.info("🔧 **Fixed:** Now looks for specific 'Agentblazer' badge patterns to prevent false positives")
    
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        
        # Column selection
        columns = df.columns.tolist()
        name_col = st.selectbox("Name column:", columns)
        roll_col = st.selectbox("Roll number column:", columns)
        url_col = st.selectbox("URL column:", columns)
        
        if st.button("🔍 Check Agentblazer Badges"):
            results = []
            progress = st.progress(0)
            status_text = st.empty()
            
            for i, row in df.iterrows():
                status_text.text(f"Checking {i+1}/{len(df)}: {row[name_col]}")
                
                result = extract_badge(row[url_col])
                
                results.append({
                    'name': row[name_col],
                    'roll_number': row[roll_col],
                    'url': row[url_col],
                    'label_badge': result['label_badge'],
                    'status': result['status']
                })
                
                progress.progress((i+1)/len(df))
                time.sleep(2)  # Increased delay
            
            result_df = pd.DataFrame(results)
            
            # Show summary
            st.subheader("📊 Results Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                legends = len(result_df[result_df['label_badge'] == 'Legend'])
                st.metric("🥇 Legends", legends)
            with col2:
                champions = len(result_df[result_df['label_badge'] == 'Champion'])
                st.metric("🥈 Champions", champions)
            with col3:
                innovators = len(result_df[result_df['label_badge'] == 'Innovator'])
                st.metric("🥉 Innovators", innovators)
            with col4:
                none_found = len(result_df[result_df['label_badge'] == 'None'])
                st.metric("❌ No Badge", none_found)
            
            # Display results
            st.subheader("📋 Detailed Results")
            st.dataframe(result_df)
            
            # Download
            csv = result_df.to_csv(index=False)
            st.download_button("💾 Download Results", csv, "agentblazer_badges.csv")

if __name__ == "__main__":
    main()
