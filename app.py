"""
Skincare-themed Streamlit demo for the BioLead driver-vs-passenger gene agent.

This is a thin UI layer only -- it imports and calls run_pipeline() from
src/pipeline.py unchanged, so nothing about the underlying agent changes.

Run with:
    pip install -r requirements-app.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    export NCBI_EMAIL=you@example.com
    streamlit run app.py
"""

import streamlit as st

from src.pipeline import run_pipeline

st.set_page_config(
    page_title="BioLead | Driver vs. Passenger Gene Agent",
    page_icon="🌿",
    layout="centered",
)

# --------------------------------------------------------------------------
# Skincare-themed styling
# --------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(180deg, #FFF8F3 0%, #FDF3EF 100%);
}

.hero {
    text-align: center;
    padding: 1.75rem 1rem 1rem 1rem;
}
.hero-icon { font-size: 2.4rem; margin-bottom: -0.4rem; }
.hero h1 {
    font-family: 'Playfair Display', serif;
    color: #B5697B;
    font-size: 2.4rem;
    margin-bottom: 0.1rem;
}
.hero .tagline {
    color: #8A7A72;
    font-size: 1rem;
    font-style: italic;
}

div[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #F1DCD8;
    border-radius: 18px;
    padding: 1.6rem 1.6rem 0.8rem 1.6rem;
    box-shadow: 0 4px 18px rgba(197, 141, 145, 0.10);
}

.stButton > button, .stFormSubmitButton > button {
    background: linear-gradient(135deg, #E8A0A5, #D6879A);
    color: white;
    border: none;
    border-radius: 999px;
    padding: 0.55rem 1.6rem;
    font-weight: 600;
    box-shadow: 0 3px 10px rgba(214, 135, 154, 0.35);
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #DD8E95, #C97389);
    color: white;
}

.result-card {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 1.5rem 1.7rem;
    margin-top: 1.3rem;
    border: 1px solid #F1DCD8;
    box-shadow: 0 4px 18px rgba(197, 141, 145, 0.10);
}

.verdict-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1.1rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 1.05rem;
    margin-bottom: 0.9rem;
}

.confidence-pill {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    background: #F5EDE9;
    color: #8A7A72;
    margin-left: 0.5rem;
}

.section-label {
    font-family: 'Playfair Display', serif;
    color: #B5697B;
    font-size: 1.05rem;
    margin: 1.1rem 0 0.4rem 0;
}

.reasoning-text {
    color: #4A423E;
    line-height: 1.55;
    font-size: 0.96rem;
}

