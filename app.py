"""
Label & Package Reader Uganda — Streamlit app.

A mobile-friendly web app for low-literacy users in Uganda.
Photograph a product label; Gemma 4 reads it and returns structured
English + simple Luganda.

PRIVACY: Uploaded images are never saved to disk or logged. They are
processed in memory, sent to the Gemma 4 API for OCR, then discarded.
"""
import html as html_module
import io
import json

import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from gemma_client import read_label, LabelReaderError
from parser import split_sections

load_dotenv()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def highlight_missing(text: str) -> str:
    """Return HTML-escaped text with 'Not clearly visible' lines highlighted.

    Lines containing 'not clearly visible' (case-insensitive) are wrapped in a
    red badge so users can instantly see which fields need a better photo.
    """
    lines = text.split("\n")
    out = []
    for line in lines:
        escaped = html_module.escape(line)
        if "not clearly visible" in line.lower():
            out.append(
                f"<span style='color:#c0392b;font-weight:bold;"
                f"background-color:#fdebd0;padding:2px 6px;"
                f"border-radius:4px;display:inline-block;margin:2px 0;'>"
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
    """Render Copy (6a) and Read-aloud (6b) buttons for the Luganda section.

    6a — Copy:  uses navigator.clipboard.writeText() with a fallback to
                document.execCommand('copy'). Shows "Copied!" feedback.
    6b — Read:  uses window.speechSynthesis. Detects Luganda voices
                (lang starts with "lg"). If none, shows a friendly
                fallback message in both languages. Button toggles to
                Stop while reading.
    """
    if not luganda_text:
        return

    # json.dumps produces a safe JavaScript string literal
    luganda_js = json.dumps(luganda_text)

    st.html(
        f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;">
          <button id="copyBtn"
            style="background:#27ae60;color:#fff;border:none;padding:10px 18px;
                   border-radius:8px;font-size:16px;cursor:pointer;">
            📋 Copy Luganda / Kopi
          </button>
          <button id="readBtn"
            style="background:#2980b9;color:#fff;border:none;padding:10px 18px;
                   border-radius:8px;font-size:16px;cursor:pointer;">
            🔊 Read in Luganda / Soma
          </button>
        </div>
        <div id="ttsMsg" style="margin-top:8px;font-size:14px;color:#555;"></div>

        <script>
        const lugandaText = {luganda_js};
        let isReading = false;

        // ---- 6a: Copy to clipboard ----
        function copyLuganda() {{
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(lugandaText).then(() => {{
              const b = document.getElementById('copyBtn');
              b.textContent = '✓ Copied! / Yakopedwa!';
              setTimeout(() => {{ b.textContent = '📋 Copy Luganda / Kopi'; }}, 2000);
            }}).catch(() => {{ fallbackCopy(); }});
          }} else {{
            fallbackCopy();
          }}
        }}

        function fallbackCopy() {{
          const ta = document.createElement('textarea');
          ta.value = lugandaText;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.select();
          try {{ document.execCommand('copy'); }} catch (e) {{}}
          document.body.removeChild(ta);
          const b = document.getElementById('copyBtn');
          b.textContent = '✓ Copied! / Yakopedwa!';
          setTimeout(() => {{ b.textContent = '📋 Copy Luganda / Kopi'; }}, 2000);
        }}

        // ---- 6b: Read aloud via speechSynthesis ----
        function readLuganda() {{
          const msg = document.getElementById('ttsMsg');
          if (isReading) {{
            speechSynthesis.cancel();
            isReading = false;
            document.getElementById('readBtn').textContent =
              '🔊 Read in Luganda / Soma';
            msg.innerHTML = '⏹ Stopped. / Yanimira.';
            return;
          }}
          if (!window.speechSynthesis) {{
            msg.innerHTML =
              '⚠️ Browser yo tekimanyi okusoma ddoboozi. ' +
              'Your browser does not support speech.';
            return;
          }}

          function trySpeak() {{
            const voices = speechSynthesis.getVoices();
            // Look for a Luganda voice (lang code starts with "lg")
            const lv = voices.find(
              v => v.lang.toLowerCase().startsWith('lg')
            );
            if (lv) {{
              speechSynthesis.cancel();
              const u = new SpeechSynthesisUtterance(lugandaText);
              u.voice = lv;
              u.lang = lv.lang;
              u.rate = 0.9;
              u.onend = () => {{
                isReading = false;
                document.getElementById('readBtn').textContent =
                  '🔊 Read in Luganda / Soma';
                msg.innerHTML = '✓ Done. / Mala.';
              }};
              u.onerror = () => {{
                isReading = false;
                document.getElementById('readBtn').textContent =
                  '🔊 Read in Luganda / Soma';
                msg.innerHTML = '⚠️ Could not read. / Tesobode.';
              }};
              speechSynthesis.speak(u);
              isReading = true;
              document.getElementById('readBtn').textContent =
                '⏹ Stop / Yanima';
              msg.innerHTML = '🔊 Reading... / Nsoma mu Luganda...';
            }} else {{
              msg.innerHTML =
                '⚠️ No Luganda voice in your browser. ' +
                'Try adding one in phone settings, or read the text yourself.<br>' +
                '⚠️ Tewali ddoboozi lya Luganda. ' +
                'Yongera mu phone, oba somo bwennyini.';
            }}
          }}

          const voices = speechSynthesis.getVoices();
          if (voices.length === 0) {{
            speechSynthesis.onvoiceschanged = trySpeak;
          }} else {{
            trySpeak();
          }}
        }}

        // Attach event listeners (DOMPurify-safe — no inline onclick)
        function setupButtons() {{
          const c = document.getElementById('copyBtn');
          const r = document.getElementById('readBtn');
          if (c) c.addEventListener('click', copyLuganda);
          if (r) r.addEventListener('click', readLuganda);
        }}
        if (document.readyState === 'loading') {{
          document.addEventListener('DOMContentLoaded', setupButtons);
        }} else {{
          setupButtons();
        }}
        </script>
        """,
        unsafe_allow_javascript=True,
    )


# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Label Reader Uganda",
    page_icon="📦",
    layout="centered",
)

# ------------------------------------------------------------------
# Title and bilingual instructions
# ------------------------------------------------------------------
st.title("📦 Label & Package Reader")
st.markdown("### Funa ekifaananyi ekirungi → Soma mu Luganda n'Olungereza")
st.info(
    "Take a **clear, close-up** photo of the label in good light.\n\n"
    "Funa ekifaananyi ekirungi eky'akabonero / paketi (katono, mu bwerere)."
)

# ------------------------------------------------------------------
# PERMANENT DISCLAIMER — always visible, not collapsible, shown
# before results. Uses st.warning for a prominent amber box.
# ------------------------------------------------------------------
st.warning(
    "**⚠️ Important / Ebikulu:**\n"
    "This tool only reads the text visible on the package. "
    "It is **not** medical, farming, or safety advice. "
    "Always follow a doctor, extension officer, or the original packaging.\n\n"
    "Ekyuma kino kisoma bu kwogerwa kweri ku paketi. "
    "Si milumbo ya eddagala, by'obulimi, oba oberebere. "
    "Manya buli kaseera koze ne musawo, omulimisa, oba paketi yakasalire."
)

# ------------------------------------------------------------------
# Tips for a good photo
# ------------------------------------------------------------------
with st.expander("📸 Tips for a good photo / Tipsi z'ekifaananyi"):
    st.markdown(
        "- **Close-up**: Fill the frame with the label text.\n"
        "- **Good light**: Use natural daylight or a bright lamp.\n"
        "- **Hold steady**: Avoid blur — hold the phone with both hands.\n"
        "- **Flat surface**: Lay the label flat, not at an angle.\n\n"
        "- **Kumpi**: Kwatira akabonero okuba kumpi nnyo.\n"
        "- **Obwerere**: Kozesa ekibalangirwa ekirungi.\n"
        "- **Totambula**: Sima amaboko, totwala ekifaananyi kibeere kyabulijjo.\n"
        "- **Kitu ekirala**: Teka akabonero ku kintu ekirala, si ku kya musaale."
    )

# ------------------------------------------------------------------
# Category selectbox
# ------------------------------------------------------------------
category = st.selectbox(
    "What is this? / Kki ekintu kye kino?",
    ["Medicine / Dawa", "Agro-input / Ebirime", "Food / Emmere", "Other / Ebindala"],
)

# ------------------------------------------------------------------
# Image input — tabs for upload vs camera
# Images stay in memory only; nothing is written to disk.
# ------------------------------------------------------------------
tab_upload, tab_camera = st.tabs(["📁 Upload / Leeta", "📷 Take Photo / Kwatira"])

image_bytes = None
image_id = None  # tracks which image we're looking at

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a photo of the label / Leeta ekifaananyi",
        type=["jpg", "jpeg", "png", "webp"],
    )
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        image_id = ("upload", uploaded_file.name, uploaded_file.size)

with tab_camera:
    camera_photo = st.camera_input(
        "Take a photo of the label / Kwatira ekifaananyi"
    )
    if camera_photo is not None:
        image_bytes = camera_photo.getvalue()
        image_id = ("camera", camera_photo.name, camera_photo.size)

# Clear stale results when the user switches to a different image
if image_id != st.session_state.get("image_id"):
    st.session_state["image_id"] = image_id
    st.session_state.pop("result", None)
    st.session_state.pop("error", None)

# ------------------------------------------------------------------
# Image preview + Read button
# ------------------------------------------------------------------
if image_bytes is not None:
    image = Image.open(io.BytesIO(image_bytes))
    st.image(image, caption="Your photo / Ekifaananyi kyo", use_container_width=True)

    if st.button("Read the Label / Soma Akabonero", type="primary"):
        with st.spinner("Reading the label... / Nsoma akabonero..."):
            try:
                raw_text = read_label(image_bytes, category)
                sections = split_sections(raw_text)
                st.session_state["result"] = sections
                st.session_state.pop("error", None)
            except LabelReaderError as e:
                st.session_state["error"] = str(e)
                st.session_state.pop("result", None)

# ------------------------------------------------------------------
# Results
# ------------------------------------------------------------------
if "result" in st.session_state:
    sections = st.session_state["result"]

    # --- Retake suggestion if most fields are missing ---
    eng_text = sections["english"] if sections["english"] else sections["raw"]
    missing, total = count_missing(eng_text)
    if total > 0 and missing >= total / 2:
        st.warning(
            "📸 Most of the label is **not clearly visible**. "
            "Please retake the photo — get closer, use better light, "
            "and hold steady.\n\n"
            "Ekitundu ekingi kya label tekyabulijjo. Muddemu ekifaananyi "
            "— kumpi, mu bwerere, otona."
        )

    st.markdown("---")

    # --- English section (normal size, clear heading) ---
    st.markdown("## 📋 English")
    if sections["english"]:
        st.markdown(
            f"<div style='white-space:pre-wrap;line-height:1.6;'>"
            f"{highlight_missing(sections['english'])}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(sections["raw"])

    # --- Luganda section (LARGER, more prominent, amber background) ---
    if sections["luganda"]:
        st.markdown("---")
        st.markdown("## 🗣️ Luganda (Simple)")
        st.markdown(
            "_⚠️ Luganda is AI-generated. Ask someone you trust to confirm "
            "important information._\n"
            "_Luganda eno yakolebwa kompyuta. Buuza omuntu oyagaza "
            "asobole okukakasa._"
        )
        st.markdown(
            f"<div style='font-size:1.3em;line-height:1.7;"
            f"white-space:pre-wrap;background-color:#fff8e1;"
            f"padding:18px;border-radius:10px;"
            f"border-left:5px solid #f39c12;'>"
            f"{highlight_missing(sections['luganda'])}"
            f"</div>",
            unsafe_allow_html=True,
        )

        # 6a: Copy Luganda + 6b: Read aloud buttons
        luganda_action_buttons(sections["luganda"])

# ------------------------------------------------------------------
# Error display
# ------------------------------------------------------------------
if "error" in st.session_state:
    st.error(st.session_state["error"])

# ------------------------------------------------------------------
# Bottom reminder (brief, always visible)
# ------------------------------------------------------------------
st.markdown("---")
st.caption(
    "⚠️ This tool only reads package text — not medical, farming, or "
    "safety advice. Always follow a professional or the original packaging."
)
