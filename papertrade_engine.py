
import datetime
import os
import time
import numpy as np
import pandas as pd
import pyotp
import streamlit as st
from SmartApi import SmartConnect

# 💻 एडवांस प्रो वेब पेज सेटिंग्स
st.set_page_config(
    page_title="पेपर ट्रेड प्रो v14.0", page_icon="📝", layout="wide"
)

# 🔄 404 Connection Drop Protection Matrix
st.markdown(
    """
    <script>
    const checkAndReload = () => {
        if (document.querySelector('h1') === null && document.readyState === 'complete') {
            window.location.reload();
        }
    };
    setInterval(checkAndReload, 2000);
    </script>
    """,
    unsafe_allow_html=True
)

st.title("📝 ज़ीरो-हीरो पेपर ट्रेड प्रो v14.0")
st.markdown("##### (CSV Storage Lock Engine 🔒 - Screen Reset-Proof Paper Trading)")
st.markdown("---")

# CSV File Path setup for Render Persistence
CSV_FILE_PATH = "saved_paper_trades.csv"

def load_permanent_trades():
    if os.path.exists(CSV_FILE_PATH):
        try:
            return pd.read_csv(CSV_FILE_PATH).to_dict(orient="records")
        except:
            return []
    return []

def save_trade_permanently(trade_record):
    trades = load_permanent_trades()
    trades.append(trade_record)
    df = pd.DataFrame(trades)
    df.to_csv(CSV_FILE_PATH, index=False)

# 🚨 साइडबार क्रेडेंशियल्स कंट्रोल्स
st.sidebar.markdown("### 🔑 एन्जिलワン API क्रेडेंशियल्स")
API_KEY = "uqURH60N"  
CLIENT_ID = st.sidebar.text_input("Angel Client ID:", type="default", value="G62352248")
PASSWORD = st.sidebar.text_input("Angel Password / MPIN:", type="password", value="")
TOTP_SECRET = st.sidebar.text_input("Angel TOTP Secret Key:", type="password", value="")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Tactical Confluence Matrix")
TARGET_POINTS = st.sidebar.slider("🎯 मैथ जैकपॉट (Pts):", min_value=15, max_value=60, value=35)
ATR_MULTIPLIER = st.sidebar.slider("🛡️ ATR एसएल आईपीएल:", min_value=1.5, max_value=3.5, value=2.8, step=0.1)

# 🔑 HARD STATE MANAGEMENT
if "price_history" not in st.session_state: st.session_state.price_history = []
if "high_history" not in st.session_state: st.session_state.high_history = []
if "low_history" not in st.session_state: st.session_state.low_history = []
if "volume_history" not in st.session_state: st.session_state.volume_history = []
if "active_position" not in st.session_state: st.session_state.active_position = None
if "last_valid_price" not in st.session_state: st.session_state.last_valid_price = 24000.00
if "last_trade_time" not in st.session_state: st.session_state.last_trade_time = datetime.datetime.min
if "obj" not in st.session_state: st.session_state.obj = None

# Load permanent history from CSV into session memory if available
permanent_records = load_permanent_trades()

# Containers Layout
metric_container = st.container()
capital_container = st.container()
control_container = st.container()
pos_container = st.container()
history_container = st.container()

def calculate_confluence_metrics(prices, highs, lows, volumes):
    min_len = 35
    p_base = prices[-1] if len(prices) > 0 else st.session_state.last_valid_price
    
    temp_prices = list(prices) + [p_base] * (min_len - len(prices)) if len(prices) < min_len else list(prices)
    temp_highs = list(highs) + [p_base + 1.5] * (min_len - len(highs)) if len(highs) < min_len else list(highs)
    temp_lows = list(lows) + [p_base - 1.5] * (min_len - len(lows)) if len(lows) < min_len else list(lows)
    temp_vols = list(volumes) + [5000] * (min_len - len(volumes)) if len(volumes) < min_len else list(volumes)

    df = pd.DataFrame({"Close": temp_prices, "High": temp_highs, "Low": temp_lows, "Volume": temp_vols})
    
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["Supply_Zone"] = df["High"].rolling(15, min_periods=1).max()
    df["Demand_Zone"] = df["Low"].rolling(15, min_periods=1).min()
    df["Avg_Volume"] = df["Volume"].rolling(20, min_periods=1).mean()
    df["ATR"] = (df["High"] - df["Low"]).rolling(14, min_periods=1).mean().fillna(1.2)
    return df

# Live Data Pipeline
live_price = st.session_state.last_valid_price
connection_status, angel_success = "🔒 क्रेडेंशियल्स का इंतजार...", False

