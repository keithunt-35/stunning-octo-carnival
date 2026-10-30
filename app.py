"""
Label & Package Reader Uganda — Picture Translate
A modern, mobile-friendly web app for Uganda with white background and green & blue color scheme.
Picture-only input (camera / upload) with structured English and simple Luganda voice outputs.
Repository: https://github.com/keithunt-35/stunning-octo-carnival
"""

import html as html_module
import io
import json
import os
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from gemma_client import read_label, LabelReaderError
from parser import split_sections

load_dotenv()

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Picture Translate | Uganda Label Reader",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------------
# Custom CSS: White Background + Green & Blue Color Scheme
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Clean white & slate background */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #0f172a !important;
    }
    
    /* Green Primary Action Buttons */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background-color: #059669 !important; /* Green */
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 0 2px 6px rgba(5, 150, 105, 0.25) !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
        background-color: #047857 !important;
        transform: translateY(-1px);
    }
    
    /* Blue Secondary Buttons */
    button[kind="secondary"], .stButton > button:not([kind="primary"]) {
        background-color: #2563eb !important; /* Blue */
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.6rem 1.3rem !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.15s ease-in-out !important;
    }
    button[kind="secondary"]:hover, .stButton > button:not([kind="primary"]):hover {
        background-color: #1d4ed8 !important;
        transform: translateY(-1px);
    }

    /* Tabs styling (Green / Blue active) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 4px !important;
        border: 1px solid #e2e8f0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 700 !important;
        border-radius: 8px !important;
        color: #475569 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* Output Card Containers */
    .pt-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .pt-card-luganda {
        border-left: 6px solid #059669 !important;
        background-color: #f0fdf4 !important;
    }
    .pt-card-english {
        border-left: 6px solid #2563eb !important;
        background-color: #eff6ff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def highlight_missing(text: str) -> str:
    """Highlight 'Not clearly visible' in a distinct red badge."""
    lines = text.split("\n")
    out = []
    for line in lines:
        escaped = html_module.escape(line)
        if "not clearly visible" in line.lower():
            out.append(
                f"<span style='color:#b91c1c;font-weight:bold;"
                f"background-color:#fee2e2;padding:3px 8px;"
                f"border-radius:6px;display:inline-block;margin:3px 0;"
                f"border:1px solid #fca5a5;'>"
                f"⚠️ {escaped}</span>"
            )
        else:
            out.append(escaped)
    return "\n".join(out)


def count_missing(text: str) -> tuple[int, int]:
    """Return (missing_count, total_lines) for a section's text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    total = len(lines)
    missing = sum(1 for l in lines if "not clearly visible" in l.lower())
    return missing, total


def luganda_action_buttons(luganda_text: str):
    """Render Copy and Read-aloud voice buttons in green & blue."""
    if not luganda_text:
        return
    luganda_js = json.dumps(luganda_text)
    st.html(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:14px;">
          <button id="copyBtn"
            style="background:#059669;color:#fff;border:none;padding:10px 18px;
                   border-radius:10px;font-size:14px;font-weight:bold;cursor:pointer;
                   box-shadow:0 2px 4px rgba(5,150,105,0.25);">
            📋 Copy Luganda / Kopi
          </button>
          <button id="readBtn"
            style="background:#2563eb;color:#fff;border:none;padding:10px 18px;
                   border-radius:10px;font-size:14px;font-weight:bold;cursor:pointer;
                   box-shadow:0 2px 4px rgba(37,99,235,0.25);">
            🔊 Read Aloud / Wuliriza
          </button>
        </div>
        <div id="readStatus" style="font-size:12px;color:#059669;font-weight:600;margin-top:8px;"></div>

        <script>
        const lugandaText = {luganda_js};
        let isSpeaking = false;

        function copyLuganda() {{
          const btn = document.getElementById('copyBtn');
          const oldText = btn.textContent;
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(lugandaText).then(() => {{
              btn.textContent = '✅ Copied! / Ekopeddwa!';
              setTimeout(() => {{ btn.textContent = oldText; }}, 2000);
            }});
          }}
        }}

        function readLuganda() {{
          const btn = document.getElementById('readBtn');
          const status = document.getElementById('readStatus');
          if (!window.speechSynthesis) {{
            alert('Speech is not supported in this browser.');
            return;
          }}
          if (isSpeaking) {{
            window.speechSynthesis.cancel();
            isSpeaking = false;
            btn.textContent = '🔊 Read Aloud / Wuliriza';
            status.textContent = '';
            return;
          }}
          const u = new SpeechSynthesisUtterance(lugandaText);
          u.rate = 0.9;
          u.pitch = 1.0;
          u.onstart = () => {{
            isSpeaking = true;
            btn.textContent = '⏹️ Stop / Lekerawo';
            status.textContent = 'Speaking... / Nsoma mu ddoboozi...';
          }};
          u.onend = () => {{
            isSpeaking = false;
            btn.textContent = '🔊 Read Aloud / Wuliriza';
            status.textContent = '';
          }};
          window.speechSynthesis.speak(u);
        }}

        const c = document.getElementById('copyBtn');
        const r = document.getElementById('readBtn');
        if (c) c.addEventListener('click', copyLuganda);
        if (r) r.addEventListener('click', readLuganda);
        </script>
        """
    )


