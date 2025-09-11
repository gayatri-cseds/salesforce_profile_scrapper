import streamlit as st
import pandas as pd

# Define Agentblazer requirements
AGENTBLAZER_REQUIREMENTS = {
    "Champion": {
        "required_trails": [
            "become-an-agentblazer-champion",
            "agentforce-fundamentals"
        ],
        "required_badges": [
            "Agent Builder Basics",
            "AI Fundamentals", 
            "Data Cloud Basics",
            "Agentforce Service Basics"
        ],
        "minimum_points": 2500,
        "required_superbadges": [],
        "description": "Build foundational AI and agent skills"
    },
    "Innovator": {
        "required_trails": [
            "become-an-agentblazer-champion",
            "agentforce-fundamentals",
            "advanced-agent-building"
        ],
        "required_badges": [
            "Agent Builder Basics",
            "AI Fundamentals",
            "Data Cloud Basics", 
            "Agentforce Service Basics",
            "Prompt Builder Templates",
        ],
        "minimum_points": 7900,
        "required_superbadges": [
            "Prompt Builder Templates Superbadge",
            "Agentforce for Service Superbadge"
        ],
        "description": "Create custom agents and handle complex use cases"
    },
    "Legend": {
        "required_trails": [
            "become-an-agentblazer-champion",
            "agentforce-fundamentals", 
            "advanced-agent-building",
            "agentforce-specialist-prep"
        ],
        "required_badges": [
            "Agent Builder Basics",
            "AI Fundamentals",
            "Data Cloud Basics",
            "Agentforce Service Basics", 
            "Prompt Builder Templates",
            "Service Cloud Agent Builder",
            "Advanced Agent Lifecycle",
            "Enterprise Agent Management"
        ],
        "minimum_points": 15000,
        "required_superbadges": [
            "Prompt Builder Templates Superbadge",
            "Agentforce for Service Superbadge",
            "Apex for Agentforce Superbadge"
        ],
        "description": "Master enterprise-level agent strategies and lifecycle management"
    }
}
def analyze_student_profile(profile_url, requirements_level="Champion"):
    """
    Analyze student's Trailhead profile against Agentblazer requirements
    """
    
    # This would extract data from the student's public profile
    profile_data = extract_profile_data(profile_url)
    
    requirements = AGENTBLAZER_REQUIREMENTS[requirements_level]
    
    verification_results = {
        "student_profile": profile_url,
        "target_level": requirements_level,
        "total_points": profile_data.get("points", 0),
        "completed_badges": profile_data.get("badges", []),
        "completed_trails": profile_data.get("trails", []),
        "completed_superbadges": profile_data.get("superbadges", []),
        "verification_status": {},
        "overall_qualified": False
    }
    
    # Check point requirements
    points_qualified = verification_results["total_points"] >= requirements["minimum_points"]
    verification_results["verification_status"]["points"] = {
        "required": requirements["minimum_points"],
        "actual": verification_results["total_points"],
        "qualified": points_qualified
    }
    
    # Check badge requirements
    badges_completed = []
    badges_missing = []
    
    for required_badge in requirements["required_badges"]:
        if any(required_badge.lower() in badge.lower() for badge in verification_results["completed_badges"]):
            badges_completed.append(required_badge)
        else:
            badges_missing.append(required_badge)
    
    badges_qualified = len(badges_missing) == 0
    verification_results["verification_status"]["badges"] = {
        "required": requirements["required_badges"],
        "completed": badges_completed,
        "missing": badges_missing,
        "qualified": badges_qualified
    }
    
    # Check superbadge requirements  
    superbadges_completed = []
    superbadges_missing = []
    
    for required_superbadge in requirements["required_superbadges"]:
        if any(required_superbadge.lower() in superbadge.lower() for superbadge in verification_results["completed_superbadges"]):
            superbadges_completed.append(required_superbadge)
        else:
            superbadges_missing.append(required_superbadge)
    
    superbadges_qualified = len(superbadges_missing) == 0
    verification_results["verification_status"]["superbadges"] = {
        "required": requirements["required_superbadges"],
        "completed": superbadges_completed, 
        "missing": superbadges_missing,
        "qualified": superbadges_qualified
    }
    
    # Overall qualification
    verification_results["overall_qualified"] = (
        points_qualified and badges_qualified and superbadges_qualified
    )
    
    # Assign badge level
    if verification_results["overall_qualified"]:
        verification_results["earned_badge"] = requirements_level
    else:
        verification_results["earned_badge"] = "Not Qualified"
    
    return verification_results

