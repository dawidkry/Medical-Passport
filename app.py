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
                st.error(f"Login failed: {e}")

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
                st.success("Registration initiated! Confirm your email in Supabase.")
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
        # --- SENIORITY METRICS ---
        current_grade = st.selectbox("Select UK grade:", ["FY1/FY2", "ST1/ST2", "ST3-ST6", "ST7-ST8", "Consultant"])
        mapping = {"FY1/FY2": "Intern", "ST1/ST2": "Resident", "ST3-ST6": "Fellow", "ST7-ST8": "Senior Fellow", "Consultant": "Attending"}
        st.metric("Global Equivalent", mapping[current_grade])

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        # Check for factors
        try:
            factors_res = supabase.auth.mfa.list_factors()
            factors = getattr(factors_res, 'all', [])
            if factors:
                st.warning(f"Active Factor Found: {factors[0].friendly_name}")
                if st.button("Reset MFA"):
                    supabase.auth.mfa.unenroll(factors[0].id)
                    st.rerun()
        except:
            pass

        if st.button("Initialize 2FA Enrollment"):
            try:
                # NEW SYNTX: Passing parameters as a dictionary or positional 
                # to satisfy the newer SyncGoTrueClient requirements
                enroll = supabase.auth.mfa.enroll({
                    "factor_type": "totp",
                    "friendly_name": "Medical Passport"
                })
                
                # Handling different response structures
                data = getattr(enroll, 'data', enroll)
                st.session_state.mfa_id = data.id
                st.session_state.qr_code = data.totp.qr_code
                st.rerun()
            except Exception as e:
                # Fallback: Trying positional arguments if dictionary fails
                try:
                    enroll = supabase.auth.mfa.enroll("totp", "Medical Passport")
                    data = getattr(enroll, 'data', enroll)
                    st.session_state.mfa_id = data.id
                    st.session_state.qr_code = data.totp.qr_code
                    st.rerun()
                except Exception as e2:
                    st.error(f"Critical Enrollment Error: {e2}")

        if 'qr_code' in st.session_state:
            st.info("Scan with Microsoft Authenticator:")
            st.image(st.session_state.qr_code)
            otp_code = st.text_input("6-Digit Code", max_chars=6)
            
            if st.button("Verify Code"):
                try:
                    challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                    c_data = getattr(challenge, 'data', challenge)
                    verify = supabase.auth.mfa.verify(
                        factor_id=st.session_state.mfa_id,
                        challenge_id=c_data.id,
                        code=otp_code
                    )
                    st.success("MFA Active!")
                    del st.session_state.qr_code
                except Exception as e:
                    st.error(f"Verification Error: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