.tier-chip {
    display: inline-block;
    padding: 0.35rem 0.8rem;
    border-radius: 12px;
    margin: 0.15rem 0.3rem 0.15rem 0;
    font-size: 0.85rem;
    background: #F5EDE9;
    color: #6E5F58;
}
.tier-chip b { color: #B5697B; }

.pmid-chip {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    margin: 0.2rem 0.3rem 0.2rem 0;
    border-radius: 999px;
    background: #EAF1E7;
    color: #5C7756;
    text-decoration: none;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid #D7E5D2;
}
.pmid-chip:hover {
    background: #DCEAD7;
    color: #46603F;
}

.caveats-box {
    background: #FBF3E9;
    border-left: 3px solid #E0B478;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    color: #7A6746;
    font-size: 0.9rem;
    margin-top: 0.9rem;
}
</style>
""",
    unsafe_allow_html=True,
)

VERDICT_STYLES = {
    "driver": {"emoji": "🌹", "label": "Likely driver", "text": "#8A3B4E", "bg": "#FBE4EA"},
    "passenger": {"emoji": "🍃", "label": "Likely passenger", "text": "#3E5C3A", "bg": "#E7F0E4"},
    "uncertain": {"emoji": "🌫️", "label": "Uncertain", "text": "#5B4B6B", "bg": "#F0E9F4"},
}

TIER_LABELS = {
    "genetic_association": "Genetic association",
    "functional_perturbation": "Functional perturbation",
    "mendelian_randomization": "Mendelian randomization",
    "expression_correlation": "Expression correlation",
    "pathway_context": "Pathway context",
    "irrelevant": "Irrelevant",
}

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
    <div class="hero-icon">🌿✨🌸</div>
    <h1>BioLead</h1>
    <p class="tagline">Separating true skin-disease drivers from passenger genes</p>
</div>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Input form
# --------------------------------------------------------------------------
with st.form("query_form"):
    col1, col2 = st.columns(2)
    with col1:
        gene = st.text_input("Gene symbol", placeholder="e.g. IL13, FLG, TSLP")
    with col2:
        disease = st.text_input(
            "Skin condition", placeholder="e.g. atopic dermatitis, psoriasis, acne"
        )
    submitted = st.form_submit_button("Analyze evidence 🔍")

# --------------------------------------------------------------------------
# Run pipeline + render results
# --------------------------------------------------------------------------
if submitted:
    if not gene.strip() or not disease.strip():
        st.warning("Enter both a gene symbol and a skin condition to run the analysis.")
    else:
        with st.spinner(f"Reading the literature on {gene.strip()}..."):
            try:
                result = run_pipeline(gene.strip(), disease.strip())
                error = None
            except Exception as exc:  # noqa: BLE001 - surface any pipeline error in the UI
                result, error = None, str(exc)

        if error:
            st.error(f"Something went wrong: {error}")
        elif result:
            verdict_key = result.get("verdict", "uncertain")
            style = VERDICT_STYLES.get(verdict_key, VERDICT_STYLES["uncertain"])
            confidence = result.get("confidence", "unknown")

            st.markdown('<div class="result-card">', unsafe_allow_html=True)

            st.markdown(
                f"""
                <span class="verdict-badge" style="background:{style['bg']}; color:{style['text']};">
                    {style['emoji']} {result.get('gene')} — {style['label']}
                    <span class="confidence-pill">confidence: {confidence}</span>
                </span>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"For **{result.get('disease')}**, based on "
                f"{result.get('num_articles_reviewed', 0)} articles reviewed "
                f"(weighted evidence score: {result.get('weighted_score', 0)})."
            )

            # --- Reasoning ---
            st.markdown('<div class="section-label">Reasoning</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="reasoning-text">{result.get("reasoning", "No reasoning returned.")}</div>',
                unsafe_allow_html=True,
            )

            # --- Evidence tier breakdown ---
            tier_counts = result.get("tier_counts", {})
            if tier_counts:
                st.markdown(
                    '<div class="section-label">Evidence tier breakdown</div>',
                    unsafe_allow_html=True,
                )
                chips = "".join(
                    f'<span class="tier-chip"><b>{count}</b> {TIER_LABELS.get(tier, tier)}</span>'
                    for tier, count in sorted(tier_counts.items(), key=lambda kv: -kv[1])
                )
                st.markdown(chips, unsafe_allow_html=True)

            # --- Supporting PMIDs, clickable ---
            supporting_pmids = result.get("supporting_pmids", [])
            if supporting_pmids:
                st.markdown(
                    '<div class="section-label">Cited sources</div>', unsafe_allow_html=True
                )
                links = "".join(
                    f'<a class="pmid-chip" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" '
                    f'target="_blank" rel="noopener noreferrer">PMID {pmid} ↗</a>'
                    for pmid in supporting_pmids
                )
                st.markdown(links, unsafe_allow_html=True)

            # --- Caveats ---
            caveats = result.get("caveats")
            if caveats:
                st.markdown(
                    f'<div class="caveats-box">🌤️ <b>Worth noting:</b> {caveats}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # --- All articles reviewed, collapsed ---
            all_pmids = result.get("pmids_reviewed", [])
            if all_pmids:
                with st.expander(f"All {len(all_pmids)} articles reviewed"):
                    links = "".join(
                        f'<a class="pmid-chip" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" '
                        f'target="_blank" rel="noopener noreferrer">PMID {pmid} ↗</a>'
                        for pmid in all_pmids
                    )
                    st.markdown(links, unsafe_allow_html=True)
