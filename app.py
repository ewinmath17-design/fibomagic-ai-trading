import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="FIBOMAGIC AI | Ultimate SMC",
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

# Fungsi Prompt (Versi Ultimate SMC + FVG + Smart TP 3 Tingkat)
def get_prompt(timeframe):
    return f"""Anda adalah seorang Prop-Firm Trading Analyst profesional dengan spesialisasi pada teknik Advanced Smart Money Concepts (SMC) untuk instrumen XAUUSD (Gold) pada Timeframe {timeframe}. 

Tugas utama Anda adalah menganalisis gambar screenshot chart trading yang diberikan dan memberikan konfirmasi eksekusi (Signal) dengan tingkat presisi tinggi layaknya indikator algoritma premium.

LAKUKAN ANALISIS BERDASARKAN 5 PARAMETER MUTLAK SMC BERIKUT:
1. Fair Value Gap (FVG) / Imbalance: Deteksi apakah ada area FVG yang belum terisi yang berpotensi menjadi magnet harga sebelum melanjutkan tren.
2. Liquidity Sweep & EQH/EQL ($$$): Identifikasi apakah ada Equal Highs/Lows yang bertindak sebagai kolam likuiditas, atau apakah Wick Sweep sudah terjadi di area tersebut.
3. Multi-Timeframe Levels: Perhatikan apakah harga sedang berinteraksi dengan level kunci seperti Previous Day High/Low (PDH/PDL) atau Previous Week High/Low (PWH/PWL).
4. Change of Character (CHoCH) & Break of Structure (BOS): Konfirmasi perubahan struktur tren yang valid.
5. Order Block (OB): Tentukan area Supply & Demand yang menjadi "Sniper Zone" untuk titik entry.

ATURAN OUTPUT:
Berikan hasil analisis Anda HANYA dalam format terstruktur di bawah ini. Jangan tambahkan narasi pembuka atau penutup.

[ HASIL ANALISIS FIBOMAGIC AI ]
TIMEFRAME: {timeframe}
STATUS MARKET: [Uptrend / Downtrend / Sideways / FVG Fill / Liquidity Sweep]
KONFIRMASI SIGNAL: [STRONG BUY / STRONG SELL / WAIT FOR CONFLUENCE]

DETAIL EKSEKUSI (SMART LOGIC):
- Entry Area: [Sebutkan rentang harga "Sniper Zone" di area OB atau FVG]
- Stop Loss (SL): [Sebutkan titik harga SL ketat di luar struktur]
- Take Profit 1 (TP1): [Sebutkan TP1 terdekat untuk amankan modal (+50 pips)]
- Take Profit 2 (TP2): [Sebutkan TP2 menengah (+100 pips)]
- Take Profit 3 (TP3): [Sebutkan TP3 maksimal untuk rasio ekstrem (+150 pips atau lebih)]

EVALUASI & DURASI:
- Evaluasi Setup: [Sebutkan kualitas setup. Tambahkan instruksi: "Geser SL ke Break Even jika TP1 hit"]
- Durasi Validitas: [Sebutkan estimasi waktu valid]

ALASAN ENTRY (LOGIKA ANALISIS):
- [Analisis FVG, EQH/EQL, atau PDH/PDL yang terlihat]
- [Analisis konfirmasi CHoCH / BOS dan reaksi di Order Block]
- [Alasan penentuan SL dan strategi partial Take Profit]
"""

