import io
import random
import time
from google import genai
from PIL import Image, ImageEnhance, ImageOps
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

/* Kad Paparan Formula Terpilih (Besar & Jelas) */
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
.selected-formula-math {
    color: #0a3880;
    font-size: 1.25rem;
    font-weight: 700;
}

/* Lencana Rekod Percubaan (cth: 1E, 2A) */
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
}
</style>
""",
    unsafe_allow_html=True,
)

# Senarai Tip Kata Kunci Rahsia Kinematik Linear Sahaja
KINEMATIC_TIPS = [
    "💡 **Kata Kunci 'Pegun' / 'Bermula dari rehat':** Halaju awal adalah sifar ($u = 0\\text{ m/s}$).",
    "💡 **Kata Kunci 'Berhenti' / 'Membrek hingga pegun':** Halaju akhir adalah sifar ($v = 0\\text{ m/s}$).",
    "💡 **Kata Kunci 'Nyahpecutan' / 'Perlahan':** Nilai pecutan wajib bertanda negatif ($a = -\\text{nilai}\\text{ m/s}^2$).",
    "💡 **Kata Kunci 'Halaju Malar / Seragam':** Tiada pecutan ($a = 0\\text{ m/s}^2$). Terus gunakan formula ringkas $s = vt$.",
    "💡 **Kata Kunci 'Berpatah Balik':** Pada detik objek berpatah balik, halajunya menjadi sifar seketika ($v = 0\\text{ m/s}$).",
]

# Bank Sandaran Sahaja (Hanya diguna jika sambungan AI terputus)
FALLBACK_QUESTIONS = [
    {"target": "s", "text": "Sebuah kereta bermula dari keadaan pegun dan memecut secara seragam pada kadar 3 m/s² selama 4 saat. Hitungkan sesaran kereta tersebut."},
    {"target": "t", "text": "Sebuah motosikal bergerak dengan halaju 25 m/s kemudian membrek dengan nyahpecutan seragam 5 m/s² sehingga berhenti. Berapakah masa yang diambil untuk motosikal itu berhenti sepenuhnya?"},
    {"target": "v", "text": "Sebuah lori memecut dari 10 m/s ke halaju akhir v merentasi jarak 75 m dengan pecutan 2 m/s². Tentukan halaju akhir lori tersebut."},
    {"target": "a", "text": "Sebuah van yang bergerak dari halaju 4 m/s mencapai kelajuan 24 m/s dalam tempoh masa 5 saat. Hitungkan pecutan van tersebut."},
    {"target": "u", "text": "Sebuah bas membrek dengan nyahpecutan 3 m/s² selama 4 saat dan berhenti sepenuhnya di lampu isyarat. Tentukan kelajuan awal bas sejurus sebelum membrek."}
]

# Inisialisasi Session State Asas
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
        st.write("**Sejarah Keputusan (Percubaan & Gred):**")
        html_badges = ""
        for rec in st.session_state.records:
            g = rec[-1] if rec else "C"
            html_badges += f"<span class='grade-record-badge badge-{g}'>{rec}</span>"
        st.markdown(html_badges, unsafe_allow_html=True)
        st.caption("Contoh: **1E** = Percubaan 1 mendapat Gred E")
    else:
        st.caption("Belum ada semakan jawapan. Cuba soalan pertama sekarang!")

    st.divider()
    st.markdown("""
    **Skala Gred Penilaian:**
    - 🟢 **A** : Cemerlang (Fizik & Algebra Tepat)
    - 🔵 **B** : Sangat Baik (Ralat minor unit / angka)
    - 🟡 **C** : Memuaskan (Ralat langkah algebra)
    - 🟠 **D** : Perlu Bimbingan (Gantian parameter silap)
    - 🔴 **E** : Asas Lemah (Formula / Konsep salah)
    """)

st.title("📐 KineMath AI Tutor")
st.caption("Modul Bimbingan Kinematik 1D & Diagnosis Algebra (Diploma UC TATI)")

# FUNGSI RAWATAN & PENGOPTIMUMAN GAMBAR
def optimize_image(uploaded_file, max_dim=1024):
    """
    1. Membaca gambar daripada pelbagai peranti & format.
    2. Membetulkan orientasi EXIF telefon (elak gambar terbalik/senget).
    3. Mengecilkan dimensi ke saiz optimum untuk diproses oleh AI.
    4. Auto-Enhance: Mencerahkan kawasan gelap dan menaikkan kontras tulisan tangan.
    5. Menghasilkan fail JPEG yang ringan (~100KB-300KB) tetapi sangat jelas.
    """
    image = Image.open(uploaded_file)

    # 1. Betulkan orientasi EXIF
    image = ImageOps.exif_transpose(image)

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # 2. Kurangkan dimensi
    image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # 3. Rawatan Pencahayaan & Ketajaman Tulisan Tangan
    image = ImageOps.autocontrast(image, cutoff=1)

    bright_enhancer = ImageEnhance.Brightness(image)
    image = bright_enhancer.enhance(1.15)

    sharp_enhancer = ImageEnhance.Sharpness(image)
    image = sharp_enhancer.enhance(1.3)

    # 4. Simpan ke penimbal dengan mampatan JPEG berkualiti seimbang
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80, optimize=True)
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

# FUNGSI UTAMA: PENJANAAN SOALAN OLEH AI SECARA SEGAR & DINAMIK
def generate_ai_kinematics_question():
    """Menjana soalan baharu secara dinamik menggunakan AI dengan sasaran parameter berbeza"""
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
        "kren kontena menarik beban di atas landasan mendatar",
        "motosikal memotong kenderaan di lebuh raya"
    ]
    chosen_scenario = random.choice(scenarios)
    past_summary = "; ".join(st.session_state.seen_questions[-3:]) if st.session_state.seen_questions else "Tiada"

    gen_prompt = f"""
    Anda pensyarah fizik mekanik. Hasilkan SATU soalan baharu topik Kinematik Linear 1 Dimensi (gerakan mendatar sahaja, bukan graviti/jatuh bebas) untuk pelajar Diploma Kejuruteraan.

    PANDUAN PEMBINAAN SOALAN:
    1. Konteks/Senario: {chosen_scenario}.
    2. SASARAN WAJIB: Soalan mesti menghendaki pelajar mengira {param_names[chosen_target]} sebagai jawapan akhir.
    3. Nyatakan nilai-nilai parameter lain secara jelas dan berikan angka yang logik serta mudah dikira (nombor bulat atau perpuluhan mudah).
    4. Pastikan ayat soalan UNIK dan berbeza daripada soalan lepas: [{past_summary}].
    5. FORMAT OUTPUT: Berikan teks soalan SAHAJA dalam Bahasa Melayu. JANGAN sertakan jawapan, formula, jalan kerja, atau tajuk pengenalan.
    """

    candidate_models = ["gemini-3.8-flash"]
    for model_name in candidate_models:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=gen_prompt
            )
            text_generated = resp.text.strip().replace('"', '').replace("`", "")
            if len(text_generated) > 20:
                st.session_state.current_target = chosen_target
                return text_generated
        except Exception:
            continue

    # Sandaran jika panggilan model terputus
    fallback = [item for item in FALLBACK_QUESTIONS if item["target"] != current_target]
    chosen_fb = random.choice(fallback)
    st.session_state.current_target = chosen_fb["target"]
    return chosen_fb["text"]

# Pastikan soalan pertama dimuatkan menggunakan AI jika belum ada
if "current_question" not in st.session_state:
    with st.spinner("Menjana soalan kinematik pertama daripada AI..."):
        first_q = generate_ai_kinematics_question()
        st.session_state.current_question = first_q
        st.session_state.seen_questions.append(first_q)

# 2. Bahagian Paparan Soalan
st.subheader("1. Soalan Fizik Kinematik (Dijana AI)")
st.info(f"📌 **Soalan Sekarang:**\n\n{st.session_state.current_question}")

col_src1, col_src2 = st.columns(2)
with col_src1:
    if st.button("✨ Jana Soalan Baharu (AI Generator)"):
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

# 3. Fasa Ekstraksi Parameter
st.subheader("2. Kenal Pasti Parameter (u, v, s, a, t)")
st.write("Tentukan status bagi setiap kuantiti gerakan:")

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

# 4. Fasa Pemilihan Formula (PERKARA 3 DENGAN PAPARAN JELAS DI BAWAH DROPDOWN)
st.subheader("3. Pilih Persamaan Kinematik")
equation_options = [
    "-- Pilih Persamaan --",
    "v = u + at",
    "s = ut + (1/2)at²",
    "v² = u² + 2as",
    "s = (1/2)(u + v)t",
]
selected_eq = st.selectbox("Persamaan yang paling sesuai:", equation_options)

# Pemetaan format matematik (LaTeX) untuk paparan yang kemas dan jelas
latex_mapping = {
    "v = u + at": r"v = u + at",
    "s = ut + (1/2)at²": r"s = ut + \frac{1}{2}at^2",
    "v² = u² + 2as": r"v^2 = u^2 + 2as",
    "s = (1/2)(u + v)t": r"s = \frac{1}{2}(u + v)t",
}

if selected_eq != "-- Pilih Persamaan --":
    formula_latex = latex_mapping.get(selected_eq, selected_eq)
    st.markdown(
        f"""
        <div class="selected-formula-card">
            <div class="selected-formula-header">📌 Persamaan Yang Anda Pilih:</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Paparkan formula dalam saiz besar menggunakan paparan formula matematik Streamlit
    st.latex(formula_latex)
