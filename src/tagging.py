"""
Evidence tagging step: given a gene, a disease/phenotype, and an abstract,
extract every sentence describing a gene-disease relationship and classify
it into an evidence tier.

Two interchangeable backends, selected via config.TAGGING_BACKEND:
  - "anthropic": Claude via the Anthropic API (default; highest accuracy on
    the fine-grained tier distinctions, e.g. genetic_association vs.
    mendelian_randomization).
  - "ollama": a local model (e.g. Qwen3) via a local Ollama server. Much
    cheaper for this high-volume step -- one call per abstract -- but
    smaller models are more prone to blurring adjacent tiers. Validate a
    sample of its output against the anthropic backend (or hand-labeled
    data) before trusting it for a real run.

Both backends share the same prompt and JSON schema, so their output is
directly comparable and pipeline.py doesn't need to know which one ran.
"""

import json

import requests
from anthropic import Anthropic

from src import config

_anthropic_client = None


def _get_anthropic_client() -> Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _anthropic_client


EVIDENCE_TIERS = [
    "genetic_association",
    "functional_perturbation",
    "mendelian_randomization",
    "expression_correlation",
    "pathway_context",
    "irrelevant",
]

_SYSTEM_PROMPT = """You are a biomedical evidence classifier for drug target validation.

Given a gene, a disease/phenotype, and a scientific abstract, extract every sentence that
describes a relationship between the gene and the disease, and classify each into exactly
one evidence tier:

- genetic_association: human genetic variants (GWAS, exome/rare variant burden, monogenic
  disease) statistically linked to the disease
- functional_perturbation: knockout, knockdown, overexpression, or rescue experiments that
  change the disease/phenotype
- mendelian_randomization: an MR study inferring a causal effect from genetic instruments
- expression_correlation: the gene is up- or down-regulated in disease tissue/cells, with
  no causal test performed -- this is the weakest tier and the classic "passenger" trap
- pathway_context: the gene's role in a pathway relevant to the disease, without direct
  causal evidence
- irrelevant: the sentence does not support a gene-disease relationship

Respond with ONLY a JSON object of the form {"items": [...]} and nothing else -- no
markdown fences, no commentary. Each entry in "items" must have exactly these keys:
{"sentence": "...", "tier": "...", "direction": "supports_causal | correlative_only | inconclusive"}

If no sentences are relevant, respond with {"items": []}.
"""

# JSON schema shared by both backends. Ollama's structured-output mode uses
# this directly; Anthropic gets the same shape via the prompt instructions
# above (Claude doesn't need schema-constrained decoding to follow it).
_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sentence": {"type": "string"},
                    "tier": {"type": "string", "enum": EVIDENCE_TIERS},
                    "direction": {
                        "type": "string",
                        "enum": ["supports_causal", "correlative_only", "inconclusive"],
                    },
                },
                "required": ["sentence", "tier", "direction"],
            },
        }
    },
    "required": ["items"],
}


def tag_abstract(gene: str, disease: str, abstract: str, pmid: str) -> list[dict]:
    """Extract and tag evidence sentences from one abstract, using whichever
    backend config.TAGGING_BACKEND selects. Returns a list of dicts, each
    stamped with the source pmid."""
    backend = config.TAGGING_BACKEND
    if backend == "anthropic":
        items = _tag_with_anthropic(gene, disease, abstract)
    elif backend == "ollama":
        items = _tag_with_ollama(gene, disease, abstract)
    else:
        raise ValueError(
            f"Unknown TAGGING_BACKEND: {backend!r} (expected 'anthropic' or 'ollama')"
        )

    for item in items:
        item["pmid"] = pmid
        item["tagging_backend"] = backend
    return items


def _user_prompt(gene: str, disease: str, abstract: str) -> str:
    return f"Gene: {gene}\nDisease/phenotype: {disease}\nAbstract:\n{abstract}"


def _tag_with_anthropic(gene: str, disease: str, abstract: str) -> list[dict]:
    response = _get_anthropic_client().messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1000,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_prompt(gene, disease, abstract)}],
    )
    text = response.content[0].text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return _parse_items(text)


def _tag_with_ollama(gene: str, disease: str, abstract: str) -> list[dict]:
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(gene, disease, abstract)},
        ],
        "format": _JSON_SCHEMA,  # constrains output to match the schema
        "stream": False,
        "options": {"temperature": 0},
    }
    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/chat", json=payload, timeout=config.OLLAMA_TIMEOUT
    )
    resp.raise_for_status()
    text = resp.json().get("message", {}).get("content", "")
    return _parse_items(text)


def _parse_items(text: str) -> list[dict]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        return data.get("items", [])
    if isinstance(data, list):  # tolerate a bare array too
        return data
    return []