def main():
    st.title("🏆 Agentblazer Badge Verification System")
    
    st.success("✅ Define your own requirements and verify student achievements!")
    
    # Show requirements
    st.subheader("📋 Agentblazer Requirements")
    
    level_tab1, level_tab2, level_tab3 = st.tabs(["Champion", "Innovator", "Legend"])
    
    with level_tab1:
        req = AGENTBLAZER_REQUIREMENTS["Champion"]
        st.write(f"**Description:** {req['description']}")
        st.write(f"**Minimum Points:** {req['minimum_points']:,}")
        st.write(f"**Required Badges:** {len(req['required_badges'])}")
        with st.expander("View Required Badges"):
            for badge in req['required_badges']:
                st.write(f"• {badge}")
    
    with level_tab2:
        req = AGENTBLAZER_REQUIREMENTS["Innovator"] 
        st.write(f"**Description:** {req['description']}")
        st.write(f"**Minimum Points:** {req['minimum_points']:,}")
        st.write(f"**Required Badges:** {len(req['required_badges'])}")
        st.write(f"**Required Superbadges:** {len(req['required_superbadges'])}")
        with st.expander("View All Requirements"):
            st.write("**Badges:**")
            for badge in req['required_badges']:
                st.write(f"• {badge}")
            st.write("**Superbadges:**")
            for superbadge in req['required_superbadges']:
                st.write(f"• {superbadge}")
    
    with level_tab3:
        req = AGENTBLAZER_REQUIREMENTS["Legend"]
        st.write(f"**Description:** {req['description']}")
        st.write(f"**Minimum Points:** {req['minimum_points']:,}")
        st.write(f"**Required Badges:** {len(req['required_badges'])}")
        st.write(f"**Required Superbadges:** {len(req['required_superbadges'])}")
    
    # Student verification
    st.subheader("🎯 Student Verification")
    
    profile_url = st.text_input("Student Profile URL:")
    target_level = st.selectbox("Target Badge Level:", ["Champion", "Innovator", "Legend"])
    
    if st.button("🔍 Verify Student Qualifications"):
        if profile_url:
            with st.spinner(f"Analyzing profile for {target_level} level..."):
                # results = analyze_student_profile(profile_url, target_level)
                
                # Demo results (replace with actual verification)
                results = {
                    "student_profile": profile_url,
                    "target_level": target_level,
                    "total_points": 8500,
                    "earned_badge": "Innovator" if target_level == "Innovator" else "Not Qualified",
                    "overall_qualified": target_level == "Innovator",
                    "verification_status": {
                        "points": {"required": 7900, "actual": 8500, "qualified": True},
                        "badges": {"missing": ["Service Cloud Agent Builder"], "qualified": False},
                        "superbadges": {"missing": [], "qualified": True}
                    }
                }
            
            # Display results
            if results["overall_qualified"]:
                st.success(f"🎉 **QUALIFIED for {results['earned_badge']} badge!**")
            else:
                st.warning(f"⚠️ **Not yet qualified for {target_level} badge**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                points_status = results["verification_status"]["points"]
                if points_status["qualified"]:
                    st.success(f"✅ **Points:** {points_status['actual']:,} / {points_status['required']:,}")
                else:
                    st.error(f"❌ **Points:** {points_status['actual']:,} / {points_status['required']:,}")
            
            with col2:
                badges_status = results["verification_status"]["badges"]
                if badges_status["qualified"]:
                    st.success("✅ **All Badges Complete**")
                else:
                    st.error(f"❌ **Missing {len(badges_status['missing'])} Badges**")
                    if badges_status.get("missing"):
                        with st.expander("Missing Badges"):
                            for badge in badges_status["missing"]:
                                st.write(f"• {badge}")
            
            with col3:
                superbadges_status = results["verification_status"]["superbadges"]
                if superbadges_status["qualified"]:
                    st.success("✅ **All Superbadges Complete**")
                else:
                    st.error(f"❌ **Missing {len(superbadges_status['missing'])} Superbadges**")
    
    # Batch verification
    st.subheader("📂 Batch Student Verification")
    
    uploaded_file = st.file_uploader("Upload Student CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        
        batch_level = st.selectbox("Verification Level:", ["Champion", "Innovator", "Legend"], key="batch")
        
        if st.button("🚀 Verify All Students"):
            results = []
            progress_bar = st.progress(0)
            
            for idx, row in df.iterrows():
                progress_bar.progress((idx + 1) / len(df))
                
                # Simulate verification (replace with actual analysis)
                qualified = idx % 3 != 0  # Demo: 2/3 qualify
                
                results.append({
                    "Name": row["Name"],
                    "Roll Number": row["Roll Number"], 
                    "Profile URL": row["Salesforce URL"],
                    "Target Level": batch_level,
                    "Qualified": "Yes" if qualified else "No",
                    "Badge Awarded": batch_level if qualified else "Not Qualified"
                })
            
            results_df = pd.DataFrame(results)
            
            # Summary
            qualified_count = len(results_df[results_df["Qualified"] == "Yes"])
            total_count = len(results_df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Students", total_count)
            with col2:
                st.metric("Qualified", qualified_count)
            with col3:
                st.metric("Qualification Rate", f"{(qualified_count/total_count)*100:.1f}%")
            
            st.dataframe(results_df)
            
            # Download results
            csv_data = results_df.to_csv(index=False)
            st.download_button("📥 Download Results", csv_data, "agentblazer_verification.csv")

if __name__ == "__main__":
    main()
