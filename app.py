import streamlit as st
import pandas as pd
import requests
from typing import Dict, List
from urllib.parse import urlparse
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

# Complete Agentblazer Requirements Database
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
    
    "Innovator": {
        "modules": [
            "AI Strategy",
            "AI+Data: Project Planning", 
            "Agentforce: Agent Planning",
            "Trusted Agentic AI",
            "Agentforce Builder Basics",
            "Agentforce SDR Setup and Customization",
            "Agentforce Sales Coach Setup and Customization"
        ],
        "projects": [
            "Quick Start: Agent Actions",
            "Customize a Service Agent with Prompts, Flows and Actions",
            "Build Your First Sales Coach"
        ],
        "superbadges": [
            "Agentforce for Service Superbadge Unit"
        ],
        "certifications": [],
        "description": "Intermediate agent building and customization",
        "min_points": 7500
    },
    
    "Legend": {
        "modules": [
            "Cert Prep: Agentforce Specialist",
            "Agent Customization: Quick Look",
            "Service Agent Customization with Prompt Builder",
            "Prompt Engineering Techniques",
            "Agent Customization with Flows", 
            "Agent Customization with Apex",
            "Grounding an Agent with Data",
            "Data Cloud-Powered Experiences",
            "Search Index Types in Data Cloud: Quick Look",
            "Retrieval Augmented Generation: Quick Look",
            "Agentforce Data Library Basics",
            "Agentforce Testing Tools and Strategies",
            "Agentforce Testing Center",
            "Agentforce Analytics and Monitoring",
            "Agentforce Configuration for Slack Deployment",
            "Agent API: Quick Look",
            "Get Started with the Models API"
        ],
        "projects": [
            "Deploy Agent Authentication",
            "Unstructured Data in Data Cloud",
            "Quick Start: Create Employee Agents in Agentforce",
            "Connect Your Agentforce Org with Slack",
            "Create an Agent Using Agentforce DX"
        ],
        "superbadges": [
            "Superbadge: Advanced Flow for Agentforce",
            "Superbadge: Apex for Agentforce"
        ],
        "certifications": [
            "Earn your Agentforce Specialist Certification"
        ],
        "description": "Advanced enterprise-level agent development and certification",
        "min_points": 15000
    }
}

def validate_profile_url(url: str) -> bool:
    """Validate that the URL is in the correct Salesforce trailblazer format"""
    return url.startswith("https://www.salesforce.com/trailblazer/") and len(url.split("/")) >= 5

def extract_username_from_url(url: str) -> str:
    """Extract username from Salesforce profile URL"""
    try:
        parts = url.rstrip('/').split('/')
        return parts[-1] if len(parts) > 0 else ''
    except:
        return ''

def extract_user_data_from_profile(profile_url: str) -> Dict:
    """
    Extract user completion data from Salesforce Trailblazer profile URL
    Uses the correct URL format: https://www.salesforce.com/trailblazer/username
    """
    try:
        # Setup Chrome driver for scraping
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to profile
        driver.get(profile_url)
        time.sleep(15)  # Wait for page load and dynamic content
        
        # Extract data from page source
        page_source = driver.page_source.lower()
        
        # Initialize data structure
        modules = []
        projects = []
        superbadges = []
        certifications = []
        points = 0
        badges = []
        
        # Extract points (look for point total - common patterns)
        points_patterns = [
            r'(\d+,?\d*)\s*points?',
            r'points[:\s]*(\d+,?\d*)',
            r'total[:\s]*(\d+,?\d*)',
            r'(\d+,?\d*)\s*trailhead\s*points'
        ]
        
        for pattern in points_patterns:
            points_match = re.search(pattern, page_source)
            if points_match:
                points = int(points_match.group(1).replace(',', ''))
                break
        
        # Extract badges count
        badge_patterns = [
            r'(\d+)\s*badges?',
            r'badges?[:\s]*(\d+)',
            r'earned[:\s]*(\d+)'
        ]
        
        for pattern in badge_patterns:
            badge_match = re.search(pattern, page_source)
            if badge_match:
                badges = [f"Badge {i+1}" for i in range(int(badge_match.group(1)))]
                break
        
        # Look for specific Agentblazer-related content
        agentblazer_keywords = [
            'artificial intelligence', 'ai fundamentals', 'generative ai',
            'large language', 'prompt builder', 'einstein trust',
            'autonomous agents', 'agentforce', 'agent builder',
            'data cloud', 'prompt engineering', 'apex for agentforce'
        ]
        
        # Count matching keywords to estimate completion
        keyword_matches = sum(1 for keyword in agentblazer_keywords if keyword in page_source)
        
        # Estimate modules based on keyword presence (simplified approach)
        if keyword_matches >= 10:  # High keyword match suggests good completion
            modules = AGENTBLAZER_REQUIREMENTS["Champion"]["modules"][:keyword_matches-5]
            if keyword_matches >= 12:
                modules.extend(AGENTBLAZER_REQUIREMENTS["Innovator"]["modules"][:3])
        elif keyword_matches >= 6:
            modules = AGENTBLAZER_REQUIREMENTS["Champion"]["modules"][:keyword_matches-2]
        elif keyword_matches >= 3:
            modules = AGENTBLAZER_REQUIREMENTS["Champion"]["modules"][:keyword_matches]
        
        # Look for project indicators
        project_keywords = ['quick start', 'build', 'connect', 'customize']
        project_matches = sum(1 for keyword in project_keywords if keyword in page_source)
        
        if project_matches >= 2:
            projects = AGENTBLAZER_REQUIREMENTS["Champion"]["projects"][:project_matches]
        
        # Look for superbadge indicators
        if 'superbadge' in page_source:
            superbadges = ["Agentforce for Service Superbadge Unit"]
        
        # Look for certification indicators
        if 'certification' in page_source and 'agentforce' in page_source:
            certifications = ["Agentforce Specialist Certification"]
        
        driver.quit()
        
        return {
            "modules": modules,
            "projects": projects,
            "superbadges": superbadges,
            "certifications": certifications,
            "points": points,
            "badges": badges,
            "keyword_matches": keyword_matches
        }
        
    except Exception as e:
        return {
            "modules": [],
            "projects": [],
            "superbadges": [],
            "certifications": [],
            "points": 0,
            "badges": [],
            "keyword_matches": 0,
            "error": str(e)
        }

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    return ' '.join(text.lower().split())

