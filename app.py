import streamlit as st
import time
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
# Page config MUST be called before any other Streamlit commands
st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_time' not in st.session_state:
    st.session_state.auth_time = 0
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. SESSION TIMEOUT SYSTEM ---
def check_session_timeout():
    """Forces a logout if the user has been logged in for too long."""
    # Clinical Standard: 30 minutes (1800 seconds)
    # Testing Suggestion: Set to 60 for 1 minute testing
    TIMEOUT_SECONDS = 1800 
    
    if st.session_state.authenticated and st.session_state.auth_time > 0:
        elapsed = time.time() - st.session_state.auth_time
        if elapsed > TIMEOUT_SECONDS:
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.auth_time = 0
            st.warning("⏱️ Security Timeout: Please re-authenticate.")
            st.rerun()

# --- 3. AUTHENTICATION UI ---
def secure_auth_system():
    st.title("🏥 Medical Passport Gateway")
    st.subheader("Clinical Provider Login")
    
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
                st.session_state.auth_time = time.time() # Start the session clock
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# --- 4. CLINICAL DASHBOARD ---
def main_dashboard():
    # Run timeout check immediately upon loading dashboard
    check_session_timeout()
    
    client = create_client(URL, KEY)
    try:
        client.auth.set_session(st.session_state.access_token, "")
    except:
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Go to", ["Main Dashboard", "Account Security"])
    
    # Calculate time remaining for the user
    if st.session_state.auth_time > 0:
        time_left = int(1800 - (time.time() - st.session_state.auth_time))
        if time_left > 0:
            st.sidebar.caption(f"⏱️ Session expires in: {time_left // 60}m")

    if st.sidebar.button("🚪 Log Out"):
        st.session_state.authenticated = False
        st.session_state.access_token = None
        st.session_state.auth_time = 0
        st.rerun()

    if page == "Main Dashboard":
        st.title("🩺 Medical Passport Dashboard")
        st.write(f"Logged in as: **{st.session_state.user_email}**")
        
        # Verify MFA Status for Dashboard Access
        try:
            f_res = client.auth.mfa.list_factors()
            factors = getattr(f_res, 'all', [])
            is_verified = any(f.status == 'verified' for f in factors)
            
            if is_verified:
                st.success("🔒 MFA Verified: Full Clinical Access Granted.")
                # PLACE YOUR PROTECTED MEDICAL CONTENT HERE
                st.info("Clinical Records, Credentials, and Passport Data are now visible.")
            else:
                st.warning("⚠️ MFA Required. Please go to 'Account Security' to verify your identity.")
        except:
            st.error("Error verifying security status.")

    elif page == "Account Security":
        st.title("🛡️ MFA Management")
        
        # 1. Check for factors
        factors = []
        try:
            f_res = client.auth.mfa.list_factors()
            factors = getattr(f_res, 'all', [])
        except: pass

        if factors:
            for f in factors:
                col_a, col_b = st.columns([3, 1])
                status_txt = "✅ VERIFIED" if f.status == 'verified' else "⏳ UNVERIFIED"
                col_a.write(f"**Factor:** {f.friendly_name} | **Status:** {status_txt}")
                if col_b.button("🗑️ Reset", key=f.id):
                    client.auth.mfa.unenroll({"factor_id": f.id})
                    st.rerun()
            st.divider()

        # 2. Enrollment
        if not factors:
            if st.button("Initialize New 2FA"):
                try:
                    enroll = client.auth.mfa.enroll({"factor_type": "totp", "friendly_name": "MedPass"})
                    st.session_state.mfa_id = str(enroll.id)
                    st.session_state.qr_code = enroll.totp.qr_code
                    st.session_state.mfa_secret = enroll.totp.secret 
                    st.rerun()
                except Exception as e:
                    st.error(f"Enrollment Error: {e}")

        # 3. Verification UI
        if st.session_state.get('qr_code'):
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.image(st.session_state.qr_code, width=250, caption="Scan QR")
            with c2:
                st.info("Manual Entry Key:")
                st.code(st.session_state.get('mfa_secret', ""), language=None)
            
            otp = st.text_input("Enter 6-Digit App Code", max_chars=6)
            if st.button("Verify & Activate"):
                try:
                    # Defensive challenge & verify
                    challenge = client.auth.mfa.challenge({"factor_id": st.session_state.mfa_id})
                    c_id = getattr(challenge, 'id', challenge.get('id') if isinstance(challenge, dict) else None)
                    
                    client.auth.mfa.verify({
                        "factor_id": st.session_state.mfa_id,
                        "challenge_id": c_id,
                        "code": str(otp).strip()
                    })
                    st.success("✅ MFA Activated!")
                    st.balloons()
                    st.session_state.pop('qr_code', None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 5. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
