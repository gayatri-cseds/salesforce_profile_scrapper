import streamlit as st
import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.log import configure_logging
import pandas as pd
import json
import os
import time
import threading
from typing import Dict, List
import asyncio
from twisted.internet import reactor, defer
import tempfile

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

class SalesforceProfileSpider(scrapy.Spider):
    name = "salesforce_profiles"
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'FEEDS': {
            'scraped_profiles.json': {'format': 'json', 'overwrite': True},
        },
        # Enable Playwright for JavaScript rendering
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            "headless": True,
            "timeout": 30000,
        }
    }
    
    def __init__(self, *args, **kwargs):
        super(SalesforceProfileSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', [])
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        "wait_for_load_state('networkidle')",
                        "wait_for_timeout(5000)"
                    ]
                }
            )
    
    def parse(self, response):
        # Extract profile data
        profile_data = self.extract_profile_data(response)
        
        yield {
            'url': response.url,
            'profile_data': profile_data,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def extract_profile_data(self, response):
        """Extract comprehensive profile data from Salesforce page"""
        
        page_text = response.text.lower()
        
        profile_data = {
            "modules": [],
            "projects": [],
            "superbadges": [],
            "certifications": [],
            "points": 0,
            "badges": [],
            "rank": ""
        }
        
        # Extract points using multiple patterns
        import re
        points_patterns = [
            r'(\d+,?\d*)\s*points?',
            r'points[:\s]*(\d+,?\d*)',
            r'(\d+,?\d*)\s*total\s*points',
            r'earned[:\s]*(\d+,?\d*)\s*points'
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
        
        # Look for Agentblazer keywords with improved matching
        agentblazer_keywords = {
            "artificial intelligence fundamentals": "Artificial Intelligence Fundamentals",
            "generative ai basics": "Generative AI Basics",
            "natural language processing": "Natural Language Processing Basics",
            "large language models": "Large Language Models",
            "data fundamentals": "Data Fundamentals for AI",
            "prompt fundamentals": "Prompt Fundamentals",
            "prompt builder": "Prompt Builder Basics",
            "einstein trust layer": "The Einstein Trust Layer",
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
        
        # Find matching modules
        for keyword, module_name in agentblazer_keywords.items():
            if keyword in page_text:
                profile_data["modules"].append(module_name)
        
        # Look for projects
        project_keywords = {
            "quick start build service agent": "Quick Start: Build a Service Agent with Agentforce",
            "quick start agent actions": "Quick Start: Agent Actions",
            "connect data cloud agentforce": "Connect Data Cloud to Agentforce and Prompt Builder",
            "customize service agent": "Customize a Service Agent with Prompts, Flows and Actions",
            "build first sales coach": "Build Your First Sales Coach",
            "employee agents": "Quick Start: Create Employee Agents in Agentforce",
            "connect agentforce slack": "Connect Your Agentforce Org with Slack",
            "agent dx": "Create an Agent Using Agentforce DX"
        }
        
        for keyword, project_name in project_keywords.items():
            if keyword in page_text:
                profile_data["projects"].append(project_name)
        
        # Look for superbadges
        if "superbadge" in page_text:
            if "agentforce service" in page_text:
                profile_data["superbadges"].append("Agentforce for Service Superbadge Unit")
            if "advanced flow agentforce" in page_text:
                profile_data["superbadges"].append("Superbadge: Advanced Flow for Agentforce")
            if "apex agentforce" in page_text:
                profile_data["superbadges"].append("Superbadge: Apex for Agentforce")
        
        # Look for certifications
        if "certification" in page_text or "certified" in page_text:
            if "agentforce specialist" in page_text:
                profile_data["certifications"].append("Earn your Agentforce Specialist Certification")
        
        # Remove duplicates
        for key in ["modules", "projects", "superbadges", "certifications"]:
            profile_data[key] = list(set(profile_data[key]))
        
        return profile_data

def run_scrapy_spider(urls: List[str]) -> List[Dict]:
    """Run Scrapy spider with given URLs and return results"""
    
    # Create temporary directory for results
    temp_dir = tempfile.mkdtemp()
    results_file = os.path.join(temp_dir, 'scraped_profiles.json')
    
    # Configure Scrapy settings
    settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 1,
        'FEEDS': {
            results_file: {'format': 'json', 'overwrite': True},
        },
        'LOG_LEVEL': 'INFO',
    }
    
    try:
        # Use CrawlerProcess for synchronous execution
        configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
        process = CrawlerProcess(settings)
        process.crawl(SalesforceProfileSpider, start_urls=urls)
        process.start(stop_after_crawl=True)
        
        # Read results
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                results = json.load(f)
            return results
        else:
            return []
            
    except Exception as e:
        st.error(f"Scrapy crawling failed: {str(e)}")
        return []

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
            
        # Fuzzy matching for completions
        completed_items = []
        for req_item in required_items:
            req_normalized = req_item.lower()
            for user_item in user_items:
                user_normalized = user_item.lower()
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
        page_title="Scrapy + Streamlit Badge Verifier",
        page_icon="🕷️",
        layout="wide"
    )
    
    st.title("🕷️ Scrapy + Streamlit Agentblazer Badge Verification System")
    st.success("✅ Powerful Scrapy scraping with beautiful Streamlit interface!")
    
    # Information about the system
    with st.expander("🔧 About This System", expanded=False):
        st.markdown("""
        **Scrapy + Streamlit Integration:**
        - **Scrapy Framework**: Professional-grade web scraping with JavaScript support
        - **Playwright Integration**: Handles dynamic content and modern web apps
        - **Streamlit Interface**: Beautiful, interactive frontend for data visualization
        - **Comprehensive Scraping**: Extracts points, badges, modules, projects, and certifications
        - **Batch Processing**: Handles multiple profiles efficiently
        - **Real-time Results**: Live progress updates and instant verification
        """)
    
    # Requirements overview
    with st.expander("📚 Agentblazer Requirements"):
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
    st.subheader("🎯 Single Profile Verification")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        profile_url = st.text_input(
            "📧 Enter Salesforce Trailblazer Profile URL:",
            placeholder="https://www.salesforce.com/trailblazer/aarathisreeballa",
            help="Enter the complete profile URL for Scrapy-powered extraction"
        )
    
    with col2:
        target_level = st.selectbox("🎯 Target Badge Level:", ["Champion", "Innovator", "Legend"])
    
    if st.button("🕷️ Scrape Profile & Verify Badge", type="primary"):
        if not profile_url:
            st.error("❌ Please enter a valid profile URL")
        elif not profile_url.startswith("https://www.salesforce.com/trailblazer/"):
            st.error("❌ Please enter a valid Salesforce trailblazer URL")
        else:
            with st.spinner("🕷️ Scrapy is crawling the profile..."):
                # Run Scrapy spider
                scraped_results = run_scrapy_spider([profile_url])
                
                if not scraped_results:
                    st.error("❌ Failed to scrape profile data")
                    st.info("💡 This may be due to:")
                    st.write("• Profile is private or restricted")
                    st.write("• Network connectivity issues")  
                    st.write("• Scrapy configuration issues")
                    st.write("• Playwright browser setup problems")
                    return
                
                profile_data = scraped_results[0]['profile_data']
                
                # Verify requirements
                verification_results = verify_badge_requirements(profile_data, target_level)
            
            # Display results
            st.subheader("📊 Scrapy Extraction & Verification Results")
            
            if verification_results["overall_qualified"]:
                st.success(f"🎉 **QUALIFIED for {verification_results['badge_awarded']} Badge!**")
                st.balloons()
            else:
                st.warning(f"⚠️ **Not yet qualified for {target_level} badge**")
            
            # Show extracted data
            with st.expander("🕷️ Scrapy Extracted Data"):
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
            
            # Detailed verification analysis
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
    st.subheader("📂 Batch Profile Verification with Scrapy")
    
    uploaded_file = st.file_uploader("Upload CSV with profile URLs", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_columns = ["Roll Number", "Name", "Salesforce URL"]
        if all(col in df.columns for col in required_columns):
            st.success(f"✅ Loaded {len(df)} students for Scrapy batch processing")
            st.dataframe(df.head())
            
            batch_level = st.selectbox("Batch Verification Level:", ["Champion", "Innovator", "Legend"], key="batch")
            max_profiles = st.number_input("Max profiles to process:", 1, len(df), min(5, len(df)))
            
            if st.button("🕷️ Start Scrapy Batch Processing", type="primary"):
                
                profiles_to_process = df.head(max_profiles)
                profile_urls = profiles_to_process['Salesforce URL'].tolist()
                
                with st.spinner(f"🕷️ Scrapy is processing {len(profile_urls)} profiles..."):
                    # Run Scrapy on all URLs
                    scraped_results = run_scrapy_spider(profile_urls)
                
                if scraped_results:
                    st.success(f"✅ Scrapy successfully processed {len(scraped_results)} profiles!")
                    
                    # Process results
                    batch_results = []
                    
                    for idx, scraped_result in enumerate(scraped_results):
                        profile_data = scraped_result['profile_data']
                        
                        # Find matching row in CSV
                        matching_row = profiles_to_process[profiles_to_process['Salesforce URL'] == scraped_result['url']]
                        
                        if not matching_row.empty:
                            row = matching_row.iloc[0]
                            
                            # Verify requirements
                            verification = verify_badge_requirements(profile_data, batch_level)
                            
                            batch_results.append({
                                "Roll Number": row["Roll Number"],
                                "Name": row["Name"],
                                "Profile URL": row["Salesforce URL"],
                                "Target Level": batch_level,
                                "Points": profile_data["points"],
                                "Modules Found": len(profile_data["modules"]),
                                "Projects Found": len(profile_data["projects"]),
                                "Qualified": "Yes" if verification["overall_qualified"] else "No",
                                "Badge Awarded": verification["badge_awarded"],
                                "Status": "Scrapy Success"
                            })
                    
                    # Display batch results
                    if batch_results:
                        results_df = pd.DataFrame(batch_results)
                        
                        # Summary metrics
                        qualified_count = len(results_df[results_df["Qualified"] == "Yes"])
                        total_count = len(results_df)
                        avg_points = results_df["Points"].mean()
                        avg_modules = results_df["Modules Found"].mean()
                        
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
                        
                        # Download results
                        csv_data = results_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Scrapy Batch Results",
                            csv_data,
                            f"scrapy_agentblazer_{batch_level.lower()}_results.csv",
                            "text/csv"
                        )
                else:
                    st.error("❌ Scrapy batch processing failed")
        
        else:
            st.error(f"❌ CSV must contain columns: {', '.join(required_columns)}")

if __name__ == "__main__":
    main()