def verify_agentblazer_requirements(profile_data: Dict, target_level: str) -> Dict:
    """
    Verify if profile meets Agentblazer requirements for target level
    """
    if target_level not in AGENTBLAZER_REQUIREMENTS:
        return {"error": f"Invalid level: {target_level}"}
    
    requirements = AGENTBLAZER_REQUIREMENTS[target_level]
    
    verification_results = {
        "profile_data": profile_data,
        "target_level": target_level,
        "requirements": requirements,
        "overall_qualified": False,
        "detailed_analysis": {}
    }
    
    # Check points requirement
    points_qualified = profile_data["points"] >= requirements["min_points"]
    verification_results["detailed_analysis"]["points"] = {
        "required": requirements["min_points"],
        "actual": profile_data["points"],
        "qualified": points_qualified,
        "completion_percentage": min(100, (profile_data["points"] / requirements["min_points"]) * 100)
    }
    
    # Check each category
    categories = ["modules", "projects", "superbadges", "certifications"]
    all_requirements_met = points_qualified
    
    for category in categories:
        required_items = requirements.get(category, [])
        user_items = profile_data.get(category, [])
        
        if not required_items:  # Skip empty categories
            continue
            
        # Normalize for comparison
        required_normalized = {normalize_text(item) for item in required_items}
        user_normalized = {normalize_text(item) for item in user_items}
        
        # Find matches using fuzzy matching
        completed_items = []
        for req_item in required_items:
            req_normalized = normalize_text(req_item)
            for user_item in user_items:
                user_normalized = normalize_text(user_item)
                # Check for partial matches (keywords)
                req_keywords = req_normalized.split()
                if any(keyword in user_normalized for keyword in req_keywords if len(keyword) > 3):
                    completed_items.append(req_item)
                    break
        
        completed_count = len(completed_items)
        required_count = len(required_items)
        missing_count = required_count - completed_count
        category_qualified = missing_count == 0
        
        if not category_qualified:
            all_requirements_met = False
        
        missing_items = [item for item in required_items if item not in completed_items]
        
        verification_results["detailed_analysis"][category] = {
            "required_count": required_count,
            "completed_count": completed_count,
            "missing_count": missing_count,
            "qualified": category_qualified,
            "completion_percentage": (completed_count / required_count * 100) if required_count > 0 else 100,
            "missing_items": missing_items,
            "completed_items": completed_items
        }
    
    verification_results["overall_qualified"] = all_requirements_met
    
    if all_requirements_met:
        verification_results["badge_awarded"] = target_level
    else:
        verification_results["badge_awarded"] = "Not Qualified"
    
    return verification_results

