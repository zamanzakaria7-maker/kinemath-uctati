import concurrent.futures
import io
import random
import time
from PIL import Image, ImageEnhance, ImageOps
from google import genai
import streamlit as st

# Konfigurasi paparan mesra telefon pintar
st.set_page_config(
    page_title="KineMath Remedial - UC TATI", page_icon="📐", layout="centered"
)

# --- SUNTIKAN CSS: KOTAK BIRU, INDIKATOR BIRU, KAD FORMULA JELAS & LENCANA GRED ---
st.markdown(
    """
<style>
/* Kotak pilihan (Selectbox) border & teks biru */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    border: 1.8px solid #1E88E5 !important;
    border-radius: 8px !important;
    background-color: #f0f7ff !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
    color: #0d47a1 !important;
    font-weight: 700 !important;
}

/* Lencana Biru di bawah setiap dropdown parameter */
.blue-param-indicator {
    background-color: #e3f2fd;
    color: #0d47a1;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: -8px;
    margin-bottom: 12px;
    display: inline-block;
    border: 1px solid #90caf9;
}

/* Kad Paparan Formula Terpilih */
.selected-formula-card {
    background: linear-gradient(135deg, #e8f4fd, #d1e9fc);
    border: 2px solid #1E88E5;
    border-left: 6px solid #0d47a1;
    border-radius: 10px;
    padding: 12px 18px;
    margin-top: 8px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(30, 136, 229, 0.15);
}
.selected-formula-header {
    color: #0d47a1;
    font-size: 0.88rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

/* Lencana Rekod Percubaan */
.grade-record-badge {
    display: inline-block;
    padding: 5px 12px;
    margin: 3px 4px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.5px;
    border: 1.5px solid;
}
.badge-A { background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
.badge-B { background-color: #e3f2fd; color: #1565c0; border-color: #90caf9; }
.badge-C { background-color: #fffde7; color: #f57f17; border-color: #fff59d; }
.badge-D { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; }
.badge-E { background-color: #ffebee; color: #c62828; border-color: #ef9a9a; }

/* Kotak Tips Animasi Semasa Menunggu */
.tips-container {
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border-left: 5px solid #1976d2;
    padding: 14px 18px;
    border-radius: 8px;
    color: #0d47a1;
    margin-top: 10px;
    margin-bottom: 16px;
    font-size: 0.95rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    transition: all 0.3s ease-in-out;
}

/* Kotak Nasihat & Pelan Tindakan */
.advice-box {
    background-color: #fdfefe;
    border: 1.5px solid #90caf9;
    border-radius: 10px;
    padding: 16px;
    margin-top: 14px;
    margin-bottom: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)

# Senarai Tip Kata Kunci Rahsia Kinematik Linear Sahaja
KINEMATIC_TIPS = [
    "💡 **Kata Kunci 'Pegun' / 'Bermula dari rehat':** Halaju awal sentiasa sifar ($u = 0\\text{ m/s}$).",
    "💡 **Kata Kunci 'Berhenti' / 'Membrek':** Halaju akhir sentiasa sifar ($v = 0\\text{ m/s}$).",
    "💡 **Kata Kunci 'Nyahpecutan' / 'Perlahan':** Nilai pecutan wajib bertanda negatif ($a = -\\text{nilai}\\text{ m/s}^2$).",
    "💡 **Kata Kunci 'Halaju Malar':** Tiada pecutan ($a = 0\\text{ m/s}^2$). Guna formula ringkas $s = vt$.",
    "💡 **Tips Pindah Tanda:** Bila sebutan negatif melintasi tanda '=', ia akan bertukar menjadi positif.",
    "💡 **Tips Kuasa Dua:** Jika $v^2 = 16$, maka $v = \\sqrt{16} = 4\\text{ m/s}$. Jangan lupa punca kuasakan jawapan akhir!",
    "💡 **Tips Unit SI:** Pastikan jarak dalam meter (m) dan masa dalam saat (s) sebelum membuat pengiraan.",
]

# Bank Sandaran Soalan
FALLBACK_QUESTIONS = [
    {"target": "s", "text": "Sebuah kereta bermula dari keadaan pegun dan memecut secara seragam pada kadar 3 m/s² selama 4 saat. Hitungkan sesaran kereta tersebut."},
    {"target": "t", "text": "Sebuah motosikal bergerak dengan halaju 25 m/s kemudian membrek dengan nyahpecutan seragam 5 m/s² sehingga berhenti. Berapakah masa yang diambil untuk motosikal itu berhenti sepenuhnya?"},
    {"target": "v", "text": "Sebuah lori memecut dari 10 m/s ke halaju akhir v merentasi jarak 75 m dengan pecutan 2 m/s². Tentukan halaju akhir lori tersebut."},
    {"target": "a", "text": "Sebuah van yang bergerak dari halaju 4 m/s mencapai kelajuan 24 m/s dalam tempoh masa 5 saat. Hitungkan pecutan van tersebut."},
    {"target": "u", "text": "Sebuah bas membrek dengan nyahpecutan 3 m/s² selama 4 saat dan berhenti sepenuhnya di lampu isyarat. Tentukan kelajuan awal bas sejurus sebelum membrek."}
]

# Inisialisasi Session State
if "records" not in st.session_state:
    st.session_state.records = []
if "seen_questions" not in st.session_state:
    st.session_state.seen_questions = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "last_review" not in st.session_state:
    st.session_state.last_review = None
if "last_grade" not in st.session_state:
    st.session_state.last_grade = None
if "current_target" not in st.session_state:
    st.session_state.current_target = "s"

# Menu Sisi: Rekod Prestasi & Gred
with st.sidebar:
    st.header("📊 Rekod Gred Percubaan")
    total_attempts = len(st.session_state.records)
    st.write(f"Jumlah Ujian Dicuba: **{total_attempts}**")

    if st.session_state.records:
        st.write("**Sejarah Keputusan:**")
        html_badges = ""
        for rec in st.session_state.records:
            g = rec[-1] if rec else "C"
            html_badges += f"<span class='grade-record-badge badge-{g}'>{rec}</span>"
        st.markdown(html_badges, unsafe_allow_html=True)
        st.caption("Contoh: **1E** = Percubaan 1 (Gred E)")
    else:
        st.caption("Belum ada semakan jawapan. Cuba soalan pertama sekarang!")

    st.divider()
    st.markdown("""
    **Skala Gred Penilaian:**
    - 🟢 **A** : Cemerlang (Fizik & Algebra Sempurna)
    - 🔵 **B** : Sangat Baik (Ralat minor unit/titik perpuluhan)
    - 🟡 **C** : Memuaskan (Ralat manipulasi algebra)
    - 🟠 **D** : Perlu Bimbingan (Silap gantian parameter)
    - 🔴 **E** : Asas Lemah (Formula salah / Konsep silap)
    """)

st.title("📐 KineMath AI Tutor")
st.caption("Modul Bimbingan Kinematik 1D & Diagnosis Algebra (Diploma UC TATI)")

# FUNGSI RAWATAN GAMBAR
def optimize_image(uploaded_file, max_dim=1024):
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    image = ImageOps.autocontrast(image, cutoff=1)
    bright_enhancer = ImageEnhance.Brightness(image)
    image = bright_enhancer.enhance(1.15)
    sharp_enhancer = ImageEnhance.Sharpness(image)
    image = sharp_enhancer.enhance(1.3)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)

# Tetapan API Key
api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("Masukkan Google Gemini API Key:", type="password")

if not api_key:
    st.info("Sila masukkan Gemini API Key di bahagian menu sisi untuk memulakan.")
    st.stop()

client = genai.Client(api_key=api_key)

# FUNGSI PENJANAAN SOALAN
def generate_ai_kinematics_question():
    current_target = st.session_state.current_target
    available_targets = [p for p in ["u", "v", "s", "a", "t"] if p != current_target]
    chosen_target = random.choice(available_targets)

    param_names = {
        "u": "halaju awal (u dalam m/s)",
        "v": "halaju akhir (v dalam m/s)",
        "s": "sesaran atau jarak (s dalam m)",
        "a": "pecutan atau nyahpecutan (a dalam m/s²)",
        "t": "masa yang diambil (t dalam saat)",
    }

    scenarios = [
        "kereta api elektrik memecut keluar dari stesen",
        "kereta lumba membrek sebelum selekoh tajam",
        "dron penghantar barang meluncur di atas trek lurus",
        "pelari pecut 100m memecut dari blok permulaan",
        "bot laju memperlahankan kelajuan menghampiri jeti",
        "kenderaan elektrik mengesan halangan dan berhenti kecemasan",
        "motosikal memotong kenderaan di lebuh raya"
    ]
    chosen_scenario = random.choice(scenarios)
    past_summary = "; ".join(st.session_state.seen_questions[-3:]) if st.session_state.seen_questions else "Tiada"

    gen_prompt = f"""
    Anda pensyarah fizik mekanik. Hasilkan SATU soalan baharu topik Kinematik Linear 1 Dimensi (gerakan mendatar sahaja, bukan graviti) untuk pelajar Diploma Kejuruteraan.
    1. Konteks/Senario: {chosen_scenario}.
    2. SASARAN WAJIB: Pelajar perlu mengira {param_names[chosen_target]} sebagai jawapan akhir.
    3. Nombor hendaklah mudah dikira (nombor bulat atau perpuluhan ringkas).
    4. Pastikan unik berbanding: [{past_summary}].
    5. Berikan teks soalan SAHAJA dalam Bahasa Melayu tanpa sebarang jalan kerja.
    """

    # Senarai model dengan sandaran (fallback)
    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    for model_name in candidate_models:
        try:
            resp = client.models.generate_content(model=model_name, contents=gen_prompt)
            text_generated = resp.text.strip().replace('"', '').replace("`", "")
            if len(text_generated) > 20:
                st.session_state.current_target = chosen_target
                return text_generated
        except Exception:
            continue

    fallback = [item for item in FALLBACK_QUESTIONS if item["target"] != current_target]
    chosen_fb = random.choice(fallback)
    st.session_state.current_target = chosen_fb["target"]
    return chosen_fb["text"]

# Inisialisasi soalan pertama
if "current_question" not in st.session_state:
    st.session_state.current_question = FALLBACK_QUESTIONS[0]["text"]
    st.session_state.seen_questions.append(st.session_state.current_question)

# 1. Bahagian Paparan Soalan
st.subheader("1. Soalan Fizik Kinematik")
st.info(f"📌 **Soalan Sekarang:**\n\n{st.session_state.current_question}")

col_src1, col_src2 = st.columns(2)
with col_src1:
    if st.button("✨ Jana Soalan Baharu (AI)"):
        with st.spinner("AI sedang menggubal soalan baharu..."):
            new_q = generate_ai_kinematics_question()
            st.session_state.current_question = new_q
            st.session_state.seen_questions.append(new_q)
            st.session_state.last_review = None
            st.session_state.last_grade = None
            st.session_state.uploader_key += 1
            st.rerun()

with col_src2:
    if st.checkbox("Tulis / Edit Teks Soalan Sendiri"):
        edited_q = st.text_area("Tulis soalan anda:", value=st.session_state.current_question, height=70)
        st.session_state.current_question = edited_q

# 2. Fasa Ekstraksi Parameter
st.subheader("2. Kenal Pasti Parameter (u, v, s, a, t)")
col1, col2 = st.columns(2)
with col1:
    u_status = st.selectbox("Halaju Awal (u):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    st.markdown(f"<div class='blue-param-indicator'>✓ Status u: <b>{u_status}</b></div>", unsafe_allow_html=True)
    v_status = st.selectbox("Halaju Akhir (v):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    st.markdown(f"<div class='blue-param-indicator'>✓ Status v: <b>{v_status}</b></div>", unsafe_allow_html=True)
    s_status = st.selectbox("Sesaran (s):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    st.markdown(f"<div class='blue-param-indicator'>✓ Status s: <b>{s_status}</b></div>", unsafe_allow_html=True)

with col2:
    a_status = st.selectbox("Pecutan (a):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    st.markdown(f"<div class='blue-param-indicator'>✓ Status a: <b>{a_status}</b></div>", unsafe_allow_html=True)
    t_status = st.selectbox("Masa (t):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2)
    st.markdown(f"<div class='blue-param-indicator'>✓ Status t: <b>{t_status}</b></div>", unsafe_allow_html=True)

# 3. Fasa Pemilihan Formula
st.subheader("3. Pilih Persamaan Kinematik")
equation_options = [
    "-- Pilih Persamaan --",
    "v = u + at",
    "s = ut + (1/2)at²",
    "v² = u² + 2as",
    "s = (1/2)(u + v)t",
]
selected_eq = st.selectbox("Persamaan yang paling sesuai:", equation_options)

latex_mapping = {
    "v = u + at": r"v = u + at",
    "s = ut + (1/2)at²": r"s = ut + \frac{1}{2}at^2",
    "v² = u² + 2as": r"v^2 = u^2 + 2as",
    "s = (1/2)(u + v)t": r"s = \frac{1}{2}(u + v)t",
}

if selected_eq != "-- Pilih Persamaan --":
    formula_latex = latex_mapping.get(selected_eq, selected_eq)
    st.markdown(
        """
        <div class="selected-formula-card">
            <div class="selected-formula-header">📌 Persamaan Yang Anda Pilih:</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.latex(formula_latex)
else:
    st.caption("ℹ️ *Sila pilih salah satu formula di atas.*")

# 4. Fasa Muat Naik Gambar
st.subheader("4. Selesaikan & Semak Jalan Kerja")
pilihan_kamera = st.radio(
    "Kaedah Ambil Gambar:",
    [
        "📁 Pilih dari Galeri / Fail Telefon (Paling Stabil)",
        "📷 Kamera Web Pelayar (Sesuai untuk Laptop)",
    ],
    horizontal=True,
)

image_file = None
if pilihan_kamera == "📁 Pilih dari Galeri / Fail Telefon (Paling Stabil)":
    image_file = st.file_uploader(
        "Pilih Fail / Gambar Kertas Jawapan:",
        type=None,
        key=f"file_up_{st.session_state.uploader_key}",
    )
else:
    image_file = st.camera_input(
        "Ambil gambar kertas jawapan sekarang",
        key=f"cam_up_{st.session_state.uploader_key}",
    )

if image_file:
    st.success("✓ Gambar sedia untuk disemak.")

# Fungsi Panggilan API
def request_ai_review(model_name, prompt_text, processed_img):
    return client.models.generate_content(
        model=model_name,
        contents=[prompt_text, processed_img]
    )

# BUTANG SEMAKAN DENGAN TIPS INTERAKTIF BERGILIR
if image_file and st.button("Semak Jalan Kerja Saya 🚀", type="primary"):
    img = optimize_image(image_file)

    prompt = f"""
    Anda pensyarah Fizik & Matematik UC TATI yang prihatin dan membina. Semak jalan kerja bertulis pelajar ini dengan teliti.

    Konteks:
    - Soalan: {st.session_state.current_question}
    - Parameter Dipilih Pelajar: u={u_status}, v={v_status}, s={s_status}, a={a_status}, t={t_status}
    - Formula Dipilih: {selected_eq}

    Format Ulasan Ringkas dan Tersusun:
    1. **Status Konsep Fizik:** (Adakah pemilihan formula & gantian nombor tepat?)
    2. **Diagnosis Ralat Algebra & Kelemahan Khusus:** (Nyatakan secara spesifik di mana kesilapan berlaku: cthnya silap tanda negatif, gagal punca kuasa, salah pindah sebutan, atau unit tertinggal. Puji jika algebra sempurna)
    3. **Langkah Penyelesaian Yang Betul:** (Tunjukkan jalan kerja ringkas yang sepatutnya)

    Rubrik Gred:
    - Gred A: Fizik & Algebra tepat sepenuhnya.
    - Gred B: Konsep betul, kesilapan kecil pembundaran/unit di akhir.
    - Gred C: Konsep betul, tetapi ada ralat manipulasi algebra di pertengahan.
    - Gred D: Formula betul tetapi silap nilai parameter atau manipulasi algebra dari awal.
    - Gred E: Formula/konsep salah atau tidak lengkap.

    WAJIB tulis tepat SATU tag gred ini di baris PALING AKHIR ulasan:
    [GRED: A] atau [GRED: B] atau [GRED: C] atau [GRED: D] atau [GRED: E]
    """

    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    tips_placeholder = st.empty()
    status_placeholder = st.empty()

    success = False
    full_response = ""

    # Rotasi Tips Semasa Menunggu Respons
    shuffled_tips = random.sample(KINEMATIC_TIPS, len(KINEMATIC_TIPS))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for model_name in candidate_models:
            status_placeholder.caption(f"🔄 Menghubungi model AI ({model_name})...")
            future = executor.submit(request_ai_review, model_name, prompt, img)

            tip_index = 0
            while not future.done():
                current_tip = shuffled_tips[tip_index % len(shuffled_tips)]
                tips_placeholder.markdown(
                    f"<div class='tips-container'>⏳ <b>Sambil menunggu semakan, semak tips ini:</b><br>{current_tip}</div>",
                    unsafe_allow_html=True,
                )
                tip_index += 1

                for _ in range(12):
                    if future.done():
                        break
                    time.sleep(0.2)

            try:
                result = future.result()
                if result and result.text:
                    full_response = result.text.strip()
                    success = True
                    break
            except Exception as err:
                err_str = str(err).lower()
                if any(k in err_str for k in ["429", "quota", "resource_exhausted", "503", "unavailable"]):
                    continue
                else:
                    st.error(f"Ralat sistem: {err}")
                    break

    tips_placeholder.empty()
    status_placeholder.empty()

    if success:
        detected_grade = "C"
        for g in ["A", "B", "C", "D", "E"]:
            if f"[GRED: {g}]" in full_response:
                detected_grade = g
                break

        display_text = full_response
        for g in ["A", "B", "C", "D", "E"]:
            display_text = display_text.replace(f"[GRED: {g}]", "")

        attempt_number = len(st.session_state.records) + 1
        record_code = f"{attempt_number}{detected_grade}"
        st.session_state.records.append(record_code)

        st.session_state.last_review = display_text
        st.session_state.last_grade = detected_grade

# PAPARAN ULASAN & SOKONGAN MOTIVASI
if st.session_state.last_review and st.session_state.last_grade:
    g = st.session_state.last_grade
    st.divider()

    # 1. Kata Semangat & Maklum Balas Berdasarkan Gred
    if g == "A":
        st.balloons()
        st.success("### 🌟 Gred A: Tahap Cemerlang!\n**Tahniah!** Anda menguasai konsep fizik dan kemahiran algebra dengan sangat tepat dan kemas. Prestasi ini membuktikan kefahaman anda kukuh.")
    elif g == "B":
        st.info("### 👍 Gred B: Sangat Baik!\n**Syabas atas usaha mantap!** Konsep utama anda tepat. Anda hanya perlu lebih teliti pada semakan unit akhir atau pembundaran angka bererti.")
    elif g == "C":
        st.warning("### 💡 Gred C: Memuaskan (Perlu Asah Algebra)!\n**Asas fizik anda sudah berada di landasan yang betul!** Anda kehilangan markah pada langkah manipulasi matematik (seperti pemindahan pembolehubah atau operasi punca kuasa).")
    elif g == "D":
        st.warning("### 🔍 Gred D: Teruskan Usaha (Perlu Bimbingan Parameter)!\n**Jangan putus asa!** Anda faham formula asas, tetapi kesilapan berlaku semasa menggantikan nombor ke dalam pembolehubah (contohnya nilai halaju awal atau tanda negatif pecutan).")
    else:
        st.error("### 🚀 Gred E: Ruang Untuk Bangkit & Belajar!\n**Setiap kesilapan adalah langkah awal untuk faham.** Jangan patah semangat! Mari fahami semula pemilihan rumus yang sesuai dengan maklumat yang diberi dalam soalan.")

    # 2. Ulasan Terperinci AI
    st.subheader("📋 Ulasan & Diagnosis Jawapan Anda")
    st.markdown(st.session_state.last_review)

    # 3. Kotak Panduan Fokus Latihan Tambahan
    weakness_guide = {
        "A": "🎯 **Cadangan Fokus:** Teruskan momentum ini dengan mencuba soalan kinematik bertingkat (multi-stage motion)!",
        "B": "🎯 **Fokus Latihan Tambahan:** Latih diri menyemak unit SI di hujung jawapan ($m/s$, $m/s^2$, $s$) sebelum selesai.",
        "C": "🎯 **Fokus Latihan Tambahan:** Buat 3-5 latihan manipulasi algebra ringkas — terutamanya melibatkan $v^2 = u^2 + 2as$ dan punca kuasa dua.",
        "D": "🎯 **Fokus Latihan Tambahan:** Buat senarai $u, v, s, a, t$ di tepi kertas sebelum mula menulis jalan kerja bagi mengelak silap gantian nombor.",
        "E": "🎯 **Fokus Latihan Tambahan:** Ulang kaji perbezaan antara halaju awal ($u$) dan halaju akhir ($v$), serta kata kunci seperti 'pegun' dan 'berhenti'."
    }
    st.markdown(
        f"""
        <div class="advice-box">
            <b>💡 Nasihat & Pelan Tindakan Pensyarah:</b><br>
            {weakness_guide.get(g, "")}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Tawaran Mencuba Latihan Seterusnya
    st.write("---")
    st.write("### 🔁 Bersedia Untuk Cuba Lagi?")
    col_retry1, col_retry2 = st.columns(2)

    with col_retry1:
        if st.button("🎯 Cuba Soalan Latihan Baharu", type="primary", use_container_width=True):
            with st.spinner("Menjana soalan latihan baharu..."):
                new_q = generate_ai_kinematics_question()
                st.session_state.current_question = new_q
                st.session_state.seen_questions.append(new_q)
                st.session_state.last_review = None
                st.session_state.last_grade = None
                st.session_state.uploader_key += 1
                st.rerun()

    with col_retry2:
        if st.button("🔄 Ulang Semula Soalan Ini", use_container_width=True):
            st.session_state.last_review = None
            st.session_state.last_grade = None
            st.session_state.uploader_key += 1
            st.rerun()
