import requests
import streamlit as st

def check_trailhead_api(trailblazer_id):
    """Try the unofficial Trailhead Badges API"""
    try:
        api_url = "https://trailheadbadges-api.herokuapp.com/users/search/findByTrailheadId"
        response = requests.get(api_url, params={"trailheadId": trailblazer_id})
        
        if response.status_code == 200:
            data = response.json()
            badges = data.get('badges', [])
            
            # Look for agentblazer badges
            for badge in badges:
                href = badge.get('href', '').lower()
                if 'agentblazer' in href:
                    if 'legend' in href:
                        return 'Legend'
                    elif 'innovator' in href:
                        return 'Innovator'  
                    elif 'champion' in href:
                        return 'Champion'
            
            return 'None'
        
        return 'API Unavailable'
        
    except Exception as e:
        return f'Error: {str(e)}'