def main():
    st.set_page_config(
        page_title="Agentblazer Badge Verifier",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Agentblazer Badge Verification System")
    st.success("✅ Enter a Salesforce Trailblazer profile URL to verify badge eligibility!")
    
    # URL Format Information
    with st.expander("ℹ️ Correct URL Format", expanded=False):
        st.markdown("""
        **Use this URL format:**
        ```
        https://www.salesforce.com/trailblazer/username
        ```
        
        **Example:**
        ```
        https://www.salesforce.com/trailblazer/aarathisreeballa
        ```
        
        **Note:** Make sure the profile is public and accessible.
        """)
    
    # Requirements Overview
    with st.expander("📋 View Agentblazer Requirements"):
        tab1, tab2, tab3 = st.tabs(["🥉 Champion", "🥈 Innovator", "🥇 Legend"])
        
        for tab, (level, req) in zip([tab1, tab2, tab3], AGENTBLAZER_REQUIREMENTS.items()):
            with tab:
                st.write(f"**Description:** {req['description']}")
                st.write(f"**Minimum Points:** {req['min_points']:,}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if req['modules']:
                        st.write(f"**📚 Modules Required:** {len(req['modules'])}")
                        with st.expander("View Required Modules"):
                            for i, module in enumerate(req['modules'], 1):
                                st.write(f"{i}. {module}")
                    
                    if req['projects']:
                        st.write(f"**🚀 Projects Required:** {len(req['projects'])}")
                        with st.expander("View Required Projects"):
                            for i, project in enumerate(req['projects'], 1):
                                st.write(f"{i}. {project}")
                
                with col2:
                    if req['superbadges']:
                        st.write(f"**🏆 Superbadges Required:** {len(req['superbadges'])}")
                        with st.expander("View Required Superbadges"):
                            for i, superbadge in enumerate(req['superbadges'], 1):
                                st.write(f"{i}. {superbadge}")
                    
                    if req['certifications']:
                        st.write(f"**🎓 Certifications Required:** {len(req['certifications'])}")
                        with st.expander("View Required Certifications"):
                            for i, cert in enumerate(req['certifications'], 1):
                                st.write(f"{i}. {cert}")
    
    # Single Profile Verification
    st.subheader("🎯 Profile Verification")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        profile_url = st.text_input(
            "📧 Enter Salesforce Trailblazer Profile URL:",
            placeholder="https://www.salesforce.com/trailblazer/aarathisreeballa",
            help="Enter the complete Salesforce trailblazer profile URL"
        )
    
    with col2:
        target_level = st.selectbox(
            "🎯 Target Badge Level:",
            ["Champion", "Innovator", "Legend"]
        )
    
    if st.button("🔍 Verify Badge Eligibility", type="primary"):
        if not profile_url:
            st.error("❌ Please enter a valid Salesforce trailblazer profile URL")
        elif not validate_profile_url(profile_url):
            st.error("❌ Please enter a valid URL in format: https://www.salesforce.com/trailblazer/username")
        else:
            with st.spinner(f"🔄 Analyzing profile for {target_level} badge eligibility..."):
                # Extract real data from profile
                profile_data = extract_user_data_from_profile(profile_url)
                
                if "error" in profile_data:
                    st.error(f"❌ Error extracting profile data: {profile_data['error']}")
                    return
                
                if profile_data["points"] == 0 and profile_data["keyword_matches"] == 0:
                    st.warning("⚠️ Could not extract meaningful data from profile. This may be due to:")
                    st.write("• Profile is private or restricted")
                    st.write("• Profile URL is incorrect") 
                    st.write("• Network/scraping restrictions")
                    st.write("• Profile has no Agentblazer-related content")
                    st.info("💡 Please verify the profile URL and ensure it's publicly accessible")
                    return
                
                # Verify against requirements
                verification_results = verify_agentblazer_requirements(profile_data, target_level)
            
            # Display results
            st.subheader("📊 Verification Results")
            
            if verification_results["overall_qualified"]:
                st.success(f"🎉 **QUALIFIED for {verification_results['badge_awarded']} Badge!**")
                st.balloons()
            else:
                st.warning(f"⚠️ **Not yet qualified for {target_level} badge**")
            
            # Show profile data found
            with st.expander("📋 Profile Data Extracted"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Points:** {profile_data['points']:,}")
                    st.write(f"**Total Badges:** {len(profile_data['badges'])}")
                    st.write(f"**Keyword Matches:** {profile_data['keyword_matches']}")
                with col2:
                    st.write(f"**Modules Found:** {len(profile_data['modules'])}")
                    st.write(f"**Projects Found:** {len(profile_data['projects'])}")
                    st.write(f"**Superbadges Found:** {len(profile_data['superbadges'])}")
            
            # Detailed requirements analysis
            for category, analysis in verification_results["detailed_analysis"].items():
                if category == "points":
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if analysis["qualified"]:
                            st.success("✅ **Points**")
                        else:
                            st.error("❌ **Points**")
                    with col2:
                        progress = min(1.0, analysis["completion_percentage"] / 100)
                        st.progress(progress, text=f"{analysis['actual']:,} / {analysis['required']:,} points ({analysis['completion_percentage']:.1f}%)")
                
                elif analysis["required_count"] > 0:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        if analysis["qualified"]:
                            st.success(f"✅ **{category.title()}**")
                        else:
                            st.error(f"❌ **{category.title()}**")
                    
                    with col2:
                        progress = analysis["completion_percentage"] / 100
                        st.progress(progress, text=f"{analysis['completed_count']}/{analysis['required_count']} completed ({analysis['completion_percentage']:.0f}%)")
                    
                    with col3:
                        if analysis["completed_count"] > 0:
                            with st.expander(f"Found ({analysis['completed_count']})"):
                                for completed_item in analysis["completed_items"]:
                                    st.write(f"✅ {completed_item}")
                        
                        if not analysis["qualified"] and analysis["missing_count"] > 0:
                            with st.expander(f"Missing ({analysis['missing_count']})"):
                                for missing_item in analysis["missing_items"]:
                                    st.write(f"❌ {missing_item}")
    
    # Batch Processing
    st.divider()
    st.subheader("📂 Batch Profile Verification")
    
    uploaded_file = st.file_uploader("Upload CSV with profile URLs", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_columns = ["Roll Number", "Name", "Salesforce URL"]
        if all(col in df.columns for col in required_columns):
            st.success(f"✅ Loaded {len(df)} students for verification")
            
            # Validate URLs in the CSV
            valid_urls = df['Salesforce URL'].apply(validate_profile_url).sum()
            st.info(f"📊 {valid_urls}/{len(df)} URLs have correct format")
            
            st.dataframe(df.head())
            
            batch_level = st.selectbox("Batch Verification Level:", ["Champion", "Innovator", "Legend"], key="batch")
            max_profiles = st.number_input("Max profiles to process:", 1, len(df), min(5, len(df)))
            
            if st.button("🚀 Start Batch Verification", type="primary"):
                batch_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, row in df.head(max_profiles).iterrows():
                    progress = (idx + 1) / max_profiles
                    progress_bar.progress(progress)
                    status_text.text(f"Verifying {idx+1}/{max_profiles}: {row['Name']}")
                    
                    if not validate_profile_url(row['Salesforce URL']):
                        batch_results.append({
                            "Roll Number": row["Roll Number"],
                            "Name": row["Name"],
                            "Profile URL": row["Salesforce URL"],
                            "Target Level": batch_level,
                            "Points": 0,
                            "Qualified": "No",
                            "Badge Awarded": "Invalid URL",
                            "Status": "URL format error"
                        })
                        continue
                    
                    # Extract profile data
                    profile_data = extract_user_data_from_profile(row['Salesforce URL'])
                    
                    if "error" in profile_data:
                        batch_results.append({
                            "Roll Number": row["Roll Number"],
                            "Name": row["Name"],
                            "Profile URL": row["Salesforce URL"],
                            "Target Level": batch_level,
                            "Points": 0,
                            "Qualified": "No",
                            "Badge Awarded": "Error",
                            "Status": profile_data["error"][:50]
                        })
                        continue
                    
                    # Verify requirements
                    verification = verify_agentblazer_requirements(profile_data, batch_level)
                    
                    batch_results.append({
                        "Roll Number": row["Roll Number"],
                        "Name": row["Name"],
                        "Profile URL": row["Salesforce URL"],
                        "Target Level": batch_level,
                        "Points": profile_data["points"],
                        "Qualified": "Yes" if verification["overall_qualified"] else "No",
                        "Badge Awarded": verification["badge_awarded"],
                        "Status": "Verified successfully"
                    })
                
                # Display results
                results_df = pd.DataFrame(batch_results)
                
                # Summary
                qualified_count = len(results_df[results_df["Qualified"] == "Yes"])
                total_count = len(results_df)
                avg_points = results_df[results_df["Points"] > 0]["Points"].mean() if len(results_df[results_df["Points"] > 0]) > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Processed", total_count)
                with col2:
                    st.metric("Qualified", qualified_count)
                with col3:
                    st.metric("Success Rate", f"{(qualified_count/total_count)*100:.1f}%")
                with col4:
                    st.metric("Avg Points", f"{avg_points:,.0f}")
                
                st.dataframe(results_df, use_container_width=True)
                
                # Download
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Verification Results",
                    csv_data,
                    f"agentblazer_{batch_level.lower()}_verification_results.csv",
                    "text/csv"
                )
        
        else:
            st.error(f"❌ CSV must contain columns: {', '.join(required_columns)}")

if __name__ == "__main__":
    main()
