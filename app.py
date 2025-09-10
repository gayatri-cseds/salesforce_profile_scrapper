import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO

def fetch_salesforce_status(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return "Not Found"

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(" ", strip=True)

        # Keywords to check
        if "Salesforce MVP" in page_text or "Legend" in page_text:
            return "Legend"
        elif "Champion" in page_text:
            return "Champion"
        elif "Innovator" in page_text:
            return "Innovator"
        else:
            return "Not Found"
    except Exception as e:
        return "Error"

st.title("Salesforce Profile Checker")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if not {"Roll Number", "Name", "Salesforce URL"}.issubset(df.columns):
        st.error("CSV must have columns: Roll Number, Name, Salesforce URL")
    else:
        st.write("Processing profiles...")

        # Fetch status for each row
        df["Status"] = df["Salesforce URL"].apply(fetch_salesforce_status)

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