if CLIENT_ID and PASSWORD and TOTP_SECRET:
    try:
        if st.session_state.obj is None:
            obj = SmartConnect(api_key=API_KEY)
            token = pyotp.TOTP(TOTP_SECRET).now()
            data = obj.generateSession(CLIENT_ID, PASSWORD, token)
            if data["status"]: st.session_state.obj = obj

        if st.session_state.obj is not None:
            response = st.session_state.obj.ltpData("NSE", "Nifty 50", "99926000")
            if response["status"] and response.get("data"):
                live_price = float(response["data"]["ltp"])
                st.session_state.last_valid_price = live_price
                connection_status, angel_success = "🟢 ANGEL LIVE Engine Active", True
    except:
        st.session_state.obj = None

if not angel_success:
    try:
        import requests
        res = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d", headers={"User-Agent": "Mozilla/5.0"}, timeout=2).json()
        if "chart" in res and res["chart"]["result"]:
            live_price = float(res["chart"]["result"][0]["meta"]["regularMarketPrice"])
            st.session_state.last_valid_price = live_price
            connection_status = "⚠️ याहू LIVE बैकअप एक्टिव 🔄"
            angel_success = True
    except: pass

if len(st.session_state.price_history) == 0 or st.session_state.price_history[-1] != live_price:
    st.session_state.price_history.append(live_price)
    st.session_state.high_history.append(live_price + 1.2)
    st.session_state.low_history.append(live_price - 1.2)
    st.session_state.volume_history.append(5500)
    if len(st.session_state.price_history) > 100:
        st.session_state.price_history.pop(0)
        st.session_state.high_history.pop(0)
        st.session_state.low_history.pop(0)
        st.session_state.volume_history.pop(0)

df_calc = calculate_confluence_metrics(st.session_state.price_history, st.session_state.high_history, st.session_state.low_history, st.session_state.volume_history)

ema_50 = round(df_calc["EMA50"].iloc[-1], 2)
supply_level = round(df_calc["Supply_Zone"].iloc[-1], 2)
demand_level = round(df_calc["Demand_Zone"].iloc[-1], 2)
high_volume_node = df_calc["Volume"].iloc[-1] > df_calc["Avg_Volume"].iloc[-1]

with control_container:
    bot_active = st.toggle("⚡ ACTIVATE ALGO ENGINE (लाइव कंबाइंड स्कैनिंग स्विच ऑन करें)", value=st.session_state.get("bot_active", False))
    st.session_state.bot_active = bot_active

with metric_container:
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    bot_status = "⚡ Velocity Paper Trading Scan LIVE..." if st.session_state.bot_active else "💤 Algo बंद है (STOPPED)"
    col1.metric(label=f"📝 PAPER MATRIX | {connection_status}", value=f"₹ {live_price}", delta=f"EMA50: {ema_50} | {bot_status}")
    total_pnl = sum([float(t.get("P&L (₹)", 0)) for t in permanent_records])
    col2.metric("💰 कुल परमानेंट P&L (₹)", f"₹ {round(total_pnl, 2)}")
    col3.metric("🟢 WIN TRADES", f"{len([t for t in permanent_records if float(t.get('P&L (₹)', 0)) > 0])}")
    col4.metric("🔴 LOSS TRADES", f"{len([t for t in permanent_records if float(t.get('P&L (₹)', 0)) < 0])}")

