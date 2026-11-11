import io
import random
import time
from google import genai
from PIL import Image
import streamlit as st

# Konfigurasi paparan mesra telefon pintar
st.set_page_config(
    page_title="KineMath Remedial - UC TATI", page_icon="📐", layout="centered"
)

# --- SUNTIKAN CSS: KOTAK BIRU, INDIKATOR BIRU & LENCANA GRED ---
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

/* Lencana Biru di bawah setiap dropdown parameter & formula */
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

# Senarai Lengkap Tip & Kata Kunci Rahsia Kinematik Linear
KINEMATIC_TIPS = [
    "💡 **Kata Kunci 'Pegun' / 'Bermula dari rehat':** Halaju awal adalah sifar ($u = 0\\text{ m/s}$).",
    "💡 **Kata Kunci 'Berhenti' / 'Membrek hingga pegun':** Halaju akhir adalah sifar ($v = 0\\text{ m/s}$).",
    "💡 **Kata Kunci 'Nyahpecutan' / 'Perlahan':** Nilai pecutan wajib bertanda negatif ($a = -\\text{nilai}\\text{ m/s}^2$).",
    "💡 **Kata Kunci 'Halaju Malar / Seragam':** Tiada pecutan ($a = 0\\text{ m/s}^2$). Terus gunakan formula ringkas $s = vt$.",
    "💡 **Kata Kunci 'Berpatah Balik':** Pada detik objek berpatah balik, halajunya menjadi sifar seketika ($v = 0\\text{ m/s}$).",
    "💡 **Tips Pilihan Formula (Tiada $s$):** Jika sesaran tidak dinyatakan atau dicari, gunakan: $v = u + at$",
    "💡 **Tips Pilihan Formula (Tiada $a$):** Jika tiada maklumat pecutan, gunakan: $s = \\frac{1}{2}(u + v)t$",
    "💡 **Tips Pilihan Formula (Tiada $v$):** Jika halaju akhir tidak terlibat, gunakan: $s = ut + \\frac{1}{2}at^2$",
    "💡 **Tips Pilihan Formula (Tiada $t$):** Jika masa tidak dinyatakan atau dicari, gunakan: $v^2 = u^2 + 2as$",
    "💡 **Perangkap Unit:** Jika soalan memberi kelajuan dalam $\\text{km/j}$, bahagikan dengan $3.6$ untuk tukar ke $\\text{m/s}$ sebelum memasukkan ke dalam rumus.",
    "💡 **Perangkap Masa:** 'Dalam saat ke-3' bukan $t = 3\\text{ s}$, sebaliknya jarak dalam saat tersebut ialah $\\Delta s = s_3 - s_2$.",
    "💡 **Masa Tindak Balas:** Semasa tempoh bertindak balas sebelum brek ditekan, kenderaan bergerak dengan halaju malar ($a = 0$).",
    "💡 **Ketelitian Algebra:** Bila memindahkan kuasa dua ($v^2$), pastikan punca kuasa dua $(\\sqrt{\\dots})$ merangkumi keseluruhan hasil tambah atau tolak di sebelah kanan.",
    "💡 **Semakan Unit Akhir:** Pastikan unit asas konsisten — halaju ($\\text{m/s}$), pecutan ($\\text{m/s}^2$), masa ($\\text{s}$), dan sesaran ($\\text{m}$).",
]

