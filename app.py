"""
BioLead demo UI -- professional/editorial styling (black, blush, white),
collapsible result sections, and an export button for the reasoning
section. This is a UI layer only -- it imports and calls run_pipeline()
from src/pipeline.py unchanged.

Run with:
    pip install -r requirements-app.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    export NCBI_EMAIL=you@example.com
    streamlit run app.py
"""

import matplotlib.pyplot as plt
import streamlit as st

from src.pipeline import run_pipeline
from src.reasoning import TIER_WEIGHTS

st.set_page_config(
    page_title="BioLead | Gene Target Validation",
    page_icon="●",
    layout="centered",
)

# --------------------------------------------------------------------------
# Styling -- black / blush / white editorial palette, bold uppercase display
# type for headlines (Archivo), clean body type (Inter). Sharp corners
# throughout rather than rounded pills, to read as a professional research
# tool rather than a consumer app.
# --------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #141414; }

.stApp { background: #FFFFFF; color-scheme: light; }

/* ---- Hero ---- */
.hero {
    background: #EFD7CE;
    padding: 2.4rem 2rem;
    margin: -1rem -1rem 1.6rem -1rem;
}
.eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4A4A4A !important;
    margin-bottom: 0.5rem;
}
.hero h1 {
    font-family: 'Archivo', sans-serif;
    font-weight: 800;
    letter-spacing: 0.01em;
    text-transform: uppercase;
    font-size: 2.3rem;
    color: #141414 !important;
    margin: 0 0 0.6rem 0;
}
.hero p {
    font-size: 0.98rem;
    color: #383838 !important;
    max-width: 640px;
    line-height: 1.5;
    margin: 0;
}

/* ---- Form ---- */
div[data-testid="stForm"] {
    border: 1px solid #E7DDD8;
    border-radius: 4px;
    padding: 1.5rem 1.5rem 0.6rem 1.5rem;
}

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    background: #141414;
    color: #FFFFFF;
    border: none;
    border-radius: 3px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
    background: #333333;
    color: #FFFFFF;
}

