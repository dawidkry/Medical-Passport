import streamlit as st
import pandas as pd
from io import BytesIO
import datetime

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="Medical CV Passport", page_icon="🛂", layout="wide")

# Custom CSS to give it a professional, 'clinical' feel
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e6ed; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GLOBAL TRANSLATION DATA ---
# This acts as the 'Rosetta Stone' for medical seniority
TRANS_MAP = {
    "United Kingdom": {
        "FY1/FY2": {"Tier": "Junior Resident", "Level": "PGY 1-2", "Auth": "Provisional/Full GMC"},
        "ST3-ST8 (Registrar)": {"Tier": "Senior Resident / Fellow", "Level": "PGY 5+", "Auth": "Specialist Registrar"},
        "Consultant": {"Tier": "Attending Physician", "Level": "Board Certified", "Auth": "Specialist Register"}
    },
    "USA": {
        "Intern": {"Tier": "Junior Resident", "Level": "PGY 1", "Auth": "State Medical Board"},
        "Resident": {"Tier": "Resident", "Level": "PGY 2-4", "Auth": "State Medical Board"},
        "Attending": {"Tier": "Attending Physician", "Level": "Specialist", "Auth": "Board Certified"}
    }
}

# --- 3. AUTHENTICATION LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("🔐 Medical CV Passport Access")
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.info("Log in to your private vault to manage your qualifications.")
            user = st.text_input("Professional Email / Username")
            pw = st.text_input("Password", type="password")
            if st.button("Access Passport"):
                if user and pw: # In demo mode, any login works
                    st.session_state.authenticated = True
                    st.session_state.username = user
                    st.rerun()
        with col2:
            st.image("https://img.icons8.com/illustrations/external-tulpahn-outline-color-tulpahn/100/external-medical-insurance-medical-tulpahn-outline-color-tulpahn.png")

# --- 4. MAIN APPLICATION ---
def main_app():
    # Sidebar Navigation
    st.sidebar.title(f"Dr. {st.session_state.username}")
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Document Vault", "Experience Translator", "Export CV"])
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "Dashboard":
        st.header("🛂 Your Digital Medical Identity")
        col1, col2, col3 = st.columns(3)
        col1.metric("Verified Degrees", "3", "MD, MRCP, PhD")
        col2.metric("Clinical Years", "8", "PGY-8")
        col3.metric("Global Tier", "Senior Specialist")
        
        st.subheader("Current Standing")
        st.write("Your profile is currently mapped to **Tier 1 (International Specialist)** standards.")

    # --- DOCUMENT VAULT ---
    elif menu == "Document Vault":
        st.header("📂 Document & Certificate Vault")
        st.markdown("Upload certificates to be digitally 'stamped' and attached to your CV.")
        
        doc_type = st.selectbox("Document Type", ["Primary Medical Degree", "Specialty Certificate", "License to Practice", "ACLS/BLS"])
        uploaded_file = st.file_uploader(f"Upload {doc_type}")
        
        if uploaded_file:
            st.success(f"Successfully uploaded: {uploaded_file.name}")
            # Mock storage list
            st.write("### Currently Stored Documents")
            st.table(pd.DataFrame({
                "Document": [uploaded_file.name, "MBBS_Certificate.pdf"],
                "Status": ["Pending Verification", "Verified ✅"],
                "Date Added": [datetime.date.today(), "2024-01-15"]
            }))

    # --- TRANSLATOR ---
    elif menu == "Experience Translator":
        st.header("🌍 Global Seniority Translator")
        st.write("Contextualize your training for international medical boards.")
        
        country = st.selectbox("Original Training System", options=list(TRANS_MAP.keys()))
        local_rank = st.selectbox("Local Grade/Rank", options=list(TRANS_MAP[country].keys()))
        
        translation = TRANS_MAP[country][local_rank]
        
        st.divider()
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            st.subheader("Global Equivalency")
            st.write(f"**Tier:** {translation['Tier']}")
            st.write(f"**Clinical Level:** {translation['Level']}")
        with t_col2:
            st.subheader("Role Description")
            st.caption(f"This role implies {translation['Auth']} authority and independent practice at {translation['Level']} level.")

    # --- EXPORT ---
    elif menu == "Export CV":
        st.header("📄 Generate Medical Passport")
        st.write("Automatically populate a CV that translates your skills into a global format.")
        
        cv_content = f"""
        MEDICAL CV PASSPORT - DR. {st.session_state.username.upper()}
        Generated on: {datetime.date.today()}
        -----------------------------------------------------
        CLINICAL SUMMARY:
        Physician trained in [System]. 
        Global Tier: Senior Specialist (PGY-8 Equivalent)
        
        CORE COMPETENCIES:
        - Advanced Clinical Decision Making
        - Surgical Proficiency: Level 4 (Independent)
        - Research: 5 Publications (PubMed Indexed)
        
        VERIFIED QUALIFICATIONS ATTACHED:
        - MD (University of ...)
        - Specialist Board Certification
        -----------------------------------------------------
        This document serves as a digital translation of medical 
        credentials for international reciprocity.
        """
        st.text_area("Preview", cv_content, height=300)
        st.download_button("Download Verified Passport (PDF/TXT)", cv_content, file_name="Medical_Passport.txt")

# --- 5. EXECUTION ---
if not st.session_state.authenticated:
    login()
else:
    main_app()
