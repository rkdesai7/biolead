"""
Final reasoning step: aggregates tagged literature evidence and Open Targets
genetic-association scores, then asks the LLM to produce a weighted,
citation-backed verdict. The weighting scheme encodes the evidence hierarchy
from the design doc so the model can't substitute mention-count for evidence
quality (the exact failure mode the "passenger gene" problem describes).
"""

import json

from anthropic import Anthropic

from src import config

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


# Relative weight per evidence tier -- tune these against your gold-standard
# validation set (see README) rather than treating them as fixed truth.
TIER_WEIGHTS = {
    "genetic_association": 4,
    "mendelian_randomization": 4,
    "functional_perturbation": 3,
    "pathway_context": 1,
    "expression_correlation": 1,
    "irrelevant": 0,
}

_SYSTEM_PROMPT = """You are a dermatology drug discovery target validation expert.

You are given a bundle of tiered evidence about whether a gene is a true causal DRIVER of
a disease/phenotype, or merely a PASSENGER -- correlated with disease but not causal (e.g.
upregulated purely as a downstream consequence of skin inflammation).

Evidence tier reliability, strongest to weakest causal signal:
1. genetic_association / mendelian_randomization -- human genetic evidence; the variant
   exists before disease onset, so it is the hardest signal to confound
2. functional_perturbation -- knockout / knockdown / overexpression / rescue experiments
3. pathway_context -- mechanistic plausibility only, no direct causal test
4. expression_correlation -- weakest signal; a gene can be strongly upregulated in disease
   tissue with zero causal role

Rules you must follow:
- Never let volume of mentions substitute for evidence quality. Twenty expression-correlation
  mentions and zero genetic evidence is still a weak driver candidate.
- If genetic_association or functional_perturbation evidence is present and consistent, lean
  toward "driver".
- If the only evidence is expression_correlation or pathway_context, lean toward "passenger"
  or "uncertain" -- do not call something a driver on correlation alone.
- If evidence conflicts across tiers, say so explicitly and lower your confidence rather than
  picking a side to sound decisive.
- Every claim in your reasoning must cite a PMID from the evidence bundle, or reference the
  Open Targets datatype score it came from.

Respond with ONLY this JSON object, no markdown fences, no extra text:
{
  "verdict": "driver | passenger | uncertain",
  "confidence": "high | medium | low",
  "reasoning": "step-by-step reasoning citing PMIDs and evidence tiers",
  "supporting_pmids": ["..."],
  "caveats": "what evidence is missing or would change this verdict"
}
"""


def score_evidence_bundle(tagged_evidence: list[dict]) -> tuple[dict, int]:
    tier_counts: dict[str, int] = {}
    for item in tagged_evidence:
        tier = item.get("tier", "irrelevant")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    weighted_score = sum(TIER_WEIGHTS.get(t, 0) * c for t, c in tier_counts.items())
    return tier_counts, weighted_score


def generate_verdict(
    gene: str,
    disease: str,
    tagged_evidence: list[dict],
    genetic_assoc_evidence: list[dict],
) -> dict:
    tier_counts, weighted_score = score_evidence_bundle(tagged_evidence)

    payload = {
        "gene": gene,
        "disease": disease,
        "tier_counts": tier_counts,
        "weighted_score": weighted_score,
        "literature_evidence": tagged_evidence,
        "open_targets_genetic_evidence": genetic_assoc_evidence,
    }
    user_prompt = "Evidence bundle:\n" + json.dumps(payload, indent=2)

    response = _get_client().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = response.content[0].text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        verdict = json.loads(text)
    except json.JSONDecodeError:
        verdict = {
            "verdict": "uncertain",
            "confidence": "low",
            "reasoning": text,
            "supporting_pmids": [],
            "caveats": "Model output was not valid JSON; showing raw text in 'reasoning'.",
        }

    verdict["tier_counts"] = tier_counts
    verdict["weighted_score"] = weighted_score
    return verdict
