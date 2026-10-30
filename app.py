"""
Picture Translate
General Picture Translation App for Uganda.
Strictly picture-only input: records what has been inserted and its result.
Features Dark/Light mode toggle and Green & Blue buttons.
"""

import io
import os
import time
from datetime import datetime

import streamlit as st
from PIL import Image

from gemma_client import LabelReaderError, read_label
from parser import split_sections

# ------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Picture Translate | General Picture Translation",
    page_icon="📷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Initialize Session State
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
if "records" not in st.session_state:
    st.session_state["records"] = []

# ------------------------------------------------------------------
# Theme: Dark or Light Mode (White background in light mode)
# ------------------------------------------------------------------
is_dark = st.session_state["theme"] == "dark"

if is_dark:
    bg_color = "#0b1120"
    text_color = "#f8fafc"
    card_bg = "#1e293b"
    card_border = "#334155"
    input_box_bg = "#0f172a"
else:
    bg_color = "#ffffff"
    text_color = "#0f172a"
    card_bg = "#f8fafc"
    card_border = "#e2e8f0"
    input_box_bg = "#ffffff"

st.markdown(
    f"""
    <style>
    /* Base Background and Text Colors */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    
    /* Green Primary Buttons */
    div.stButton > button:first-child {{
        background-color: #059669;
        color: #ffffff;
        font-weight: 700;
        font-size: 15px;
        border-radius: 12px;
        border: none;
        padding: 10px 20px;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.25);
        transition: all 0.2s ease;
        width: 100%;
    }}
    div.stButton > button:first-child:hover {{
        background-color: #047857;
        color: #ffffff;
    }}

    /* Blue Upload Dropzone */
    div[data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed #2563eb !important;
        border-radius: 14px !important;
        background-color: {'#172554' if is_dark else '#eff6ff'} !important;
    }}

    .pt-card {{
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 16px;
        border: 1px solid {card_border};
        background-color: {card_bg};
        color: {text_color};
    }}

    .pt-card-luganda {{
        border: 2px solid #059669;
        background-color: {'#064e3b22' if is_dark else '#f0fdf4'};
    }}

    .pt-card-english {{
        border: 2px solid #2563eb;
        background-color: {'#1e3a8a22' if is_dark else '#eff6ff'};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Header with Brand and Dark/Light Mode Switch
# ------------------------------------------------------------------
col_brand, col_theme = st.columns([5, 2])

with col_brand:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="background:linear-gradient(135deg, #059669, #2563eb);
                        width:46px;height:46px;border-radius:12px;display:flex;
                        align-items:center;justify-content:center;color:#fff;
                        font-size:18px;font-weight:900;">
                PT
            </div>
            <div>
                <span style="font-size:22px;font-weight:900;">Picture<span style="color:#2563eb;">Translate</span></span>
                <span style="background:#dcfce7;color:#166534;font-size:10px;font-weight:800;padding:2px 6px;border-radius:4px;margin-left:4px;">UGANDA 🇺🇬</span>
                <p style="font-size:12px;color:#64748b;margin:0;">General Picture Translation • Luganda & English</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_theme:
    current_label = "☀️ Light Mode" if is_dark else "🌙 Dark Mode"
    if st.button(current_label, key="theme_btn"):
        st.session_state["theme"] = "light" if is_dark else "dark"
        st.rerun()

st.markdown("<hr style='border:none;border-top:1px solid " + card_border + ";margin:16px 0;'>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 1. SELECT REQUIRED LANGUAGE
# ------------------------------------------------------------------
st.markdown("#### 1. Select Required Language Output / Londa Olulimi")
lang_choice = st.radio(
    "Choose language:",
    ["🇺🇬 Luganda Only", "🇬🇧 English Only", "🌐 Both Languages"],
    horizontal=True,
    label_visibility="collapsed",
)

# ------------------------------------------------------------------
# 2. PICTURE INPUT ONLY (Camera & Upload)
# ------------------------------------------------------------------
st.markdown("#### 2. Take Picture or Upload / Kwatira oba Leeta Ekifaananyi")

tab_cam, tab_up, tab_test = st.tabs([
    "📷 Take Photo (Kamera)",
    "📁 Upload Picture (Galari)",
    "🧪 Sample Picture",
])

image_bytes = None
image_id = None

with tab_cam:
    cam = st.camera_input("Take photo with camera / Kwatira ekifaananyi")
    if cam is not None:
        image_bytes = cam.getvalue()
        image_id = ("cam", cam.name, cam.size)

with tab_up:
    up = st.file_uploader("Upload picture from device / Leeta ekifaananyi", type=["jpg", "jpeg", "png", "webp"])
    if up is not None:
        image_bytes = up.getvalue()
        image_id = ("up", up.name, up.size)

with tab_test:
    st.markdown("Test instantly with a sample picture:")
    mock_file = os.path.join(os.path.dirname(__file__), "test_samples", "mock_medicine_label.png")
    if os.path.exists(mock_file):
        if st.button("Load Sample Picture", key="load_sample"):
            with open(mock_file, "rb") as f:
                image_bytes = f.read()
            image_id = ("mock", "mock_medicine_label.png", len(image_bytes))

# If a new image was provided, clear active result
if image_id != st.session_state.get("image_id"):
    st.session_state["image_id"] = image_id
    st.session_state.pop("active_record", None)
    st.session_state.pop("error", None)

# Action button to read & translate
if image_bytes is not None:
    st.image(image_bytes, caption="Inserted Picture", use_container_width=True)

    if st.button("🔍 Read & Translate Picture / Vvuunula Ekifaananyi", type="primary"):
        with st.spinner("Reading text and translating... / Nsoma era nvvuunula..."):
            try:
                # Pass None for category since categories are removed
                raw_text = read_label(image_bytes, None)
                sections = split_sections(raw_text)

                new_record = {
                    "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                    "inserted_text": sections.get("english", "") or raw_text,
                    "luganda_result": sections.get("luganda", "") or "Tewali Luganda lufunise.",
                    "english_result": sections.get("english", "") or raw_text,
                }

                # Record into session state history
                st.session_state["active_record"] = new_record
                st.session_state["records"].insert(0, new_record)
                st.session_state.pop("error", None)
            except LabelReaderError as e:
                st.session_state["error"] = str(e)

if "error" in st.session_state:
    st.error(st.session_state["error"])

# ------------------------------------------------------------------
# 3. WHAT HAS BEEN INSERTED & ITS RESULT
# ------------------------------------------------------------------
if "active_record" in st.session_state:
    rec = st.session_state["active_record"]

    st.markdown("<hr style='border:none;border-top:1px solid " + card_border + ";margin:24px 0;'>", unsafe_allow_html=True)
    
    st.markdown("### 📋 What Has Been Inserted (Ebiwandiiko Ebifunise)")
    st.code(rec["inserted_text"], language="text")

    st.markdown("### 🎯 Translation Results (Ebivuddemu)")
    show_lug = "Luganda" in lang_choice or "Both" in lang_choice
    show_eng = "English" in lang_choice or "Both" in lang_choice

    if show_lug and rec["luganda_result"]:
        st.markdown(
            f"""
            <div class="pt-card pt-card-luganda">
                <h4 style="margin:0 0 8px 0;color:#059669;">🗣️ Luganda Result (Olulimi Olwangu)</h4>
                <div style="font-size:1.1em;line-height:1.7;white-space:pre-wrap;">{rec['luganda_result']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if show_eng and rec["english_result"]:
        st.markdown(
            f"""
            <div class="pt-card pt-card-english">
                <h4 style="margin:0 0 8px 0;color:#2563eb;">📋 English Result</h4>
                <div style="line-height:1.6;white-space:pre-wrap;">{rec['english_result']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------
# 4. RECORD LOG OF WHAT HAS BEEN INSERTED & RESULTS
# ------------------------------------------------------------------
if len(st.session_state["records"]) > 0:
    st.markdown("<hr style='border:none;border-top:1px solid " + card_border + ";margin:24px 0;'>", unsafe_allow_html=True)
    
    col_hist_title, col_hist_clear = st.columns([4, 1])
    with col_hist_title:
        st.markdown(f"#### 📜 Recorded Translations ({len(st.session_state['records'])})")
    with col_hist_clear:
        if st.button("🗑️ Clear Log", key="clear_log"):
            st.session_state["records"] = []
            st.session_state.pop("active_record", None)
            st.rerun()

    for idx, r in enumerate(st.session_state["records"]):
        preview = r['inserted_text'][:40].replace("\n", " ")
        with st.expander(f"🕒 {r['timestamp']} — {preview}..."):
            st.markdown("**What Was Inserted:**")
            st.text(r["inserted_text"])
            st.markdown("**Luganda Result:**")
            st.write(r["luganda_result"])
            st.markdown("**English Result:**")
            st.write(r["english_result"])
