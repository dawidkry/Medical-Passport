import streamlit as st
from supabase import create_client, Client

# --- 1. STATE-LOCKED CONNECTION ---
# This decorator ensures the 'supabase' object doesn't reset/lose memory
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

st.set_page_config(page_title="Medical Passport", page_icon="🏥", layout="wide")

# Initialize Session States
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

# --- 2. AUTHENTICATION SYSTEM ---
def secure_auth_system():
    st.title("🏥 Medical Passport Gateway")
    st.markdown("---")
    
    email = st.text_input("Professional Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In", use_container_width=True):
        try:
            # We don't just sign in; we explicitly refresh the client session
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.session:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
        except Exception as e:
            st.error(f"Login Error: {e}")

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"Logged in: **{st.session_state.user_email}**")
    
    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Professional Medical Passport")
        st.write("Welcome, Doctor.")

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        # Verify user is still 'seen' by the server
        user = supabase.auth.get_user()
        if not user:
            st.warning("Session lost. Please log out and back in.")
            return

        if st.button("Generate 2FA QR Code"):
            try:
                # Absolute simplest enrollment call
                enroll = supabase.auth.mfa.enroll({"factor_type": "totp"})
                
                # Check for nested data structure
                data = getattr(enroll, 'data', enroll)
                st.session_state.mfa_id = data.id
                st.session_state.qr_code = data.totp.qr_code
                st.rerun()
            except Exception as e:
                st.error(f"Enrollment Error: {e}")

        if 'qr_code' in st.session_state:
            st.divider()
            st.image(st.session_state.qr_code, caption="Scan with Authenticator App")
            
            otp = st.text_input("Enter 6-digit code", max_chars=6)
            if st.button("Verify & Activate"):
                try:
                    challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                    c_id = getattr(challenge, 'id', getattr(challenge, 'data', challenge).id)
                    
                    supabase.auth.mfa.verify({
                        "factor_id": st.session_state.mfa_id,
                        "challenge_id": c_id,
                        "code": otp
                    })
                    st.success("✅ MFA Activated!")
                    del st.session_state.qr_code
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
