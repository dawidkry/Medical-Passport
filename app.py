import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Log In", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.session:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
            except Exception as e:
                st.error(f"Login Error: {e}")
                
    with col2:
        if st.button("Register New Account", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("Registration sent! Check email/Supabase to confirm.")
            except Exception as e:
                st.error(f"Signup Error: {e}")

# --- 3. CLINICAL DASHBOARD ---
def main_dashboard():
    st.sidebar.title("🧭 Navigation")
    st.sidebar.write(f"Logged in: **{st.session_state.user_email}**")
    
    # Check session health on every load
    current_session = None
    try:
        session_res = supabase.auth.get_session()
        current_session = session_res.session if session_res else None
    except:
        pass

    page = st.sidebar.radio("Go to", ["Dashboard", "Account Security"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.authenticated = False
        st.session_state.user_email = ""
        st.rerun()

    if page == "Dashboard":
        st.title("🩺 Professional Medical Passport")
        st.info("Your clinical portfolio is secured.")
        # Add your CV content here later

    elif page == "Account Security":
        st.title("🛡️ MFA Setup")
        
        if not current_session:
            st.warning("⚠️ Session token is stale. Please Log Out and back in to refresh.")
            return

        # Self-Healing: Check for 'ghost' factors
        try:
            factors_res = supabase.auth.mfa.list_factors()
            factors = getattr(factors_res, 'all', [])
            if factors:
                st.info(f"Existing Factor: {factors[0].friendly_name}")
                if st.button("Reset / Unenroll"):
                    supabase.auth.mfa.unenroll(factors[0].id)
                    st.rerun()
        except:
            pass

        if st.button("Generate 2FA QR Code"):
            try:
                # Dict-style params for modern Supabase library
                enroll = supabase.auth.mfa.enroll({
                    "factor_type": "totp",
                    "friendly_name": f"MedPassport-{st.session_state.user_email[:5]}"
                })
                st.session_state.mfa_id = enroll.id
                st.session_state.qr_code = enroll.totp.qr_code
                st.rerun()
            except Exception as e:
                st.error(f"Security Error: {e}")

        if 'qr_code' in st.session_state:
            st.divider()
            st.write("1. Scan this with Microsoft Authenticator:")
            st.image(st.session_state.qr_code)
            
            otp = st.text_input("2. Enter 6-digit code from phone", max_chars=6)
            if st.button("Verify & Activate"):
                try:
                    challenge = supabase.auth.mfa.challenge(st.session_state.mfa_id)
                    supabase.auth.mfa.verify({
                        "factor_id": st.session_state.mfa_id,
                        "challenge_id": challenge.id,
                        "code": otp
                    })
                    st.success("✅ MFA Fully Activated!")
                    del st.session_state.qr_code
                except Exception as e:
                    st.error(f"Verification Failed: {e}")

# --- 4. EXECUTION ---
if not st.session_state.authenticated:
    secure_auth_system()
else:
    main_dashboard()
