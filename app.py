import streamlit as st
import requests
import time

# --- CONFIGURATION ---
# Replace placeholders with your real API credentials securely
API_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum"
API_KEY = "MBYY0FBSBFC"

# --- PAGE SETUP ---
st.set_page_config(page_title="SMS Activation Panel", page_icon="📱", layout="centered")

st.title("📱 Instant SMS Activation Panel")
st.write("Get temporary virtual numbers and receive OTP verifications instantly.")
st.divider()

# Initialize session states to track active orders across user interactions
if "active_number" not in st.session_state:
    st.session_state.active_number = None
if "active_order_id" not in st.session_state:
    st.session_state.active_order_id = None
if "current_otp" not in st.session_state:
    st.session_state.current_otp = "Waiting for OTP..."

# --- STEP 1: REQUEST A NUMBER ---
st.header("1. Request a Virtual Number")

# Dropdown for selecting target platforms
service = st.selectbox(
    "Select the application you want to verify:",
    ["WhatsApp", "Facebook", "Instagram", "Telegram", "Google"]
)

if st.button("Generate Number", type="primary"):
    with st.spinner("Communicating with the API server..."):
        try:
            # Preparing the query payload required by your provider's API structure
            payload = {
                "key": API_KEY,
                "service": service.lower(),
                "action": "getNumber"
            }
            
            # Sending request to your MauthAPI endpoint
            response = requests.get(API_URL, params=payload, timeout=10)
            data = response.json()
            
            # Standard parsing structure (adjust keys depending on your API's exact output JSON)
            if response.status_code == 200 and data.get("status") == "success":
                st.session_state.active_number = data.get("number")
                st.session_state.active_order_id = data.get("id")
                st.session_state.current_otp = "Waiting for OTP..."
                st.success(f"Number successfully allocated!")
            else:
                st.error(f"API Error: {data.get('message', 'Failed to fetch number.')}")
                
        except Exception as e:
            st.error(f"Failed to connect to the authentication server: {str(e)}")

# Display current active number if one exists
if st.session_state.active_number:
    st.info(f"**Your Active Number:** `{st.session_state.active_number}`")
    st.caption("Copy this number into your app setup screen, then proceed below.")

st.divider()

# --- STEP 2: RECEIVE THE OTP ---
st.header("2. Verification Status")

if not st.session_state.active_number:
    st.warning("Please generate a phone number first to listen for incoming OTP codes.")
else:
    st.write(f"Monitoring incoming messages for ID: `{st.session_state.active_order_id}`")
    
    # Display the current status block
    st.code(st.session_state.current_otp, language="text")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh OTP Status"):
            with st.spinner("Checking SMS logs..."):
                try:
                    # Update parameters to query the OTP status for the specific order ID
                    status_payload = {
                        "key": API_KEY,
                        "action": "getStatus",
                        "id": st.session_state.active_order_id
                    }
                    
                    response = requests.get(API_URL, params=status_payload, timeout=10)
                    data = response.json()
                    
                    if data.get("status") == "STATUS_OK":
                        st.session_state.current_otp = f"YOUR OTP CODE IS: {data.get('otp')}"
                        st.balloons()
                    elif data.get("status") == "STATUS_WAITING":
                        st.toast("No SMS received yet. Keep waiting or try resending from the app.")
                    else:
                        st.session_state.current_otp = data.get("message", "Session expired or canceled.")
                        
                except Exception as e:
                    st.error(f"Error checking status: {str(e)}")
                    
    with col2:
        if st.button("❌ Cancel / Release Number", type="secondary"):
            # Clean app state variables to allow picking a new number
            st.session_state.active_number = None
            st.session_state.active_order_id = None
            st.session_state.current_otp = "Waiting for OTP..."
            st.rerun()
  
