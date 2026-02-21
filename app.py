import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

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
        st.write(f"Logged in as: **{st.session_state.user_email}**")
        try:
            f_res = client.auth.mfa.list_factors()
            factors = getattr(f_res, 'all', [])
            if any(f.status == 'verified' for f in factors):
                st.success("🔒 MFA Status: Verified (High Security)")
            else:
                st.warning("⚠️ MFA Status: Incomplete")
        except:
            pass

    elif page == "Account Security":
        st.title("🛡️ MFA Setup & Management")
        
        # --- FACTOR AUDIT ---
        factors = []
        try:
            f_res = client.auth.mfa.list_factors()
            factors = getattr(f_res, 'all', [])
        except:
            st.error("Could not retrieve factors.")

        if factors:
            for f in factors:
                col_a, col_b = st.columns([3, 1])
                status_icon = "✅" if f.status == 'verified' else "⏳"
                col_a.write(f"{status_icon} **Name:** {f.friendly_name} | **Status:** {f.status.upper()}")
                if col_b.button("🗑️ Reset", key=f.id):
                    try:
                        client.auth.mfa.unenroll({"factor_id": f.id})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Reset failed: {e}")
            st.divider()

        # --- ENROLLMENT ---
        if not factors:
            if st.button("Initialize New 2FA Enrollment"):
                try:
                    enroll = client.auth.mfa.enroll({"factor_type": "totp", "friendly_name": "MedPass"})
                    st.session_state.mfa_id = str(enroll.id)
                    st.session_state.qr_code = enroll.totp.qr_code
                    st.session_state.mfa_secret = enroll.totp.secret 
                    st.rerun()
                except Exception as e:
                    st.error(f"Enrollment Error: {e}")

        # --- VERIFICATION ---
        if st.session_state.get('qr_code'):
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.image(st.session_state.qr_code, width=250, caption="Scan with Microsoft Authenticator")
            with c2:
                st.info("Manual Key:")
                st.code(st.session_state.get('mfa_secret', ""), language=None)
            
            otp = st.text_input("Enter 6-Digit Code", max_chars=6)
            if st.button("Verify & Activate"):
                try:
                    # 1. Generate the challenge
                    challenge = client.auth.mfa.challenge(st.session_state.mfa_id)
                    
                    # 2. Extract Challenge ID (Universal extraction)
                    c_id = getattr(challenge, 'id', None)
                    if not c_id and isinstance(challenge, dict):
                        c_id = challenge.get('id')
                    
                    # 3. Final Verification Payload
                    # This structure is designed to avoid the 'str' object attribute error
                    verification_data = {
                        "factor_id": str(st.session_state.mfa_id),
                        "challenge_id": str(c_id),
                        "code": str(otp).strip()
                    }
                    
                    # Pass the dictionary as the single positional argument
                    client.auth.mfa.verify(verification_data)
                    
                    st.success("✅ MFA Fully Activated!")
                    st.balloons()
                    st.session_state.pop('qr_code', None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
