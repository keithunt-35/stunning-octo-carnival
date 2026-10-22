# 📦 Label & Package Reader Uganda

A mobile-friendly web app that helps people in Uganda read product labels
(medicine, agro-inputs, food, and more) using AI-powered OCR. The user
takes a photo of a label, and the app reads the text and presents it in two
sections: structured **English** and simple **Luganda** (short sentences,
everyday words, suitable for reading aloud).

**Built with Gemma 4 (gemma-4-26b-a4b-it) via the Gemini API. Multimodal OCR
+ simple Luganda explanation for low-literacy users in Uganda.**

---

## Who is it for?

People who may have difficulty reading small print on product packages —
medicine boxes, fertiliser bags, food labels, pesticide containers. The app
reads what's on the label and explains it in simple Luganda so it can be
understood by someone with limited schooling.

---

## Screenshots

<!-- Add screenshots here after the demo -->
<!-- ![Main screen](screenshots/main.png) -->
<!-- ![Results](screenshots/results.png) -->

---

## Setup

### 1. Get a free Gemini API key

Go to **https://aistudio.google.com/apikey** and create a key.

### 2. Clone and set up the environment

```bash
git clone https://github.com/keithunt-35/stunning-octo-carnival.git
cd stunning-octo-carnival

# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate         # Mac/Linux
# venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Add your API key

```bash
cp .env.example .env
```

Edit `.env` and replace the placeholder with your real key:

```
GOOGLE_API_KEY=AIzaSy...your_real_key...
```

### 4. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## How it works

1. **User takes a photo** of a product label (upload or camera).
2. **Image preprocessing** (Pillow): fixes EXIF rotation, converts transparent
   PNGs to RGB on a white background, resizes to max 1600px, compresses to JPEG.
3. **Gemma 4 reads the label** via the Gemini API. The system prompt constrains
   the model to OCR-only extraction — it only reads text that is clearly visible.
   If something is blurry or cut off, it writes "Not clearly visible" instead of
   guessing.
4. **Output is split** into two sections:
   - **English** — structured fields (product name, ingredients, dose, warnings,
     expiry date, manufacturer).
   - **Luganda (Simple)** — the same information in short, simple Luganda
     sentences for easy reading aloud.
5. **Safety disclaimer** is always visible — the tool only reads package text
   and is not medical, farming, or safety advice.

### Key features

- Bilingual interface (English + Luganda)
- Category selector (Medicine, Agro-input, Food, Other)
- "Not clearly visible" fields are highlighted in red
- Retake suggestion when most of the label is unreadable
- **Copy Luganda text** button
- **Read in Luganda** button (browser speech synthesis, with graceful fallback
  if no Luganda voice is available)
- Permanent safety disclaimer
- No images are stored or logged — processed in memory only

---

## Project structure

```
├── app.py            # Streamlit web app (UI + results display)
├── prompts.py        # System prompt and user prompt builder
├── gemma_client.py   # Gemma 4 API call, image preprocessing, error handling
├── parser.py         # Splits model output into English / Luganda sections
├── check_api.py      # Phase 0: verifies API key and model access
├── test_client.py    # Runs read_label on a test image from the terminal
├── requirements.txt  # Pinned dependencies
├── .env.example      # Template — copy to .env and add your key
├── .gitignore
├── test_samples/     # Sample label photos for testing
└── README.md
```

---

## Limitations

- **AI-generated Luganda may contain errors.** The Luganda translation is
  produced by the AI model and should be confirmed by someone you trust.
- **Not advice.** This tool only reads the text on the package. It is not
  medical advice, farming advice, or safety advice. Always follow a doctor,
  extension officer, or the original packaging.
- **Depends on photo quality.** Blurry, dark, or angled photos will result in
  "Not clearly visible" for some or all fields. Take a clear, close-up photo
  in good light.
- **Luganda voice may not be available.** The "Read in Luganda" button uses
  the browser's built-in speech synthesis. Many browsers do not have a Luganda
  voice installed. If none is available, a friendly message is shown instead.

---

## Safety disclaimer

> ⚠️ This tool only reads the text visible on the package. It is **not**
> medical, farming, or safety advice. Always follow a doctor, extension
> officer, or the original packaging.
>
> Ekyuma kino kisoma bu kwogerwa kweri ku paketi. Si milumbo ya eddagala,
> by'obulimi, oba oberebere. Manya buli kaseera koze ne musawo, omulimisa,
> oba paketi yakasalire.

---

## Deployment

### Option A: Streamlit Community Cloud (free, recommended)

1. Push your code to GitHub.
2. Go to **https://share.streamlit.io/** and sign in with GitHub.
3. Click **New app**:
   - **Repository**: `keithunt-35/stunning-octo-carnival`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Click **Advanced settings → Secrets** and add:
   ```toml
   GOOGLE_API_KEY = "AIzaSy...your_real_key..."
   ```
5. Click **Deploy**. Wait 1–3 minutes for the build.
6. You'll get a public URL like `https://stunning-octo-carnival.streamlit.app`.
   Open it on your phone.

The app reads the key from `st.secrets` (Cloud) or `.env` (local) automatically.

### Option B: Local + ngrok (fallback for quick demos)

```bash
# Terminal 1 — run the app
source venv/bin/activate
streamlit run app.py

# Terminal 2 — create a public tunnel
ngrok http 8501
```

Use the ngrok URL (e.g. `https://abc123.ngrok.io`) to access the app from your phone.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| UI + Backend | Streamlit (Python) |
| AI Model | Gemma 4 (`gemma-4-26b-a4b-it`) via Gemini API |
| SDK | `google-genai` |
| Image handling | Pillow |
| Optional TTS | Browser Web Speech API |
| Deployment | Streamlit Community Cloud or local + ngrok |

---

## License

This project was built for a hackathon. See the Gemma 4 license terms at
https://ai.google.dev/gemma/docs/core/model_card_4 for model usage.
