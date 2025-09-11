import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Salesforce Profile Scraper",
    page_icon="🏆",
    layout="wide"
)

st.title("Salesforce Trailblazer Profile Scraper")
st.write("Enter the Salesforce Trailblazer profile URL to fetch data:")

# Input URL
profile_url = st.text_input("Profile URL", "")

def scrape_salesforce_profile(url):
    """Scrape badges and points from a Salesforce Trailblazer profile"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None, f"Error fetching URL. Status code: {response.status_code}"

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract user info (example: name)
    name_tag = soup.find('h1')
    name = name_tag.text.strip() if name_tag else "N/A"

    # Extract badges
    badges = []
    badge_tags = soup.find_all('div', class_='trailmix__badge')  # Example class, may need to update
    for badge in badge_tags:
        badge_name_tag = badge.find('div', class_='badge-name')
        badge_name = badge_name_tag.text.strip() if badge_name_tag else "Unknown"

        badge_points_tag = badge.find('div', class_='badge-points')
        badge_points = badge_points_tag.text.strip() if badge_points_tag else "0"

        badges.append({"Badge Name": badge_name, "Points": badge_points})

    # Convert to DataFrame
    df = pd.DataFrame(badges)
    return df, name

if profile_url:
    with st.spinner("Scraping Salesforce profile..."):
        df, name_or_error = scrape_salesforce_profile(profile_url)
    
    if df is None:
        st.error(name_or_error)
    else:
        st.success(f"Data fetched for {name_or_error}")
        st.dataframe(df)

        # Option to download as CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='salesforce_profile.csv',
            mime='text/csv'
        )
