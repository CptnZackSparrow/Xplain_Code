import streamlit as st
import requests
import json
import re

st.set_page_config(
    page_title="Explain My Code Like I'm 10",
    page_icon="ELI10",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka+One&family=Nunito:wght@400;600;700;800&display=swap');

.big-title {
    font-family: 'Fredoka One', cursive;
    font-size: 2.8rem;
    background: linear-gradient(135deg, #ff6b6b, #ffd166, #06d6a0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    line-height: 1.2;
}
.subtitle {
    text-align: center;
    color: #888;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}
.step-box {
    border-left: 4px solid #06d6a0;
    background: #f0fdf9;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.7rem;
}
.step-title {
    font-weight: 800;
    font-size: 0.95rem;
}
.step-desc {
    font-size: 0.9rem;
    color: #444;
    margin-top: 0.2rem;
}
.confusing-box {
    border-left: 4px solid #ff6b6b;
    background: #fff5f5;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.7rem;
}
.confusing-term {
    font-weight: 800;
    color: #c53030;
    font-size: 0.95rem;
}
.confusing-explain {
    font-size: 0.9rem;
    color: #444;
    margin-top: 0.2rem;
}
.summary-box {
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 1rem;
    color: #0c4a6e;
    line-height: 1.7;
}
.lang-badge {
    display: inline-block;
    background: #ede9fe;
    color: #6d28d9;
    border-radius: 6px;
    padding: 0.2rem 0.7rem;
    font-weight: 800;
    font-size: 0.85rem;
    margin-right: 0.5rem;
}
.one-liner {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a1a2e;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">Xplain Code</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Paste any code — get plain-English steps, a flow diagram, and decoded confusing parts</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.caption("Free key at [console.groq.com](https://console.groq.com)")
    st.divider()
    lang = st.selectbox("Language hint", [
        "Auto-detect", "Python", "JavaScript", "TypeScript",
        "Java", "C++", "C", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin"
    ])

code_input = st.text_area(
    "Paste your code here",
    height=250,
    placeholder="def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
)

explain_btn = st.button("Explain It", use_container_width=True, type="primary")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a brilliant teacher who explains code to 10-year-olds.
Given a code snippet, respond ONLY with a valid JSON object (no markdown fences, no extra text) with these exact keys:

{
  "language": "detected language",
  "one_liner": "One sentence: what does this code DO overall?",
  "summary": "2-3 sentences ELI10 summary using simple analogies. No jargon.",
  "steps": [
    {"title": "short title", "explanation": "ELI10 explanation"}
  ],
  "confusing_parts": [
    {"term": "tricky keyword or concept", "kid_explanation": "plain English meaning with a simple analogy"}
  ],
  "mermaid": "valid Mermaid flowchart TD syntax only — strictly follow these rules: 1) start with 'flowchart TD' on its own line, 2) every node ID must be alphanumeric only like A, B, C or Step1, Step2, 3) node labels go inside square brackets like A[Label here], 4) use only --> for arrows, 5) keep labels under 30 characters, 6) no parentheses, no quotes, no special characters inside brackets, 7) no subgraphs, 8) return raw mermaid code only with no fences"
}

Rules:
- steps: 3 to 6 logical steps in order
- confusing_parts: 2 to 4 genuinely tricky things
- Use cheerful encouraging language throughout
- Return ONLY the raw JSON object, nothing else, no markdown
"""

def call_groq(code: str, lang_hint: str, key: str) -> dict:
    lang_str = "" if lang_hint == "Auto-detect" else f" (language: {lang_hint})"
    payload = {
        "model": MODEL,
        "temperature": 0.3,
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Explain this code{lang_str}:\n\n{code}"}
        ]
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"].strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw)


def sanitize_mermaid(raw: str) -> str:
    """Clean up common AI mermaid mistakes."""
    # Strip fences
    raw = re.sub(r'^```(?:mermaid)?\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    # Ensure it starts with flowchart TD
    if not raw.startswith("flowchart"):
        raw = "flowchart TD\n" + raw

    lines = raw.splitlines()
    cleaned = []
    for line in lines:
        # Remove emojis and non-ASCII from node labels
        line = re.sub(r'[^\x00-\x7F]+', '', line)
        # Remove quotes inside brackets
        line = re.sub(r'\["([^"]+)"\]', r'[\1]', line)
        line = re.sub(r"\['([^']+)'\]", r'[\1]', line)
        # Remove parentheses-style nodes (Mermaid stadium shape) — replace with square brackets
        line = re.sub(r'\(\(([^)]+)\)\)', r'[\1]', line)
        line = re.sub(r'\(([^)]+)\)', r'[\1]', line)
        cleaned.append(line)

    return "\n".join(cleaned)


def build_fallback_mermaid(steps: list) -> str:
    """Build a simple valid mermaid diagram from the steps list."""
    lines = ["flowchart TD"]
    prev = None
    for i, step in enumerate(steps):
        node_id = f"S{i}"
        # Sanitize label: strip non-ASCII, truncate
        label = re.sub(r'[^\x00-\x7F]+', '', step.get("title", f"Step {i+1}"))
        label = label.replace('"', '').replace('[', '').replace(']', '').strip()[:28]
        lines.append(f'    {node_id}[{label}]')
        if prev is not None:
            lines.append(f'    {prev} --> {node_id}')
        prev = node_id
    return "\n".join(lines)


STEP_COLORS = ["#06d6a0", "#ffd166", "#ff6b6b", "#118ab2", "#a855f7", "#f97316", "#ec4899"]

if explain_btn:
    if not api_key:
        st.error("Enter your Groq API key in the sidebar first.")
    elif not code_input.strip():
        st.warning("Please paste some code first.")
    else:
        with st.spinner("Thinking... making it kid-friendly..."):
            try:
                result = call_groq(code_input.strip(), lang, api_key)
            except requests.HTTPError as e:
                st.error(f"API error {e.response.status_code}: {e.response.text[:300]}")
                st.stop()
            except json.JSONDecodeError as e:
                st.error(f"Could not parse AI response: {e}")
                st.stop()
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        st.markdown(
            f'<span class="lang-badge">{result.get("language", "Code")}</span>'
            f'<span class="one-liner">{result.get("one_liner", "")}</span>',
            unsafe_allow_html=True
        )
        st.divider()

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.subheader("Step-by-Step Breakdown")
            steps = result.get("steps", [])
            for i, step in enumerate(steps):
                color = STEP_COLORS[i % len(STEP_COLORS)]
                st.markdown(f"""
                <div class="step-box" style="border-left-color:{color};">
                  <div class="step-title" style="color:{color};">Step {i+1}: {step.get('title', '')}</div>
                  <div class="step-desc">{step.get('explanation', '')}</div>
                </div>""", unsafe_allow_html=True)

            st.subheader("Confusing Parts — Decoded")
            confusing = result.get("confusing_parts", [])
            if confusing:
                for cp in confusing:
                    st.markdown(f"""
                    <div class="confusing-box">
                      <div class="confusing-term">{cp.get('term', '')}</div>
                      <div class="confusing-explain">{cp.get('kid_explanation', '')}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.success("No confusing parts found — great code!")

        with col_right:
            st.subheader("Flow Diagram")

            raw_mermaid = result.get("mermaid", "")
            mermaid_code = sanitize_mermaid(raw_mermaid) if raw_mermaid else build_fallback_mermaid(steps)

            # We pass both the AI version and fallback to JS;
            # if AI version fails to render, JS swaps in the fallback.
            fallback_mermaid = build_fallback_mermaid(steps)

            # Escape for JS template literal
            def js_escape(s):
                return s.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

            mermaid_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; padding: 0; background: transparent; font-family: sans-serif; }}
  #diagram {{ background: #f8fafc; border-radius: 10px; padding: 1rem; min-height: 180px; }}
  #error-msg {{ color: #c53030; font-size: 0.85rem; padding: 0.5rem; display: none; }}
</style>
</head>
<body>
<div id="diagram">
  <div class="mermaid" id="mermaid-div">{mermaid_code}</div>
</div>
<div id="error-msg">Flow diagram could not be rendered. Showing simplified version.</div>

<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

  const primaryCode = `{js_escape(mermaid_code)}`;
  const fallbackCode = `{js_escape(fallback_mermaid)}`;

  mermaid.initialize({{ startOnLoad: false, theme: 'default', securityLevel: 'loose' }});

  async function tryRender(code, el) {{
    try {{
      const {{ svg }} = await mermaid.render('mermaid-svg', code);
      el.innerHTML = svg;
      return true;
    }} catch(e) {{
      return false;
    }}
  }}

  const el = document.getElementById('mermaid-div');
  const ok = await tryRender(primaryCode, el);
  if (!ok) {{
    document.getElementById('error-msg').style.display = 'block';
    const ok2 = await tryRender(fallbackCode, el);
    if (!ok2) {{
      el.innerHTML = '<p style="color:#888;font-size:0.9rem;">Could not render diagram.</p>';
    }}
  }}
</script>
</body>
</html>
"""
            st.components.v1.html(mermaid_html, height=420, scrolling=True)

            st.subheader("In Plain English")
            st.markdown(
                f'<div class="summary-box">{result.get("summary", "")}</div>',
                unsafe_allow_html=True
            )

else:
    st.info("Paste your code above, add your Groq API key in the sidebar, then click Explain It.")
    st.markdown("Works with Python, JavaScript, Java, C++, Go, Rust, Ruby, and more.")