# ------------------------------------------------------------------
# Brand Header (Picture Translate Uganda)
# ------------------------------------------------------------------
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown(
        """
        <div style="background:linear-gradient(135deg, #059669, #2563eb);
                    width:56px;height:56px;border-radius:14px;display:flex;
                    align-items:center;justify-content:center;color:#fff;
                    font-size:22px;font-weight:900;box-shadow:0 4px 10px rgba(5,150,105,0.3);">
            PT
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_title:
    st.markdown(
        """
        <div style="line-height:1.2;">
            <span style="font-size:26px;font-weight:900;color:#0f172a;">Picture<span style="color:#2563eb;">Translate</span></span>
            <span style="background:#dcfce7;color:#166534;font-size:11px;font-weight:800;padding:2px 8px;border-radius:6px;border:1px solid #86efac;margin-left:6px;">UGANDA 🇺🇬</span>
            <p style="font-size:13px;color:#64748b;margin-top:2px;margin-bottom:0;">Funa ekifaananyi ekirungi → Soma mu Luganda n'Olungereza</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# PERMANENT SAFETY DISCLAIMER
# ------------------------------------------------------------------
st.markdown(
    """
    <div style="background-color:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:14px;margin-bottom:18px;">
        <div style="font-weight:800;color:#92400e;font-size:13px;margin-bottom:4px;">
            ⚠️ Important / Ebikulu:
        </div>
        <div style="font-size:12px;color:#78350f;line-height:1.5;">
            This tool only reads the text visible on the package. It is <strong>not</strong> medical, farming, or safety advice. Always follow a doctor, extension officer, or the original packaging.
            <br>
            <em>Ekyuma kino kisoma bu kwogerwa kweri ku paketi. Si milumbo ya eddagala, by'obulimi, oba oberebere. Manya buli kaseera koze ne musawo, omulimisa, oba paketi yakasalire.</em>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Category Selector (Pure Picture Workflow, No Text Input!)
# ------------------------------------------------------------------
category = st.radio(
    "What is this? / Kiki ekintu kino?",
    ["Medicine / Dawa", "Agro-input / Ebirime", "Food / Emmere", "Other / Ebindala"],
    horizontal=True,
)

# ------------------------------------------------------------------
# Photo Quality Tips
# ------------------------------------------------------------------
with st.expander("📸 Tips for a good photo / Tipsi z'ekifaananyi"):
    st.markdown(
        """
        - **Close-up / Kumpi**: Fill the frame with the label text (Kwatira kumpi nnyo).
        - **Good light / Obwerere**: Use bright daylight or a lamp (Kozesa omusana).
        - **Hold steady / Totambula**: Avoid blur — hold with both hands.
        - **Flat surface / Kitu ekirala**: Lay the packaging flat, not tilted.
        """
    )

# ------------------------------------------------------------------
# Picture Input Tabs (Camera & Upload)
# ------------------------------------------------------------------
tab_camera, tab_upload, tab_mock = st.tabs([
    "📷 Take Photo / Kamera",
    "📁 Upload Picture / Galari",
    "🧪 Test with Repo Sample",
])

image_bytes = None
image_id = None

with tab_camera:
    camera_photo = st.camera_input("Take a photo of the label / Kwatira ekifaananyi")
    if camera_photo is not None:
        image_bytes = camera_photo.getvalue()
        image_id = ("camera", camera_photo.name, camera_photo.size)

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a picture of the label / Leeta ekifaananyi",
        type=["jpg", "jpeg", "png", "webp"],
    )
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        image_id = ("upload", uploaded_file.name, uploaded_file.size)

with tab_mock:
    st.markdown("Test instantly using `mock_medicine_label.png` from this repository:")
    mock_path = os.path.join(os.path.dirname(__file__), "test_samples", "mock_medicine_label.png")
    if os.path.exists(mock_path):
        if st.button("Load Panadol Extra Sample / Kwatira Sample", key="mock_btn"):
            with open(mock_path, "rb") as mf:
                image_bytes = mf.read()
            image_id = ("mock", "mock_medicine_label.png", len(image_bytes))
    else:
        st.info("Place an image in `test_samples/mock_medicine_label.png` to use this button.")

# Clear stale results when image changes
if image_id != st.session_state.get("image_id"):
    st.session_state["image_id"] = image_id
    st.session_state.pop("result", None)
    st.session_state.pop("error", None)

# ------------------------------------------------------------------
# Image Preview & Action Button
# ------------------------------------------------------------------
if image_bytes is not None:
    image = Image.open(io.BytesIO(image_bytes))
    st.image(image, caption="Your photo / Ekifaananyi kyo", use_container_width=True)

    if st.button("🔍 Read & Translate Label / Soma Akabonero", type="primary"):
        with st.spinner("Picture Translate is reading label... / Nsoma akabonero..."):
            try:
                raw_text = read_label(image_bytes, category)
                sections = split_sections(raw_text)
                st.session_state["result"] = sections
                st.session_state.pop("error", None)
            except LabelReaderError as e:
                st.session_state["error"] = str(e)
                st.session_state.pop("result", None)

# ------------------------------------------------------------------
# Results Display
# ------------------------------------------------------------------
if "result" in st.session_state:
    sections = st.session_state["result"]

    # Retake suggestion if most fields are missing
    eng_text = sections["english"] if sections["english"] else sections["raw"]
    missing, total = count_missing(eng_text)
    if total > 0 and missing >= total / 2:
        st.warning(
            "📸 Most of the label is **not clearly visible**. "
            "Please retake the photo — get closer, use better light, and hold steady.\n\n"
            "Ekitundu ekingi kya label tekyabulijjo. Muddemu ekifaananyi — kumpi, mu bwerere, otona."
        )

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:24px 0;'>", unsafe_allow_html=True)

    # 1. SIMPLE LUGANDA SECTION (Green Theme, Large font)
    if sections["luganda"]:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <span style="width:10px;height:10px;border-radius:50%;background:#059669;"></span>
                <h2 style="font-size:22px;font-weight:900;color:#065f46;margin:0;">🗣️ Olusolo lwa Luganda (Simple)</h2>
            </div>
            <p style="font-size:12px;color:#64748b;margin-bottom:12px;">
                <em>⚠️ Luganda eno yakolebwa kompyuta. Buuza omuntu gwe weesiga akukakasize.</em>
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='pt-card pt-card-luganda' style='font-size:1.15em;line-height:1.7;white-space:pre-wrap;color:#0f172a;'>"
            f"{highlight_missing(sections['luganda'])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        luganda_action_buttons(sections["luganda"])

    # 2. STRUCTURED ENGLISH SECTION (Blue Theme)
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="width:10px;height:10px;border-radius:50%;background:#2563eb;"></span>
            <h2 style="font-size:20px;font-weight:900;color:#1e40af;margin:0;">📋 Structured English</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if sections["english"]:
        st.markdown(
            f"<div class='pt-card pt-card-english' style='line-height:1.6;white-space:pre-wrap;color:#0f172a;'>"
            f"{highlight_missing(sections['english'])}"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(sections["raw"])

# ------------------------------------------------------------------
# Error display
# ------------------------------------------------------------------
if "error" in st.session_state:
    st.error(st.session_state["error"])

# ------------------------------------------------------------------
# Emergency & Official Resources Footer
# ------------------------------------------------------------------
st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:32px 0 16px;'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align:center;font-size:11px;color:#64748b;">
        <strong>Picture Translate Uganda</strong> • Complies with NDA & UNBS standards.<br>
        Emergency / Counterfeit Drugs: <strong>National Drug Authority (NDA) 0800 101 999</strong> (Toll-Free).
    </div>
    """,
    unsafe_allow_html=True,
)