else:
    st.caption("ℹ️ *Sila pilih salah satu formula di atas yang sepadan dengan parameter yang dikenal pasti.*")

# 5. Fasa Muat Naik / Tangkap Gambar Jawapan
st.subheader("4. Selesaikan & Semak Algebra")
pilihan_kamera = st.radio(
    "Kaedah Ambil Gambar:",
    [
        "📁 Pilih dari Galeri / Fail Telefon (Paling Stabil)",
        "📷 Kamera Web Pelayar (Sesuai untuk Telefon & Laptop)",
    ],
    horizontal=True,
)

image_file = None
if pilihan_kamera == "📁 Pilih dari Galeri / Fail Telefon (Paling Stabil)":
    st.caption("💡 **Tips Telefon:** Ambil gambar kertas jawapan menggunakan kamera biasa telefon terlebih dahulu, kemudian klik butang di bawah dan pilih daripada Galeri / Fail.")
    image_file = st.file_uploader(
        "Pilih Fail / Gambar Kertas Jawapan:",
        type=None,
        key=f"file_up_{st.session_state.uploader_key}",
    )
else:
    st.caption("💡 **Auto-Pencahayaan:** Gambar akan dicerahkan dan ditajamkan kontrasnya secara automatik sekiranya bilik malap.")
    image_file = st.camera_input(
        "Ambil gambar kertas jawapan sekarang",
        key=f"cam_up_{st.session_state.uploader_key}",
    )

