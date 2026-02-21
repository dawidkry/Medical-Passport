import streamlit as st
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions  # <-- New Import

# --- 1. CONFIGURATION ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. AUTHENTICATION SYSTEM ---
def secure_auth_system():
    st.title("🏥 Medical Passport Gateway")
    email = st.text_input("Professional Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In", use_container_width=True):
        try:
            # Simple client for initial login
            temp_client = create_client(URL, KEY)
            res = temp_client.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                st.session_state.access_token = res.session.access_token
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    # Properly format the options object
    opts = ClientOptions(headers={"Authorization": f"Bearer {st.session_state.access_token}"})
    
    # Create the authenticated client
    client = create_client(URL, KEY, options=opts)
    
    # Force set the session into the client's auth memory
    client.auth.set_session(st.session_state.access_token, "")

    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.authenticated = False
        st.session_state.access_token = None
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Medical Passport Dashboard")
        st.write(f"Secure session active for: {st.session_state.user_email}")

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        if st.button("Generate 2FA QR Code"):
            try:
                enroll = client.auth.mfa.enroll({"factor_type": "totp", "friendly_name": "MedPass"})
                st.session_state.mfa_id = enroll.id
                st.session_state.qr_code = enroll.totp.qr_code
                st.session_state.mfa_secret = enroll.totp.secret 
                st.rerun()
            except Exception as e:
                st.error(f"Security Error: {e}")

        if 'qr_code' in st.session_state:
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Option 1: Scan QR")
                st.image(st.session_state.qr_code, width=300)
            
            with col2:
                st.write("### Option 2: Manual Entry")
                st.info("Manual Secret Key:")
                st.code(st.session_state.mfa_secret, language=None)
                st.write("**Account Name:** Medical Passport")
                st.write("**Type:** TOTP")

            st.divider()
            otp = st.text_input("Enter 6-Digit Code from App", max_chars=6)
            
            if st.button("Verify & Activate"):
                try:
                    challenge = client.auth.mfa.challenge(st.session_state.mfa_id)
                    client.auth.mfa.verify({
                        "factor_id": st.session_state.mfa_id,
                        "challenge_id": challenge.id,
                        "code": otp
                    })
                    st.success("✅ MFA Activated!")
                    del st.session_state.qr_code
                    if 'mfa_secret' in st.session_state:
                        del st.session_state.mfa_secret
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
