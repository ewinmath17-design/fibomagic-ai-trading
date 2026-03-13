import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="FIBOMAGIC AI | Sniper Entry",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inisialisasi Session State untuk History Trading
if 'trading_history' not in st.session_state:
    st.session_state.trading_history = []

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #cbd5e1; }
    .metric-card { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .signal-buy { color: #34d399; font-weight: bold; background: rgba(52, 211, 153, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(52, 211, 153, 0.2); }
    .signal-sell { color: #fb7185; font-weight: bold; background: rgba(251, 113, 133, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(251, 113, 133, 0.2); }
    .signal-wait { color: #fbbf24; font-weight: bold; background: rgba(251, 191, 36, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(251, 191, 36, 0.2); }
    [data-testid="stDataFrame"] { background-color: #0f172a; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Fungsi Prompt (Versi Sniper Elite FX - Extreme Risk:Reward)
def get_prompt(timeframe):
    return f"""Anda adalah seorang Prop-Firm Trading Analyst profesional dengan spesialisasi pada teknik Smart Money Concepts (SMC) dan "Sniper Entry System" untuk instrumen XAUUSD (Gold) pada Timeframe {timeframe}. 

Tugas utama Anda adalah menganalisis gambar screenshot chart trading yang diberikan dan memberikan konfirmasi eksekusi (Signal) dengan tingkat presisi di atas 80% (High Win Rate) dan rasio Risk:Reward yang sangat ekstrem.

LAKUKAN ANALISIS BERDASARKAN 3 PARAMETER MUTLAK SNIPER (SMC):
1. Liquidity Sweep: Apakah terlihat adanya manipulasi harga yang menyapu area likuiditas (Stop Loss hunter) di level ekstrem sebelum harga berbalik?
2. Change of Character (CHoCH): Apakah ada tanda awal perubahan struktur yang sangat jelas dari Bearish ke Bullish (atau sebaliknya)?
3. Break of Structure (BOS): Apakah struktur harga telah berhasil menembus level kunci untuk mengonfirmasi tren baru?

PRINSIP SNIPER ENTRY:
- "Less frequency + More Precision + More Rewards". Jika 3 konfirmasi di atas TIDAK terlihat jelas, Anda WAJIB memberikan sinyal WAIT. Jangan memaksakan entry.
- Risk/Reward sangat ekstrem (target 1:10, 1:15, hingga 1:30). Ini membutuhkan "SNIPER ZONE" (Area Entry) yang sangat sempit dan Stop Loss yang sangat ketat.

ATURAN OUTPUT:
Berikan hasil analisis Anda HANYA dalam format terstruktur di bawah ini. Jangan tambahkan narasi pembuka atau penutup.

[ HASIL ANALISIS FIBOMAGIC AI ]
TIMEFRAME: {timeframe}
STATUS MARKET: [Uptrend / Downtrend / Sideways / Liquidity Sweep Detected]
KONFIRMASI SIGNAL: [STRONG BUY / STRONG SELL / WAIT FOR SETUP]

DETAIL EKSEKUSI:
- Entry Area: [Sebutkan rentang harga "SNIPER ZONE" yang sangat sempit di ekstrem Order Block]
- Stop Loss (SL): [Sebutkan titik harga SL yang SANGAT KETAT, tepat di luar Sniper Zone]
- Take Profit (TP): [Sebutkan titik harga "TP ZONE" yang jauh untuk rasio R:R ekstrem]

EVALUASI & DURASI:
- Evaluasi Setup: [Sebutkan kualitas setup, misal: Valid Sniper Setup, Win Rate 80% Potential, atau Invalid Setup]
- Durasi Validitas: [Sebutkan estimasi waktu valid]

ALASAN ENTRY (LOGIKA ANALISIS):
- [Analisis Liquidity Sweep & penentuan area Sniper Zone]
- [Analisis konfirmasi CHoCH / BOS]
- [Alasan penentuan SL ketat dan TP Zone ekstrem]
"""

# Fungsi Parsing Regex
def parse_result(text):
    def safe_extract(pattern, text, default="-"):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace('*', '').strip()
        return default

    status = safe_extract(r'STATUS MARKET:\s*(.*?)(?=\n|$)', text)
    signal = safe_extract(r'KONFIRMASI SIGNAL:\s*(.*?)(?=\n|$)', text)
    entry = safe_extract(r'Entry Area:\s*(.*?)(?=\n|$)', text)
    sl = safe_extract(r'Stop Loss \(SL\):\s*(.*?)(?=\n|$)', text)
    tp = safe_extract(r'Take Profit \(TP\):\s*(.*?)(?=\n|$)', text)
    evaluation = safe_extract(r'Evaluasi Setup:\s*(.*?)(?=\n|$)', text)
    duration = safe_extract(r'Durasi Validitas:\s*(.*?)(?=\n|$)', text)

    reasons_split = re.split(r'ALASAN ENTRY \(LOGIKA ANALISIS\):', text, flags=re.IGNORECASE)
    reasons = []
    if len(reasons_split) > 1:
        reasons_text = reasons_split[1].strip()
        reasons = [r.replace('-', '').replace('*', '').strip() for r in reasons_text.split('\n') if len(r.strip()) > 5]
    
    if not reasons:
        reasons = ["Menunggu konfirmasi validasi Sniper Entry System."]

    return {
        'status': status, 'signal': signal, 'entry': entry,
        'sl': sl, 'tp': tp, 'evaluation': evaluation,
        'duration': duration, 'reasons': reasons, 'raw': text
    }

# Header App
st.markdown("### ⚡ FIBOMAGIC **AI** | `SNIPER ENTRY SYSTEM`")
st.markdown("---")

# Layout Grid
col1, col2 = st.columns([4, 6], gap="large")

with col1:
    st.markdown("#### 🕒 Select Timeframe")
    timeframe = st.radio("Timeframe", options=['M1', 'M5', 'M15', 'M30', 'H1', 'H4'], horizontal=True, label_visibility="collapsed")
    
    st.markdown("#### 🖼️ Upload Chart")
    uploaded_file = st.file_uploader("Supports PNG, JPG, WEBP", type=['png', 'jpg', 'jpeg', 'webp'], label_visibility="collapsed")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Chart Ready for Analysis", use_container_width=True)
    
    analyze_btn = st.button("📈 Generate Sniper Signal", type="primary", use_container_width=True, disabled=not uploaded_file)

    st.markdown("---")
    st.markdown("**System Parameters**")
    st.caption(f"**Instrument:** XAUUSD (Gold)\n\n**Timeframe:** {timeframe}\n\n**Algorithm:** Prop-Firm SMC & Extreme Risk-Reward")

with col2:
    if analyze_btn and uploaded_file is not None:
        with st.spinner("🤖 Mendeteksi Sniper Zone & TP Zone Ekstrem..."):
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                
                safe_image = image.convert('RGB')
                valid_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                target_model = valid_models[0] if valid_models else None
                for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision']:
                    for vm in valid_models:
                        if preferred in vm:
                            target_model = vm
                            break
                    if target_model != valid_models[0]: 
                        break
                
                st.caption(f"*System Info: Menggunakan mesin AI `{target_model}`*")
                
                model = genai.GenerativeModel(target_model)
                prompt = get_prompt(timeframe)
                
                response = model.generate_content([prompt, safe_image])
                res = parse_result(response.text)
                
                sig_upper = res['signal'].upper()
                if "BUY" in sig_upper: sig_class = "signal-buy"
                elif "SELL" in sig_upper: sig_class = "signal-sell"
                else: sig_class = "signal-wait"

                # ---------------------------------------------------------
                # SIMPAN KE HISTORY
                # ---------------------------------------------------------
                history_entry = {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "TF": timeframe,
                    "Sinyal": res['signal'],
                    "Entry (Sniper Zone)": res['entry'],
                    "SL (Ketar)": res['sl'],
                    "TP (Extreme)": res['tp'],
                    "Status": res['status']
                }
                st.session_state.trading_history.insert(0, history_entry)

                # Tampilan UI Akhir
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 16px;">
                        <div>
                            <p style="color: #94a3b8; font-size: 12px; margin: 0;">MARKET STATUS</p>
                            <h3 style="margin: 0; color: #f8fafc;">{res['status']}</h3>
                        </div>
                        <div style="text-align: right;">
                            <p style="color: #94a3b8; font-size: 12px; margin: 0; margin-bottom: 4px;">CONFIRMATION SIGNAL</p>
                            <span class="{sig_class}">{res['signal']}</span>
                        </div>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px; font-weight: bold; margin-bottom: 8px;">🎯 SNIPER EXECUTION DETAILS</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Sniper Zone (Entry)</p>
                            <p style="font-size: 14px; color: #e2e8f0; font-family: monospace; margin: 0;">{res['entry']}</p>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Stop Loss (SL)</p>
                            <p style="font-size: 14px; color: #fb7185; font-family: monospace; margin: 0;">{res['sl']}</p>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">TP Zone</p>
                            <p style="font-size: 14px; color: #34d399; font-family: monospace; margin: 0;">{res['tp']}</p>
                        </div>
                    </div>
                    <p style="color: #94a3b8; font-size: 14px; font-weight: bold; margin-bottom: 8px;">⏱️ EVALUATION & VALIDITY</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                        <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Setup Eval</p>
                            <p style="font-size: 13px; color: #cbd5e1; margin: 0;">{res['evaluation']}</p>
                        </div>
                        <div style="background: #0f172a; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Valid Duration</p>
                            <p style="font-size: 13px; color: #cbd5e1; margin: 0;">{res['duration']}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**🧠 Logika Sniper (SMC Analysis):**")
                for reason in res['reasons']:
                    st.markdown(f"- {reason}")
                    
            except Exception as e:
                st.error(f"Sistem Gagal Mengeksekusi: {str(e)}")
    elif not analyze_btn:
        st.info("👈 Silakan pilih timeframe, unggah screenshot chart XAUUSD Anda di panel kiri, lalu klik 'Generate Sniper Signal'.")

# ---------------------------------------------------------
# RENDER HISTORY TRADING (DI BAWAH KEDUA KOLOM)
# ---------------------------------------------------------
if st.session_state.trading_history:
    st.markdown("---")
    st.markdown("### 📚 Trading Journal History")
    st.caption("Riwayat analisis Anda selama sesi ini berjalan. Data akan hilang jika halaman di-refresh.")
    
    df_history = pd.DataFrame(st.session_state.trading_history)
    st.dataframe(
        df_history, 
        use_container_width=True, 
        hide_index=True
    )
