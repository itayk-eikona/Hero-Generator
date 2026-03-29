import streamlit as st
import anthropic
import base64
import json
from pathlib import Path

st.set_page_config(
    page_title="Hero Image Generator",
    page_icon="🖼️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0e0e0e; color: #e8e8e0; }

section[data-testid="stSidebar"] {
    background: #151515;
    border-right: 1px solid #2a2a2a;
}

h1, h2, h3 {
    font-family: 'DM Sans', sans-serif;
    font-weight: 300;
    letter-spacing: -0.02em;
    color: #e8e8e0;
}

.block-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 6px;
}

.stTextInput > div > div > input {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
    color: #e8e8e0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}

.stButton > button {
    background: #e8e8e0 !important;
    color: #0e0e0e !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    padding: 10px 24px !important;
    width: 100% !important;
}

.stButton > button:hover { opacity: 0.85 !important; }

.stFileUploader > div {
    background: #1a1a1a !important;
    border: 1px dashed #333 !important;
    border-radius: 8px !important;
}

.concept-card {
    background: #151515;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

.concept-index {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.12em;
    color: #444;
    text-transform: uppercase;
    margin-bottom: 12px;
}

.concept-title {
    font-size: 16px;
    font-weight: 500;
    color: #e8e8e0;
    margin-bottom: 16px;
}

.field-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 4px;
}

.field-value {
    font-size: 13px;
    color: #aaa;
    line-height: 1.6;
    margin-bottom: 14px;
    padding: 10px 14px;
    background: #1a1a1a;
    border-radius: 6px;
    border: 1px solid #222;
}

.prompt-value {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #8ab4f8;
    line-height: 1.7;
    padding: 12px 14px;
    background: #0d1a2e;
    border-radius: 6px;
    border: 1px solid #1a2e4a;
    margin-bottom: 14px;
    white-space: pre-wrap;
}

.stSlider > div { color: #888 !important; }
.stMarkdown p { color: #888; font-size: 14px; }
hr { border-color: #222 !important; }
[data-testid="stImage"] img { border-radius: 6px; border: 1px solid #2a2a2a; }
</style>
""", unsafe_allow_html=True)

SUPPORTED_MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "gif": "image/gif", "webp": "image/webp",
}

def get_mime(filename): return SUPPORTED_MIME.get(Path(filename).suffix.lstrip(".").lower(), "image/jpeg")
def img_to_b64(b): return base64.standard_b64encode(b).decode("utf-8")


def generate_concepts(client, email_b64, email_mime, num_concepts):
    prompt = f"""You are an expert email marketing art director.

Analyze this email and generate exactly {num_concepts} hero image concepts for A/B testing.

For each concept return:
- concept: A short name/theme for this visual direction (3-6 words)
- visual_prompt: A detailed visual prompt for an AI image generator (Nano Banana 2 / Flux style). Describe only the visual scene — NO text, NO copy, NO UI overlays. Be specific about: subject, lighting, mood, color palette, composition, camera angle, style.
- headline: A compelling main headline for the email (under 55 chars)
- cta: Button text (2-5 words)

Return ONLY a valid JSON array, no markdown, no explanation:
[
  {{
    "concept": "...",
    "visual_prompt": "...",
    "headline": "...",
    "cta": "..."
  }}
]"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": email_mime, "data": email_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw = message.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").strip()
    if raw.endswith("```"): raw = raw[:-3].strip()
    return json.loads(raw)


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("## 🖼️ Hero Generator")
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("<p class='block-label'>Anthropic API Key</p>", unsafe_allow_html=True)
    api_key = st.text_input("", type="password", placeholder="sk-ant-...", label_visibility="collapsed")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("<p class='block-label'>Number of concepts</p>", unsafe_allow_html=True)
    num_concepts = st.slider("", min_value=1, max_value=10, value=5, label_visibility="collapsed")


# ── Main ─────────────────────────────────────────────────────────────────────

col_left, col_right = st.columns([1, 1.6], gap="large")

with col_left:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("### Reference email")

    st.markdown("<p class='block-label'>Upload email screenshot</p>", unsafe_allow_html=True)
    email_file = st.file_uploader("", type=["png","jpg","jpeg","webp"], key="email", label_visibility="collapsed")

    if email_file:
        st.image(email_file, use_container_width=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    generate_btn = st.button("GENERATE CONCEPTS →", use_container_width=True)

with col_right:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("### Concepts")

    if "concepts" not in st.session_state: st.session_state.concepts = None
    if "error_msg" not in st.session_state: st.session_state.error_msg = None

    if generate_btn:
        st.session_state.concepts = None
        st.session_state.error_msg = None

        if not api_key:
            st.session_state.error_msg = "Enter your Anthropic API key in the sidebar."
        elif not email_file:
            st.session_state.error_msg = "Upload an email screenshot."
        else:
            try:
                client = anthropic.Anthropic(api_key=api_key)
                email_b64 = img_to_b64(email_file.read())
                email_mime = get_mime(email_file.name)

                with st.spinner("Analyzing email and generating concepts..."):
                    st.session_state.concepts = generate_concepts(client, email_b64, email_mime, num_concepts)

            except Exception as e:
                st.session_state.error_msg = str(e)

    if st.session_state.error_msg:
        st.error(st.session_state.error_msg)

    if st.session_state.concepts:
        for i, c in enumerate(st.session_state.concepts):
            with st.container():
                st.markdown(f"""
<div class="concept-card">
  <div class="concept-index">Concept {i+1}</div>
  <div class="concept-title">{c.get('concept','')}</div>

  <div class="field-label">Visual Prompt</div>
  <div class="prompt-value">{c.get('visual_prompt','')}</div>

  <div class="field-label">Headline</div>
  <div class="field-value">{c.get('headline','')}</div>

  <div class="field-label">CTA</div>
  <div class="field-value">{c.get('cta','')}</div>
</div>
""", unsafe_allow_html=True)
                st.code(c.get('visual_prompt',''), language=None)

    elif not st.session_state.error_msg:
        st.markdown("""
<div style="border: 1px dashed #2a2a2a; border-radius: 8px; padding: 60px 24px;
     text-align: center; color: #444; font-family: 'DM Mono', monospace;
     font-size: 12px; letter-spacing: 0.08em;">
    CONCEPTS WILL APPEAR HERE
</div>
""", unsafe_allow_html=True)
