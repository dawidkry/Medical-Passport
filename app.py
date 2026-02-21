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

# --- 2. THE RECOVERY HANDLER ---
def handle_recovery():
    params = st.query_params
    auth_code = params.get("code")
    is_recovery = params.get("type") == "recovery"

    if auth_code and is_recovery:
        st.title("🛡️ Reset Your Password")
        st.info("Identity verified. Please set your new credentials.")
        
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Password", use_container_width=True):
                if new_p == conf_p and len(new_p) >= 6:
                    try:
                        client.auth.exchange_code_for_session({"auth_code": auth_code})
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
        with col2:
            if st.button("Cancel & Go Back", use_container_width=True):
                st.query_params.clear()
                st.rerun()
        return True
    return False

# --- 3. THE MULTI-MODE AUTHENTICATION UI ---
def login_screen():
    # Only show recovery if the URL has the secret code
    if handle_recovery():
        return

    st.title("🏥 Medical Passport Gateway")
    mode = st.radio("Select Action", ["Login", "Register New Account", "Forgot Password"], horizontal=True)
    st.write("---")

    if mode == "Login":
        email = st.text_input("Professional Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            try:
                res = client.auth.sign_in_with_password({"email": email, "password": password})
                if res.session:
                    st.session_state.authenticated = True
                    st.rerun()
            except:
                st.error("Login failed. Check credentials or verify email.")

    elif mode == "Register New Account":
        st.subheader("Create Clinical Provider Account")
        # THESE WERE MISSING - RESTORED:
        new_email = st.text_input("Enter Work Email", key="reg_email")
        new_pass = st.text_input("Create Password", type="password", key="reg_pass")
        confirm_pass = st.text_input("Confirm Password", type="password", key="reg_conf")
        
        if st.button("Complete Registration", use_container_width=True):
            if new_pass != confirm_pass:
                st.error("Passwords do not match.")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    res = client.auth.sign_up({"email": new_email, "password": new_pass})
                    if res.user and res.user.identities == []:
                        st.warning("This email is already registered. Try logging in.")
                    else:
                        st.success(f"Verification email sent to {new_email}!")
                except Exception as e:
                    st.error(f"Registration error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        reset_email = st.text_input("Enter your registered email")
        if st.button("Send Recovery Link", use_container_width=True):
            try:
                # Replace with your actual production URL
                actual_url = "https://medical-passport.streamlit.app" 
                client.auth.reset_password_for_email(
                    reset_email, 
                    options={"redirect_to": f"{actual_url}?type=recovery"}
                )
                st.success("Recovery link sent! (Subject to hourly limits)")
            except Exception as e:
                st.error(f"API Error: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    login_screen()
else:
    st.title("🩺 Medical Passport Dashboard")
    st.info("Welcome, Dr. User. Your secure portal is active.")
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.rerun()
