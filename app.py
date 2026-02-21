import streamlit as st
from supabase import create_client, Client

# --- 1. SECURE CLIENT INITIALIZATION ---
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    # We disable session persistence to handle it manually ourselves
    return create_client(url, key)

supabase = get_supabase_client()

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
    
    if st.button("Log In", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                # WE SAVE THE TOKEN MANUALLY
                st.session_state.access_token = res.session.access_token
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
        except Exception as e:
            st.error(f"Login Error: {e}")

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"Logged in: **{st.session_state.user_email}**")
    
    # EVERY TIME THE DASHBOARD RUNS, WE RE-INJECT THE TOKEN
    if st.session_state.access_token:
        supabase.auth.set_session(st.session_state.access_token, "")

    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.access_token = None
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Professional Medical Passport")
        st.write("System online. Your session is manually verified.")

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        if st.button("Generate 2FA QR Code"):
            try:
                # Force the session one last time before the sensitive call
                supabase.auth.set_session(st.session_state.access_token, "")
                
                # Using the single dictionary parameter format
                enroll = supabase.auth.mfa.enroll({"factor_type": "totp", "friendly_name": "MedPass"})
                
                # Capture the ID and QR code from the result
                # Note: Newer versions return the object directly
                st.session_state.mfa_id = enroll.id
                st.session_state.qr_code = enroll.totp.qr_code
                st.rerun()
            except Exception as e:
                st.error(f"Critical Error: {e}")
                st.info("Technical Note: If this fails, your Supabase 'Anon' key might have restricted MFA permissions.")

        if 'qr_code' in st.session_state:
            st.divider()
            st.image(st.session_state.qr_code, caption="Scan with Microsoft Authenticator")
            
            otp = st.text_input("6-Digit Code", max_chars=6)
            if st.button("Verify & Activate"):
                try:
                    # Final verification step
                    challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                    supabase.auth.mfa.verify({
                        "factor_id": st.session_state.mfa_id,
                        "challenge_id": challenge.id,
                        "code": otp
                    })
                    st.success("✅ MFA Activated!")
                    del st.session_state.qr_code
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
