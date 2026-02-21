import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
TRUST_WINDOW = 7200 

# Initialize States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'last_mfa_time' not in st.session_state:
    st.session_state.last_mfa_time = 0 
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. THE MULTI-MODE AUTHENTICATION UI ---
def login_screen():
    st.title("🏥 Medical Passport Gateway")
    
    # Selection menu for the user
    mode = st.radio("Select Action", ["Login", "Register New Account", "Forgot Password"], horizontal=True)
    st.write("---")
    
    client = create_client(URL, KEY)

    if mode == "Login":
        email = st.text_input("Professional Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            try:
                res = client.auth.sign_in_with_password({"email": email, "password": password})
                if res.session:
                    st.session_state.access_token = res.session.access_token
                    st.session_state.user_email = email
                    st.session_state.authenticated = True
                    st.rerun()
            except Exception as e:
                st.error("Login failed. Ensure your email is verified.")

    elif mode == "Register New Account":
        st.subheader("Create Clinical Provider Account")
        new_email = st.text_input("Enter Work Email")
        new_pass = st.text_input("Create Password", type="password", help="Minimum 6 characters")
        confirm_pass = st.text_input("Confirm Password", type="password")
        
        if st.button("Sign Up", use_container_width=True):
            if new_pass != confirm_pass:
                st.error("Passwords do not match.")
            else:
                try:
                    client.auth.sign_up({"email": new_email, "password": new_pass})
                    st.success(f"Verification email sent to {new_email}! Please check your inbox (and spam) before logging in.")
                except Exception as e:
                    st.error(f"Registration error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        reset_email = st.text_input("Enter your registered email")
        if st.button("Send Recovery Link", use_container_width=True):
            try:
                # This sends an email with a link that redirects back to your app
                client.auth.reset_password_for_email(reset_email)
                st.success("If an account exists with this email, a reset link has been sent.")
            except Exception as e:
                st.error("Error initiating reset.")

# --- 3. (KEEP YOUR EXISTING mfa_gate AND is_mfa_trusted FUNCTIONS HERE) ---
def is_mfa_trusted():
    return (time.time() - st.session_state.last_mfa_time) < TRUST_WINDOW

def mfa_gate():
    st.title("🛡️ Identity Verification")
    st.warning("MFA Refresh Required.")
    client = create_client(URL, KEY)
    client.auth.set_session(st.session_state.access_token, "")
    try:
        f_res = client.auth.mfa.list_factors()
        factors = getattr(f_res, 'all', [])
        if not factors:
            # If they just registered, they might need to set up MFA for the first time
            st.info("No MFA detected. Redirecting to setup...")
            # (Insert your MFA enrollment code here if needed)
            return
        
        otp = st.text_input("Enter 6-digit Authenticator Code", max_chars=6)
        if st.button("Verify & Unlock", use_container_width=True):
            challenge = client.auth.mfa.challenge({"factor_id": factors[0].id})
            c_id = getattr(challenge, 'id', challenge.get('id') if isinstance(challenge, dict) else None)
            client.auth.mfa.verify({"factor_id": factors[0].id, "challenge_id": c_id, "code": str(otp).strip()})
            st.session_state.last_mfa_time = time.time()
            st.rerun()
    except:
        st.session_state.authenticated = False

# --- 4. DASHBOARD & EXECUTION ---
def main_dashboard():
    st.sidebar.title("🏥 Clinical Session")
    # (Existing Countdown Logic)
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🩺 Medical Passport Dashboard")
    st.write(f"Welcome, {st.session_state.user_email}")

if not st.session_state.authenticated:
    login_screen()
else:
    if is_mfa_trusted():
        main_dashboard()
    else:
        mfa_gate()