# Bank Soalan Dikategorikan Berdasarkan Parameter Yang Dicari (target)
QUESTION_BANK_CATEGORIZED = [
    {
        "target": "s",
        "text": "Sebuah kereta bermula dari keadaan pegun dan memecut secara seragam pada kadar 3 m/s² selama 4 saat. Hitungkan sesaran kereta tersebut.",
    },
    {
        "target": "t",
        "text": "Sebuah motosikal bergerak dengan halaju 25 m/s kemudian membrek dengan nyahpecutan seragam 5 m/s² sehingga berhenti. Berapakah masa yang diambil untuk motosikal itu berhenti sepenuhnya?",
    },
    {
        "target": "v",
        "text": "Sebuah lori memecut dari 10 m/s ke halaju akhir v merentasi jarak 75 m dengan pecutan 2 m/s². Tentukan halaju akhir lori tersebut.",
    },
    {
        "target": "a",
        "text": "Sebuah van yang bergerak dari halaju 4 m/s mencapai kelajuan 24 m/s dalam tempoh masa 5 saat. Hitungkan pecutan van tersebut.",
    },
    {
        "target": "u",
        "text": "Sebuah bas membrek dengan nyahpecutan 3 m/s² selama 4 saat dan berhenti sepenuhnya di lampu isyarat. Tentukan kelajuan awal bas sejurus sebelum membrek.",
    },
    {
        "target": "s",
        "text": "Sebuah kereta api bergerak pada halaju 30 m/s menekan brek kecemasan dan berhenti selepas 6 saat. Hitungkan jarak yang dilalui sepanjang tempoh membrek tersebut.",
    },
    {
        "target": "t",
        "text": "Sebuah kenderaan elektrik memecut dari keadaan pegun pada kadar 4 m/s² sehingga merentasi jarak 72 m. Cari masa yang diambil untuk perjalanan itu.",
    },
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
if "current_question" not in st.session_state:
    st.session_state.current_question = QUESTION_BANK_CATEGORIZED[0]["text"]
    st.session_state.seen_questions.append(QUESTION_BANK_CATEGORIZED[0]["text"])

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
            html_badges += (
                f"<span class='grade-record-badge badge-{g}'>{rec}</span>"
            )
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
    api_key = st.sidebar.text_input(
        "Masukkan Google Gemini API Key:", type="password"
    )

if not api_key:
    st.info(
        "Sila masukkan Gemini API Key di bahagian menu sisi untuk memulakan."
    )
    st.stop()

client = genai.Client(api_key=api_key)


# Fungsi Dapatkan Soalan Seterusnya dengan Variasi Parameter yang Berbeza
def get_varied_next_question():
    current_target = st.session_state.current_target
    available_targets = [
        p for p in ["u", "v", "s", "a", "t"] if p != current_target
    ]
    chosen_target = random.choice(available_targets)

    # Cari soalan dalam bank soalan yang belum pernah dijawab dan mensasarkan parameter baharu
    candidates = [
        item
        for item in QUESTION_BANK_CATEGORIZED
        if item["target"] == chosen_target
        and item["text"] not in st.session_state.seen_questions
    ]

    if candidates:
        selected = random.choice(candidates)
        st.session_state.current_target = selected["target"]
        return selected["text"]

    # Jika soalan dalam bank habis bagi sasaran tersebut, minta AI jana soalan unik dengan target berbeza
    param_names = {
        "u": "halaju awal (u)",
        "v": "halaju akhir (v)",
        "s": "jarak atau sesaran (s)",
        "a": "pecutan atau nyahpecutan (a)",
        "t": "masa yang diambil (t)",
    }

    past_summary = "; ".join(st.session_state.seen_questions[-3:])
    gen_prompt = f"""
    Hasilkan satu soalan baharu fizik topik Kinematik 1 Dimensi (gerakan mendatar, bukan jatuh bebas) untuk pelajar Diploma Kejuruteraan.
    SYARAT WAJIB:
    1. Soalan MESTI meminta pelajar mencari {param_names[chosen_target]} sebagai jawapan akhir.
    2. Jangan buat soalan yang mencari parameter yang sama seperti soalan-soalan sebelum ini.
    3. Rujukan soalan terdahulu (elakkan sama): [{past_summary}].
    Tulis TEKS SOALAN SAHAJA dalam Bahasa Melayu ringkas tanpa sebarang jalan kerja.
    """
    try:
        resp = client.models.generate_content(
            model="gemini-3.8-flash", contents=gen_prompt
        )
        text_generated = resp.text.strip()
        if text_generated:
            st.session_state.current_target = chosen_target
            return text_generated
    except Exception:
        pass

    # Fallback
    fallback = [
        item
        for item in QUESTION_BANK_CATEGORIZED
        if item["target"] != current_target
    ]
    chosen = random.choice(fallback)
    st.session_state.current_target = chosen["target"]
    return chosen["text"]


# 2. Bahagian Paparan Soalan
st.subheader("1. Soalan Fizik Kinematik")
st.info(f"📌 **Soalan Sekarang:**\n\n{st.session_state.current_question}")

col_src1, col_src2 = st.columns(2)
with col_src1:
    if st.button("🎲 Tukar Variasi Soalan (Parameter Lain)"):
        st.session_state.current_question = get_varied_next_question()
        st.session_state.seen_questions.append(st.session_state.current_question)
        st.session_state.last_review = None
        st.session_state.last_grade = None
        st.session_state.uploader_key += 1
        st.rerun()

with col_src2:
    if st.checkbox("Tulis / Edit Teks Soalan Sendiri"):
        edited_q = st.text_area(
            "Tulis soalan anda:",
            value=st.session_state.current_question,
            height=70,
        )
        st.session_state.current_question = edited_q

# 3. Fasa Ekstraksi Parameter
st.subheader("2. Kenal Pasti Parameter (u, v, s, a, t)")
st.write("Tentukan status bagi setiap kuantiti gerakan:")

col1, col2 = st.columns(2)
with col1:
    u_status = st.selectbox(
        "Halaju Awal (u):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2
    )
    st.markdown(
        f"<div class='blue-param-indicator'>✓ Status u: <b>{u_status}</b></div>",
        unsafe_allow_html=True,
    )

    v_status = st.selectbox(
        "Halaju Akhir (v):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2
    )
    st.markdown(
        f"<div class='blue-param-indicator'>✓ Status v: <b>{v_status}</b></div>",
        unsafe_allow_html=True,
    )

    s_status = st.selectbox(
        "Sesaran (s):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2
    )
    st.markdown(
        f"<div class='blue-param-indicator'>✓ Status s: <b>{s_status}</b></div>",
        unsafe_allow_html=True,
    )

with col2:
    a_status = st.selectbox(
        "Pecutan (a):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2
    )
    st.markdown(
        f"<div class='blue-param-indicator'>✓ Status a: <b>{a_status}</b></div>",
        unsafe_allow_html=True,
    )

    t_status = st.selectbox(
        "Masa (t):", ["Diberi", "Dicari", "Tidak Terlibat"], index=2
    )
    st.markdown(
        f"<div class='blue-param-indicator'>✓ Status t: <b>{t_status}</b></div>",
        unsafe_allow_html=True,
    )

# 4. Fasa Pemilihan Formula
st.subheader("3. Pilih Persamaan Kinematik")
equation_options = [
    "-- Pilih Persamaan --",
    "v = u + at",
    "s = ut + (1/2)at²",
    "v² = u² + 2as",
    "s = (1/2)(u + v)t",
]
selected_eq = st.selectbox("Persamaan yang paling sesuai:", equation_options)

if selected_eq != "-- Pilih Persamaan --":
    st.markdown(
        f"<div class='blue-param-indicator'>✓ Formula Dipilih: <b>{selected_eq}</b></div>",
        unsafe_allow_html=True,
    )

# 5. Fasa Muat Naik / Tangkap Gambar Jawapan
st.subheader("4. Selesaikan & Semak Algebra")
pilihan_kamera = st.radio(
    "Kaedah Ambil Gambar:",
    [
        "📱 Buka Kamera Telefon / Muat Naik Fail (Paling Mudah)",
        "📷 Kamera Web Pelayar (Streamlit)",
    ],
    horizontal=True,
)

image_file = None
if pilihan_kamera == "📱 Buka Kamera Telefon / Muat Naik Fail (Paling Mudah)":
    st.caption(
        "💡 *Tips:* Klik butang di bawah dan pilih kamera telefon untuk terus menangkap gambar tulisan tangan."
    )
    image_file = st.file_uploader(
        "Pilih Fail / Buka Kamera",
        type=["jpg", "jpeg", "png"],
        key=f"file_up_{st.session_state.uploader_key}",
    )
else:
    image_file = st.camera_input(
        "Ambil gambar kertas jawapan",
        key=f"cam_up_{st.session_state.uploader_key}",
    )

# Butang Semakan & Penilaian Gred
if image_file and st.button("Semak Jalan Kerja Saya 🚀", type="primary"):
    # 1. Pilih Tips Rawak dan Paparkan Semasa Waktu Menunggu
    random_tip = random.choice(KINEMATIC_TIPS)
    tips_placeholder = st.empty()
    tips_placeholder.markdown(
        f"<div class='tips-container'>⏳ <b>Sementara menunggu semakan:</b><br>{random_tip}</div>",
        unsafe_allow_html=True,
    )

    with st.spinner("Memproses gambar jawapan..."):
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

    candidate_models = [
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
    ]
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
                            display_live = display_live.replace(
                                f"[GRED: {g}]", ""
                            )
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

        # 2. Hentikan & padam paparan tips sebaik sahaja proses selesai
        tips_placeholder.empty()

        if success:
            # Kenal pasti gred daripada ulasan
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

            # Paparan Kotak Gred & Kata-Kata Semangat (Rekod kod dikeluarkan dari tajuk)
            st.divider()
            if detected_grade == "A":
                st.balloons()
                st.success(
                    "### 🌟 GRED A (Cemerlang)\n\n**Hebat sekali!** Penguasaan konsep fizik dan ketelitian algebra anda bertaraf kelas pertama. Kekalkan momentum cemerlang ini!"
                )
            elif detected_grade == "B":
                st.info(
                    "### 👍 GRED B (Sangat Baik)\n\n**Usaha yang sangat mantap!** Konsep dan jalan kerja utama anda sudah kukuh. Cuma perlu sedikit lebih teliti pada semakan unit atau pengiraan akhir."
                )
            elif detected_grade == "C":
                st.warning(
                    "### 💡 GRED C (Memuaskan)\n\n**Asas fizik anda sudah betul!** Beri perhatian lebih pada pemindahan simbol dan manipulasi algebra di langkah pertengahan."
                )
            elif detected_grade == "D":
                st.warning(
                    "### 🔍 GRED D (Perlu Usaha Tambahan)\n\n**Jangan berputus asa!** Semak semula gantian nilai ke dalam pembolehubah formula. Teliti di mana kesilapan berlaku pada diagnosis di atas."
                )
            else:
                st.error(
                    "### 🚀 GRED E (Bina Semula Asas)\n\n**Setiap pakar bermula dari kesilapan.** Ambil masa fahami semula pemilihan formula dan nilai parameter. Cuba soalan baharu di bawah!"
                )
        else:
            st.error("Pelayan AI sedang sibuk. Sila tekan butang sekali lagi.")

# 6. Bahagian Menu Langkah Seterusnya (Bersih tanpa teks rekod/parameter)
if st.session_state.last_review:
    st.divider()
    st.subheader("🎯 Langkah Seterusnya")

    if st.button("➡️ Cuba Soalan Seterusnya (Variasi Parameter Baharu)", type="primary"):
        st.session_state.current_question = get_varied_next_question()
        st.session_state.seen_questions.append(st.session_state.current_question)
        st.session_state.last_review = None
        st.session_state.last_grade = None
        st.session_state.uploader_key += 1
        st.rerun()
