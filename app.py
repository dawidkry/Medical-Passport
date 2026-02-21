import streamlit as st
from supabase import create_client, Client

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
    client = create_client(URL, KEY)
    
    try:
        client.auth.set_session(st.session_state.access_token, "")
    except Exception as e:
        st.sidebar.error("Session stale. Please log in again.")

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
        
        # Check for existing factors
        try:
            f_res = client.auth.mfa.list_factors()
            factors = getattr(f_res, 'all', [])
            if factors:
                st.warning(f"Active Factor: {factors[0].friendly_name}")
                if st.button("Disable & Reset MFA"):
                    client.auth.mfa.unenroll(factors[0].id)
                    st.rerun()
        except:
            pass

        if st.button("Generate 2FA QR Code"):
            try:
                enroll = client.auth.mfa.enroll({"factor_type": "totp", "friendly_name": "MedPass"})
                
                # We carefully save every piece of data to session_state
                st.session_state.mfa_id = enroll.id
                st.session_state.qr_code = enroll.totp.qr_code
                st.session_state.mfa_secret = enroll.totp.secret 
                st.rerun()
            except Exception as e:
                st.error(f"Security Error: {e}")

        # Use 'get' to check for existence safely
        if st.session_state.get('qr_code'):
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Option 1: Scan QR")
                st.image(st.session_state.qr_code, width=300)
            
            with col2:
                st.write("### Option 2: Manual Entry")
                st.info("Manual Secret Key:")
                # Safe access to the secret
                st.code(st.session_state.get('mfa_secret', "Not Found"), language=None)
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
                    # Clean up
                    st.session_state.pop('qr_code', None)
                    st.session_state.pop('mfa_secret', None)
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
