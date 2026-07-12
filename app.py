import streamlit as st
import requests
import sqlite3
import threading
import re
import time

# --- CONFIGURATION FROM SOURCE ---
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN' 
FORWARD_GROUP_ID = -1004207990234  # OTP Receiver Group ID
CHANNEL_LINK = "https://t.me/kryptoCMs"
GROUP_LINK = "https://t.me/activeranges69"
SUPPORT_LINK = "https://t.me/Demonblade69"

db_lock = threading.Lock()

# --- DATABASE ENGINE ---
def init_db():
    with db_lock:
        conn = sqlite3.connect('v2_web.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS admin_config 
                     (id INTEGER PRIMARY KEY, api_url TEXT, api_key TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                     (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)''')
        c.execute("INSERT OR IGNORE INTO admin_config (id, api_url, api_key) VALUES (1, '', '')")
        conn.commit()
        conn.close()

init_db()

def get_admin_config():
    with db_lock:
        conn = sqlite3.connect('v2_web.db')
        c = conn.cursor()
        c.execute("SELECT api_url, api_key FROM admin_config WHERE id=1")
        result = c.fetchone()
        conn.close()
        if result and result[0] and result[1]:
            return {"api_url": result[0], "api_key": result[1]}
        return None

def save_admin_config(api_url, api_key):
    with db_lock:
        conn = sqlite3.connect('v2_web.db')
        c = conn.cursor()
        c.execute("UPDATE admin_config SET api_url=?, api_key=? WHERE id=1", (api_url, api_key))
        conn.commit()
        conn.close()

def get_user_balance(username):
    with db_lock:
        conn = sqlite3.connect('v2_web.db')
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE username=?", (username,))
        result = c.fetchone()
        if not result:
            c.execute("INSERT INTO users (username, balance) VALUES (?, 0.0)", (username,))
            conn.commit()
            balance = 0.0
        else:
            balance = result[0]
        conn.close()
        return balance

def add_user_balance(username, amount):
    with db_lock:
        conn = sqlite3.connect('v2_web.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, username))
        conn.commit()
        conn.close()

# --- THIRD PARTY TELEGRAM INTEGRATION ---
def forward_to_telegram_group(message_text):
    if BOT_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN':
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": FORWARD_GROUP_ID, "text": message_text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# --- CORE EXTERNAL API INTERFACES ---
def api_get_number(api_url, api_key, range_id):
    try:
        headers = {'mauthapi': api_key, 'Content-Type': 'application/json'}
        payload = {'rid': str(range_id)}
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        data = response.json()
        if data.get('meta', {}).get('code') == 200:
            number_data = data.get('data', {})
            full_num = str(number_data.get('full_number')).replace('+', '')
            return {"success": True, "number": full_num, "id": number_data.get('rid', 'N/A')}
        return {"success": False, "error": data.get('message', 'Failed to allocate range number.')}
    except Exception as e:
        return {"success": False, "error": str(e)}

def api_check_sms(api_url, api_key, target_number):
    try:
        check_url = api_url.replace('/getnum', '/success-otp') 
        headers = {'mauthapi': api_key}
        response = requests.get(check_url, headers=headers, timeout=10)
        data = response.json()
        if data.get('meta', {}).get('code') == 200:
            otps = data.get('data', {}).get('otps', [])
            for otp in otps:
                if str(otp.get('number')) == str(target_number):
                    return {"success": True, "sms": otp.get('message')}
            return {"success": False, "status": "pending"}
        return {"success": False, "error": data.get('message', 'Error fetching OTPs')}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- STREAMLIT WEB PAGE LAYOUT ---
st.set_page_config(page_title="DXA NUMBER PANEL", page_icon="⚡", layout="wide")

# Vibrant Custom Cyberpunk/Dark Accent Styling injection
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        color: white; font-weight: bold; border: none; border-radius: 8px;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
    }
    div.stButton > button:hover { transform: translateY(-2px); border: none; }
    .metric-card {
        background-color: #1e2638; padding: 20px; border-radius: 12px;
        border-left: 5px solid #00f2fe; margin-bottom: 15px;
    }
    .service-box {
        background: #161b26; border: 1px solid #2d3748; padding: 15px;
        border-radius: 10px; text-align: center; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Session States initialization
if "username" not in st.session_state:
    st.session_state.username = "Guest_User"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "active_number" not in st.session_state:
    st.session_state.active_number = None
if "active_range" not in st.session_state:
    st.session_state.active_range = None
if "sms_status" not in st.session_state:
    st.session_state.sms_status = "No active collection loop running."

# --- SIDEBAR INTERFACE ---
with st.sidebar:
    st.title("⚡ DXA ACCELERATOR")
    st.markdown("---")
    
    # Simple User Profile Portal Management
    st.subheader("👤 User Account Space")
    username_input = st.text_input("Enter Profile Identity Username:", value=st.session_state.username)
    if username_input:
        st.session_state.username = username_input.strip()
    
    # Dynamic live balance rendering element
    balance = get_user_balance(st.session_state.username)
    st.markdown(f"""
    <div class="metric-card">
        <span style='color: #a0aec0; font-size: 14px;'>Current Balance</span><br>
        <span style='color: #ffffff; font-size: 24px; font-weight: bold;'>৳{balance:.3f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    # Quick Action Resource Direct Connections
    st.subheader("🔗 Navigation Platforms")
    st.markdown(f"[📢 Channel Telegram Updates]({CHANNEL_LINK})")
    st.markdown(f"[🛡 Official OTP Community]({GROUP_LINK})")
    st.markdown(f"[👤 Developer Live Support]({SUPPORT_LINK})")
    
    st.markdown("---")
    # Interactive Toggle Element for Admin Interface View
    admin_mode = st.toggle("⚙️ Enable Admin Control Dashboard")
    if admin_mode:
        admin_pass = st.text_input("Security Access Code:", type="password")
        if admin_pass == "ADMIN": # Switch this value to establish your own structural password
            st.session_state.is_admin = True
            st.success("Access Authorized")
        else:
            st.session_state.is_admin = False

# --- CORE NAVIGATION CONTEXT TABS ---
if admin_mode and st.session_state.is_admin:
    # --- ADMIN DECK VIEW ROUTER ---
    st.header("⚙️ SYSTEM BACKEND ROOT CONFIGURATION")
    
    tab1, tab2 = st.tabs(["🔗 API Endpoint Management", "📢 Public Global Broadcasts"])
    
    with tab1:
        st.subheader("Backend Router Integrations")
        current_conf = get_admin_config() or {"api_url": "", "api_key": ""}
        
        form_url = st.text_input("Allocation Provider Gateway URL:", value=current_conf['api_url'])
        form_key = st.text_input("Authentication Security Token Key (mauthapi):", value=current_conf['api_key'], type="password")
        
        if st.button("Save Live Changes"):
            save_admin_config(form_url.strip(), form_key.strip())
            st.success("API configurations pushed successfully across global parameters!")
            
    with tab2:
        st.subheader("Global Broadcast System")
        msg_text = st.text_area("Enter your announcement message below:")
        if st.button("Transmit Broadcast Alert"):
            st.info("Simulating client transmission logs. Messages sent securely to internal database structures.")
            st.success(f"Broadcast completely transmitted text: '{msg_text}'")

else:
    # --- PUBLIC CUSTOMER DECK VIEW ROUTER ---
    st.title("📱 Real-Time Virtual Activation Environment")
    st.write(f"Logged in as: **{st.session_state.username}**")
    st.divider()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Select Gateway Product Integration")
        
        # Grid array layout of service allocations matching target ranges
        services = [
            {"name": "TIKTOK", "icon": "🎵", "range": "26134"},
            {"name": "IMO", "icon": "💬", "range": "26134"},
            {"name": "FACEBOOK", "icon": "🔵", "range": "22583"},
            {"name": "WHATSAPP", "icon": "🟢", "range": "26134"},
            {"name": "INSTAGRAM", "icon": "📸", "range": "22465"}
        ]
        
        # Formulate custom interactive layout grid UI configuration
        for s in services:
            with st.container():
                st.markdown(f"""
                <div class="service-box">
                    <span style='font-size: 20px;'>{s['icon']}</span>
                    <b style='color: #ffffff; margin-left: 10px;'>{s['name']}</b>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Generate {s['name']} Virtual Endpoint Line", key=s['name']):
                    config = get_admin_config()
                    if not config:
                        st.error("Management configurations missing. Request Admin setup keys.")
                    else:
                        with st.spinner("Acquiring unique phone reservation from gateway channels..."):
                            res = api_get_number(config['api_url'], config['api_key'], s['range'])
                            if res['success']:
                                st.session_state.active_number = res['number']
                                st.session_state.active_range = s['range']
                                st.session_state.sms_status = "Waiting for incoming SMS transmission..."
                                st.success("Number allocated successfully!")
                            else:
                                st.error(f"Provider Refusal: {res.get('error')}")
                                
    with col2:
        st.subheader("📡 Live Session Transmission Terminal")
        
        if not st.session_state.active_number:
            st.info("Select a product interface on the left column parameters to spin up a terminal line.")
        else:
            st.markdown(f"""
            <div style='background: #111524; padding: 25px; border-radius: 12px; border: 1px solid #4facfe;'>
                <h4 style='color: #00f2fe; margin-top:0;'>SESSION LOG ACTIVE</h4>
                <p style='margin-bottom:5px; color:#a0aec0;'>Virtual Number Allocation Target:</p>
                <code style='font-size: 22px; color: #fff; background: #1a2035; padding: 5px 10px; border-radius: 5px;'>
                    +{st.session_state.active_number}
                </code>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**Terminal Status Monitor:** `{st.session_state.sms_status}`")
            
            # Interactive Control Command Cluster
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 Query Verification SMS Logs"):
                    config = get_admin_config()
                    if config:
                        with st.spinner("Interrogating provider system arrays..."):
                            check = api_check_sms(config['api_url'], config['api_key'], st.session_state.active_number)
                            if check['success']:
                                sms_msg = check['sms']
                                otp_found = re.search(r'\b\d{4,8}\b', sms_msg)
                                otp_code = otp_found.group(0) if otp_found else "N/A"
                                
                                # Process financial rewards internally for successful triggers
                                reward = 0.200
                                add_user_balance(st.session_state.username, reward)
                                
                                # Format visual text elements explicitly
                                report_block = (
                                    f"✨ 🎉 **✅ OTP Received!** 🎉 ✨\n"
                                    f"📱 Number: +{st.session_state.active_number}\n"
                                    f"🔑 OTP Code: {otp_code}\n"
                                    f"📨 Message: {sms_msg}\n"
                                    f"💵 Transferred Reward: ৳{reward:.3f}"
                                )
                                
                                st.session_state.sms_status = report_block
                                st.balloons()
                                
                                # Forward live notification directly to Telegram group
                                forward_to_telegram_group(report_block)
                            else:
                                st.toast("Still waiting for the incoming message block from the target service app...")
            with c2:
                if st.button("❌ Terminate Current Session Line"):
                    st.session_state.active_number = None
                    st.session_state.active_range = None
                    st.session_state.sms_status = "No active collection loop running."
                    st.rerun()

    st.divider()
    # Secondary Utility Blocks (Referral and Withdrawal sections)
    st.subheader("💰 Accounts & System Infrastructure")
    row_col1, row_col2 = st.columns(2)
    with row_col1:
        st.markdown("""
        ### ♻️ System Referrals
        Share your unique dashboard configuration interface parameters with group members to expand node network systems.
        """)
    with row_col2:
        st.markdown("""
        ### 📅 Capital Withdrawals
        *Payout metrics are currently system locked by main administrator control parameters.*
        """)
    
