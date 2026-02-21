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

# --- 2. RECOVERY HANDLER ---
def handle_recovery():
    params = st.query_params
    # We check for 'type=recovery' which we manually append in the redirect
    if params.get("type") == "recovery":
        st.title("🛡️ Reset Your Password")
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password"):
            if new_p == conf_p and len(new_p) >= 6:
                try:
                    # When clicking a reset link, Supabase creates a temporary session
                    # so we can call update_user immediately.
                    client.auth.update_user({"password": new_p})
                    st.success("Password updated! Redirecting to login...")
                    time.sleep(2)
                    st.query_params.clear() 
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
            else:
                st.error("Passwords must match (min 6 chars).")
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
                # This 'triage' step ensures the user comes back to the right place
                # If running locally, it uses localhost. If on cloud, it uses your URL.
                # Use st.navigation or hardcode your production URL here:
                actual_url = "https://medical-passport.streamlit.app" 
                
                client.auth.reset_password_for_email(
                    reset_email, 
                    options={"redirect_to": f"{actual_url}?type=recovery"}
                )
                st.success("Recovery link sent! Check your email.")
            except Exception as e:
                st.error(f"API Error: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    login_screen()
else:
    st.write("Logged In")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
