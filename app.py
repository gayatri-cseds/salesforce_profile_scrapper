import streamlit as st
import requests
import json

def call_gemini_api(api_key, content):
    """Call Google Gemini API to analyze content"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Analyze this Salesforce profile HTML content and extract the Agentblazer badge level:
    
    {content[:4000]}  # Limit content for API
    
    Look for these exact patterns:
    - "banner-level-3.png" or "Agentblazer Legend" = Legend
    - "banner-level-2.png" or "Agentblazer Innovator" = Innovator  
    - "banner-level-1.png" or "Agentblazer Champion" = Champion
    - No agentblazer content found = None
    
    Respond with only one word: Champion, Innovator, Legend, or None
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    else:
        return f"API Error: {response.status_code}"

def get_page_content(url):
    """Fetch page content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.text
        else:
            return f"HTTP Error: {response.status_code}"
            
    except Exception as e:
        return f"Request Error: {str(e)}"

def main():
    # Page config
    st.set_page_config(
        page_title="Badge Detector", 
        page_icon="🏆",
        layout="centered"
    )
    
    st.title("🏆 Salesforce Badge Detector")
    st.markdown("*Using Google AI Studio API*")
    
    # API Key input
    st.subheader("🔑 API Configuration")
    api_key = st.text_input(
        "Enter your Google AI Studio API Key:", 
        type="password",
        help="Get your free API key from https://ai.google.dev"
    )
    
    # Instructions
    if not api_key:
        st.info("""
        **How to get your FREE API key:**
        1. Go to [ai.google.dev](https://ai.google.dev)
        2. Click "Get API key"
        3. Sign in with Google account
        4. Create a new API key (free!)
        5. Copy and paste it above
        
        **Free limits**: 1.5 million tokens per day 🎉
        """)
        st.stop()
    
    # URL input
    st.subheader("📋 Profile Analysis")
    url = st.text_input(
        "Enter Salesforce Profile URL:",
        value="https://www.salesforce.com/trailblazer/aarathisreeballa",
        help="Format: https://www.salesforce.com/trailblazer/username"
    )
    
    # Detection button
    if st.button("🔍 Detect Badge", type="primary"):
        
        if not url:
            st.error("Please enter a profile URL")
            return
        
        # Progress indicators
        with st.spinner("Loading profile page..."):
            content = get_page_content(url)
        
        if content.startswith("HTTP Error") or content.startswith("Request Error"):
            st.error(f"Failed to load page: {content}")
            return
        
        with st.spinner("Analyzing with Google AI Studio..."):
            badge_result = call_gemini_api(api_key, content)
        
        if badge_result.startswith("API Error"):
            st.error(f"AI analysis failed: {badge_result}")
            return
        
        # Display results
        st.divider()
        st.subheader("🎯 Detection Results")
        
        # Badge level with styling
        if badge_result == "Legend":
            st.success("🥇 **Badge Level: LEGEND**")
        elif badge_result == "Innovator":
            st.info("🥈 **Badge Level: INNOVATOR**")
        elif badge_result == "Champion":
            st.warning("🥉 **Badge Level: CHAMPION**")
        elif badge_result == "None":
            st.write("❌ **No Agentblazer badge found**")
        else:
            st.write(f"🤖 **AI Response:** {badge_result}")
        
        # Additional info
        with st.expander("ℹ️ Analysis Details"):
            st.write(f"**Profile URL:** {url}")
            st.write(f"**Content Length:** {len(content):,} characters")
            st.write(f"**API Response:** {badge_result}")

if __name__ == "__main__":
    main()