/* ---- Result summary block ---- */
.verdict-block {
    padding: 1.5rem 1.7rem;
    margin-top: 1.4rem;
    border: 1px solid #E7DDD8;
    border-radius: 4px;
}
.verdict-block.driver { background: #F7EAE4; }
.verdict-block.passenger { background: #F3F2F0; }
.verdict-block.uncertain { background: #FFFFFF; border-style: dashed; }

.verdict-headline {
    font-family: 'Archivo', sans-serif;
    font-weight: 800;
    text-transform: uppercase;
    font-size: 1.5rem;
    letter-spacing: 0.01em;
    color: #141414 !important;
    margin: 0.15rem 0 0.4rem 0;
}
.confidence-tag {
    display: inline-block;
    border: 1px solid #141414;
    border-radius: 999px;
    padding: 0.15rem 0.7rem;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #141414 !important;
    margin-left: 0.6rem;
    vertical-align: middle;
}
.meta-line { font-size: 0.88rem; color: #4A4A4A !important; margin-top: 0.2rem; }

/* ---- Expander sections ---- */
div[data-testid="stExpander"] {
    border: 1px solid #E7DDD8 !important;
    border-radius: 4px !important;
    margin-top: 0.8rem;
}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary:hover,
div[data-testid="stExpander"] summary:focus,
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary:hover p,
div[data-testid="stExpander"][open] summary p,
div[data-testid="stExpander"] details[open] summary p {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #FFFFFF !important;
}
/* the little expand/collapse chevron icon also picks up the accent color
   on hover/open by default -- pin it to match the (white) header text */
div[data-testid="stExpander"] summary svg,
div[data-testid="stExpander"] summary:hover svg,
div[data-testid="stExpander"][open] summary svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}

.reasoning-text { line-height: 1.6; font-size: 0.95rem; color: #2A2A2A !important; }

.tier-row { font-size: 0.9rem; padding: 0.35rem 0; border-bottom: 1px solid #F0EAE6; }
.tier-row b { color: #141414 !important; }
.tier-row span { color: #6B6B6B !important; }

a.pmid-link {
    display: inline-block;
    border: 1px solid #141414;
    border-radius: 3px;
    padding: 0.3rem 0.7rem;
    margin: 0.2rem 0.35rem 0.2rem 0;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: #141414 !important;
    text-decoration: none;
}
a.pmid-link:hover { background: #141414; color: #FFFFFF !important; }

.caveats-box {
    border-left: 2px solid #141414;
    padding: 0.7rem 1rem;
    font-size: 0.9rem;
    color: #383838 !important;
    background: #FAFAFA;
}

/* Spinner shown while the pipeline runs -- recolor from Streamlit's
   default red accent to match the theme, and keep the label dark. */
div[data-testid="stSpinner"] {
    color: #141414 !important;
}
div[data-testid="stSpinner"] > div {
    border-top-color: #C97389 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

VERDICT_META = {
    "driver": {"class": "driver", "label": "Likely driver"},
    "passenger": {"class": "passenger", "label": "Likely passenger"},
    "uncertain": {"class": "uncertain", "label": "Uncertain"},
}

TIER_LABELS = {
    "genetic_association": "Genetic association",
    "functional_perturbation": "Functional perturbation",
    "mendelian_randomization": "Mendelian randomization",
    "expression_correlation": "Expression correlation",
    "pathway_context": "Pathway context",
    "irrelevant": "Irrelevant",
}

# Ordered strongest-to-weakest causal signal, independent of how many
# mentions each tier got -- this ordering is what makes the chart legible
# as "evidence quality", not just "evidence volume".
_TIER_ORDER = [
    "genetic_association",
    "mendelian_randomization",
    "functional_perturbation",
    "pathway_context",
    "expression_correlation",
    "irrelevant",
]


def _tier_chart(tier_counts: dict):
    """Two-panel horizontal bar chart: raw mention count per tier next to
    that tier's weighted contribution to the overall score. Tiers are
    ordered by causal reliability (strongest at top), not by count, so the
    chart reads as a quality comparison rather than a popularity contest."""
    present_tiers = [t for t in _TIER_ORDER if t in tier_counts and t != "irrelevant"]
    if not present_tiers:
        return None

    labels = [TIER_LABELS[t] for t in present_tiers]
    counts = [tier_counts[t] for t in present_tiers]
    weighted = [tier_counts[t] * TIER_WEIGHTS.get(t, 0) for t in present_tiers]
    y = range(len(present_tiers))

    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(7, 0.55 * len(present_tiers) + 0.8), sharey=True
    )
    fig.patch.set_facecolor("white")

    ax_left.barh(y, counts, color="#141414", height=0.55)
    ax_left.set_title("Mentions", fontsize=10, fontweight="bold", loc="left", color="#141414")
    ax_left.invert_xaxis()
    ax_left.invert_yaxis()  # shared with ax_right -- inverting once affects both

    ax_right.barh(y, weighted, color="#C97389", height=0.55)
    ax_right.set_title(
        "Weighted contribution", fontsize=10, fontweight="bold", loc="left", color="#141414"
    )

    for ax in (ax_left, ax_right):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False)
        ax.set_xlabel("")

    ax_left.set_yticks(list(y))
    ax_left.set_yticklabels(labels, fontsize=9, color="#141414")

    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
    <div class="eyebrow">Target validation · AI-assisted</div>
    <h1>BioLead</h1>
    <p>Separates true causal driver genes from correlated passenger genes in
    diseases, weighing functional evidence over
    expression correlation alone.</p>
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
    submitted = st.form_submit_button("Analyze evidence")

# --------------------------------------------------------------------------
# Run pipeline + render results
# --------------------------------------------------------------------------
if submitted:
    if not gene.strip() or not disease.strip():
        st.warning("Enter both a gene symbol and a skin condition to run the analysis.")
    else:
        with st.spinner(f"Looking into {gene.strip()}..."):
            try:
                result = run_pipeline(gene.strip(), disease.strip())
                error = None
            except Exception as exc:  # noqa: BLE001 - surface any pipeline error in the UI
                result, error = None, str(exc)

        if error:
            st.error(f"Something went wrong: {error}")
        elif result:
            verdict_key = result.get("verdict", "uncertain")
            meta = VERDICT_META.get(verdict_key, VERDICT_META["uncertain"])

            # --- Always-visible summary block ---
            st.markdown(
                f"""
                <div class="verdict-block {meta['class']}">
                    <div class="eyebrow">Result</div>
                    <div class="verdict-headline">
                        {result.get('gene')} — {meta['label']}
                        <span class="confidence-tag">Confidence: {result.get('confidence', 'unknown')}</span>
                    </div>
                    <div class="meta-line">
                        {result.get('disease')} ·
                        {result.get('num_articles_reviewed', 0)} articles reviewed ·
                        weighted evidence score {result.get('weighted_score', 0)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # --- Reasoning (collapsible, exportable) ---
            with st.expander("Reasoning", expanded=True):
                reasoning_text = result.get("reasoning", "No reasoning returned.")
                st.markdown(
                    f'<div class="reasoning-text">{reasoning_text}</div>',
                    unsafe_allow_html=True,
                )

                export_lines = [
                    f"# BioLead reasoning — {result.get('gene')} / {result.get('disease')}",
                    "",
                    f"Verdict: {meta['label']} (confidence: {result.get('confidence', 'unknown')})",
                    f"Weighted evidence score: {result.get('weighted_score', 0)}",
                    f"Articles reviewed: {result.get('num_articles_reviewed', 0)}",
                    "",
                    "## Reasoning",
                    reasoning_text,
                ]
                if result.get("supporting_pmids"):
                    export_lines += [
                        "",
                        "## Cited sources",
                        *[
                            f"- PMID {pmid}: https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                            for pmid in result["supporting_pmids"]
                        ],
                    ]
                if result.get("caveats"):
                    export_lines += ["", "## Caveats", result["caveats"]]

                st.download_button(
                    label="Export reasoning",
                    data="\n".join(export_lines),
                    file_name=f"{result.get('gene')}_{result.get('disease')}_reasoning.md".replace(
                        " ", "_"
                    ),
                    mime="text/markdown",
                )

            # --- Evidence tier breakdown (collapsible, with chart) ---
            tier_counts = result.get("tier_counts", {})
            if tier_counts:
                with st.expander("Evidence tier breakdown", expanded=True):
                    fig = _tier_chart(tier_counts)
                    if fig is not None:
                        st.pyplot(fig, use_container_width=True)
                        st.caption(
                            "Mentions (left) vs. that tier's actual contribution to the "
                            "weighted score (right) — a tier can have many mentions and "
                            "still barely move the verdict if it's low-reliability evidence."
                        )

                    rows = "".join(
                        f'<div class="tier-row"><b>{count}</b> '
                        f'<span>&nbsp;{TIER_LABELS.get(tier, tier)}</span></div>'
                        for tier, count in sorted(tier_counts.items(), key=lambda kv: -kv[1])
                    )
                    st.markdown(rows, unsafe_allow_html=True)

            # --- Cited sources (collapsible) ---
            supporting_pmids = result.get("supporting_pmids", [])
            if supporting_pmids:
                with st.expander("Cited sources"):
                    links = "".join(
                        f'<a class="pmid-link" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" '
                        f'target="_blank" rel="noopener noreferrer">PMID {pmid} &nbsp;→</a>'
                        for pmid in supporting_pmids
                    )
                    st.markdown(links, unsafe_allow_html=True)

            # --- All articles reviewed (collapsible) ---
            all_pmids = result.get("pmids_reviewed", [])
            if all_pmids:
                with st.expander(f"All {len(all_pmids)} articles reviewed"):
                    links = "".join(
                        f'<a class="pmid-link" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/" '
                        f'target="_blank" rel="noopener noreferrer">PMID {pmid} &nbsp;→</a>'
                        for pmid in all_pmids
                    )
                    st.markdown(links, unsafe_allow_html=True)

            # --- Caveats (collapsible, only if present) ---
            if result.get("caveats"):
                with st.expander("Caveats"):
                    st.markdown(
                        f'<div class="caveats-box">{result["caveats"]}</div>',
                        unsafe_allow_html=True,
                    )
