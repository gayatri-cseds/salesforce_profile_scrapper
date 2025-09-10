import streamlit as st
import pandas as pd
import requests
import re
import time

def extract_badge(profile_url):
    """Simple badge extraction - just the basics"""
    try:
        if not profile_url.startswith('http'):
            profile_url = f"https://{profile_url}"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(profile_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {'label_badge': 'Error', 'status': 'Cannot Access'}
        
        content = response.text.lower()
        
        # Simple text search
        if 'legend' in content:
            return {'label_badge': 'Legend', 'status': 'Success'}
        elif 'champion' in content:
            return {'label_badge': 'Champion', 'status': 'Success'}
        elif 'innovator' in content:
            return {'label_badge': 'Innovator', 'status': 'Success'}
        else:
            return {'label_badge': 'None', 'status': 'No Badge'}
            
    except:
        return {'label_badge': 'Error', 'status': 'Failed'}

def main():
    st.title("🏅 Badge Checker - Simple")
    
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        
        # Column selection
        columns = df.columns.tolist()
        name_col = st.selectbox("Name column:", columns)
        roll_col = st.selectbox("Roll number column:", columns)
        url_col = st.selectbox("URL column:", columns)
        
        if st.button("Check Badges"):
            results = []
            progress = st.progress(0)
            
            for i, row in df.iterrows():
                st.text(f"Processing {i+1}/{len(df)}: {row[name_col]}")
                
                result = extract_badge(row[url_col])
                
                results.append({
                    'name': row[name_col],
                    'roll_number': row[roll_col],
                    'url': row[url_col],
                    'label_badge': result['label_badge'],
                    'status': result['status']
                })
                
                progress.progress((i+1)/len(df))
                time.sleep(1)
            
            result_df = pd.DataFrame(results)
            st.dataframe(result_df)
            
            # Download
            csv = result_df.to_csv(index=False)
            st.download_button("Download Results", csv, "badges.csv")

if __name__ == "__main__":
    main()