with capital_container:
    st.markdown("### 💰 लाइव trading एवं कंबाइंड क्वांटिटी कॉन्फ़िगरेशन")
    cc1, cc2, cc3, cc4 = st.columns(4)
    qty_mode = cc1.radio("📐 मोड चुनें:", ["ऑतो-कैपिटल लोड", "मैनुअल लॉट ओवरराइड"])
    TEST_AMOUNT = cc2.number_input("टेस्टिंग अमाउंट (₹):", value=10000, step=1000)
    AVG_PREMIUM = cc3.number_input("औसत ऑप्शन प्रीमियम prijs (₹):", value=100, step=10)
    
    if qty_mode == "ऑतो-कैपिटल लोड":
        FINAL_QTY = (int(TEST_AMOUNT // (AVG_PREMIUM * 25))) * 25
        MANUAL_LOTS = FINAL_QTY // 25
        cc4.number_input("मैनुअल लॉट साइज दर्ज करें:", value=int(MANUAL_LOTS), disabled=True)
    else:
        MANUAL_LOTS = cc4.number_input("मैनुअल लॉट साइज दर्ज करें:", value=4, min_value=1, step=1)
        FINAL_QTY = int(MANUAL_LOTS * 25)

    price_change_velocity = 0.0
    if len(st.session_state.price_history) > 2:
        price_change_velocity = round(live_price - st.session_state.price_history[-2], 2)
    st.info(f"📊 **Storage Locked Tracker:** Velocity: {price_change_velocity} Pts | CSV File Sync Active ✅")

st.markdown("---")

with pos_container:
    if st.session_state.active_position:
        pos = st.session_state.active_position
        is_pe = pos["type"] == "PE"
        pnl_pts = (pos["entry"] - live_price) if is_pe else (live_price - pos["entry"])
        pnl_rupees = round(pnl_pts * pos["qty"], 2)
        
        if pnl_pts >= 10.0 and pos.get("stage", 0) == 0:
            pos["sl"] = pos["entry"]
            pos["stage"] = 1
            
        bg_color = "#e74c3c" if is_pe else "#2ecc71"
        pnl_color = "#ff4d4d" if pnl_rupees < 0 else "#2ecc71"
        
        st.markdown(f"""
        <div style='background-color: #111111; padding: 20px; border-radius: 12px; border-left: 6px solid {bg_color}; margin-top: 15px;'>
            <h3 style='margin:0 0 10px 0; color: #ffffff;'>💼 एक्टिव पेपर पोजीशन: <span style='color: {bg_color}; font-weight: bold;'>{pos['strike']}</span></h3>
            <p style='margin: 5px 0; color: #ffffff;'>📥 <b>एंट्री PRICE:</b> <span style='color: #f1c40f;'>₹ {round(pos['entry'], 2)}</span> | 🛡️ <b>लाइव एसएल:</b> <span style='color: #ff4757;'>₹ {round(pos['sl'], 2)}</span></p>
            <h2 style='margin: 10px 0 0 0; color: {pnl_color}; font-weight: bold;'>लाइव P&L: ₹ {pnl_rupees} ({round(pnl_pts, 2)} Pts)</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if pnl_pts >= TARGET_POINTS or (live_price >= pos["sl"] if is_pe else live_price <= pos["sl"]):
            new_record = {
                "Time": datetime.datetime.now().strftime("%H:%M:%S"), "Strike Price": pos["strike"],
                "Quantity": pos["qty"], "Entry": pos["entry"], "Exit": live_price,
                "P&L (₹)": pnl_rupees, "Status": "🎯 TARGET HIT" if pnl_pts >= TARGET_POINTS else "🛡️ SL HIT"
            }
            save_trade_permanently(new_record)
            st.session_state.active_position = None
            st.session_state.last_trade_time = datetime.datetime.now()
            st.rerun()
    else:
        if st.session_state.bot_active:
            time_since_last_trade = (datetime.datetime.now() - st.session_state.last_trade_time).total_seconds()
            if time_since_last_trade < 30:
                st.warning(f"⏳ कूलडाउन सुरक्षा एक्टिव है... {int(30 - time_since_last_trade)} सेकंड प्रतीक्षा करें।")
            else:
                strike_round = int(round(live_price / 50.0) * 50)
                qty = FINAL_QTY if FINAL_QTY > 0 else 25
                
                # 🟢 CALL ENTRY (Breakout OR Velocity Burst)
                if (live_price > ema_50 and live_price > supply_level) or (price_change_velocity >= 15.0 and high_volume_node):
                    st.session_state.active_position = {
                        "type": "CE", "strike": f"NIFTY {strike_round} CE", "qty": qty, 
                        "entry": live_price, "sl": live_price - 12.0, "stage": 0, "strat": "Velocity CE Burst"
                    }
                    st.rerun()
                        
                # 🔴 PUT ENTRY (Breakdown OR Velocity Crash)
                elif (live_price < ema_50 and live_price < demand_level) or (price_change_velocity <= -15.0 and high_volume_node):
                    st.session_state.active_position = {
                        "type": "PE", "strike": f"NIFTY {strike_round} PE", "qty": qty, 
                        "entry": live_price, "sl": live_price + 12.0, "stage": 0, "strat": "Velocity PE Crash"
                    }
                    st.rerun()
        else:
            st.info("💤 सिस्टम अभी स्टैंडबाय मोड पर शांत बैठा है भाई। स्कैनिंग शुरू करने के लिए स्विच ON कर दीजिए!")

with history_container:
    if permanent_records:
        st.subheader("📜 कम्पलीट कंबाइंड परमानेंट पेपर ट्रेड LOG (CSV-Backed)")
        st.dataframe(pd.DataFrame(permanent_records), use_container_width=True)

time.sleep(3)
st.rerun()
