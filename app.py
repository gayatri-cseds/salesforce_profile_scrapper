import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
import re
import time
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
            "Prompt Fundamentals",
            "Prompt Builder Basics",
            "Einstein Trust Layer",
            "Autonomous Agents",
            "Introduction to Agentforce",
            "Agentforce for Service"
        ],
        "keywords": [
            "artificial intelligence", "generative ai", "natural language",
            "large language", "data fundamentals", "prompt fundamentals",
            "prompt builder", "einstein trust", "autonomous agents", 
            "agentforce", "service agent"
        ],
        "min_points": 2500,
        "min_keywords": 5
    },
    
    "Innovator": {
        "modules": [
            "AI Strategy",
            "AI+Data: Project Planning", 
            "Agentforce: Agent Planning",
            "Trusted Agentic AI",
            "Agentforce Builder Basics",
            "Agentforce SDR Setup",
            "Sales Coach Setup"
        ],
        "keywords": [
            "ai strategy", "project planning", "agent planning",
            "trusted agentic", "agentforce builder", "agentforce sdr",
            "sales coach", "superbadge"
        ],
        "min_points": 7500,
        "min_keywords": 4
    },
    
    "Legend": {
        "modules": [
            "Agentforce Specialist",
            "Agent Customization",
            "Prompt Engineering Techniques",
            "Agent Customization with Apex",
            "Data Cloud Experiences",
            "Retrieval Augmented Generation",
            "Testing Tools and Strategies"
        ],
        "keywords": [
            "agentforce specialist", "agent customization", "prompt engineering",
            "apex", "data cloud", "retrieval augmented", "testing tools",
            "certification", "advanced"
        ],
        "min_points": 15000,
        "min_keywords": 6
    }
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def scrape_salesforce_profile(url: str) -> Dict:
    """
    Scrape Salesforce Trailblazer profile using Playwright
    """
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security'
                ]
            )
            
            # Create page with realistic settings
            page = browser.new_page()
            
            # Set headers to appear more like a real browser
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })
            
            # Navigate to profile
            page.goto(url, timeout=30000, wait_until='networkidle')
            
            # Wait for dynamic content to load
            page.wait_for_timeout(5000)
            
            # Get page content
            content = page.content()
            text_content = page.inner_text('body').lower()
            
            # Initialize profile data
            profile_data = {
                "points": 0,
                "badges": 0,
                "modules": [],
                "keywords_found": [],
                "rank": "",
                "profile_url": url,
                "success": True
            }
            
            # Extract points using multiple patterns
            points_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*points?',
                r'points?[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'earned[:\s]*(\d{1,3}(?:,\d{3})*)\s*points?',
                r'total[:\s]*(\d{1,3}(?:,\d{3})*)\s*points?'
            ]
            
            for pattern in points_patterns:
                points_match = re.search(pattern, text_content)
                if points_match:
                    try:
                        profile_data["points"] = int(points_match.group(1).replace(',', ''))
                        break
                    except ValueError:
                        continue
            
            # Extract badges count
            badge_patterns = [
                r'(\d+)\s*badges?',
                r'badges?[:\s]*(\d+)',
                r'earned[:\s]*(\d+)\s*badges?'
            ]
            
            for pattern in badge_patterns:
                badge_match = re.search(pattern, text_content)
                if badge_match:
                    try:
                        profile_data["badges"] = int(badge_match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Extract rank information
            rank_patterns = [
                r'(ranger|adventurer|mountaineer|explorer)',
                r'rank[:\s]*(ranger|adventurer|mountaineer|explorer)'
            ]
            
            for pattern in rank_patterns:
                rank_match = re.search(pattern, text_content)
                if rank_match:
                    profile_data["rank"] = rank_match.group(1).title()
                    break
            
            # Look for Agentblazer keywords across all levels
            all_keywords = []
            for level_req in AGENTBLAZER_REQUIREMENTS.values():
                all_keywords.extend(level_req["keywords"])
            
            # Remove duplicates and find matches
            unique_keywords = list(set(all_keywords))
            
            for keyword in unique_keywords:
                if keyword in text_content:
                    profile_data["keywords_found"].append(keyword)
            
            # Estimate modules based on keywords (simplified approach)
            for level, requirements in AGENTBLAZER_REQUIREMENTS.items():
                matching_keywords = [kw for kw in profile_data["keywords_found"] if kw in requirements["keywords"]]
                if len(matching_keywords) >= requirements["min_keywords"] // 2:  # At least half the keywords
                    # Add some modules for this level
                    sample_modules = requirements["modules"][:len(matching_keywords)]
                    profile_data["modules"].extend(sample_modules)
            
            # Remove duplicate modules
            profile_data["modules"] = list(set(profile_data["modules"]))
            
            browser.close()
            return profile_data
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "points": 0,
            "badges": 0,
            "keywords_found": [],
            "modules": [],
            "profile_url": url
        }

