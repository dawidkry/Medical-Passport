import streamlit as st
import time
import pandas as pd
from supabase import create_client, Client

# --- 1. CORE CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
client = create_client(URL, KEY)

# Initialize ALL session states at once
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'last_mfa_time' not in st.session_state:
    st.session_state.last_mfa_time = 0 
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. THE CONTENT (The "Passport") ---
def main_dashboard():
    st.sidebar.title("🏥 Clinical Session")
    
    # 2-Hour Trust Countdown
    elapsed = time.time() - st.session_state.last_mfa_time
    mins_left = int((7200 - elapsed) // 60)
    
    if mins_left > 0:
        st.sidebar.success(f"🔒 MFA Active: {mins_left}m left")
    else:
        st.sidebar.warning("⌛ MFA Refresh Required")

    if st.sidebar.button("🚪 Log Out"):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🩺 Professional Medical Passport")
    st.write(f"Verified Provider: **{st.session_state.user_email}**")
    st.divider()

    t1, t2, t3 = st.tabs(["📊 ID & Overview", "🏥 Rotations", "💉 Procedures"])
    
    with t1:
        c1, c2 = st.columns(2)
        c1.info("**GMC Status:** Registered / Clear")
        c2.info("**Current Grade:** Specialty Trainee")
        st.write("### Digital Credentials")
        st.code("MD-AUTH-VERIFIED-2026", language=None)

    with t2:
        st.subheader("Experience Ledger")
        data = [{"Hospital": "General Hospital", "Unit": "ICU", "Dates": "2024-25"}]
        st.table(data)

    with t3:
        st.subheader("Procedural Competency")
        pdf = pd.DataFrame({"Procedure": ["Intubation", "PICC Line"], "Count": [15, 8]})
        st.dataframe(pdf, use_container_width=True)

# --- 3. THE SECURITY GATES ---

def handle_recovery():
    params = st.query_params
    if params.get("type") == "recovery" and params.get("code"):
        st.title("🛡️ Reset Password")
        new_p = st.text_input("New Password", type="password")
        if st.button("Update"):
            try:
                client.auth.exchange_code_for_session({"auth_code": params.get("code")})
                client.auth.update_user({"password": new_p})
                st.success("Success! Redirecting...")
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
        return True
    return False

def login_screen():
    st.title("🏥 Medical Passport Gateway")
    mode = st.radio("Action", ["Login", "Register", "Forgot Password"], horizontal=True)
    
    if mode == "Login":
        e = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            try:
                res = client.auth.sign_in_with_password({"email": e, "password": p})
                if res.session:
                    st.session_state.authenticated = True
                    st.session_state.user_email = e
                    st.rerun()
            except: st.error("Login Failed")

    elif mode == "Register":
        st.subheader("New Account")
        reg_e = st.text_input("Email")
        reg_p = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            try:
                client.auth.sign_up({"email": reg_e, "password": reg_p})
                st.success("Verification email sent!")
            except Exception as e: st.error(f"Error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Recovery")
        f_e = st.text_input("Email")
        if st.button("Send Link"):
            try:
                client.auth.reset_password_for_email(f_e, options={"redirect_to": "https://medical-passport.streamlit.app?type=recovery"})
                st.success("Link sent!")
            except Exception as e: st.error(f"Error: {e}")

# --- 4. THE EXECUTION CONTROLLER ---
# This is the "Triage" that prevents a blank page

if handle_recovery():
    # If the URL says we are recovering, only show that.
    pass 
elif st.session_state.authenticated:
    # If logged in, show the dashboard.
    main_dashboard()
else:
    # Default: Show the login gateway.
    login_screen()
