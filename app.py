import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import shutil
import time
from io import BytesIO

# Initialize Chrome + Chromedriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Find chromium/chromedriver installed by packages.txt
    chrome_path = shutil.which("chromium-browser")
    driver_path = shutil.which("chromedriver")

    chrome_options.binary_location = chrome_path
    service = Service(driver_path)

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to fetch Salesforce profile status
def fetch_salesforce_status(driver, url):
    try:
        driver.get(url)
        time.sleep(3)  # wait for dynamic content to load
        page_text = driver.page_source

        if "Legend" in page_text or "Salesforce MVP" in page_text:
            return "Legend"
        elif "Champion" in page_text:
            return "Champion"
        elif "Innovator" in page_text:
            return "Innovator"
        else:
            return "Not Found"
    except Exception:
        return "Error"

# Streamlit App
st.title("🚀 Salesforce Profile Checker")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if not {"Roll Number", "Name", "Salesforce URL"}.issubset(df.columns):
        st.error("CSV must have columns: Roll Number, Name, Salesforce URL")
    else:
        st.info("Launching Selenium browser... Please wait ⏳")

        driver = init_driver()
        statuses = []

        for url in df["Salesforce URL"]:
            status = fetch_salesforce_status(driver, url)
            statuses.append(status)

        driver.quit()

        df["Status"] = statuses
        st.success("✅ Profiles processed successfully!")
        st.dataframe(df)

        # Download enriched CSV
        output = BytesIO()
        df.to_csv(output, index=False)
        st.download_button(
            label="Download Updated CSV",
            data=output.getvalue(),
            file_name="salesforce_profiles.csv",
            mime="text/csv"
        )
