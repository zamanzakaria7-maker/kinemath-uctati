import streamlit as st
from google import genai
from PIL import Image
import io
import time
import random

# Konfigurasi paparan mesra telefon pintar
st.set_page_config(page_title="KineMath Remedial - UC TATI", page_icon="📐", layout="centered")

# Inisialisasi Sistem Gamifikasi dalam Session State
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "badges" not in st.session_state:
    st.session_state.badges = []
if "questions_solved" not in st.session_state:
    st.session_state.questions_solved = 0

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
    st.write(f"Soalan Disemak: **{st.session_state.questions_solved}**")
    
    st.divider()
    st.write("🎁 **Koleksi Hadiah Anda:**")
    if st.session_state.badges:
        for b in set(st.session_state.badges):
            count = st.session_state.badges.count(b)
            st.write(f"- {b} x{count}")
    else:
        st.caption("Selesaikan latihan untuk kumpul hadiah misteri!")

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

# 2. Pengurusan Soalan Fizik
st.subheader("1. Soalan Fizik Kinematik")

preset_questions = {
    "Senario 1: Memecut dari Pegun (Cari Sesaran)": 
        "Sebuah kereta bermula dari keadaan pegun dan memecut secara seragam pada kadar 3 m/s² selama 4 saat. Hitungkan sesaran kereta tersebut.",
    "Senario 2: Membrek / Nyahpecutan (Cari Masa Berhenti)": 
        "Sebuah motosikal bergerak dengan halaju 25 m/s kemudian membrek dengan nyahpecutan seragam 5 m/s² sehingga berhenti. Berapakah masa yang diambil untuk motosikal itu berhenti sepenuhnya?",
    "Senario 3: Memecut Memotong Kenderaan (Cari Halaju Akhir)": 
        "Sebuah lori memecut dari 10 m/s ke halaju akhir v merentasi jarak 75 m dengan pecutan 2 m/s². Tentukan halaju akhir lori tersebut.",
    "Senario 4: Nyahpecutan Kecemasan (Cari Jarak Berhenti)": 
        "Sebuah kereta api bergerak pada 30 m/s menekan brek kecemasan dan berhenti selepas 6 saat. Hitungkan jarak yang dilalui sepanjang tempoh membrek."
}

mode = st.radio("Pilih Sumber Soalan:", ["Bank Soalan", "Jana Soalan Baharu (AI) 🎲", "Taip Soalan Sendiri"], horizontal=True)

if "current_question" not in st.session_state:
    st.session_state.current_question = preset_questions["Senario 1: Memecut dari Pegun (Cari Sesaran)"]

if mode == "Bank Soalan":
    pilihan = st.selectbox("Pilih Senario Latihan:", list(preset_questions.keys()))
    st.session_state.current_question = preset_questions[pilihan]
    question = st.text_area("Teks Soalan:", value=st.session_state.current_question, height=90)

elif mode == "Jana Soalan Baharu (AI) 🎲":
    if st.button("Jana Soalan Rawak Baharu ✨"):
        with st.spinner("AI sedang menjana soalan fizik 1D baharu..."):
            gen_prompt = "Hasilkan satu soalan fizik peringkat Diploma topik Kinematik 1 Dimensi (bukan jatuh bebas / bukan graviti). Berikan teks soalan sahaja dalam Bahasa Melayu tanpa jawapan. Pastikan nilai nombor mudah untuk diselesaikan."
            try:
                gen_resp = client.models.generate_content(model="gemini-2.5-flash", contents=gen_prompt)
                st.session_state.current_question = gen_resp.text.strip()
            except Exception:
                st.session_state.current_question = "Sebuah bas bergerak dari halaju 12 m/s memecut pada 1.5 m/s² selama 8 saat. Cari jarak yang dilalui."
    question = st.text_area("Teks Soalan Dijana:", value=st.session_state.current_question, height=90)

else:
    question = st.text_area("Tampal atau Taip Soalan Anda:", value="", placeholder="Tulis soalan fizik di sini...", height=90)

# 3. Fasa Ekstraksi Maklumat (Lalai: Tidak Terlibat)
st.subheader("2. Kenal Pasti Parameter (u, v, s, a, t)")
st.write("Tentukan status bagi setiap kuantiti gerakan:")

col1, col2 = st.columns(2)
with col1:
    u_status = st.selectbox("Halaju Awal (u):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    v_status = st.selectbox("Halaju Akhir (v):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    s_status = st.selectbox("Sesaran (s):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
with col2:
    a_status = st.selectbox("Pecutan (a):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    t_status = st.selectbox("Masa (t):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)

# 4. Fasa Pemilihan Formula
st.subheader("3. Pilih Persamaan Kinematik")
equation_options = [
    "-- Pilih Persamaan --",
    "v = u + at",
    "s = ut + (1/2)at²",
    "v² = u² + 2as",
    "s = (1/2)(u + v)t"
]
selected_eq = st.selectbox("Persamaan yang paling sesuai:", equation_options)

# 5. Fasa Muat Naik / Tangkap Gambar Jalan Kerja
st.subheader("4. Selesaikan & Semak Algebra")
st.write("Selesaikan jalan kerja di atas kertas, kemudian ambil gambar:")

pilihan_kamera = st.radio(
    "Pilihan kaedah gambar:",
    ["📱 Buka Kamera Telefon / Muat Naik Fail (Paling Mudah)", "📷 Kamera Web Pelayar (Streamlit)"],
    horizontal=True
)

image_file = None

if pilihan_kamera == "📱 Buka Kamera Telefon / Muat Naik Fail (Paling Mudah)":
    st.caption("💡 *Tips Telefon Pintar:* Tekan butang di bawah dan pilih **Camera** untuk terus guna kamera belakang telefon anda.")
    image_file = st.file_uploader("Tekan untuk Buka Kamera / Pilih Gambar", type=["jpg", "jpeg", "png"])
else:
    st.caption("💡 *Tips Kamera Web:* Jika kamera menghadap muka (selfie), tekan ikon pusingan **(⟲)** di penjuru atas kotak kamera untuk tukar ke kamera belakang.")
    image_file = st.camera_input("Ambil gambar kertas jawapan")

if image_file and st.button("Semak Jalan Kerja Saya 🚀", type="primary"):
    if not question.strip():
        st.warning("Sila pastikan teks soalan diisi terlebih dahulu.")
        st.stop()

    with st.spinner("Memproses gambar..."):
        img = optimize_image(image_file)
    
    # Prompt ringkas & terus ke punca masalah untuk jimat masa pemprosesan
    prompt = f"""
    Anda pensyarah Fizik & Matematik UC TATI. Semak gambar jalan kerja tulisan tangan pelajar ini secara ringkas, padat dan segera.

    Konteks:
    - Soalan: {question}
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

    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    success = False

    response_placeholder = st.empty()
    full_response = ""

    with st.spinner("AI sedang menganalisis secara langsung..."):
        for model_name in candidate_models:
            try:
                # Streaming untuk maklum balas pantas (muncul dalam 1-2 saat)
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
                if "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg:
                    time.sleep(1)
                    continue
                else:
                    st.error(f"Ralat: {err}")
                    break

        if success:
            st.session_state.questions_solved += 1
            
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

            st.success("🔥 Teruskan momentum! Sila cuba soalan seterusnya di atas.")
        else:
            st.error("Pelayan AI sedang sibuk. Sila tekan butang sekali lagi.")
