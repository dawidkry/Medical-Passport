import streamlit as st
import time
import pandas as pd
from supabase import create_client, Client

# --- 1. CORE CONFIGURATION ---
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

# Secure connection to Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
client = create_client(URL, KEY)

# Initialize Session States for Persistence during the session
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'rotations' not in st.session_state:
    st.session_state.rotations = [] 
if 'credentials' not in st.session_state:
    st.session_state.credentials = []

# --- 2. THE PASSPORT DASHBOARD ---
def main_dashboard():
    # Sidebar Navigation
    st.sidebar.title("🏥 Clinical Session")
    st.sidebar.write(f"**Verified User:**\n{st.session_state.user_email}")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🩺 Professional Medical Passport")
    st.caption("A secure, portable ledger for clinical training and credentials.")
    st.divider()

    # Organized Tabs for the Clinical Portfolio
    tab1, tab2 = st.tabs(["🏥 Clinical Rotations", "📜 Credential Vault"])

    with tab1:
        st.subheader("Clinical Experience Ledger")
        st.write("Maintain a verified history of your placements. Double-click cells to edit.")

        if st.session_state.rotations:
            # Display current ledger as an editable table
            df = pd.DataFrame(st.session_state.rotations)
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic", 
                use_container_width=True,
                key="rotation_editor"
            )
            
            if st.button("💾 Save Ledger Changes"):
                st.session_state.rotations = edited_df.to_dict('records')
                st.success("Changes saved to session.")
                st.rerun()
        else:
            st.info("Your clinical ledger is empty. Log your first rotation below.")

        st.write("---")
        st.subheader("➕ Log New Experience")
        with st.form("rotation_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            hosp = c1.text_input("Hospital Name", placeholder="e.g. St Thomas' Hospital")
            spec = c2.text_input("Specialty", placeholder="e.g. Cardiology")
            dates = st.text_input("Dates", placeholder="e.g. Aug 2025 - Feb 2026")
            
            if st.form_submit_button("Add to Passport"):
                if hosp and spec and dates:
                    new_entry = {"Hospital": hosp, "Specialty": spec, "Dates": dates}
                    st.session_state.rotations.append(new_entry)
                    st.rerun()
                else:
                    st.error("All clinical fields are required.")

    with tab2:
        st.subheader("🛡️ Verified Credential Vault")
        st.write("Upload primary source documents (GMC Certificates, ALS, Diplomas).")

        # PDF Uploader Logic
        uploaded_file = st.file_uploader("Upload Document (PDF only)", type="pdf")
        
        if uploaded_file is not None:
            if not any(d['Filename'] == uploaded_file.name for d in st.session_state.credentials):
                new_doc = {
                    "Document Name": uploaded_file.name.split('.')[0].replace('_', ' ').title(),
                    "Filename": uploaded_file.name,
                    "Size": f"{uploaded_file.size / 1024:.1f} KB",
                    "Upload Date": time.strftime("%Y-%m-%d")
                }
                st.session_state.credentials.append(new_doc)
                st.success(f"Verified & Added: {uploaded_file.name}")

        st.divider()

        if st.session_state.credentials:
            st.write("### Stored Credentials")
            cred_df = pd.DataFrame(st.session_state.credentials)
            st.dataframe(cred_df, use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Clear Vault"):
                st.session_state.credentials = []
                st.rerun()
        else:
            st.info("No credentials uploaded yet.")

# --- 3. AUTHENTICATION GATES ---

def handle_recovery():
    """Triage for password reset links."""
    params = st.query_params
    if params.get("type") == "recovery" and params.get("code"):
        st.title("🛡️ Reset Password")
        new_p = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            try:
                client.auth.exchange_code_for_session({"auth_code": params.get("code")})
                client.auth.update_user({"password": new_p})
                st.success("Credentials updated! Please login.")
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
        return True
    return False

def login_screen():
    st.title("🏥 Medical Passport Gateway")
    mode = st.radio("Access Mode", ["Login", "Register New Account", "Forgot Password"], horizontal=True)
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
            except: st.error("Authentication failed.")

    elif mode == "Register New Account":
        st.subheader("Clinical Account Registration")
        reg_e = st.text_input("Work Email")
        reg_p = st.text_input("Create Password (6+ characters)", type="password")
        if st.button("Initialize Account", use_container_width=True):
            try:
                res = client.auth.sign_up({"email": reg_e, "password": reg_p})
                if res.user and not res.user.identities:
                    st.warning("⚠️ This email is already in our system. Try Login.")
                else:
                    st.success("Verification email sent! Please check your clinical inbox.")
            except Exception as e: st.error(f"Error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        f_e = st.text_input("Enter Email")
        if st.button("Send Reset Link"):
            try:
                actual_url = "https://medical-passport.streamlit.app" 
                client.auth.reset_password_for_email(f_e, options={"redirect_to": f"{actual_url}?type=recovery"})
                st.success("Link sent (check spam if not received within 5 mins).")
            except Exception as e: st.error(f"API Error: {e}")

# --- 4. EXECUTION FLOW ---
if not handle_recovery():
    if st.session_state.authenticated:
        main_dashboard()
    else:
        login_screen()
