import time # Add this at the top

# --- 1. CONFIGURATION ---
# (Keep your existing URL/KEY/Secrets)

# Initialize Session States with a Timestamp
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_time' not in st.session_state:
    st.session_state.auth_time = 0  # To track when they logged in

# --- SESSION TIMEOUT LOGIC ---
def check_session_timeout():
    # Set timeout period (e.g., 30 minutes)
    TIMEOUT_SECONDS = 30 * 60 
    
    if st.session_state.authenticated:
        current_time = time.time()
        elapsed_time = current_time - st.session_state.auth_time
        
        if elapsed_time > TIMEOUT_SECONDS:
            # Session expired - Clear everything
            st.session_state.authenticated = False
            st.session_state.access_token = None
            st.session_state.auth_time = 0
            st.warning("⏱️ Session expired for security. Please log in again.")
            st.rerun()

# --- 2. AUTHENTICATION SYSTEM UPDATE ---
def secure_auth_system():
    # ... (Your existing email/pass UI)
    if st.button("Log In"):
        # ... (Your login logic)
        if res.session:
            st.session_state.auth_time = time.time() # Start the clock here!
            # ... rest of login
