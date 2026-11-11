import streamlit as st
from google import genai
from PIL import Image
import io
import time
import random

# Konfigurasi paparan mesra telefon pintar
st.set_page_config(page_title="KineMath Remedial - UC TATI", page_icon="📐", layout="centered")

# --- SUNTIKAN CSS: TUKAR WARNA PILIHAN JADI BIRU (PERKARA 2 & 3) ---
st.markdown("""
<style>
/* Tukar warna border dan teks bagi parameter & formula yang dipilih kepada BIRU */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    border: 1.8px solid #1E88E5 !important;
    border-radius: 8px !important;
    background-color: #f0f7ff !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
    color: #0d47a1 !important;
    font-weight: 700 !important;
}

/* Gaya badge pilihan berwarna biru lembut */
.blue-badge {
    display: inline-block;
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.88rem;
    font-weight: 600;
    margin: 2px 4px;
    border: 1px solid #90caf9;
}
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "badges" not in st.session_state:
    st.session_state.badges = []
if "questions_solved" not in st.session_state:
    st.session_state.questions_solved = 0
if "seen_questions" not in st.session_state:
    st.session_state.seen_questions = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "last_review" not in st.session_state:
    st.session_state.last_review = None

# Senarai Bank Soalan Pelbagai Senario Kinematik 1D
QUESTION_BANK = [
    "Sebuah kereta bermula dari keadaan pegun dan memecut secara seragam pada kadar 3 m/s² selama 4 saat. Hitungkan sesaran kereta tersebut.",
    "Sebuah motosikal bergerak dengan halaju 25 m/s kemudian membrek dengan nyahpecutan seragam 5 m/s² sehingga berhenti. Berapakah masa yang diambil untuk motosikal itu berhenti sepenuhnya?",
    "Sebuah lori memecut dari 10 m/s ke halaju akhir v merentasi jarak 75 m dengan pecutan 2 m/s². Tentukan halaju akhir lori tersebut.",
    "Sebuah kereta api bergerak pada 30 m/s menekan brek kecemasan dan berhenti selepas 6 saat. Hitungkan jarak yang dilalui sepanjang tempoh membrek.",
    "Sebuah bas bergerak dari halaju 12 m/s dan memecut secara seragam pada 1.5 m/s² selama 8 saat. Cari jarak yang dilalui oleh bas tersebut.",
    "Sebuah van bergerak dari keadaan pegun mencapai halaju 20 m/s dalam masa 5 saat. Hitungkan nilai pecutan van tersebut.",
    "Sebuah skuter elektrik bergerak dengan kelajuan 16 m/s dan mengalami nyahpecutan 2 m/s² sehingga berhenti. Berapakah sesaran yang dilalui sebelum ia berhenti?"
]

if "current_question" not in st.session_state:
    st.session_state.current_question = QUESTION_BANK[0]

# Pengiraan Level Pelajar
def get_level(xp):
    if xp < 200:
        return "Level 1: Novis Kinematik 🥉", 200
    elif xp < 500:
        return "Level 2: Pakar Gerakan 🥈", 500
    elif xp < 900:
        return "Level 3: Jaguh Newton 🥇", 900
    else:
        return "Level 4: Master Algebra UC TATI 🎓", 1500

current_level, next_level_xp = get_level(st.session_state.xp)

# Menu Sisi: Profil & Peti Hadiah
with st.sidebar:
    st.header("🏆 Profil & Peti Hadiah")
    st.subheader(current_level)
    progress = min(st.session_state.xp / next_level_xp, 1.0)
    st.progress(progress)
    st.caption(f"Terkumpul: **{st.session_state.xp} XP** / Sasaran Seterusnya: {next_level_xp} XP")
    st.write(f"Soalan Selesai: **{st.session_state.questions_solved}**")
    
    st.divider()
    st.write("🎁 **Koleksi Hadiah Anda:**")
    if st.session_state.badges:
        for b in set(st.session_state.badges):
            count = st.session_state.badges.count(b)
            st.write(f"- {b} x{count}")
    else:
        st.caption("Selesaikan latihan untuk kumpul hadiah!")

st.title("📐 KineMath AI Tutor")
st.caption("Modul Bimbingan Kinematik 1D & Diagnosis Algebra (Diploma UC TATI)")

# Fungsi kecilkan saiz imej ultra-pantas (768px, kualiti 70%)
def optimize_image(uploaded_file, max_dim=768):
    image = Image.open(uploaded_file)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((max_dim, max_dim), Image.Resampling.BILINEAR)
    
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=70, optimize=False)
    buffer.seek(0)
    return Image.open(buffer)

# 1. Tetapan API Key
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")

if not api_key:
    st.info("Sila masukkan Gemini API Key di bahagian menu sisi untuk memulakan.")
    st.stop()

client = genai.Client(api_key=api_key)

# Fungsi Dapatkan Soalan Unik Seterusnya
def get_unique_next_question():
    unseen = [q for q in QUESTION_BANK if q not in st.session_state.seen_questions]
    if unseen:
        return random.choice(unseen)
    
    try:
        past_q_summary = "; ".join(st.session_state.seen_questions[-4:])
        gen_prompt = f"""
        Hasilkan satu soalan fizik baharu topik Kinematik 1 Dimensi (bukan graviti/jatuh bebas) untuk pelajar Diploma Kejuruteraan.
        Pastikan soalan ini BERBEZA daripada soalan-soalan berikut:
        [{past_q_summary}]
        Tulis teks soalan sahaja dalam Bahasa Melayu tanpa jawapan.
        """
        resp = client.models.generate_content(model="gemini-3.8-flash", contents=gen_prompt)
        new_q = resp.text.strip()
        if new_q:
            return new_q
    except Exception:
        pass
    
    return random.choice(QUESTION_BANK)

# 2. Bahagian Paparan Soalan
st.subheader("1. Soalan Fizik Kinematik")
st.info(f"📌 **Soalan Sekarang:**\n\n{st.session_state.current_question}")

col_src1, col_src2 = st.columns(2)
with col_src1:
    if st.button("🎲 Tukar Soalan Lain Secara Rawak"):
        st.session_state.current_question = get_unique_next_question()
        st.session_state.last_review = None
        st.session_state.uploader_key += 1
        st.rerun()

with col_src2:
    if st.checkbox("Tulis / Edit Teks Soalan Sendiri"):
        edited_q = st.text_area("Tulis soalan anda:", value=st.session_state.current_question, height=70)
        st.session_state.current_question = edited_q

# 3. Fasa Ekstraksi Maklumat (Perkara 2 - Dengan Visual Biru)
st.subheader("2. Kenal Pasti Parameter (u, v, s, a, t)")
st.caption("Pilihan yang aktif akan diwarnakan dengan :blue[**warna biru**]:")

col1, col2 = st.columns(2)
with col1:
    u_status = st.selectbox("Halaju Awal (u):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    v_status = st.selectbox("Halaju Akhir (v):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    s_status = st.selectbox("Sesaran (s):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
with col2:
    a_status = st.selectbox("Pecutan (a):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    t_status = st.selectbox("Masa (t):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)

# Paparan Pengesahan Pilihan Parameter (Warna Biru)
st.markdown(
    f"""
    <div style="background-color: #f0f7ff; padding: 8px 12px; border-radius: 8px; border-left: 4px solid #1E88E5; margin-top: 5px;">
        <span style="font-size: 0.85rem; color: #555;">Pilihan Semasa:</span><br>
        <span class="blue-badge">u: <b>{u_status}</b></span>
        <span class="blue-badge">v: <b>{v_status}</b></span>
        <span class="blue-badge">s: <b>{s_status}</b></span>
        <span class="blue-badge">a: <b>{a_status}</b></span>
        <span class="blue-badge">t: <b>{t_status}</b></span>
    </div>
    """, 
    unsafe_allow_html=True
)

# 4. Fasa Pemilihan Formula (Perkara 3 - Dengan Visual Biru)
st.subheader("3. Pilih Persamaan Kinematik")
equation_options = [
    "-- Pilih Persamaan --",
    "v = u + at",
    "s = ut + (1/2)at²",
    "v² = u² + 2as",
    "s = (1/2)(u + v)t"
]
selected_eq = st.selectbox("Persamaan yang paling sesuai:", equation_options)

# Paparan Pengesahan Formula Dipilih (Warna Biru)
if selected_eq != "-- Pilih Persamaan --":
    st.markdown(
        f"""
        <div style="background-color: #f0f7ff; padding: 8px 12px; border-radius: 8px; border-left: 4px solid #1E88E5; margin-top: 5px;">
            <span style="font-size: 0.85rem; color: #555;">Formula Dipilih:</span> 
            <span class="blue-badge" style="font-size: 0.95rem;">📐 <b>{selected_eq}</b></span>
        </div>
        """,
        unsafe_allow_html=True
    )

# 5. Fasa Muat Naik / Tangkap Gambar Jalan Kerja
st.subheader("4. Selesaikan & Semak Algebra")
pilihan_kamera = st.radio(
    "Kaedah Ambil Gambar:",
    ["📱 Buka Kamera Telefon / Muat Naik Fail (Paling Mudah)", "📷 Kamera Web Pelayar (Streamlit)"],
    horizontal=True
)

image_file = None
if pilihan_kamera == "📱 Buka Kamera Telefon / Muat Naik Fail (Paling Mudah)":
    st.caption("💡 *Tips Telefon:* Tekan kotak di bawah dan pilih **Camera** untuk terus menggunakan kamera belakang.")
    image_file = st.file_uploader("Pilih Fail / Buka Kamera", type=["jpg", "jpeg", "png"], key=f"file_up_{st.session_state.uploader_key}")
else:
    st.caption("💡 *Tips Kamera Web:* Jika menghadap muka, tekan ikon **(⟲)** di atas kamera untuk tukar ke kamera belakang.")
    image_file = st.camera_input("Ambil gambar kertas jawapan", key=f"cam_up_{st.session_state.uploader_key}")

# Butang Semakan
if image_file and st.button("Semak Jalan Kerja Saya 🚀", type="primary"):
    with st.spinner("Memproses gambar jawapan..."):
        img = optimize_image(image_file)
    
    prompt = f"""
    Anda pensyarah Fizik & Matematik UC TATI. Semak gambar jalan kerja tulisan tangan pelajar ini secara ringkas, padat dan segera.

    Konteks:
    - Soalan: {st.session_state.current_question}
    - Parameter: u={u_status}, v={v_status}, s={s_status}, a={a_status}, t={t_status}
    - Formula: {selected_eq}

    Format Ulasan Ringkas (Maksimum 2 ayat setiap seksyen):
    1. **Status Konsep Fizik:** (Adakah formula & gantian nombor tepat?)
    2. **Diagnosis Ralat Algebra:** (Nyatakan baris ralat tanda/pindah/pecahan/kuasa jika ada, atau puji jika betul)
    3. **Langkah Betul:** (Tunjukkan jalan pembetulan ringkas)
    
    Wajib tulis kod verdik ini di baris paling akhir:
    - `[VERDIK: SEMPURNA]` jika semua 100% betul.
    - `[VERDIK: PEMBAIKAN]` jika fizik betul tetapi ada silap algebra.
    - `[VERDIK: CUBA_LAGI]` jika formula atau konsep salah.
    """

    candidate_models = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
    success = False
    response_placeholder = st.empty()
    full_response = ""

    with st.spinner("AI sedang menganalisis secara langsung..."):
        for model_name in candidate_models:
            try:
                response_stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=[prompt, img]
                )
                for chunk in response_stream:
                    if chunk.text:
                        full_response += chunk.text
                        display_live = full_response.replace("[VERDIK: SEMPURNA]", "").replace("[VERDIK: PEMBAIKAN]", "").replace("[VERDIK: CUBA_LAGI]", "")
                        response_placeholder.markdown(display_live)
                
                success = True
                break
            except Exception as err:
                err_msg = str(err).lower()
                if "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg or "not found" in err_msg:
                    time.sleep(1)
                    continue
                else:
                    st.error(f"Ralat ({model_name}): {err}")
                    break

        if success:
            st.session_state.last_review = full_response
            st.session_state.questions_solved += 1
            
            if st.session_state.current_question not in st.session_state.seen_questions:
                st.session_state.seen_questions.append(st.session_state.current_question)

            # Ganjaran Gamifikasi
            if "[VERDIK: SEMPURNA]" in full_response:
                st.balloons()
                st.session_state.xp += 100
                gift_list = ["🏆 Piala Newton", "🚀 Roket Kinematik Emas", "⚡ Lencana Kilat Vektor", "⭐ Bintang Cemerlang SPM"]
                earned_gift = random.choice(gift_list)
                st.session_state.badges.append(earned_gift)
                st.success(f"🎉 **SYABAS! JAWAPAN TEPAT!** (+100 XP) | Hadiah Terbuka: **{earned_gift}**!")
            elif "[VERDIK: PEMBAIKAN]" in full_response:
                st.session_state.xp += 40
                st.session_state.badges.append("🔧 Lencana Pembaikan Algebra")
                st.info("💡 **KONSEP FIZIK MANTAP!** (+40 XP) Cuma ada sedikit ralat algebra.")
            else:
                st.session_state.xp += 20
                st.warning("💪 **JANGAN PUTUS ASA!** (+20 XP) Teruskan mencuba soalan lain!")
        else:
            st.error("Pelayan AI sedang sibuk. Sila tekan butang sekali lagi.")

# 6. Bahagian Menu & Butang Soalan Seterusnya
if st.session_state.last_review:
    st.divider()
    st.subheader("🎯 Langkah Seterusnya")
    st.write(f"Tahniah! Anda telah melengkapkan latihan ini. Rekod soalan yang telah dicuba: **{len(st.session_state.seen_questions)}**")
    
    if st.button("➡️ Cuba Soalan Seterusnya (Soalan Baharu)", type="primary"):
        st.session_state.current_question = get_unique_next_question()
        st.session_state.last_review = None
        st.session_state.uploader_key += 1
        st.rerun()