def verify_agentblazer_badge(profile_data: Dict, target_level: str) -> Dict:
    """Verify if profile meets Agentblazer badge requirements"""
    
    if not profile_data.get("success", False):
        return {
            "qualified": False,
            "error": profile_data.get("error", "Unknown error"),
            "target_level": target_level
        }
    
    requirements = AGENTBLAZER_REQUIREMENTS[target_level]
    
    # Check points requirement
    points_qualified = profile_data["points"] >= requirements["min_points"]
    
    # Check keywords requirement
    matching_keywords = [kw for kw in profile_data["keywords_found"] if kw in requirements["keywords"]]
    keywords_qualified = len(matching_keywords) >= requirements["min_keywords"]
    
    # Overall qualification
    overall_qualified = points_qualified and keywords_qualified
    
    return {
        "qualified": overall_qualified,
        "target_level": target_level,
        "points": {
            "actual": profile_data["points"],
            "required": requirements["min_points"],
            "qualified": points_qualified
        },
        "keywords": {
            "found": len(matching_keywords),
            "required": requirements["min_keywords"],
            "qualified": keywords_qualified,
            "matching_keywords": matching_keywords
        },
        "badge_awarded": target_level if overall_qualified else "Not Qualified",
        "profile_data": profile_data
    }

def main():
    st.set_page_config(
        page_title="Playwright Badge Verifier",
        page_icon="🎭",
        layout="wide"
    )
    
    st.title("🎭 Playwright-Based Agentblazer Badge Verification")
    st.success("✅ JavaScript-rendered content scraping with Playwright!")
    
    # About Playwright
    with st.expander("🎭 About Playwright Scraping"):
        st.markdown("""
        **Playwright Advantages:**
        - **JavaScript Rendering**: Handles dynamic content that loads after page render
        - **Real Browser**: Uses actual Chromium browser for authentic scraping  
        - **Anti-Bot Evasion**: Better success rate against detection systems
        - **Network Control**: Waits for content to fully load before scraping
        - **Reliable Extraction**: More accurate than simple HTTP requests
        """)
    
    # Requirements Overview
    with st.expander("📚 Agentblazer Badge Requirements"):
        for level, req in AGENTBLAZER_REQUIREMENTS.items():
            st.subheader(f"🏆 {level} Badge")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Minimum Points:** {req['min_points']:,}")
                st.write(f"**Required Keywords:** {req['min_keywords']}")
            with col2:
                st.write(f"**Sample Modules:** {len(req['modules'])}")
                with st.expander(f"View {level} Modules"):
                    for module in req['modules'][:5]:  # Show first 5
                        st.write(f"• {module}")
    
    # Single Profile Verification
    st.subheader("🎯 Single Profile Verification")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        profile_url = st.text_input(
            "📧 Salesforce Trailblazer Profile URL:",
            placeholder="https://www.salesforce.com/trailblazer/aarathisreeballa",
            help="Enter the complete profile URL for Playwright-powered scraping"
        )
    
    with col2:
        target_level = st.selectbox("🎯 Target Badge Level:", ["Champion", "Innovator", "Legend"])
    
    if st.button("🎭 Scrape with Playwright & Verify", type="primary"):
        if not profile_url:
            st.error("❌ Please enter a valid profile URL")
        elif not profile_url.startswith("https://www.salesforce.com/trailblazer/"):
            st.error("❌ Please enter a valid Salesforce trailblazer URL")
        else:
            with st.spinner("🎭 Playwright is scraping the profile..."):
                # Scrape profile
                profile_data = scrape_salesforce_profile(profile_url)
                
                if not profile_data.get("success", False):
                    st.error(f"❌ Scraping failed: {profile_data.get('error', 'Unknown error')}")
                    st.info("💡 Common issues:")
                    st.write("• Profile is private or restricted")
                    st.write("• Network connectivity problems")
                    st.write("• Playwright browser issues")
                    st.write("• Anti-scraping measures blocking access")
                    return
                
                # Verify badge requirements
                verification = verify_agentblazer_badge(profile_data, target_level)
            
            # Display results
            st.subheader("📊 Playwright Scraping & Verification Results")
            
            if verification["qualified"]:
                st.success(f"🎉 **QUALIFIED for {verification['badge_awarded']} Badge!**")
                st.balloons()
            else:
                st.warning(f"⚠️ **Not yet qualified for {target_level} badge**")
            
            # Show scraped data
            with st.expander("🎭 Playwright Scraped Data"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Points", f"{profile_data['points']:,}")
                    st.metric("Total Badges", profile_data['badges'])
                
                with col2:
                    st.metric("Keywords Found", len(profile_data['keywords_found']))
                    st.metric("Estimated Modules", len(profile_data['modules']))
                
                with col3:
                    if profile_data['rank']:
                        st.metric("Trailblazer Rank", profile_data['rank'])
                    else:
                        st.metric("Rank", "Not detected")
            
            # Detailed verification results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Points Analysis")
                points_data = verification["points"]
                if points_data["qualified"]:
                    st.success("✅ **Points Requirement Met**")
                else:
                    st.error("❌ **Points Requirement Not Met**")
                
                progress = min(1.0, points_data["actual"] / points_data["required"])
                st.progress(progress, text=f"{points_data['actual']:,} / {points_data['required']:,} points")
            
            with col2:
                st.subheader("🔍 Keywords Analysis")
                keywords_data = verification["keywords"]
                if keywords_data["qualified"]:
                    st.success("✅ **Keywords Requirement Met**")
                else:
                    st.error("❌ **Keywords Requirement Not Met**")
                
                progress = min(1.0, keywords_data["found"] / keywords_data["required"])
                st.progress(progress, text=f"{keywords_data['found']} / {keywords_data['required']} keywords")
                
                if keywords_data["matching_keywords"]:
                    with st.expander("View Matching Keywords"):
                        for keyword in keywords_data["matching_keywords"]:
                            st.write(f"✅ {keyword.title()}")
    
    # Batch Processing
    st.divider()
    st.subheader("📂 Batch Processing with Playwright")
    
    uploaded_file = st.file_uploader("Upload CSV with profile URLs", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_columns = ["Roll Number", "Name", "Salesforce URL"]
        if all(col in df.columns for col in required_columns):
            st.success(f"✅ Loaded {len(df)} students for Playwright batch processing")
            st.dataframe(df.head())
            
            batch_level = st.selectbox("Batch Verification Level:", ["Champion", "Innovator", "Legend"], key="batch")
            max_profiles = st.number_input("Max profiles to process:", 1, len(df), min(5, len(df)))
            
            if st.button("🎭 Start Playwright Batch Processing", type="primary"):
                
                batch_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                profiles_to_process = df.head(max_profiles)
                
                for idx, row in profiles_to_process.iterrows():
                    progress = (idx + 1) / max_profiles
                    progress_bar.progress(progress)
                    status_text.text(f"🎭 Playwright processing {idx+1}/{max_profiles}: {row['Name']}")
                    
                    # Scrape profile
                    profile_data = scrape_salesforce_profile(row['Salesforce URL'])
                    
                    if profile_data.get("success", False):
                        # Verify requirements
                        verification = verify_agentblazer_badge(profile_data, batch_level)
                        
                        batch_results.append({
                            "Roll Number": row["Roll Number"],
                            "Name": row["Name"],
                            "Profile URL": row["Salesforce URL"],
                            "Target Level": batch_level,
                            "Points": profile_data["points"],
                            "Keywords Found": len(profile_data["keywords_found"]),
                            "Qualified": "Yes" if verification["qualified"] else "No",
                            "Badge Awarded": verification["badge_awarded"],
                            "Status": "Playwright Success"
                        })
                    else:
                        batch_results.append({
                            "Roll Number": row["Roll Number"],
                            "Name": row["Name"],
                            "Profile URL": row["Salesforce URL"],
                            "Target Level": batch_level,
                            "Points": 0,
                            "Keywords Found": 0,
                            "Qualified": "No",
                            "Badge Awarded": "Error",
                            "Status": f"Failed: {profile_data.get('error', 'Unknown')[:50]}"
                        })
                    
                    # Small delay between requests
                    time.sleep(2)
                
                # Display batch results
                if batch_results:
                    results_df = pd.DataFrame(batch_results)
                    
                    # Summary metrics
                    qualified_count = len(results_df[results_df["Qualified"] == "Yes"])
                    total_count = len(results_df)
                    success_count = len(results_df[results_df["Status"] == "Playwright Success"])
                    avg_points = results_df[results_df["Points"] > 0]["Points"].mean() if len(results_df[results_df["Points"] > 0]) > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Processed", total_count)
                    with col2:
                        st.metric("Successfully Scraped", success_count)
                    with col3:
                        st.metric("Qualified", qualified_count)
                    with col4:
                        st.metric("Avg Points", f"{avg_points:,.0f}")
                    
                    st.dataframe(results_df, use_container_width=True)
                    
                    # Download results
                    csv_data = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Playwright Batch Results",
                        csv_data,
                        f"playwright_agentblazer_{batch_level.lower()}_results.csv",
                        "text/csv"
                    )
        
        else:
            st.error(f"❌ CSV must contain columns: {', '.join(required_columns)}")
    
    # Usage Tips
    st.divider()
    with st.expander("💡 Playwright Usage Tips"):
        st.markdown("""
        **For Best Results:**
        - Ensure profile URLs are complete and accurate
        - Make sure profiles are public and accessible
        - Be patient - Playwright needs time to render JavaScript content
        - Process smaller batches (5-10 profiles) for better reliability
        - Check your internet connection if scraping fails
        
        **Common Issues:**
        - Private profiles cannot be scraped
        - Some profiles may have anti-bot protection
        - Network timeouts can occur with slow connections
        - JavaScript-heavy pages need extra time to load
        """)

if __name__ == "__main__":
    main()
