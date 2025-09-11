import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from typing import Dict

# Agentblazer Requirements
REQUIREMENTS = {
    "Champion": {
        "min_points": 2500,
        "keywords": ["artificial intelligence", "agentforce", "prompt builder", "data fundamentals", "autonomous agents"]
    },
    "Innovator": {
        "min_points": 7500, 
        "keywords": ["ai strategy", "agentforce builder", "trusted agentic", "superbadge"]
    },
    "Legend": {
        "min_points": 15000,
        "keywords": ["agentforce specialist", "apex", "certification", "advanced"]
    }
}

def scrape_profile(url: str) -> Dict:
    """Simple profile scraping with requests"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ').lower()
        
        # Extract points
        points_match = re.search(r'(\d+[\,\d]*)\s*points?', text)
        points = int(points_match.group(1).replace(',', '')) if points_match else 0
        
        # Find keywords
        found_keywords = []
        for level, req in REQUIREMENTS.items():
            for keyword in req["keywords"]:
                if keyword in text:
                    found_keywords.append(keyword)
        
        return {
            "points": points,
            "keywords": list(set(found_keywords)),
            "text_length": len(text)
        }
        
    except Exception as e:
        return {"error": str(e)}

def verify_badge(profile_data: Dict, target_level: str) -> Dict:
    """Simple badge verification"""
    if "error" in profile_data:
        return {"qualified": False, "reason": profile_data["error"]}
    
    req = REQUIREMENTS[target_level]
    points_ok = profile_data["points"] >= req["min_points"]
    keywords_found = len([k for k in profile_data["keywords"] if k in req["keywords"]])
    keywords_ok = keywords_found >= 2  # At least 2 relevant keywords
    
    qualified = points_ok and keywords_ok
    
    return {
        "qualified": qualified,
        "points": profile_data["points"],
        "points_required": req["min_points"],
        "keywords_found": keywords_found,
        "keywords_list": profile_data["keywords"],
        "reason": "Meets requirements" if qualified else "Insufficient points or keywords"
    }

def main():
    st.set_page_config(page_title="Minimal Badge Verifier", page_icon="🏆")
    
    st.title("🏆 Minimal Agentblazer Badge Verifier")
    st.success("✅ Simple, fast, and working!")
    
    # Single profile
    st.subheader("🎯 Single Profile Check")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        profile_url = st.text_input(
            "Profile URL:",
            placeholder="https://www.salesforce.com/trailblazer/username"
        )
    
    with col2:
        target_level = st.selectbox("Badge Level:", ["Champion", "Innovator", "Legend"])
    
    if st.button("🔍 Check Badge", type="primary"):
        if profile_url:
            with st.spinner("Checking profile..."):
                profile_data = scrape_profile(profile_url)
                verification = verify_badge(profile_data, target_level)
            
            if verification["qualified"]:
                st.success(f"🎉 **QUALIFIED for {target_level} badge!**")
                st.balloons()
            else:
                st.warning(f"⚠️ **Not qualified: {verification['reason']}**")
            
            # Show details
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Points", f"{verification['points']:,}")
                st.metric("Required", f"{verification['points_required']:,}")
            
            with col2:
                st.metric("Keywords Found", verification['keywords_found'])
                if verification['keywords_list']:
                    st.write("**Topics Found:**")
                    for keyword in verification['keywords_list']:
                        st.write(f"• {keyword.title()}")
    
    # Batch processing
    st.divider()
    st.subheader("📂 Batch Processing")
    
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        if all(col in df.columns for col in ["Name", "Salesforce URL"]):
            st.dataframe(df.head())
            
            batch_level = st.selectbox("Batch Level:", ["Champion", "Innovator", "Legend"], key="batch")
            
            if st.button("🚀 Process All"):
                results = []
                progress_bar = st.progress(0)
                
                for idx, row in df.iterrows():
                    progress_bar.progress((idx + 1) / len(df))
                    
                    profile_data = scrape_profile(row['Salesforce URL'])
                    verification = verify_badge(profile_data, batch_level)
                    
                    results.append({
                        "Name": row["Name"],
                        "Points": verification["points"],
                        "Qualified": "Yes" if verification["qualified"] else "No",
                        "Badge": batch_level if verification["qualified"] else "None",
                        "Status": verification["reason"]
                    })
                
                results_df = pd.DataFrame(results)
                
                # Summary
                qualified = len(results_df[results_df["Qualified"] == "Yes"])
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total", len(results_df))
                with col2:
                    st.metric("Qualified", qualified)
                with col3:
                    st.metric("Success Rate", f"{(qualified/len(results_df)*100):.1f}%")
                
                st.dataframe(results_df)
                
                # Download
                csv_data = results_df.to_csv(index=False)
                st.download_button("📥 Download Results", csv_data, "badge_results.csv")
        
        else:
            st.error("CSV must have columns: Name, Salesforce URL")

if __name__ == "__main__":
    main()
