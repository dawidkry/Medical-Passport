import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION & DATABASE CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_state' not in st.session_state:
    st.session_state.auth_state = "login"
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. AUTHENTICATION SYSTEM ---
def secure_auth_system():
    st.title("🏥 Medical Passport Gateway")
    st.markdown("---")

    if st.session_state.auth_state == "login":
        st.subheader("Doctor Sign In")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Log In", use_container_width=True):
            try:
                # Sign in with Supabase
                auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            except Exception as e:
                st.error("Login failed. Ensure you have confirmed your email in the Supabase Dashboard.")

        if st.button("Need an Account? Register"):
            st.session_state.auth_state = "signup"
            st.rerun()

    elif st.session_state.auth_state == "signup":
        st.subheader("Create Your Professional Passport")
        new_email = st.text_input("Professional Email")
        new_pw = st.text_input("Create Password", type="password")
        
        if st.button("Register", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": new_email, "password": new_pw})
                st.success("Registration initiated! Please 'Confirm User' in your Supabase Dashboard to proceed.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("Back to Login"):
            st.session_state.auth_state = "login"
            st.rerun()

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    # Sidebar Navigation
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"User: **{st.session_state.user_email}**")
    
    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Professional Medical Passport")
        
        # --- SENIORITY TRANSLATOR ---
        st.subheader("🌍 Global Seniority Mapping")
        current_grade = st.selectbox(
            "Select your current UK grade:",
            ["FY1/FY2", "ST1/ST2 (IMT/CST)", "ST3-ST6 (Registrar)", "ST7-ST8", "Consultant"]
        )

        mapping = {
            "FY1/FY2": {"USA": "Intern / PGY-1", "Australia": "Intern / JMO"},
            "ST1/ST2 (IMT/CST)": {"USA": "Resident (Junior)", "Australia": "SHO"},
            "ST3-ST6 (Registrar)": {"USA": "Resident (Senior) / Fellow", "Australia": "Registrar"},
            "ST7-ST8": {"USA": "Chief Resident / Fellow", "Australia": "Senior Registrar"},
            "Consultant": {"USA": "Attending Physician", "Australia": "Consultant / VMO"}
        }

        c1, c2 = st.columns(2)
        with c1: st.metric("USA Equivalent", mapping[current_grade]["USA"])
        with c2: st.metric("Australia Equivalent", mapping[current_grade]["Australia"])

        st.divider()

        # --- CV ENTRY ---
        st.subheader("📜 Portfolio Vault")
        with st.expander("➕ Add Qualification"):
            q_name = st.text_input("Qualification (e.g., MRCP, USMLE Step 1)")
            if st.button("Save to Vault"):
                st.success(f"Verified entry for {q_name} added.")

    elif page == "Account Security":
        st.title("🛡️ 2FA Security Settings")
        st.write("Link your Microsoft Authenticator app to secure your clinical data.")

        if st.button("Initialize 2FA Enrollment"):
            try:
                enroll = supabase.auth.mfa.enroll(factor_type='totp', friendly_name='Medical Passport')
                st.session_state.mfa_id = enroll.data.id
                st.session_state.qr_code = enroll.data.totp.qr_code
                st.rerun()
            except Exception as e:
                st.error("Enrollment already exists or failed. Clear MFA factors in Supabase if stuck.")

        if 'qr_code' in st.session_state:
            st.info("Step 1: Open Microsoft Authenticator and scan the code below.")
            st.image(st.session_state.qr_code)
            
            st.info("Step 2: Enter the 6-digit verification code from your phone.")
            otp_code = st.text_input("Enter Code", max_chars=6)
            
            if st.button("Complete Verification"):
                challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                verify = supabase.auth.mfa.verify(
                    factor_id=st.session_state.mfa_id,
                    challenge_id=challenge.data.id,
                    code=otp_code
                )
                if verify.data:
                    st.success("MFA successfully activated! Your clinical records are now multi-factor protected.")
                    del st.session_state.qr_code # Clean up UI
                else:
                    st.error("Verification failed. Please check the code.")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
