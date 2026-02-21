import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

# Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'mfa_verified' not in st.session_state:
    st.session_state.mfa_verified = False  # New Gatekeeper State
if 'auth_time' not in st.session_state:
    st.session_state.auth_time = 0
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. TIMEOUT SYSTEM ---
def check_session_timeout():
    TIMEOUT_SECONDS = 1800 # 30 Mins
    if st.session_state.authenticated and st.session_state.auth_time > 0:
        elapsed = time.time() - st.session_state.auth_time
        if elapsed > TIMEOUT_SECONDS:
            for key in ['authenticated', 'mfa_verified', 'access_token', 'auth_time']:
                st.session_state[key] = (False if 'verified' in key or 'auth' in key else None)
            st.warning("⏱️ Session Expired. Please re-authenticate.")
            st.rerun()

# --- 3. THE MFA CHALLENGE GATE ---
def mfa_challenge_screen(client):
    st.title("🛡️ Identity Verification Required")
    st.info(f"Account: {st.session_state.user_email}")
    
    # Check for existing factors
    try:
        f_res = client.auth.mfa.list_factors()
        factors = getattr(f_res, 'all', [])
        
        if not factors:
            st.error("No MFA factor found. Please contact admin or enroll via the recovery link.")
            if st.button("Back to Login"):
                st.session_state.authenticated = False
                st.rerun()
            return

        factor = factors[0] # Assuming one primary factor
        otp = st.text_input("Enter 6-Digit Code from Authenticator App", max_chars=6)
        
        if st.button("Verify & Enter Dashboard", use_container_width=True):
            try:
                challenge = client.auth.mfa.challenge({"factor_id": factor.id})
                c_id = getattr(challenge, 'id', challenge.get('id') if isinstance(challenge, dict) else None)
                
                client.auth.mfa.verify({
                    "factor_id": factor.id,
                    "challenge_id": c_id,
                    "code": str(otp).strip()
                })
                
                st.session_state.mfa_verified = True
                st.session_state.auth_time = time.time() # Reset clock on successful 2FA
                st.rerun()
            except Exception as e:
                st.error(f"Invalid Code: {e}")
                
    except Exception as e:
        st.error(f"Security Sync Error: {e}")

# --- 4. AUTH UI ---
def secure_auth_system():
    st.title("🏥 Medical Passport Gateway")
    email = st.text_input("Professional Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Step 1: Log In", use_container_width=True):
        try:
            temp_client = create_client(URL, KEY)
            res = temp_client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                st.session_state.access_token = res.session.access_token
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# --- 5. MAIN DASHBOARD (PROTECTED) ---
def main_dashboard():
    check_session_timeout()
    st.title("🩺 Medical Passport Dashboard")
    st.sidebar.success("Verified Session Active")
    
    if st.sidebar.button("🚪 Log Out"):
        for key in ['authenticated', 'mfa_verified', 'access_token']:
            st.session_state[key] = False
        st.rerun()

    # YOUR PRIVATE CLINICAL CONTENT GOES HERE
    st.write("---")
    st.subheader("Your Secure Clinical Credentials")
    st.info("This content is only visible because you passed the 2FA Gate.")

# --- 6. EXECUTION LOGIC ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    # They are logged in with password, now check for 2FA Gate
    client = create_client(URL, KEY)
    client.auth.set_session(st.session_state.access_token, "")
    
    if not st.session_state.mfa_verified:
        mfa_challenge_screen(client)
    else:
        main_dashboard()
