import streamlit as st
import pandas as pd
import subprocess
import os
import time
import tempfile
import csv
from pathlib import Path

class ScrapyRunner:
    """Class to handle Scrapy operations within Streamlit"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent / "scrapy_project"
        self.ensure_project_structure()
    
    def ensure_project_structure(self):
        """Create Scrapy project structure if it doesn't exist"""
        
        # Create directories
        (self.project_dir / "salesforce_badges").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "salesforce_badges" / "spiders").mkdir(exist_ok=True)
        
        # Create __init__.py files
        (self.project_dir / "salesforce_badges" / "__init__.py").touch()
        (self.project_dir / "salesforce_badges" / "spiders" / "__init__.py").touch()
        
        # Create scrapy.cfg
        scrapy_cfg = self.project_dir / "scrapy.cfg"
        if not scrapy_cfg.exists():
            scrapy_cfg.write_text("""[settings]
default = salesforce_badges.settings

[deploy]
project = salesforce_badges
""")
        
        # Create settings.py
        settings_py = self.project_dir / "salesforce_badges" / "settings.py"
        settings_py.write_text('''
BOT_NAME = 'salesforce_badges'
SPIDER_MODULES = ['salesforce_badges.spiders']
NEWSPIDER_MODULE = 'salesforce_badges.spiders'

# Splash Configuration
SPLASH_URL = 'http://localhost:8050'

DOWNLOADER_MIDDLEWARES = {
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
ROBOTSTXT_OBEY = True

LOG_LEVEL = 'WARNING'
''')
        
        # Create items.py
        items_py = self.project_dir / "salesforce_badges" / "items.py"
        items_py.write_text('''
import scrapy

class BadgeItem(scrapy.Item):
    roll_number = scrapy.Field()
    name = scrapy.Field()
    profile_url = scrapy.Field()
    badge_level = scrapy.Field()
    badge_image_url = scrapy.Field()
    alt_text = scrapy.Field()
    detection_method = scrapy.Field()
    status = scrapy.Field()
''')
        
        # Create the spider
        spider_py = self.project_dir / "salesforce_badges" / "spiders" / "badge_spider.py"
        spider_py.write_text('''
import scrapy
from scrapy_splash import SplashRequest
import csv
from salesforce_badges.items import BadgeItem

class AgentblazerSpider(scrapy.Spider):
    name = 'agentblazer'
    
    lua_script = """
        function main(splash, args)
            splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            assert(splash:go(args.url))
            assert(splash:wait(8))
            
            -- Additional wait for dynamic content
            splash:wait_for_resume([[
                function() {
                    setTimeout(function() { splash.resume(); }, 3000);
                }
            ]], 5)
            
            return splash:html()
        end
    """
    
    def __init__(self, csv_file=None, *args, **kwargs):
        super(AgentblazerSpider, self).__init__(*args, **kwargs)
        self.csv_file = csv_file
        self.profiles = self.load_profiles() if csv_file else []
    
    def load_profiles(self):
        profiles = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    profiles.append({
                        'roll_number': row.get('Roll Number', ''),
                        'name': row.get('Name', ''),
                        'profile_url': row.get('Salesforce URL', '')
                    })
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
        return profiles
    
    def start_requests(self):
        for profile in self.profiles:
            if profile['profile_url']:
                yield SplashRequest(
                    url=profile['profile_url'],
                    callback=self.parse_profile,
                    endpoint='execute',
                    args={
                        'lua_source': self.lua_script,
                        'wait': 8,
                        'html': 1,
                        'timeout': 30
                    },
                    meta={'profile': profile}
                )
    
    def parse_profile(self, response):
        profile = response.meta['profile']
        
        item = BadgeItem()
        item['roll_number'] = profile['roll_number']
        item['name'] = profile['name']
        item['profile_url'] = profile['profile_url']
        
        # Extract agentblazer badge
        agentblazer_images = response.xpath('//img[contains(@src, "agentblazer") or contains(@alt, "agentblazer")]')
        
        badge_found = False
        
        for img in agentblazer_images:
            src = img.xpath('./@src').get() or ''
            alt = img.xpath('./@alt').get() or ''
            
            if 'banner-level-3.png' in src:
                item['badge_level'] = 'Legend'
                item['badge_image_url'] = src
                item['alt_text'] = alt
                item['detection_method'] = 'Agentblazer Banner Level 3'
                item['status'] = 'Success'
                badge_found = True
                break
            elif 'banner-level-2.png' in src:
                item['badge_level'] = 'Innovator'
                item['badge_image_url'] = src
                item['alt_text'] = alt
                item['detection_method'] = 'Agentblazer Banner Level 2'
                item['status'] = 'Success'
                badge_found = True
                break
            elif 'banner-level-1.png' in src:
                item['badge_level'] = 'Champion'
                item['badge_image_url'] = src
                item['alt_text'] = alt
                item['detection_method'] = 'Agentblazer Banner Level 1'
                item['status'] = 'Success'
                badge_found = True
                break
            
            # Check alt text as backup
            alt_lower = alt.lower()
            if 'legend' in alt_lower:
                item['badge_level'] = 'Legend'
                badge_found = True
            elif 'innovator' in alt_lower:
                item['badge_level'] = 'Innovator'
                badge_found = True
            elif 'champion' in alt_lower:
                item['badge_level'] = 'Champion'
                badge_found = True
            
            if badge_found:
                item['badge_image_url'] = src
                item['alt_text'] = alt
                item['detection_method'] = 'Alt Text Detection'
                item['status'] = 'Success'
                break
        
        if not badge_found:
            item['badge_level'] = 'None'
            item['badge_image_url'] = ''
            item['alt_text'] = ''
            item['detection_method'] = 'No Badge Found'
            item['status'] = 'No Badge'
        
        yield item
''')
    
    def run_spider(self, csv_file_path):
        """Run Scrapy spider with the given CSV file"""
        
        # Change to project directory
        original_dir = os.getcwd()
        os.chdir(self.project_dir)
        
        try:
            # Run Scrapy command
            cmd = [
                'scrapy', 'crawl', 'agentblazer',
                '-a', f'csv_file={csv_file_path}',
                '-o', 'results.csv',
                '--loglevel=WARNING'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Scraping timeout - process took too long"
        except Exception as e:
            return False, "", str(e)
        finally:
            os.chdir(original_dir)
    
    def get_results(self):
        """Get results from the scrapy output"""
        results_file = self.project_dir / "results.csv"
        if results_file.exists():
            return pd.read_csv(results_file)
        return pd.DataFrame()

def check_splash_server():
    """Check if Splash server is running"""
    try:
        import requests
        response = requests.get('http://localhost:8050', timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    st.set_page_config(
        page_title="Scrapy Badge Extractor",
        page_icon="🕷️",
        layout="wide"
    )
    
    st.title("🕷️ Salesforce Badge Extractor with Scrapy + Splash")
    st.success("✅ Professional scraping with JavaScript support!")
    
    # Check prerequisites
    st.subheader("🔧 Prerequisites Check")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Check Splash server
        if check_splash_server():
            st.success("✅ Splash server is running on localhost:8050")
        else:
            st.error("❌ Splash server not running")
            st.info("""
            **To start Splash server:**
            ```
            docker run -p 8050:8050 scrapinghub/splash
            ```
            Or install locally and run.
            """)
            return
    
    with col2:
        # Check Scrapy installation
        try:
            import scrapy
            import scrapy_splash
            st.success("✅ Scrapy and Scrapy-Splash installed")
        except ImportError:
            st.error("❌ Missing dependencies")
            st.info("""
            **Install dependencies:**
            ```
            pip install scrapy scrapy-splash pandas
            ```
            """)
            return
    
    # File upload
    st.subheader("📂 Upload Profile Data")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type="csv",
        help="CSV should contain: Roll Number, Name, Salesforce URL"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            required_cols = ['Roll Number', 'Name', 'Salesforce URL']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if len(missing_cols) > 0:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                return
            
            st.success(f"✅ Loaded {len(df)} profiles successfully!")
            
            # Preview data
            with st.expander("📋 Data Preview", expanded=True):
                st.dataframe(df.head())
            
            # Configuration
            st.subheader("⚙️ Scraping Configuration")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                delay = st.slider("Request delay (seconds)", 1, 10, 3)
            
            with col2:
                concurrent = st.slider("Concurrent requests", 1, 5, 2)
            
            with col3:
                max_profiles = st.number_input(
                    "Max profiles (0 = all)", 
                    0, len(df), 
                    min(10, len(df))
                )
            
            # Start scraping
            if st.button("🚀 Start Scrapy Badge Detection", type="primary"):
                
                # Limit profiles if specified
                profiles_to_process = df.head(max_profiles) if max_profiles > 0 else df
                
                # Save CSV to temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                    profiles_to_process.to_csv(tmp_file.name, index=False)
                    tmp_csv_path = tmp_file.name
                
                st.info(f"🕷️ Starting Scrapy to process {len(profiles_to_process)} profiles...")
                
                # Initialize Scrapy runner
                scrapy_runner = ScrapyRunner()
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Scrapy is crawling profiles with JavaScript support..."):
                    
                    status_text.text("🕷️ Initializing Scrapy spider...")
                    
                    # Run the spider
                    success, stdout, stderr = scrapy_runner.run_spider(tmp_csv_path)
                    
                    if success:
                        st.success("🎉 Scrapy crawling completed successfully!")
                        
                        # Get results
                        results_df = scrapy_runner.get_results()
                        
                        if not results_df.empty:
                            
                            # Summary statistics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Total Processed", len(results_df))
                            
                            with col2:
                                badges_found = len(results_df[results_df['badge_level'].isin(['Champion', 'Innovator', 'Legend'])])
                                st.metric("Badges Found", badges_found)
                            
                            with col3:
                                innovators = len(results_df[results_df['badge_level'] == 'Innovator'])
                                st.metric("Innovators", innovators)
                            
                            with col4:
                                champions = len(results_df[results_df['badge_level'] == 'Champion'])
                                st.metric("Champions", champions)
                            
                            # Additional metrics
                            col5, col6 = st.columns(2)
                            with col5:
                                legends = len(results_df[results_df['badge_level'] == 'Legend'])
                                st.metric("Legends", legends)
                            with col6:
                                none_found = len(results_df[results_df['badge_level'] == 'None'])
                                st.metric("No Badge", none_found)
                            
                            # Results table
                            st.subheader("📊 Detailed Results")
                            st.dataframe(results_df, use_container_width=True)
                            
                            # Badge distribution chart
                            if not results_df.empty:
                                badge_counts = results_df['badge_level'].value_counts()
                                st.subheader("📈 Badge Distribution")
                                st.bar_chart(badge_counts)
                            
                            # Download results
                            csv_data = results_df.to_csv(index=False)
                            
                            st.download_button(
                                label="📥 Download Results CSV",
                                data=csv_data,
                                file_name=f"scrapy_badge_results_{int(time.time())}.csv",
                                mime="text/csv",
                                type="primary"
                            )
                            
                        else:
                            st.warning("⚠️ No results generated. Check the logs.")
                    
                    else:
                        st.error("❌ Scrapy crawling failed")
                        if stderr:
                            st.error(f"Error: {stderr}")
                        if stdout:
                            st.text(f"Output: {stdout}")
                
                # Cleanup
                try:
                    os.unlink(tmp_csv_path)
                except:
                    pass
        
        except Exception as e:
            st.error(f"❌ Error processing CSV: {str(e)}")
    
    # Instructions
    st.divider()
    
    st.subheader("📚 Setup Instructions")
    
    with st.expander("Complete Setup Guide"):
        st.markdown("""
        ### 🐳 **1. Start Splash Server**
        ```
        # Using Docker (recommended)
        docker run -p 8050:8050 scrapinghub/splash
        
        # Or install locally
        pip install scrapy-splash
        ```
        
        ### 📦 **2. Install Dependencies**
        ```
        pip install scrapy scrapy-splash pandas streamlit
        ```
        
        ### 📋 **3. Prepare CSV File**
        Your CSV must have these exact columns:
        - `Roll Number`
        - `Name` 
        - `Salesforce URL` (format: https://www.salesforce.com/trailblazer/username)
        
        ### 🚀 **4. Run Application**
        ```
        streamlit run streamlit_scrapy_app.py
        ```
        
        ### 🎯 **How It Works**
        1. **Scrapy + Splash**: Handles JavaScript-rendered content
        2. **Dynamic Detection**: Waits for badges to load via JS
        3. **Pattern Matching**: Finds exact agentblazer banner images
        4. **Batch Processing**: Processes multiple profiles efficiently
        5. **CSV Export**: Downloads results for further analysis
        """)

if __name__ == "__main__":
    main()
