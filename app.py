import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
from io import BytesIO

def fetch_status(url):
    """
    Fetch Salesforce Trailblazer profile page and extract Champion/Innovator/Legend
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}  # mimic a browser
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return "Error"

        soup = BeautifulSoup(response.text, "html.parser")

        # 🔍 Adjust selector after inspecting profile page
        status_tag = soup.find("span", class_="profile-rank")

        if status_tag:
            return status_tag.text.strip()

        return "Not Found"

    except Exception as e:
        return f"Error: {str(e)}"


def process_dataframe(df):
    statuses = []
    for i, row in df.iterrows():
        url = row["Salesforce URL"]
        st.write(f"🔎 Fetching {url} ...")

        status = fetch_status(url)
        statuses.append(status)

        # polite scraping (1–3 sec delay)
        time.sleep(random.uniform(1, 3))

    df["Status"] = statuses
    return df


# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Salesforce Profile Scraper", layout="centered")

st.title("🚀 Salesforce Trailblazer Status Scraper")
st.write("Upload a CSV with columns: **Roll Number, Name, Salesforce URL**. The app will fetch Agentblazer status (Champion / Innovator / Legend).")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("📂 Input Data Preview:")
    st.dataframe(df)

    if st.button("Start Processing"):
        st.info("Processing started... please wait ⏳")
        result_df = process_dataframe(df)

        st.success("✅ Processing complete!")
        st.write("📊 Result Preview:")
        st.dataframe(result_df)

        # Convert to downloadable CSV
        buffer = BytesIO()
        result_df.to_csv(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Result CSV",
            data=buffer,
            file_name="output.csv",
            mime="text/csv"
        )
