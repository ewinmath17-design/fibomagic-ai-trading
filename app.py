import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="FIBOMAGIC AI | XAUUSD Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #cbd5e1; }
    .metric-card { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .signal-buy { color: #34d399; font-weight: bold; background: rgba(52, 211, 153, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(52, 211, 153, 0.2); }
    .signal-sell { color: #fb7185; font-weight: bold; background: rgba(251, 113, 133, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(251, 113, 133, 0.2); }
    .signal-wait { color: #fbbf24; font-weight: bold; background: rgba(251, 191, 36, 0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(251, 191, 36, 0.2); }
    </style>
""", unsafe_allow_html=True)

# Fungsi Prompt
def get_prompt(timeframe):
    return f"""Anda adalah seorang AI Trading Analyst profesional dengan spesialisasi pada teknik trading, khususnya untuk instrumen XAUUSD (Gold) pada Timeframe {timeframe}. 

Tugas utama Anda adalah menganalisis gambar screenshot chart trading yang diberikan dan memberikan konfirmasi eksekusi (Signal) yang sangat logis, objektif, dan berbasis probabilitas tinggi.

LAKUKAN ANALISIS BERDASARKAN POIN BERIKUT:
1. Identifikasi Tren ({timeframe}): Apakah harga sedang membuat Higher High/Higher Low (Uptrend), Lower High/Lower Low (Downtrend), atau Ranging/Sideways?
2. Key Levels: Tentukan titik Support dan Resistance terdekat (dinamis maupun statis) yang relevan dengan harga saat ini.
3. Price Action & Candlestick: Deteksi pola candlestick terakhir dan momentum penolakan di area penting.
4. Indikator Tambahan: Baca sinyal dari indikator yang terpasang di chart.

ATURAN OUTPUT:
Berikan hasil analisis Anda HANYA dalam format terstruktur di bawah ini. Jangan tambahkan narasi pembuka atau penutup.

[ HASIL ANALISIS FIBOMAGIC AI ]
TIMEFRAME: {timeframe}
STATUS MARKET: [Uptrend / Downtrend / Sideways]
KONFIRMASI SIGNAL: [STRONG BUY / STRONG SELL / WAIT]

DETAIL EKSEKUSI:
- Entry Area: [Sebutkan rentang harga]
- Stop Loss (SL): [Sebutkan titik harga SL]
- Take Profit (TP): [Sebutkan titik harga TP]

EVALUASI & DURASI:
- Evaluasi Setup: [Sebutkan evaluasi singkat]
- Durasi Validitas: [Sebutkan estimasi waktu valid]

ALASAN ENTRY (LOGIKA ANALISIS):
- [Alasan 1]
- [Alasan 2]
"""

# Fungsi Parsing Regex
def parse_result(text):
    def safe_extract(pattern, default="-"):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    status = safe_extract(r'STATUS MARKET:\s*\*?([^*]+)\*?')
    signal = safe_extract(r'KONFIRMASI SIGNAL:\s*\*?([^*]+)\*?')
    entry = safe_extract(r'- Entry Area:\s*\*?([^*]+)\*?')
    sl = safe_extract(r'- Stop Loss \(SL\):\s*\*?([^*]+)\*?')
    tp = safe_extract(r'- Take Profit \(TP\):\s*\*?([^*]+)\*?')
    evaluation = safe_extract(r'- Evaluasi Setup:\s*\*?([^*]+)\*?')
    duration = safe_extract(r'- Durasi Validitas:\s*\*?([^*]+)\*?')

    reasons_split = re.split(r'ALASAN ENTRY \(LOGIKA ANALISIS\):', text, flags=re.IGNORECASE)
    reasons = []
    if len(reasons_split) > 1:
        reasons_text = reasons_split[1].strip()
        reasons = [r.replace('-', '').strip() for r in reasons_text.split('\n') if len(r.strip()) > 5]

    return {
        'status': status, 'signal': signal, 'entry': entry,
        'sl': sl, 'tp': tp, 'evaluation': evaluation,
        'duration': duration, 'reasons': reasons, 'raw': text
    }

# Header App
st.markdown("### ⚡ FIBOMAGIC **AI** | `XAUUSD ANALYSIS`")
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
    
    analyze_btn = st.button("📈 Generate Signal", type="primary", use_container_width=True, disabled=not uploaded_file)

    st.markdown("---")
    st.markdown("**System Parameters**")
    st.caption(f"**Instrument:** XAUUSD (Gold)\n\n**Timeframe:** {timeframe}\n\n**Strategy:** {'Aggressive Scalping' if timeframe in ['M1', 'M5'] else 'Day Trading'}")

with col2:
    if analyze_btn and uploaded_file is not None:
        with st.spinner("🤖 Menganalisis Struktur Market & Price Action..."):
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                safe_image = image.convert('RGB')
                
                # ---------------------------------------------------------
                # DETEKSI MODEL OTOMATIS BERDASARKAN API KEY (ANTI ERROR 404)
                # ---------------------------------------------------------
                valid_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        valid_models.append(m.name.replace('models/', ''))
                
                if not valid_models:
                    st.error("API Key Anda tidak memiliki akses ke model AI apapun. Pastikan API Key valid.")
                    st.stop()
                
                # Cari model terbaik yang ada di daftar valid
                target_model = None
                for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision']:
                    for vm in valid_models:
                        if preferred in vm:
                            target_model = vm
                            break
                    if target_model:
                        break
                
                # Jika tidak menemukan yang biasa, pakai model pertama yang tersedia di API Anda
                if not target_model:
                    target_model = valid_models[0]
                
                st.caption(f"*System Info: Menggunakan mesin AI `{target_model}`*")
                
                # Eksekusi dengan model yang pasti valid
                model = genai.GenerativeModel(target_model)
                prompt = get_prompt(timeframe)
                response = model.generate_content([prompt, safe_image])
                
                # Parsing & Render Hasil
                res = parse_result(response.text)
                
                sig_upper = res['signal'].upper()
                if "BUY" in sig_upper: sig_class = "signal-buy"
                elif "SELL" in sig_upper: sig_class = "signal-sell"
                else: sig_class = "signal-wait"

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
                    <p style="color: #94a3b8; font-size: 14px; font-weight: bold; margin-bottom: 8px;">🎯 EXECUTION DETAILS</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Entry Area</p>
                            <p style="font-size: 14px; color: #e2e8f0; font-family: monospace; margin: 0;">{res['entry']}</p>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Stop Loss (SL)</p>
                            <p style="font-size: 14px; color: #fb7185; font-family: monospace; margin: 0;">{res['sl']}</p>
                        </div>
                        <div style="background: #020617; padding: 12px; border-radius: 8px; border: 1px solid #1e293b;">
                            <p style="font-size: 11px; color: #64748b; margin: 0;">Take Profit (TP)</p>
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
                
                st.markdown("**🧠 Analysis Logic (Alasan Entry):**")
                for reason in res['reasons']:
                    st.markdown(f"- {reason}")
                    
            except Exception as e:
                st.error(f"Sistem Gagal Mengeksekusi: {str(e)}")
    elif not analyze_btn:
        st.info("👈 Silakan pilih timeframe, unggah screenshot chart XAUUSD Anda di panel kiri, lalu klik 'Generate Signal'.")
