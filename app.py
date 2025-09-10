import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from io import BytesIO
import time

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_salesforce_status(driver, url):
    try:
        driver.get(url)
        time.sleep(3)  # wait for page to load completely
        page_text = driver.page_source

        if "Legend" in page_text or "Salesforce MVP" in page_text:
            return "Legend"
        elif "Champion" in page_text:
            return "Champion"
        elif "Innovator" in page_text:
            return "Innovator"
        else:
            return "Not Found"
    except Exception as e:
        return "Error"

st.title("Salesforce Profile Checker (Selenium Powered)")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if not {"Roll Number", "Name", "Salesforce URL"}.issubset(df.columns):
        st.error("CSV must have columns: Roll Number, Name, Salesforce URL")
    else:
        st.write("🚀 Launching browser... Please wait.")

        driver = init_driver()

        statuses = []
        for url in df["Salesforce URL"]:
            status = fetch_salesforce_status(driver, url)
            statuses.append(status)

        df["Status"] = statuses
        driver.quit()

        st.dataframe(df)

        # Option to download
        output = BytesIO()
        df.to_csv(output, index=False)
        st.download_button(
            label="Download Updated CSV",
            data=output.getvalue(),
            file_name="salesforce_profiles.csv",
            mime="text/csv"
        )
