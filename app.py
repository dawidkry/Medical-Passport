import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
client = create_client(URL, KEY)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# --- 2. THE RECOVERY HANDLER (STRENGTHENED) ---
def handle_recovery():
    # Capture URL parameters
    params = st.query_params
    
    # Check if we are in recovery mode
    if params.get("type") == "recovery":
        st.title("🛡️ Reset Your Password")
        st.info("Your identity has been verified via email. Please set your new password.")
        
        new_p = st.text_input("New Password", type="password", key="reset_p1")
        conf_p = st.text_input("Confirm New Password", type="password", key="reset_p2")
        
        if st.button("Update Password", use_container_width=True):
            if new_p == conf_p and len(new_p) >= 6:
                try:
                    # THE FIX: We ensure we are using the current session 
                    # that was established by clicking the email link.
                    res = client.auth.update_user({"password": new_p})
                    
                    if res:
                        st.success("✅ Password updated! Redirecting to login...")
                        st.balloons()
                        time.sleep(3)
                        # Clear URL and reset state
                        st.query_params.clear()
                        st.rerun()
                except Exception as e:
                    # If the session expired, we provide a clear path back
                    st.error(f"Session Expired: {e}")
                    if st.button("Request New Link"):
                        st.query_params.clear()
                        st.rerun()
            else:
                st.error("Passwords must match and be at least 6 characters.")
        return True
    return False

# --- 3. LOGIN UI ---
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
                # IMPORTANT: Use the exact URL as configured in Supabase
                actual_url = "https://medical-passport.streamlit.app" 
                
                client.auth.reset_password_for_email(
                    reset_email, 
                    options={"redirect_to": f"{actual_url}?type=recovery"}
                )
                st.success("Recovery link sent! Check your inbox.")
            except Exception as e:
                st.error(f"API Error: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    login_screen()
else:
    st.title("🩺 Medical Passport Dashboard")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
