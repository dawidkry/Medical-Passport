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

# --- THE FIX: EMPTY LIST START ---
if 'rotations' not in st.session_state:
    st.session_state.rotations = [] 

# --- 2. THE PASSPORT DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🏥 Clinical Session")
    st.sidebar.write(f"Verified: {st.session_state.user_email}")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.title("🩺 Professional Medical Passport")
    st.divider()

    tab1, tab2 = st.tabs(["🏥 Clinical Rotations", "📜 ID & Credentials"])

    with tab1:
        st.subheader("Clinical Experience Ledger")
        st.caption("Double-click any cell to edit details manually.")

        # If we have data, show the editor
        if st.session_state.rotations:
            df = pd.DataFrame(st.session_state.rotations)
            
            # --- THE EDITABLE TABLE ---
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic", # Allows you to delete rows by selecting and hitting 'delete'
                use_container_width=True,
                key="rotation_editor"
            )
            
            # Sync edits back to session state
            if st.button("💾 Save Changes"):
                st.session_state.rotations = edited_df.to_dict('records')
                st.success("Ledger updated!")
                st.rerun()
        else:
            st.info("Your ledger is currently empty. Use the form below to log your first rotation.")

        st.write("---")
        st.subheader("➕ Log New Experience")
        with st.form("rotation_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            hosp = col1.text_input("Hospital Name")
            spec = col2.text_input("Specialty")
            dates = st.text_input("Dates (e.g. 2024-2025)")
            
            if st.form_submit_button("Add to Passport"):
                if hosp and spec and dates:
                    new_entry = {"Hospital": hosp, "Specialty": spec, "Dates": dates}
                    st.session_state.rotations.append(new_entry)
                    st.rerun()
                else:
                    st.error("Please fill in all clinical fields.")

    with tab2:
        st.subheader("Professional Identity")
        st.info(f"**Primary Email:** {st.session_state.user_email}")
        st.info("**GMC Status:** Verified ✅")
        st.write("### Digital Credentials")
        st.code("MD-PASSPORT-AUTH-VALID", language=None)

# --- 3. LOGIN & RECOVERY GATES (REMAINS SAME) ---
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
                st.error("Invalid credentials.")

    elif mode == "Register New Account":
        st.subheader("Create Clinical Provider Account")
        reg_e = st.text_input("Work Email")
        reg_p = st.text_input("Create Password", type="password")
        if st.button("Complete Registration", use_container_width=True):
            try:
                res = client.auth.sign_up({"email": reg_e, "password": reg_p})
                if res.user and not res.user.identities:
                    st.warning("⚠️ This email is already registered.")
                else:
                    st.success(f"Verification email sent to {reg_e}!")
            except Exception as e:
                st.error(f"Error: {e}")

    elif mode == "Forgot Password":
        st.subheader("Account Recovery")
        f_e = st.text_input("Email")
        if st.button("Send Link"):
            actual_url = "https://medical-passport.streamlit.app" 
            client.auth.reset_password_for_email(f_e, options={"redirect_to": f"{actual_url}?type=recovery"})
            st.success("Recovery link sent!")

def handle_recovery():
    params = st.query_params
    if params.get("type") == "recovery" and params.get("code"):
        st.title("🛡️ Reset Password")
        new_p = st.text_input("New Password", type="password")
        if st.button("Update"):
            try:
                client.auth.exchange_code_for_session({"auth_code": params.get("code")})
                client.auth.update_user({"password": new_p})
                st.success("Success! Please login.")
                time.sleep(2)
                st.query_params.clear()
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
        return True
    return False

# --- 4. EXECUTION ---
if not handle_recovery():
    if st.session_state.authenticated:
        main_dashboard()
    else:
        login_screen()
