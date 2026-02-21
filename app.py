import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
client = create_client(URL, KEY)

# Initialize Session State
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. THE RECOVERY HANDLER (PKCE COMPATIBLE) ---
def handle_recovery():
    params = st.query_params
    
    # 1. Look for the 'code' parameter sent by Supabase PKCE
    auth_code = params.get("code")
    is_recovery = params.get("type") == "recovery"

    if auth_code and is_recovery:
        st.title("🛡️ Reset Your Password")
        st.info("Identity verified. Please enter your new clinical credentials.")
        
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password", use_container_width=True):
            if new_p == conf_p and len(new_p) >= 6:
                try:
                    # EXCHANGE THE CODE FOR A SESSION
                    # This is the magic step that fixes 'Auth Session Missing'
                    client.auth.exchange_code_for_session({"auth_code": auth_code})
                    
                    # NOW we have a session, so we can update the user
                    client.auth.update_user({"password": new_p})
                    
                    st.success("✅ Password updated! Redirecting...")
                    st.balloons()
                    time.sleep(2)
                    st.query_params.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Recovery failed: {e}")
            else:
                st.error("Passwords must match and be 6+ characters.")
        return True
    return False

# --- 3. LOGIN SCREEN ---
def login_screen():
    if handle_recovery():
        return

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
                    st.rerun()
            except: st.error("Invalid Login")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        reset_email = st.text_input("Email")
        if st.button("Send Reset Link"):
            try:
                # We point back to our app and tell it we are in 'recovery' mode
                actual_url = "https://medical-passport.streamlit.app" 
                client.auth.reset_password_for_email(
                    reset_email, 
                    options={"redirect_to": f"{actual_url}?type=recovery"}
                )
                st.success("Recovery link sent! Check your email.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    login_screen()
else:
    st.title("🩺 Medical Passport Dashboard")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
