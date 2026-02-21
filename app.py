import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

# Initialize States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'last_mfa_time' not in st.session_state:
    st.session_state.last_mfa_time = 0  # Persistent timestamp
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. THE TRUST LOGIC ---
def is_mfa_trusted():
    """Checks if the last MFA was done within the last hour."""
    ONE_HOUR = 3600 
    current_time = time.time()
    elapsed = current_time - st.session_state.last_mfa_time
    
    # If MFA was done less than an hour ago, return True
    return elapsed < ONE_HOUR

# --- 3. LOGIN SCREEN (STEP 1) ---
def login_screen():
    st.title("🏥 Medical Passport Gateway")
    email = st.text_input("Professional Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Sign In", use_container_width=True):
        try:
            client = create_client(URL, KEY)
            res = client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                st.session_state.access_token = res.session.access_token
                st.session_state.user_email = email
                st.session_state.authenticated = True
                st.rerun()
        except Exception:
            st.error("Invalid credentials.")

# --- 4. MFA GATE (STEP 2 - CONDITIONAL) ---
def mfa_gate():
    st.title("🛡️ Identity Verification")
    st.info("High-security re-authentication required (Hourly Check).")
    
    client = create_client(URL, KEY)
    client.auth.set_session(st.session_state.access_token, "")

    try:
        f_res = client.auth.mfa.list_factors()
        factors = getattr(f_res, 'all', [])
        
        if not factors:
            st.error("MFA not configured.")
            return

        otp = st.text_input("Enter 6-digit Authenticator Code", max_chars=6)
        
        if st.button("Verify & Access", use_container_width=True):
            try:
                challenge = client.auth.mfa.challenge({"factor_id": factors[0].id})
                c_id = getattr(challenge, 'id', challenge.get('id') if isinstance(challenge, dict) else None)
                
                client.auth.mfa.verify({
                    "factor_id": factors[0].id,
                    "challenge_id": c_id,
                    "code": str(otp).strip()
                })
                
                # UPDATE TRUST TIMESTAMP
                st.session_state.last_mfa_time = time.time()
                st.rerun()
            except Exception:
                st.error("Incorrect code.")
                
    except Exception as e:
        st.error("Session stale. Please log in again.")
        st.session_state.authenticated = False

# --- 5. PROTECTED DASHBOARD ---
def main_dashboard():
    st.title("🩺 Medical Passport Dashboard")
    
    # Show trust status in sidebar
    time_remaining = int(3600 - (time.time() - st.session_state.last_mfa_time))
    st.sidebar.success(f"🔒 MFA Trusted for {time_remaining // 60}m")
    
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.authenticated = False
        # Note: We do NOT reset last_mfa_time here, allowing the 1-hour trust to persist
        st.rerun()

    st.write("---")
    st.subheader("Verified Clinical View")
    st.write("Welcome back, Dr. " + st.session_state.user_email.split('@')[0].capitalize())

# --- 6. EXECUTION LOGIC ---


if not st.session_state.authenticated:
    login_screen()
else:
    # They are logged in with password. Now, do we need MFA?
    if is_mfa_trusted():
        main_dashboard()
    else:
        mfa_gate()
