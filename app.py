import streamlit as st
import pandas as pd
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json

class SalesforceBadgeAgent:
    def __init__(self, api_key):
        self.llm = OpenAI(temperature=0, openai_api_key=api_key)
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.driver = None
        self.setup_tools()
        
    def setup_driver(self):
        """Setup optimized Chrome driver"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        
    def navigate_to_profile(self, url):
        """Tool: Navigate to Salesforce profile"""
        try:
            if not self.driver:
                self.setup_driver()
            
            self.driver.get(url)
            time.sleep(8)  # Wait for dynamic content
            
            page_source = self.driver.page_source
            return f"Successfully navigated to {url}. Page loaded with {len(page_source)} characters of content."
        
        except Exception as e:
            return f"Error navigating to profile: {str(e)}"
    
    def analyze_page_for_badges(self, analysis_request):
        """Tool: Analyze current page for Agentblazer badges"""
        try:
            if not self.driver:
                return "No active browser session. Please navigate to a profile first."
            
            page_source = self.driver.page_source
            
            # Use LLM to analyze page content
            analysis_prompt = f"""
            Analyze this HTML content for Salesforce Agentblazer badges:
            
            {page_source[:5000]}  # Limit content for LLM
            
            Look for these specific patterns:
            1. Images with "banner-level-1.png" = Champion
            2. Images with "banner-level-2.png" = Innovator  
            3. Images with "banner-level-3.png" = Legend
            4. Alt text containing "Agentblazer Champion/Innovator/Legend"
            
            Return only: Champion, Innovator, Legend, or None
            """
            
            badge_result = self.llm(analysis_prompt)
            return badge_result.strip()
            
        except Exception as e:
            return f"Error analyzing page: {str(e)}"
    
    def extract_profile_info(self, extraction_request):
        """Tool: Extract profile information"""
        try:
            page_source = self.driver.page_source if self.driver else ""
            
            info_prompt = f"""
            Extract profile information from this Salesforce page:
            
            {page_source[:3000]}
            
            Return a JSON with:
            - profile_name: The person's name
            - profile_url: Current URL
            - badge_detected: Champion/Innovator/Legend/None
            - confidence: High/Medium/Low
            """
            
            result = self.llm(info_prompt)
            return result
            
        except Exception as e:
            return f"Error extracting profile info: {str(e)}"
    
    def setup_tools(self):
        """Setup agent tools"""
        self.tools = [
            Tool(
                name="NavigateToProfile",
                func=self.navigate_to_profile,
                description="Navigate to a Salesforce profile URL. Input should be a valid URL."
            ),
            Tool(
                name="AnalyzeBadges", 
                func=self.analyze_page_for_badges,
                description="Analyze the current page for Agentblazer badges. Input should be 'analyze badges'."
            ),
            Tool(
                name="ExtractProfileInfo",
                func=self.extract_profile_info,
                description="Extract structured profile information. Input should be 'extract info'."
            )
        ]
        
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent="conversational-react-description",
            memory=self.memory,
            verbose=True
        )
    
    def process_profile(self, profile_url, name, roll_number):
        """Process a single profile with AI agent reasoning"""
        try:
            # Agent instruction
            instruction = f"""
            You are a Salesforce badge extraction expert. Process this profile:
            
            Name: {name}
            Roll Number: {roll_number}
            Profile URL: {profile_url}
            
            Steps:
            1. Navigate to the profile URL
            2. Analyze the page for Agentblazer badges
            3. Extract structured profile information
            4. Return the badge level found
            
            Focus on finding Agentblazer Champion, Innovator, or Legend badges.
            """
            
            result = self.agent.run(instruction)
            
            # Parse agent result
            badge_level = "None"
            if "Champion" in result:
                badge_level = "Champion"
            elif "Innovator" in result:
                badge_level = "Innovator"
            elif "Legend" in result:
                badge_level = "Legend"
            
            return {
                'Roll Number': roll_number,
                'Name': name,
                'Profile URL': profile_url,
                'Badge Level': badge_level,
                'Agent Analysis': result[:200] + "..." if len(result) > 200 else result,
                'Status': 'Success'
            }
            
        except Exception as e:
            return {
                'Roll Number': roll_number,
                'Name': name, 
                'Profile URL': profile_url,
                'Badge Level': 'Error',
                'Agent Analysis': f'Error: {str(e)}',
                'Status': 'Failed'
            }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

def main():
    st.set_page_config(
        page_title="AI Agent Badge Extractor",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 AI Agent Salesforce Badge Extractor")
    st.success("✅ Intelligent agent with reasoning capabilities for bulk badge detection!")
    
    # API Configuration
    st.subheader("🔑 AI Agent Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        openai_api_key = st.text_input("OpenAI API Key:", type="password")
    
    with col2:
        agent_model = st.selectbox("AI Model:", ["gpt-4", "gpt-3.5-turbo"])
    
    if not openai_api_key:
        st.info("Please enter your OpenAI API key to activate the AI agent")
        st.stop()
    
    # File Upload
    st.subheader("📂 Upload Student Data")
    
    uploaded_file = st.file_uploader("Upload CSV with student profiles", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        required_cols = ['Roll Number', 'Name', 'Salesforce URL']
        if all(col in df.columns for col in required_cols):
            
            st.success(f"✅ Loaded {len(df)} student profiles")
            st.dataframe(df.head())
            
            # Agent Configuration
            st.subheader("🤖 Agent Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_profiles = st.number_input("Max profiles to process", 1, len(df), min(10, len(df)))
            
            with col2:
                delay_between = st.slider("Delay between profiles (seconds)", 1, 10, 3)
            
            # Start Processing
            if st.button("🚀 Deploy AI Agent", type="primary"):
                
                # Initialize agent
                agent = SalesforceBadgeAgent(openai_api_key)
                
                profiles_to_process = df.head(max_profiles)
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.empty()
                
                results = []
                
                for idx, row in profiles_to_process.iterrows():
                    progress = (idx + 1) / len(profiles_to_process)
                    progress_bar.progress(progress)
                    
                    status_text.text(f"AI Agent processing {idx+1}/{len(profiles_to_process)}: {row['Name']}")
                    
                    # Agent processes profile
                    result = agent.process_profile(
                        row['Salesforce URL'],
                        row['Name'], 
                        row['Roll Number']
                    )
                    
                    results.append(result)
                    
                    # Show real-time result
                    with results_container:
                        st.write(f"✅ {result['Name']}: **{result['Badge Level']}**")
                    
                    # Delay between profiles
                    if idx < len(profiles_to_process) - 1:
                        time.sleep(delay_between)
                
                # Cleanup
                agent.cleanup()
                
                # Final Results
                results_df = pd.DataFrame(results)
                
                st.success("🎉 AI Agent processing completed!")
                
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Processed", len(results_df))
                
                with col2:
                    successful = len(results_df[results_df['Status'] == 'Success'])
                    st.metric("Successful", successful)
                
                with col3:
                    badges_found = len(results_df[~results_df['Badge Level'].isin(['None', 'Error'])])
                    st.metric("Badges Found", badges_found)
                
                with col4:
                    success_rate = (successful / len(results_df)) * 100 if len(results_df) > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Detailed Results
                st.subheader("📊 AI Agent Analysis Results")
                st.dataframe(results_df, use_container_width=True)
                
                # Badge Distribution
                badge_counts = results_df['Badge Level'].value_counts()
                if not badge_counts.empty:
                    st.subheader("📈 Badge Distribution")
                    st.bar_chart(badge_counts)
                
                # Download Results
                csv_data = results_df.to_csv(index=False)
                st.download_button(
                    "📥 Download AI Agent Results",
                    csv_data,
                    f"ai_agent_badge_results_{int(time.time())}.csv",
                    "text/csv",
                    type="primary"
                )

if __name__ == "__main__":
    main()