if image_file:
    st.success("✓ Gambar sedia untuk disemak.")

# Butang Semakan & Penilaian Gred
if image_file and st.button("Semak Jalan Kerja Saya 🚀", type="primary"):
    random_tip = random.choice(KINEMATIC_TIPS)
    tips_placeholder = st.empty()
    tips_placeholder.markdown(
        f"<div class='tips-container'>⏳ <b>Sementara menunggu semakan:</b><br>{random_tip}</div>",
        unsafe_allow_html=True,
    )

    with st.spinner("Mencerahkan & memproses gambar jawapan..."):
        img = optimize_image(image_file)

    prompt = f"""
    Anda pensyarah Fizik & Matematik UC TATI. Semak gambar jalan kerja tulisan tangan pelajar ini secara profesional, padat dan berstruktur.

    Konteks:
    - Soalan: {st.session_state.current_question}
    - Parameter Dipilih Pelajar: u={u_status}, v={v_status}, s={s_status}, a={a_status}, t={t_status}
    - Formula Dipilih: {selected_eq}

    Format Ulasan Ringkas (Maksimum 2 ayat setiap seksyen):
    1. **Status Konsep Fizik:** (Adakah pemilihan formula & gantian nombor tepat?)
    2. **Diagnosis Ralat Algebra:** (Nyatakan baris kesilapan tanda/pindah/pecahan/kuasa jika ada, atau puji jika tepat)
    3. **Langkah Betul:** (Tunjukkan jalan penyelesaian ringkas yang sepatutnya)

    Rubrik Gred:
    - Gred A: Konsep fizik tepat, algebra sempurna, jawapan akhir betul.
    - Gred B: Formula dan konsep tepat, cuma ada kesilapan kecil pembundaran/unit di akhir.
    - Gred C: Konsep fizik betul, tetapi ada ralat manipulasi algebra di peringkat pertengahan.
    - Gred D: Formula tepat tetapi gantian parameter salah atau algebra bercelaru dari awal.
    - Gred E: Formula salah, konsep kinematik tidak tepat atau jawapan belum lengkap.

    WAJIB tulis tepat satu tag gred ini di baris PALING AKHIR ulasan:
    [GRED: A] atau [GRED: B] atau [GRED: C] atau [GRED: D] atau [GRED: E]
    """

    candidate_models = ["gemini-3.8-flash"]
    success = False
    response_placeholder = st.empty()
    full_response = ""

    with st.spinner("AI sedang menganalisis dan menilai gred..."):
        for model_name in candidate_models:
            try:
                response_stream = client.models.generate_content_stream(
                    model=model_name, contents=[prompt, img]
                )
                for chunk in response_stream:
                    if chunk.text:
                        full_response += chunk.text
                        display_live = full_response
                        for g in ["A", "B", "C", "D", "E"]:
                            display_live = display_live.replace(f"[GRED: {g}]", "")
                        response_placeholder.markdown(display_live)

                success = True
                break
            except Exception as err:
                err_msg = str(err).lower()
                if (
                    "503" in err_msg
                    or "unavailable" in err_msg
                    or "high demand" in err_msg
                    or "not found" in err_msg
                ):
                    time.sleep(1)
                    continue
                else:
                    st.error(f"Ralat ({model_name}): {err}")
                    break

        tips_placeholder.empty()

        if success:
            detected_grade = "C"
            for g in ["A", "B", "C", "D", "E"]:
                if f"[GRED: {g}]" in full_response:
                    detected_grade = g
                    break

            attempt_number = len(st.session_state.records) + 1
            record_code = f"{attempt_number}{detected_grade}"
            st.session_state.records.append(record_code)

            st.session_state.last_review = full_response
            st.session_state.last_grade = detected_grade

            st.divider()
            if detected_grade == "A":
                st.balloons()
                st.success("### 🌟 GRED A (Cemerlang)\n\n**Hebat sekali!** Penguasaan konsep fizik dan ketelitian algebra anda bertaraf kelas pertama. Kekalkan momentum cemerlang ini!")
            elif detected_grade == "B":
                st.info("### 👍 GRED B (Sangat Baik)\n\n**Usaha yang sangat mantap!** Konsep dan jalan kerja utama anda sudah kukuh. Cuma perlu sedikit lebih teliti pada semakan unit atau pengiraan akhir.")
            elif detected_grade == "C":
                st.warning("### 💡 GRED C (Memuaskan)\n\n**Asas fizik anda sudah betul!** Beri perhatian lebih pada pemindahan simbol dan manipulasi algebra di langkah pertengahan.")
            elif detected_grade == "D":
                st.warning("### 🔍 GRED D (Perlu Usaha Tambahan)\n\n**Jangan berputus asa!** Semak semula gantian nilai ke dalam pembolehubah formula. Teliti di mana kesilapan berlaku pada diagnosis di atas.")
            else:
                st.error("### 🚀 GRED E (Bina Semula Asas)\n\n**Setiap pakar bermula dari kesilapan.** Ambil masa fahami semula pemilihan formula dan nilai parameter. Cuba soalan baharu di bawah!")
