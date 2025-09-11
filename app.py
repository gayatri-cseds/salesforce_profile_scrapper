import streamlit as st
import pandas as pd
import zipfile
import io

def salesforce_data_export_guide():
    st.title("📊 Salesforce Data Export for Badge Tracking")
    
    st.info("""
    **Why This Works:**
    - ✅ Uses official Salesforce functionality
    - ✅ No scraping or API limitations
    - ✅ Exports all user and badge data as CSV
    - ✅ Can be automated with scheduling
    """)
    
    # Step-by-step guide
    st.subheader("📋 Step-by-Step Implementation")
    
    steps = [
        "**Step 1:** Log into your Salesforce org as admin",
        "**Step 2:** Go to Setup → Quick Find → 'Data Export'",
        "**Step 3:** Click 'Export Now' or 'Schedule Export'",
        "**Step 4:** Select 'Include all data' and relevant objects",
        "**Step 5:** Choose to include images/attachments",
        "**Step 6:** Start export and wait for email notification",
        "**Step 7:** Download ZIP file containing CSV exports",
        "**Step 8:** Extract and analyze CSV files for badge data",
        "**Step 9:** Map badge information to student records"
    ]
    
    for step in steps:
        st.write(f"• {step}")
    
    # CSV Processing Tool
    st.subheader("🔧 CSV Badge Analysis Tool")
    
    uploaded_file = st.file_uploader("Upload Salesforce Export CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} records")
        
        # Show columns to help identify badge fields
        st.write("**Available Columns:**")
        st.write(df.columns.tolist())
        
        # Look for badge-related columns
        badge_columns = [col for col in df.columns if 'badge' in col.lower() or 'trailhead' in col.lower()]
        
        if badge_columns:
            st.success(f"🎯 Found potential badge columns: {badge_columns}")
            st.dataframe(df[badge_columns].head())
        else:
            st.info("No obvious badge columns found. Check User-related objects in the export.")

def main():
    salesforce_data_export_guide()

if __name__ == "__main__":
    main()
