import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

# --- 2. AUTHENTICATION SYSTEM ---
def secure_auth_system():
    st.title("🏥 Medical Passport Gateway")
    st.markdown("---")
    
    email = st.text_input("Professional Email")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Log In", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.session:
                    # WE CAPTURE THE TOKEN HERE
                    st.session_state.access_token = res.session.access_token
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
            except Exception as e:
                st.error(f"Login Error: {e}")
                
    with col2:
        if st.button("Register New Account", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Registration sent! Check Supabase to confirm the user.")
            except Exception as e:
                st.error(f"Signup Error: {e}")

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"Logged in: **{st.session_state.user_email}**")
    
    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except:
            pass
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.session_state.access_token = None
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Professional Medical Passport")
        st.write("Welcome, Doctor. Your secure portal is active.")

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        # We manually set the session before making MFA calls
        # This is the "Force Refresh" for the library
        if st.session_state.access_token:
            supabase.auth.set_session(st.session_state.access_token, "")

        # Check for 'ghost' factors
        try:
            factors_res = supabase.auth.mfa.list_factors()
            factors = getattr(factors_res, 'all', [])
            if factors:
                st.info(f"Existing Factor: {factors[0].friendly_name}")
                if st.button("Reset / Unenroll"):
                    supabase.auth.mfa.unenroll(factors[0].id)
                    st.rerun()
        except Exception as e:
            # If we still get a session error here, it's a library state issue
            st.warning("Unable to verify factors. Please try the 'Generate' button below.")

        if st.button("Generate 2FA QR Code"):
            try:
                # Ensure session is set again right before the call
                supabase.auth.set_session(st.session_state.access_token, "")
                
                enroll = supabase.auth.mfa.enroll({
                    "factor_type": "totp",
                    "friendly_name": "MedicalPassport"
                })
                st.session_state.mfa_id = enroll.id
                st.session_state.qr_code = enroll.totp.qr_code
                st.rerun()
            except Exception as e:
                st.error(f"Security Error: {e}")

        if 'qr_code' in st.session_state:
            st.divider()
            st.write("1. Scan this with Microsoft Authenticator:")
            st.image(st.session_state.qr_code)
            
            otp = st.text_input("2. Enter 6-digit code from phone", max_chars=6)
            if st.button("Verify & Activate"):
                try:
                    challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                    supabase.auth.mfa.verify({
                        "factor_id": st.session_state.mfa_id,
                        "challenge_id": challenge.id,
                        "code": otp
                    })
                    st.success("✅ MFA Fully Activated!")
                    del st.session_state.qr_code
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
