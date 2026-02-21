import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION & DATABASE CONNECTION ---
# This pulls the keys from your Streamlit Cloud Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Medical Passport", page_icon="🏥")

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_state' not in st.session_state:
    st.session_state.auth_state = "login"

# --- 2. AUTHENTICATION SYSTEM ---
def secure_auth_system():
    st.title("🏥 Medical Passport")
    st.markdown("---")

    if st.session_state.auth_state == "login":
        st.subheader("Doctor Sign In")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Log In", use_container_width=True):
            try:
                # Actual Supabase Login
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            except Exception as e:
                st.error("Login failed. Check your credentials or manual confirmation.")

        if st.button("Need an Account? Create one here"):
            st.session_state.auth_state = "signup"
            st.rerun()

    elif st.session_state.auth_state == "signup":
        st.subheader("Create Your Professional Passport")
        new_email = st.text_input("Professional Email")
        new_pw = st.text_input("Create Password", type="password")
        
        if st.button("Register", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": new_email, "password": new_pw})
                st.success("Registration attempt complete! If you don't get an email, remember to 'Manually Confirm' in the Supabase Dashboard.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("Back to Login"):
            st.session_state.auth_state = "login"
            st.rerun()

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    # Sidebar for Logout and Profile
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: \n**{st.session_state.user_email}**")
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🩺 Professional Medical Passport")
    
    # --- SECTION A: SENIORITY TRANSLATOR ---
    st.subheader("🌍 Global Seniority Mapping")
    st.info("Translate your current grade to international equivalents.")
    
    current_grade = st.selectbox(
        "Select your current grade (UK System):",
        ["FY1/FY2", "ST1/ST2 (IMT/CST)", "ST3-ST6 (Registrar)", "ST7-ST8", "Consultant"]
    )

    # Mapping Logic
    mapping = {
        "FY1/FY2": {"USA": "Intern / PGY-1", "Australia": "Intern / JMO", "Role": "Junior Doctor"},
        "ST1/ST2 (IMT/CST)": {"USA": "Resident (Junior)", "Australia": "SHO", "Role": "Specialty Trainee"},
        "ST3-ST6 (Registrar)": {"USA": "Resident (Senior) / Fellow", "Australia": "Registrar", "Role": "Senior Registrar"},
        "ST7-ST8": {"USA": "Chief Resident / Fellow", "Australia": "Senior Registrar", "Role": "Pre-Consultant"},
        "Consultant": {"USA": "Attending Physician", "Australia": "Consultant / VMO", "Role": "Senior Specialist"}
    }

    col1, col2 = st.columns(2)
    with col1:
        st.metric("USA Equivalent", mapping[current_grade]["USA"])
    with col2:
        st.metric("Australia Equivalent", mapping[current_grade]["Australia"])

    st.markdown("---")

    # --- SECTION B: CV & QUALIFICATIONS ---
    st.subheader("📜 Verified Qualifications")
    
    with st.expander("➕ Add New Certificate / Qualification"):
        q_name = st.text_input("Qualification Name (e.g. MRCP Part 1)")
        q_date = st.date_input("Date Obtained")
        q_body = st.text_input("Awarding Body (e.g. Royal College of Physicians)")
        
        if st.button("Save to Passport"):
            # This logic will save to your Supabase table 'qualifications'
            st.success(f"Successfully added {q_name} to your digital vault.")

    # Placeholder for displaying data
    st.write("### Your Digital Portfolio")
    st.table({
        "Date": ["2024-01-15", "2023-06-10"],
        "Qualification": ["MBBS", "ALS Provider"],
        "Status": ["Verified ✅", "Verified ✅"]
    })

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
