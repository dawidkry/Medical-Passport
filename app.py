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
                supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            except Exception as e:
                st.error("Login failed. Check your credentials.")

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
                st.success("Registration initiated! Please confirm your email in Supabase.")
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("Back to Login"):
            st.session_state.auth_state = "login"
            st.rerun()

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"User: **{st.session_state.user_email}**")
    
    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Professional Medical Passport")
        st.subheader("🌍 Global Seniority Mapping")
        current_grade = st.selectbox("Select UK grade:", ["FY1/FY2", "ST1/ST2", "ST3-ST6", "ST7-ST8", "Consultant"])
        
        mapping = {
            "FY1/FY2": {"USA": "Intern", "Aus": "JMO"},
            "ST1/ST2": {"USA": "Resident", "Aus": "SHO"},
            "ST3-ST6": {"USA": "Fellow", "Aus": "Registrar"},
            "ST7-ST8": {"USA": "Senior Fellow", "Aus": "Senior Registrar"},
            "Consultant": {"USA": "Attending", "Aus": "Consultant"}
        }
        c1, c2 = st.columns(2)
        c1.metric("USA", mapping[current_grade]["USA"])
        c2.metric("Australia", mapping[current_grade]["Aus"])

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        # --- SELF-HEALING LOGIC ---
        # We check for existing factors every time this page loads
        factors_res = supabase.auth.mfa.list_factors()
        factors = factors_res.data.all if factors_res.data else []
        
        if factors:
            st.warning(f"Found {len(factors)} pending/active security factor(s).")
            if st.button("Clear All Factors & Reset"):
                for f in factors:
                    supabase.auth.mfa.unenroll(f.id)
                st.success("System reset! You can now initialize a fresh 2FA setup.")
                st.rerun()

        if st.button("Initialize 2FA Enrollment"):
            try:
                # Force-clear any unverified factors first to avoid the 'Already exists' error
                for f in factors:
                    if f.status == "unverified":
                        supabase.auth.mfa.unenroll(f.id)
                
                enroll = supabase.auth.mfa.enroll(factor_type='totp', friendly_name='Medical Passport')
                st.session_state.mfa_id = enroll.data.id
                st.session_state.qr_code = enroll.data.totp.qr_code
                st.rerun()
            except Exception as e:
                st.error(f"Enrollment Error: {e}")

        if 'qr_code' in st.session_state:
            st.info("Scan with Microsoft Authenticator:")
            st.image(st.session_state.qr_code)
            otp_code = st.text_input("6-Digit Code", max_chars=6)
            
            if st.button("Complete Verification"):
                challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                verify = supabase.auth.mfa.verify(
                    factor_id=st.session_state.mfa_id,
                    challenge_id=challenge.data.id,
                    code=otp_code
                )
                if verify.data:
                    st.success("MFA Active!")
                    del st.session_state.qr_code
                else:
                    st.error("Invalid code.")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
