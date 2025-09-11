import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List
import time

# Your Agentblazer Requirements (same as before)
AGENTBLAZER_REQUIREMENTS = {
    "Champion": {
        "modules": [
            "Artificial Intelligence Fundamentals",
            "Generative AI Basics", 
            "Natural Language Processing Basics",
            "Large Language Models",
            "Data Fundamentals for AI",
            "Data+AI+CRM: Quick Look",
            "Prompt Fundamentals",
            "Prompt Builder Basics",
            "The Einstein Trust Layer",
            "Autonomous Agents",
            "Introduction to Agentforce",
            "Introduction to Agentforce Builder",
            "Agentforce for Service",
            "Agentforce for Sales: Quick Look"
        ],
        "projects": [
            "Quick Start: Build a Service Agent with Agentforce",
            "Connect Data Cloud to Agentforce and Prompt Builder"
        ],
        "superbadges": [],
        "certifications": [],
        "description": "Foundation-level AI and Agentforce skills",
        "min_points": 2500
    },
    # Add other levels...
}

def scrape_profile_with_requests(profile_url: str) -> Dict:
    """
    Alternative scraping approach using requests (no browser needed)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        st.info(f"🔄 Fetching profile data from: {profile_url}")
        
        response = requests.get(profile_url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch profile (Status: {response.status_code})"}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = response.text.lower()
        
        # Initialize data structure
        profile_data = {
            "modules": [],
            "projects": [],
            "superbadges": [],
            "certifications": [],
            "points": 0,
            "badges": []
        }
        
        # Extract points
        points_patterns = [
            r'(\d+,?\d*)\s*points?',
            r'points[:\s]*(\d+,?\d*)',
            r'(\d+,?\d*)\s*total\s*points'
        ]
        
        for pattern in points_patterns:
            match = re.search(pattern, page_text)
            if match:
                try:
                    profile_data["points"] = int(match.group(1).replace(',', ''))
                    break
                except:
                    continue
        
        # Extract badges count
        badge_patterns = [
            r'(\d+)\s*badges?',
            r'badges?[:\s]*(\d+)'
        ]
        
        for pattern in badge_patterns:
            match = re.search(pattern, page_text)
            if match:
                try:
                    badges_count = int(match.group(1))
                    profile_data["badges"] = [f"Badge {i+1}" for i in range(badges_count)]
                    break
                except:
                    continue
        
        # Look for Agentblazer keywords
        agentblazer_keywords = {
            "artificial intelligence": "Artificial Intelligence Fundamentals",
            "generative ai": "Generative AI Basics",
            "natural language processing": "Natural Language Processing Basics",
            "large language models": "Large Language Models",
            "data fundamentals": "Data Fundamentals for AI",
            "prompt fundamentals": "Prompt Fundamentals",
            "prompt builder": "Prompt Builder Basics",
            "einstein trust": "The Einstein Trust Layer",
            "autonomous agents": "Autonomous Agents",
            "agentforce": "Introduction to Agentforce",
            "ai strategy": "AI Strategy",
            "trusted agentic": "Trusted Agentic AI"
        }
        
        # Find matching modules
        for keyword, module_name in agentblazer_keywords.items():
            if keyword in page_text:
                profile_data["modules"].append(module_name)
        
        # Look for projects
        if "quick start" in page_text:
            if "service agent" in page_text:
                profile_data["projects"].append("Quick Start: Build a Service Agent with Agentforce")
            if "agent actions" in page_text:
                profile_data["projects"].append("Quick Start: Agent Actions")
        
        if "connect data cloud" in page_text:
            profile_data["projects"].append("Connect Data Cloud to Agentforce and Prompt Builder")
        
        # Look for superbadges
        if "superbadge" in page_text and "agentforce" in page_text:
            profile_data["superbadges"].append("Agentforce for Service Superbadge Unit")
        
        # Remove duplicates
        for key in ["modules", "projects", "superbadges", "certifications"]:
            profile_data[key] = list(set(profile_data[key]))
        
        return profile_data
        
    except Exception as e:
        return {"error": str(e)}

def main():
    st.set_page_config(
        page_title="Agentblazer Badge Verifier - No Browser",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Agentblazer Badge Verification System")
    st.success("✅ ChromeDriver issues resolved - using requests-based scraping!")
    
    with st.expander("🔧 About This Fix"):
        st.markdown("""
        **ChromeDriver Issue Resolved:**
        - Eliminated browser automation dependency
        - Uses direct HTTP requests instead of Selenium
        - No ChromeDriver version conflicts
        - Faster and more reliable
        - Works on any platform
        """)
    
    # Profile verification
    st.subheader("🎯 Profile Verification")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        profile_url = st.text_input(
            "📧 Enter Salesforce Trailblazer Profile URL:",
            placeholder="https://www.salesforce.com/trailblazer/aarathisreeballa",
            help="Enter the profile URL for automatic data extraction"
        )
    
    with col2:
        target_level = st.selectbox("🎯 Target Badge Level:", ["Champion", "Innovator", "Legend"])
    
    if st.button("🔍 Extract & Verify Profile", type="primary"):
        if not profile_url:
            st.error("❌ Please enter a valid profile URL")
        elif not profile_url.startswith("https://www.salesforce.com/trailblazer/"):
            st.error("❌ Please enter a valid Salesforce trailblazer URL")
        else:
            with st.spinner("🔄 Extracting profile data..."):
                profile_data = scrape_profile_with_requests(profile_url)
                
                if "error" in profile_data:
                    st.error(f"❌ Error: {profile_data['error']}")
                    st.info("💡 This may be due to:")
                    st.write("• Profile is private or restricted")
                    st.write("• Network connectivity issues")
                    st.write("• Salesforce anti-scraping measures")
                    return
                
                # Verify against requirements
                requirements = AGENTBLAZER_REQUIREMENTS[target_level]
                
                # Points check
                points_qualified = profile_data["points"] >= requirements["min_points"]
                
                # Module check (simplified)
                modules_found = len(profile_data["modules"])
                modules_required = len(requirements["modules"])
                modules_qualified = modules_found >= (modules_required * 0.7)  # 70% threshold
                
                # Projects check
                projects_found = len(profile_data["projects"])
                projects_required = len(requirements["projects"])
                projects_qualified = projects_found >= projects_required
                
                # Overall qualification
                overall_qualified = points_qualified and modules_qualified and projects_qualified
                
                # Display results
                st.subheader("📊 Verification Results")
                
                if overall_qualified:
                    st.success(f"🎉 **QUALIFIED for {target_level} Badge!**")
                    st.balloons()
                else:
                    st.warning(f"⚠️ **Not yet qualified for {target_level} badge**")
                
                # Show extracted data
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Points", f"{profile_data['points']:,}")
                    color = "normal" if points_qualified else "inverse"
                    st.metric("Points Status", "✅ Met" if points_qualified else "❌ Need more", delta=f"Required: {requirements['min_points']:,}")
                
                with col2:
                    st.metric("Modules Found", modules_found)
                    st.metric("Modules Status", "✅ Met" if modules_qualified else "❌ Need more", delta=f"Required: {modules_required}")
                
                with col3:
                    st.metric("Projects Found", projects_found)
                    st.metric("Projects Status", "✅ Met" if projects_qualified else "❌ Need more", delta=f"Required: {projects_required}")
                
                # Show found modules
                if profile_data["modules"]:
                    with st.expander("📚 Found Modules"):
                        for module in profile_data["modules"]:
                            st.write(f"✅ {module}")
                
                # Show found projects
                if profile_data["projects"]:
                    with st.expander("🚀 Found Projects"):
                        for project in profile_data["projects"]:
                            st.write(f"✅ {project}")

if __name__ == "__main__":
    main()
