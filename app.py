import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def fetch_badge_status(profile_url):
    """Fetch Salesforce Trailblazer badge status using <img alt> attribute"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(profile_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Find the image with "banner-level" in its src
        img_tag = soup.find("img", {"src": re.compile(r"banner-level-\d+\.png")})
        if img_tag and img_tag.get("alt"):
            return img_tag["alt"]  # keep exact alt text (e.g., "Agentblazer Innovator")

        return "None"  # No badge found
    except Exception:
        return "None"


# --- Streamlit UI ---
st.set_page_config(page_title="Salesforce Badge Dashboard", page_icon="🏆", layout="wide")

st.title("🏆 Salesforce Badge Extractor Dashboard")

uploaded_file = st.file_uploader("Upload CSV (roll number, name, profile_url)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Validate required columns
    required_cols = {"roll number", "name", "profile_url"}
    if not required_cols.issubset(df.columns):
        st.error(f"CSV must contain these columns: {required_cols}")
    else:
        st.info("Fetching badge data... Please wait ⏳")

        # Extract badge status
        df["badge_status"] = df["profile_url"].apply(fetch_badge_status)

        # Keep only required columns
        result_df = df[["roll number", "name", "profile_url", "badge_status"]]

        # Show results
        st.subheader("📊 Extracted Badge Data")
        st.dataframe(result_df, use_container_width=True)

        # Download option
        csv_out = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Download Results CSV",
            data=csv_out,
            file_name="badge_results.csv",
            mime="text/csv"
        )
