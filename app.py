import streamlit as st
import time
import pandas as pd
from supabase import create_client, Client

# --- 1. CORE CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
client = create_client(URL, KEY)

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'rotations' not in st.session_state:
    # Starting with some sample data
    st.session_state.rotations = [
        {"Hospital": "St. Mary's", "Specialty": "Acute Medicine", "Dates": "Aug 2024 - Feb 2025"},
        {"Hospital": "Royal Infirmary", "Specialty": "Emergency Dept", "Dates": "Feb 2025 - Aug 2025"}
    ]

# --- 2. THE PASSPORT DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🏥 Clinical Session")
    st.sidebar.write(f"User: {st.session_state.user_email}")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🩺 Medical Passport: Professional Ledger")
    st.divider()

    tab1, tab2 = st.tabs(["🏥 Clinical Rotations", "📜 ID & Credentials"])

    with tab1:
        st.subheader("Current & Past Rotations")
        # Display the rotations in a clean table
        df = pd.DataFrame(st.session_state.rotations)
        st.table(df)

        st.write("---")
        st.subheader("➕ Add New Experience")
        with st.form("rotation_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            hosp = col1.text_input("Hospital Name")
            spec = col2.text_input("Specialty")
            dates = st.text_input("Dates (e.g. Aug 25 - Feb 26)")
            
            if st.form_submit_button("Log Experience"):
                if hosp and spec and dates:
                    new_entry = {"Hospital": hosp, "Specialty": spec, "Dates": dates}
                    st.session_state.rotations.append(new_entry)
                    st.success("Experience added to your passport!")
                    st.rerun()
                else:
                    st.error("Please fill in all clinical fields.")

    with tab2:
        st.subheader("Professional Identity")
        st.info(f"**Primary Email:** {st.session_state.user_email}")
        st.info("**GMC Status:** Verified ✅")
        st.write("### Digital Credentials")
        st.code("MD-PASSPORT-AUTH-VALID", language=None)

# --- 3. LOGIN & REGISTRATION GATEWAY ---
def login_screen():
    st.title("🏥 Medical Passport Gateway")
    mode = st.radio("Select Action", ["Login", "Register New Account", "Forgot Password"], horizontal=True)
    st.write("---")

    if mode == "Login":
        e = st.text_input("Professional Email")
        p = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            try:
                res = client.auth.sign_in_with_password({"email": e, "password": p})
                if res.session:
                    st.session_state.authenticated = True
                    st.session_state.user_email = e
                    st.rerun()
            except:
                st.error("Invalid credentials. Please verify your email and password.")

    elif mode == "Register New Account":
        st.subheader("Create Clinical Provider Account")
        reg_e = st.text_input("Work Email")
        reg_p = st.text_input("Create Password (6+ chars)", type="password")
        
        if st.button("Complete Registration", use_container_width=True):
            try:
                # The 'Bulletproof' Check
                res = client.auth.sign_up({"email": reg_e, "password": reg_p})
                
                # If identities is empty, it means the email is already in the DB
                if res.user and not res.user.identities:
                    st.warning("⚠️ This clinical email is already registered. Please use the 'Login' tab.")
                else:
                    st.success(f"Verification email sent to {reg_e}! Check your inbox.")
            except Exception as e:
                st.error(f"Error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        f_e = st.text_input("Enter Registered Email")
        if st.button("Send Recovery Link", use_container_width=True):
            try:
                actual_url = "https://medical-passport.streamlit.app" 
                client.auth.reset_password_for_email(f_e, options={"redirect_to": f"{actual_url}?type=recovery"})
                st.success("Recovery link sent!")
            except Exception as e:
                st.error(f"API Error: {e}")

# --- 4. THE TRIAGE CONTROLLER ---
def handle_recovery():
    params = st.query_params
    if params.get("type") == "recovery" and params.get("code"):
        st.title("🛡️ Reset Password")
        new_p = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            try:
                client.auth.exchange_code_for_session({"auth_code": params.get("code")})
                client.auth.update_user({"password": new_p})
                st.success("Updated! Please login.")
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
        return True
    return False

if not handle_recovery():
    if st.session_state.authenticated:
        main_dashboard()
    else:
        login_screen()