# Fungsi Parsing Regex (Diperbarui untuk 3 Tingkat TP)
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
    
    # Ekstraksi TP Bertingkat
    tp1 = safe_extract(r'Take Profit 1 \(TP1\):\s*(.*?)(?=\n|$)', text)
    tp2 = safe_extract(r'Take Profit 2 \(TP2\):\s*(.*?)(?=\n|$)', text)
    tp3 = safe_extract(r'Take Profit 3 \(TP3\):\s*(.*?)(?=\n|$)', text)
    
    # Penggabungan TP untuk ditampilkan di UI
    if tp2 != "-" and tp3 != "-":
        tp_combined = f"TP1: {tp1} | TP2: {tp2} | TP3: {tp3}"
    else:
        tp_combined = tp1

    evaluation = safe_extract(r'Evaluasi Setup:\s*(.*?)(?=\n|$)', text)
    duration = safe_extract(r'Durasi Validitas:\s*(.*?)(?=\n|$)', text)

    reasons_split = re.split(r'ALASAN ENTRY \(LOGIKA ANALISIS\):', text, flags=re.IGNORECASE)
    reasons = []
    if len(reasons_split) > 1:
        reasons_text = reasons_split[1].strip()
        reasons = [r.replace('-', '').replace('*', '').strip() for r in reasons_text.split('\n') if len(r.strip()) > 5]
    
    if not reasons:
        reasons = ["Menunggu konfirmasi validasi Advanced SMC."]

    return {
        'status': status, 'signal': signal, 'entry': entry,
        'sl': sl, 'tp': tp_combined, 'evaluation': evaluation,
        'duration': duration, 'reasons': reasons, 'raw': text
    }

# Header App
st.markdown("### ⚡ FIBOMAGIC **AI** | `ULTIMATE SMC SYSTEM`")
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
    
    analyze_btn = st.button("📈 Generate Smart Signal", type="primary", use_container_width=True, disabled=not uploaded_file)

    st.markdown("---")
    st.markdown("**System Parameters**")
    st.caption(f"**Instrument:** XAUUSD (Gold)\n\n**Timeframe:** {timeframe}\n\n**Algorithm:** Advanced SMC, FVG & Multi-TP Logic")

with col2:
    if analyze_btn and uploaded_file is not None:
        with st.spinner("🤖 Menganalisis FVG, Liquidity & Order Block..."):
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
                
                # Eksekusi AI
                response = model.generate_content([prompt, safe_image])
                res = parse_result(response.text)
                
                sig_upper = res['signal'].upper()
                if "BUY" in sig_upper: sig_class = "signal-buy"
                elif "SELL" in sig_upper: sig_class = "signal-sell"
                else: sig_class = "signal-wait"

                # ---------------------------------------------------------
                # SIMPAN KE HISTORY TRADING
                # ---------------------------------------------------------
                history_entry = {
                    "Waktu": datetime.now().strftime("%H:%M:%S"),
                    "TF": timeframe,
                    "Sinyal": res['signal'],
                    "Sniper Zone": res['entry'],
                    "SL": res['sl'],
                    "Target TP": res['tp'],
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
                    <p style="color: #94a3b8; font-size: 14px; font-weight: bold; margin-bottom: 8px;">🎯 SMART EXECUTION DETAILS</p>
                    <div style="display: grid; grid-template-columns: 1fr; gap: 10px; margin-bottom: 10px;">
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Sniper Zone (Entry)</p>
                            <p style="font-size: 14px; color: #e2e8f0; font-family: monospace; margin: 0;">{res['entry']}</p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Stop Loss (SL)</p>
                            <p style="font-size: 14px; color: #fb7185; font-family: monospace; margin: 0;">{res['sl']}</p>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Multi-Target (TP1, TP2, TP3)</p>
                            <p style="font-size: 12px; color: #34d399; font-family: monospace; margin: 0;">{res['tp']}</p>
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
                
                st.markdown("**🧠 Logika Smart Money (SMC Analysis):**")
                for reason in res['reasons']:
                    st.markdown(f"- {reason}")
                    
            except Exception as e:
                st.error(f"Sistem Gagal Mengeksekusi: {str(e)}")
    elif not analyze_btn:
        st.info("👈 Silakan pilih timeframe, unggah screenshot chart XAUUSD Anda di panel kiri, lalu klik 'Generate Smart Signal'.")

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
