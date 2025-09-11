import streamlit as st
import pandas as pd
import requests
from typing import Dict, List, Tuple
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

def extract_user_data_from_profile(profile_url: str) -> Dict:
    """
    Extract user completion data from Trailhead profile URL
    This function scrapes the actual profile page to get real data
    """
    try:
        # Setup Chrome driver for scraping
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to profile
        driver.get(profile_url)
        time.sleep(10)  # Wait for page load
        
        # Extract data from page source
        page_source = driver.page_source
        
        # Parse completed modules, projects, superbadges
        # This is a simplified extraction - you'd need to enhance this
        # based on the actual HTML structure of Trailhead profiles
        
        modules = []
        projects = []
        superbadges = []
        certifications = []
        points = 0
        
        # Extract points (look for point total)
        points_match = re.search(r'(\d+,?\d*)\s*points?', page_source, re.IGNORECASE)
        if points_match:
            points = int(points_match.group(1).replace(',', ''))
        
        # Extract badges/modules (look for completed items)
        # This would need to be enhanced based on actual HTML structure
        module_matches = re.findall(r'completed.*?([A-Za-z\s]+(?:Fundamentals|Basics|Introduction))', page_source, re.IGNORECASE)
        modules.extend(module_matches)
        
        project_matches = re.findall(r'completed.*?([A-Za-z\s]*Quick Start[A-Za-z\s]*)', page_source, re.IGNORECASE)
        projects.extend(project_matches)
        
        superbadge_matches = re.findall(r'completed.*?([A-Za-z\s]*Superbadge[A-Za-z\s]*)', page_source, re.IGNORECASE)
        superbadges.extend(superbadge_matches)
        
        driver.quit()
        
        return {
            "modules": modules,
            "projects": projects, 
            "superbadges": superbadges,
            "certifications": certifications,
            "points": points
        }
        
    except Exception as e:
        st.error(f"Error extracting data from profile: {str(e)}")
        return {
            "modules": [],
            "projects": [],
            "superbadges": [],
            "certifications": [],
            "points": 0
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
        
        # Find matches
        completed_items = []
        for req_item in required_normalized:
            for user_item in user_normalized:
                if req_item in user_item or user_item in req_item:
                    completed_items.append(req_item)
                    break
        
        completed_count = len(completed_items)
        required_count = len(required_items)
        missing_count = required_count - completed_count
        category_qualified = missing_count == 0
        
        if not category_qualified:
            all_requirements_met = False
        
        verification_results["detailed_analysis"][category] = {
            "required_count": required_count,
            "completed_count": completed_count,
            "missing_count": missing_count,
            "qualified": category_qualified,
            "completion_percentage": (completed_count / required_count * 100) if required_count > 0 else 100,
            "missing_items": [item for item in required_items if normalize_text(item) not in [normalize_text(c) for c in completed_items]]
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
    
    st.title("🏆 Real-Time Agentblazer Badge Verification")
    st.success("✅ Enter a Trailhead profile URL to verify badge eligibility!")
    
    # Requirements Overview
    with st.expander("📋 View Agentblazer Requirements", expanded=False):
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
            "📧 Enter Trailhead Profile URL:",
            placeholder="https://trailhead.salesforce.com/profile/username",
            help="Enter the complete Trailhead profile URL to verify"
        )
    
    with col2:
        target_level = st.selectbox(
            "🎯 Target Badge Level:",
            ["Champion", "Innovator", "Legend"]
        )
    
    if st.button("🔍 Verify Badge Eligibility", type="primary"):
        if not profile_url:
            st.error("❌ Please enter a valid Trailhead profile URL")
        elif not profile_url.startswith("https://trailhead.salesforce.com"):
            st.error("❌ Please enter a valid Trailhead profile URL starting with https://trailhead.salesforce.com")
        else:
            with st.spinner(f"🔄 Analyzing profile for {target_level} badge eligibility..."):
                # Extract real data from profile
                profile_data = extract_user_data_from_profile(profile_url)
                
                if profile_data["points"] == 0 and not profile_data["modules"]:
                    st.warning("⚠️ Could not extract data from profile. This may be due to:")
                    st.write("• Profile is private or restricted")
                    st.write("• Profile URL is incorrect")
                    st.write("• Network/scraping restrictions")
                    st.info("💡 Try entering profile data manually or use a different approach")
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
                    st.write(f"**Modules Found:** {len(profile_data['modules'])}")
                    st.write(f"**Projects Found:** {len(profile_data['projects'])}")
                with col2:
                    st.write(f"**Superbadges Found:** {len(profile_data['superbadges'])}")
                    st.write(f"**Certifications Found:** {len(profile_data['certifications'])}")
            
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
                        if not analysis["qualified"] and analysis["missing_count"] > 0:
                            with st.expander(f"Missing ({analysis['missing_count']})"):
                                for missing_item in analysis["missing_items"]:
                                    st.write(f"• {missing_item}")
    
    # Batch Processing
    st.divider()
    st.subheader("📂 Batch Profile Verification")
    
    uploaded_file = st.file_uploader("Upload CSV with profile URLs", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_columns = ["Roll Number", "Name", "Salesforce URL"]
        if all(col in df.columns for col in required_columns):
            st.success(f"✅ Loaded {len(df)} students for verification")
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
                    
                    # Extract profile data
                    profile_data = extract_user_data_from_profile(row['Salesforce URL'])
                    
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
                        "Overall Progress": f"{sum(1 for cat in verification['detailed_analysis'].values() if cat.get('qualified', False))}/{len([cat for cat in verification['detailed_analysis'].values() if cat.get('required_count', 0) > 0])}"
                    })
                
                # Display results
                results_df = pd.DataFrame(batch_results)
                
                # Summary
                qualified_count = len(results_df[results_df["Qualified"] == "Yes"])
                total_count = len(results_df)
                avg_points = results_df["Points"].mean()
                
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
    
    # Footer
    st.divider()
    with st.expander("ℹ️ How This Works & Troubleshooting"):
        st.markdown("""
        ### **🔍 How the Verification Works:**
        
        1. **Profile Data Extraction** - Scrapes actual completion data from Trailhead profiles
        2. **Requirements Matching** - Compares against official Agentblazer criteria
        3. **Automatic Verification** - Determines qualification based on completions
        4. **Badge Awarding** - Awards appropriate badge level for qualified profiles
        
        ### **⚠️ Common Issues:**
        
        - **Private Profiles**: Cannot extract data from private/restricted profiles
        - **Network Issues**: Scraping may fail due to connectivity or anti-bot measures  
        - **URL Format**: Must use complete Trailhead profile URL
        - **Loading Time**: Profile verification takes 10-15 seconds per student
        
        ### **💡 Tips for Best Results:**
        
        - Ensure profile URLs are public and accessible
        - Test with one profile before batch processing
        - Use smaller batches (5-10 profiles) for better reliability
        - Students should make their profiles public before verification
        """)

if __name__ == "__main__":
    main()
