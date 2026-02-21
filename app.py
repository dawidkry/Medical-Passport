import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
client = create_client(URL, KEY)

# Initialize States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'last_mfa_time' not in st.session_state:
    st.session_state.last_mfa_time = 0 
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. PASSWORD RECOVERY HANDLER ---
def handle_recovery():
    """Checks if the user landed here from a 'Reset Password' email."""
    # Streamlit can read URL parameters
    params = st.query_params
    if "type" in params and params["type"] == "recovery":
        st.title("🛡️ Reset Your Password")
        st.info("Please enter your new clinical credentials below.")
        
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password & Login"):
            if new_p == conf_p and len(new_p) >= 6:
                try:
                    client.auth.update_user({"password": new_p})
                    st.success("Password updated! You can now log in.")
                    # Clear the URL parameters so the form disappears
                    st.query_params.clear()
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")
            else:
                st.error("Passwords must match and be at least 6 characters.")
        return True
    return False

# --- 3. UPDATED LOGIN/REGISTER UI ---
def login_screen():
    # First, check if we are in 'Recovery Mode'
    if handle_recovery():
        return # Stop here and show the recovery form

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
                    st.session_state.access_token = res.session.access_token
                    st.session_state.user_email = email
                    st.session_state.authenticated = True
                    st.rerun()
            except:
                st.error("Login failed. Check credentials or verify your email.")

    elif mode == "Register New Account":
        st.subheader("Create Clinical Provider Account")
        new_email = st.text_input("Enter Work Email")
        new_pass = st.text_input("Create Password", type="password")
        
        if st.button("Sign Up", use_container_width=True):
            try:
                # Sign up will return an empty user object if email exists but isn't confirmed
                # or throw an error depending on Supabase settings.
                res = client.auth.sign_up({"email": new_email, "password": new_pass})
                
                # Check if user already exists (identities list will be empty if new)
                if res.user and res.user.identities == []:
                    st.warning("This email is already registered. Try logging in or resetting your password.")
                else:
                    st.success(f"Verification email sent to {new_email}!")
            except Exception as e:
                st.error(f"Registration error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        reset_email = st.text_input("Enter your registered email")
        if st.button("Send Recovery Link", use_container_width=True):
            try:
                # redirectTo ensures the user comes back to YOUR app URL
                client.auth.reset_password_for_email(reset_email)
                st.success("Check your email for the secure reset link.")
            except Exception as e:
                st.error("Error initiating reset.")

# --- (Rest of your Dashboard and Execution Logic remains the same) ---
def main_dashboard():
    st.title("🩺 Medical Passport Dashboard")
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.rerun()

if not st.session_state.authenticated:
    login_screen()
else:
    main_dashboard()
