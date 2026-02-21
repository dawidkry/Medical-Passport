import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

# Standardized Trust Window: 2 Hours (7200 Seconds)
TRUST_WINDOW = 7200 

# Initialize States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'last_mfa_time' not in st.session_state:
    st.session_state.last_mfa_time = 0 
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. ADAPTIVE TRUST LOGIC ---
def is_mfa_trusted():
    """Checks if the MFA 'Lease' is still valid."""
    current_time = time.time()
    elapsed = current_time - st.session_state.last_mfa_time
    return elapsed < TRUST_WINDOW

# --- 3. LOGIN SCREEN (STEP 1) ---
def login_screen():
    st.title("🏥 Medical Passport Gateway")
    st.write("---")
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
            st.error("Invalid credentials. Please verify your email and password.")

# --- 4. MFA GATE (STEP 2 - CONDITIONAL) ---
def mfa_gate():
    st.title("🛡️ Identity Verification")
    st.warning("A 2-hour security refresh is required.")
    
    client = create_client(URL, KEY)
    client.auth.set_session(st.session_state.access_token, "")

    try:
        f_res = client.auth.mfa.list_factors()
        factors = getattr(f_res, 'all', [])
        
        if not factors:
            st.error("MFA not configured for this account.")
            return

        otp = st.text_input("Enter 6-digit Authenticator Code", max_chars=6)
        
        if st.button("Verify & Unlock", use_container_width=True):
            try:
                # Using the dict-wrapped challenge we perfected
                challenge = client.auth.mfa.challenge({"factor_id": factors[0].id})
                c_id = getattr(challenge, 'id', challenge.get('id') if isinstance(challenge, dict) else None)
                
                client.auth.mfa.verify({
                    "factor_id": factors[0].id,
                    "challenge_id": c_id,
                    "code": str(otp).strip()
                })
                
                # Success: Set the 2-hour anchor point
                st.session_state.last_mfa_time = time.time()
                st.rerun()
            except Exception:
                st.error("Verification failed. Check your authenticator app.")
                
    except Exception as e:
        st.error("Auth session stale. Please log in again.")
        st.session_state.authenticated = False

# --- 5. PROTECTED DASHBOARD ---
def main_dashboard():
    # Sidebar Security Info
    st.sidebar.title("🏥 Clinical Session")
    
    # Calculate countdown
    time_elapsed = time.time() - st.session_state.last_mfa_time
    seconds_left = int(TRUST_WINDOW - time_elapsed)
    mins_left = seconds_left // 60
    
    if mins_left > 0:
        st.sidebar.success(f"🔒 MFA Valid: {mins_left}m remaining")
    else:
        st.sidebar.error("⌛ MFA Lease Expiring...")

    if st.sidebar.button("🚪 Log Out"):
        st.session_state.authenticated = False
        st.rerun()

    # Dashboard Content
    st.title("🩺 Medical Passport Dashboard")
    st.write(f"Verified User: **{st.session_state.user_email}**")
    st.write("---")
    
    # Placeholder for the clinical data
    st.subheader("Your Encrypted Credentials")
    st.info("Medical degree, Specialist certifications, and ID checks are currently unlocked.")

# --- 6. EXECUTION LOGIC ---
if not st.session_state.authenticated:
    login_screen()
else:
    if is_mfa_trusted():
        main_dashboard()
    else:
        mfa_gate()
