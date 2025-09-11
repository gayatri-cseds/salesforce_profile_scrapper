import streamlit as st
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
from typing import Dict, List

# Agentblazer Requirements Database
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

def setup_chrome_driver():
    """Setup Chrome driver with proper configuration"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use webdriver-manager to handle version compatibility
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        st.error(f"ChromeDriver setup failed: {str(e)}")
        return None

def scrape_salesforce_profile(profile_url: str) -> Dict:
    """
    Scrape Salesforce Trailblazer profile to extract completion data
    """
    driver = setup_chrome_driver()
    if not driver:
        return {"error": "Failed to setup ChromeDriver"}
    
    try:
        st.info(f"🔄 Loading profile: {profile_url}")
        
        # Navigate to profile
        driver.get(profile_url)
        
        # Wait for page to load
        time.sleep(15)
        
        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Initialize data structure
        profile_data = {
            "modules": [],
            "projects": [],
            "superbadges": [],
            "certifications": [],
            "points": 0,
            "badges": [],
            "rank": "",
            "raw_text": page_source.lower()
        }
        
        # Extract points (look for various point patterns)
        points_patterns = [
            r'(\d+,?\d*)\s*points?',
            r'points[:\s]*(\d+,?\d*)',
            r'(\d+,?\d*)\s*total\s*points',
            r'earned[:\s]*(\d+,?\d*)\s*points'
        ]
        
        for pattern in points_patterns:
            match = re.search(pattern, page_source.lower())
            if match:
                try:
                    profile_data["points"] = int(match.group(1).replace(',', ''))
                    break
                except:
                    continue
        
        # Extract badges count
        badge_patterns = [
            r'(\d+)\s*badges?',
            r'badges?[:\s]*(\d+)',
            r'earned[:\s]*(\d+)\s*badges?'
        ]
        
        badges_count = 0
        for pattern in badge_patterns:
            match = re.search(pattern, page_source.lower())
            if match:
                try:
                    badges_count = int(match.group(1))
                    profile_data["badges"] = [f"Badge {i+1}" for i in range(badges_count)]
                    break
                except:
                    continue
        
        # Extract rank information
        rank_patterns = [
            r'(ranger|adventurer|mountaineer|explorer)',
            r'rank[:\s]*(ranger|adventurer|mountaineer|explorer)',
            r'trailblazer[:\s]*(ranger|adventurer|mountaineer|explorer)'
        ]
        
        for pattern in rank_patterns:
            match = re.search(pattern, page_source.lower())
            if match:
                profile_data["rank"] = match.group(1).title()
                break
        
        # Look for Agentblazer specific content
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
            "introduction to agentforce": "Introduction to Agentforce",
            "agentforce builder": "Introduction to Agentforce Builder",
            "agentforce for service": "Agentforce for Service",
            "agentforce for sales": "Agentforce for Sales: Quick Look",
            "ai strategy": "AI Strategy",
            "trusted agentic": "Trusted Agentic AI",
            "agentforce sdr": "Agentforce SDR Setup and Customization",
            "sales coach": "Agentforce Sales Coach Setup and Customization",
            "prompt engineering": "Prompt Engineering Techniques",
            "agent customization": "Agent Customization",
            "data cloud": "Data Cloud-Powered Experiences",
            "retrieval augmented": "Retrieval Augmented Generation",
            "agentforce specialist": "Cert Prep: Agentforce Specialist"
        }
        
        # Find matching modules based on keywords
        text_content = page_source.lower()
        for keyword, module_name in agentblazer_keywords.items():
            if keyword in text_content:
                profile_data["modules"].append(module_name)
        
        # Look for project indicators
        project_keywords = {
            "quick start": ["Quick Start: Build a Service Agent with Agentforce", "Quick Start: Agent Actions"],
            "build": ["Quick Start: Build a Service Agent with Agentforce", "Build Your First Sales Coach"],
            "connect data cloud": "Connect Data Cloud to Agentforce and Prompt Builder",
            "customize": "Customize a Service Agent with Prompts, Flows and Actions",
            "employee agents": "Quick Start: Create Employee Agents in Agentforce",
            "slack": "Connect Your Agentforce Org with Slack",
            "agent dx": "Create an Agent Using Agentforce DX"
        }
        
        for keyword, project_names in project_keywords.items():
            if keyword in text_content:
                if isinstance(project_names, list):
                    profile_data["projects"].extend(project_names)
                else:
                    profile_data["projects"].append(project_names)
        
        # Look for superbadges
        if "superbadge" in text_content:
            if "agentforce" in text_content and "service" in text_content:
                profile_data["superbadges"].append("Agentforce for Service Superbadge Unit")
            if "advanced flow" in text_content:
                profile_data["superbadges"].append("Superbadge: Advanced Flow for Agentforce")
            if "apex" in text_content and "agentforce" in text_content:
                profile_data["superbadges"].append("Superbadge: Apex for Agentforce")
        
        # Look for certifications
        if "certification" in text_content or "certified" in text_content:
            if "agentforce specialist" in text_content:
                profile_data["certifications"].append("Earn your Agentforce Specialist Certification")
        
        # Remove duplicates
        profile_data["modules"] = list(set(profile_data["modules"]))
        profile_data["projects"] = list(set(profile_data["projects"]))
        profile_data["superbadges"] = list(set(profile_data["superbadges"]))
        profile_data["certifications"] = list(set(profile_data["certifications"]))
        
        return profile_data
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        driver.quit()

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    return ' '.join(text.lower().split())

def verify_badge_requirements(profile_data: Dict, target_level: str) -> Dict:
    """Verify if profile meets badge requirements"""
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
        
        if not required_items:
            continue
            
        # Match items using fuzzy matching
        completed_items = []
        for req_item in required_items:
            req_normalized = normalize_text(req_item)
            for user_item in user_items:
                user_normalized = normalize_text(user_item)
                # Check for keyword matches
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
    verification_results["badge_awarded"] = target_level if all_requirements_met else "Not Qualified"
    
    return verification_results

def main():
    st.set_page_config(
        page_title="Agentblazer Badge Verifier - Profile Scraper",
        page_icon="🏆",
        layout="wide"
    )
    
    st.title("🏆 Agentblazer Badge Verification System")
    st.success("✅ Automatically extracts and verifies profile data from Salesforce Trailblazer URLs!")
    
    # URL Format Guide
    with st.expander("📋 Correct URL Format & Requirements", expanded=False):
        st.markdown("""
        **Use this URL format:**
        ```
        https://www.salesforce.com/trailblazer/username
        ```
        
        **Example:**
        ```
        https://www.salesforce.com/trailblazer/aarathisreeballa
        ```
        
        **Requirements:**
        - Profile must be **public** and accessible
        - Complete URL including https://
        - Valid Salesforce Trailblazer username
        """)
    
    # Requirements Overview
    with st.expander("📚 View Agentblazer Requirements"):
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
            help="Enter the complete Salesforce trailblazer profile URL for automatic data extraction"
        )
    
    with col2:
        target_level = st.selectbox(
            "🎯 Target Badge Level:",
            ["Champion", "Innovator", "Legend"]
        )
    
    if st.button("🔍 Extract Profile Data & Verify Badge", type="primary"):
        if not profile_url:
            st.error("❌ Please enter a valid Salesforce trailblazer profile URL")
        elif not profile_url.startswith("https://www.salesforce.com/trailblazer/"):
            st.error("❌ Please enter a valid URL in format: https://www.salesforce.com/trailblazer/username")
        else:
            with st.spinner(f"🔄 Scraping profile and analyzing for {target_level} badge eligibility..."):
                # Extract profile data
                profile_data = scrape_salesforce_profile(profile_url)
                
                if "error" in profile_data:
                    st.error(f"❌ Error extracting profile data: {profile_data['error']}")
                    
                    # Provide troubleshooting advice
                    st.subheader("🔧 Troubleshooting")
                    st.write("**Common issues and solutions:**")
                    st.write("• **ChromeDriver version mismatch**: Run `pip install --upgrade webdriver-manager`")
                    st.write("• **Profile is private**: Make sure the profile is public and accessible")
                    st.write("• **Network issues**: Check internet connection and try again")
                    st.write("• **Anti-bot protection**: Profile may be temporarily blocked from scraping")
                    
                    return
                
                if profile_data["points"] == 0 and len(profile_data["modules"]) == 0:
                    st.warning("⚠️ Could not extract meaningful data from profile. This may be due to:")
                    st.write("• Profile is private or has restricted access")
                    st.write("• Profile contains no Agentblazer-related content")
                    st.write("• Profile URL is incorrect or user doesn't exist")
                    st.write("• Anti-scraping measures are blocking data extraction")
                    return
                
                # Verify requirements
                verification_results = verify_badge_requirements(profile_data, target_level)
            
            # Display results
            st.subheader("📊 Verification Results")
            
            if verification_results["overall_qualified"]:
                st.success(f"🎉 **QUALIFIED for {verification_results['badge_awarded']} Badge!**")
                st.balloons()
            else:
                st.warning(f"⚠️ **Not yet qualified for {target_level} badge**")
            
            # Show extracted profile data
            with st.expander("📋 Extracted Profile Data"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Points", f"{profile_data['points']:,}")
                    st.metric("Total Badges", len(profile_data['badges']))
                
                with col2:
                    st.metric("Modules Found", len(profile_data['modules']))
                    st.metric("Projects Found", len(profile_data['projects']))
                
                with col3:
                    st.metric("Superbadges Found", len(profile_data['superbadges']))
                    st.metric("Certifications Found", len(profile_data['certifications']))
                
                if profile_data["rank"]:
                    st.info(f"🏅 **Trailblazer Rank:** {profile_data['rank']}")
            
            # Detailed requirements analysis
            st.subheader("📈 Detailed Requirements Analysis")
            
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
                            with st.expander(f"✅ Found ({analysis['completed_count']})"):
                                for completed_item in analysis["completed_items"]:
                                    st.write(f"• {completed_item}")
                        
                        if not analysis["qualified"] and analysis["missing_count"] > 0:
                            with st.expander(f"❌ Missing ({analysis['missing_count']})"):
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
                    status_text.text(f"Scraping {idx+1}/{max_profiles}: {row['Name']}")
                    
                    # Extract profile data
                    profile_data = scrape_salesforce_profile(row['Salesforce URL'])
                    
                    if "error" in profile_data:
                        batch_results.append({
                            "Roll Number": row["Roll Number"],
                            "Name": row["Name"],
                            "Profile URL": row["Salesforce URL"],
                            "Target Level": batch_level,
                            "Points": 0,
                            "Qualified": "No",
                            "Badge Awarded": "Error",
                            "Status": f"Scraping failed: {profile_data['error'][:50]}..."
                        })
                        continue
                    
                    # Verify requirements
                    verification = verify_badge_requirements(profile_data, batch_level)
                    
                    batch_results.append({
                        "Roll Number": row["Roll Number"],
                        "Name": row["Name"],
                        "Profile URL": row["Salesforce URL"],
                        "Target Level": batch_level,
                        "Points": profile_data["points"],
                        "Modules Found": len(profile_data["modules"]),
                        "Qualified": "Yes" if verification["overall_qualified"] else "No",
                        "Badge Awarded": verification["badge_awarded"],
                        "Status": "Successfully verified"
                    })
                    
                    # Small delay to avoid overwhelming the server
                    time.sleep(2)
                
                # Display results
                results_df = pd.DataFrame(batch_results)
                
                # Summary
                qualified_count = len(results_df[results_df["Qualified"] == "Yes"])
                total_count = len(results_df)
                avg_points = results_df[results_df["Points"] > 0]["Points"].mean() if len(results_df[results_df["Points"] > 0]) > 0 else 0
                success_count = len(results_df[results_df["Status"] == "Successfully verified"])
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Processed", total_count)
                with col2:
                    st.metric("Successfully Scraped", success_count)
                with col3:
                    st.metric("Qualified for Badge", qualified_count)
                with col4:
                    st.metric("Avg Points", f"{avg_points:,.0f}")
                
                st.dataframe(results_df, use_container_width=True)
                
                # Download results
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
