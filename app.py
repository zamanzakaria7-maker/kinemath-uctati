import streamlit as st
from google import genai
from PIL import Image
import time

# Konfigurasi paparan mesra telefon pintar
st.set_page_config(page_title="KineMath Remedial - UC TATI", page_icon="📐", layout="centered")

st.title("📐 KineMath AI Tutor")
st.caption("Modul Bimbingan Kinematik 1D & Diagnosis Algebra (Diploma UC TATI)")

# 1. Tetapan API Key
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")

if not api_key:
    st.info("Sila masukkan Gemini API Key di bahagian menu sisi untuk memulakan.")
    st.stop()

client = genai.Client(api_key=api_key)

# 2. Pengurusan Soalan Fizik (Bank Soalan + Penjana AI)
st.subheader("1. Soalan Fizik Kinematik")

# Koleksi soalan preset pelbagai senario
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

# Simpan soalan dalam session state supaya tidak hilang semasa ambil gambar
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
                gen_resp = client.models.generate_content(model="gemini-3.8-flash", contents=gen_prompt)
                st.session_state.current_question = gen_resp.text.strip()
            except Exception:
                st.session_state.current_question = "Sebuah bas bergerak dari halaju 12 m/s memecut pada 1.5 m/s² selama 8 saat. Cari jarak yang dilalui."
    question = st.text_area("Teks Soalan Dijana:", value=st.session_state.current_question, height=90)

else:
    question = st.text_area("Tampal atau Taip Soalan Anda:", value="", placeholder="Tulis soalan fizik di sini...", height=90)

# 3. Fasa Ekstraksi Maklumat (Scaffolding Fizik)
st.subheader("2. Kenal Pasti Parameter (u, v, s, a, t)")
st.write("Tentukan status bagi setiap kuantiti gerakan:")

col1, col2 = st.columns(2)
with col1:
    u_status = st.selectbox("Halaju Awal (u):", ["Diberi", "Dicari", "Tidak Terlibat"], index=0)
    v_status = st.selectbox("Halaju Akhir (v):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    s_status = st.selectbox("Sesaran (s):", ["Diberi", "Dicari", "Tidak Terlibat"], index=1)
with col2:
    a_status = st.selectbox("Pecutan (a):", ["Diberi", "Dicari", "Tidak Terlibat"], index=0)
    t_status = st.selectbox("Masa (t):", ["Diberi", "Dicari", "Tidak Terlibat"], index=0)

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

source = st.radio("Pilihan input gambar:", ["Guna Kamera Telefon", "Muat Naik Fail"], horizontal=True)

image_file = None
if source == "Guna Kamera Telefon":
    image_file = st.camera_input("Ambil gambar kertas jawapan anda")
else:
    image_file = st.file_uploader("Pilih gambar dari galeri", type=["jpg", "jpeg", "png"])

if image_file and st.button("Semak Jalan Kerja Saya 🚀", type="primary"):
    if not question.strip():
        st.warning("Sila pastikan teks soalan diisi terlebih dahulu.")
        st.stop()

    img = Image.open(image_file)
    
    prompt = f"""
    Anda adalah pensyarah Fizik dan Matematik perintis di UC TATI. 
    Tugasan anda adalah mendiagnosis jalan kerja tulisan tangan pelajar ini secara empati dan konstruktif.

    Konteks Masalah:
    - Soalan: {question}
    - Parameter yang dipilih pelajar: u={u_status}, v={v_status}, s={s_status}, a={a_status}, t={t_status}
    - Formula yang dipilih pelajar: {selected_eq}

    Tugasan Semakan:
    1. Teliti gambar jalan kerja bertulis pelajar yang dilampirkan.
    2. Tentukan sama ada formula fizik yang ditulis dan gantian nombor awal adalah tepat.
    3. Semak setiap baris operasi algebra:
       - Adakah berlaku kesalahan tanda (+/-)?
       - Adakah berlaku kesalahan pemindahan sebutan (transposition)?
       - Adakah pembahagian/pendaraban pecahan betul?
       - Adakah operasi punca kuasa atau kuasa dua betul?
    4. Berikan maklum balas berstruktur:
       - **Status Konsep Fizik:** (Nyatakan sama ada konsep & gantian formula betul)
       - **Diagnosis Ralat Algebra:** (Jika ada ralat, tunjukkan baris mana dan terangkan prinsip matematik yang betul dengan mudah)
       - **Langkah Pembetulan:** (Tunjukkan satu langkah demi satu cara menyelesaikan algebra tersebut dengan jelas)
    
    Gunakan Bahasa Melayu yang mesra dan mudah difahami oleh pelajar diploma.
    """

    candidate_models = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
    success = False

    with st.spinner("AI sedang membaca tulisan tangan dan menyemak operasi algebra..."):
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, img]
                )
                st.success(f"Analisis Selesai! (Diproses oleh {model_name})")
                st.markdown(response.text)
                success = True
                break
            except Exception as err:
                err_msg = str(err).lower()
                if "503" in err_msg or "unavailable" in err_msg or "high demand" in err_msg:
                    st.warning(f"Model {model_name} sedang sibuk, beralih ke model sandaran...")
                    time.sleep(2)
                    continue
                else:
                    st.error(f"Ralat: {err}")
                    break

        if not success:
            st.error("Pelayan AI sedang mengalami kesesakan luar biasa pada semua model. Sila cuba tekan butang semak sekali lagi dalam masa beberapa saat.")
