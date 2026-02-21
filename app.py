# --- REPLACE THE main_dashboard() FUNCTION IN YOUR CODE WITH THIS ---

def main_dashboard():
    # 1. Sidebar Navigation & Session Info
    st.sidebar.title("🏥 Clinical Session")
    
    # Calculate countdown for your 2-hour trust window
    time_elapsed = time.time() - st.session_state.get('last_mfa_time', 0)
    seconds_left = int(7200 - time_elapsed)
    
    if seconds_left > 0:
        st.sidebar.success(f"🔒 MFA Valid: {seconds_left // 60}m remaining")
    else:
        st.sidebar.warning("⌛ MFA Refresh Needed Soon")

    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    # 2. Top Header
    st.title("🩺 Professional Medical Passport")
    st.write(f"Digital Portfolio for: **{st.session_state.user_email}**")
    st.divider()

    # 3. Content Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview & ID", 
        "🏥 Clinical Rotations", 
        "💉 Procedure Log", 
        "📜 Academic & CV"
    ])

    with tab1:
        st.subheader("Professional Identity")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**GMC Number:** 1234567 (Example)")
            st.info("**Primary Specialty:** Internal Medicine")
        with c2:
            st.info("**Current Grade:** ST3")
            st.info("**Last Appraisal:** Jan 2026")
        
        st.write("### Digital Badge")
        st.code("VERIFIED_PROVIDER_TOKEN: 8823-XJ99-2026", language=None)

    with tab2:
        st.subheader("Clinical Experience Ledger")
        # Example data - In the future, this will come from your Supabase Database
        rotation_data = [
            {"Hospital": "St. Mary's", "Specialty": "Cardiology", "Dates": "2024-2025", "Supervisor": "Dr. Smith"},
            {"Hospital": "Royal Victoria", "Specialty": "Acute Med", "Dates": "2023-2024", "Supervisor": "Dr. Jones"},
        ]
        st.table(rotation_data)
        
        if st.button("➕ Add New Rotation"):
            st.write("*(Feature: This would open a form to save to your database)*")

    with tab3:
        st.subheader("Verified Procedure Log")
        # Using a dataframe for a "Surgical Logbook" feel
        import pandas as pd
        proc_df = pd.DataFrame({
            "Procedure": ["Lumbar Puncture", "Central Line", "Chest Drain"],
            "Quantity": [12, 5, 3],
            "Status": ["Independent", "Supervised", "Independent"]
        })
        st.dataframe(proc_df, use_container_width=True)

    with tab4:
        st.subheader("Academic Portfolio")
        st.markdown("""
        * **Publications:** *'AI in Clinical Triage'* - BMJ 2025
        * **Audit:** *'Reducing Door-to-Needle time in Stroke'* (QIP)
        * **Courses:** ALS, ATLS, Level 1 Ultrasound
        """)
        
        st.download_button("📄 Download Full CV (PDF)", data="Dummy Data", file_name="Medical_CV.pdf")
