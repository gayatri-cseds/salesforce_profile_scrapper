import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import time

# --- Configure Streamlit ---
st.set_page_config(page_title="Salesforce Badge Extractor", page_icon="🏆", layout="wide")

# --- Function to fetch badge status ---
def fetch_badge_status(profile_url):
    """Fetch Salesforce badge (Champion, Innovator, Legend) using Selenium headless browser"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

        driver.get(profile_url)
        time.sleep(3)  # wait for JS to render

        html = driver.page_source
        driver.quit()

        # Look for <img ... alt="Agentblazer Innovator">
        match = re.search(r'banner-level-\d+\.png"[^>]*alt="([^"]+)"', html)
        if match:
            return match.group(1)  # exact alt text like "Agentblazer Champion"
        return "None"
    except Exception as e:
        return "None"

# --- Streamlit UI ---
st.title("🏆 Salesforce Badge Extractor")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Ensure required columns exist
    if not {"rollnumber", "name", "profile link"}.issubset(df.columns):
        st.error("CSV must contain columns: rollnumber, name, profile link")
    else:
        st.write("✅ CSV uploaded successfully. Extracting badge status...")

        results = []
        for _, row in df.iterrows():
            roll = row["rollnumber"]
            name = row["name"]
            link = row["profile link"]

            badge_status = fetch_badge_status(link)
            results.append({"rollnumber": roll, "name": name, "profile link": link, "badge status": badge_status})

        out_df = pd.DataFrame(results)
        st.dataframe(out_df)

        # Download button
        csv = out_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Results CSV", csv, "badge_results.csv", "text/csv")
