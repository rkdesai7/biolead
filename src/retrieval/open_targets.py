"""
Pulls structured genetic-evidence scores from the Open Targets Platform.
This is the highest-value data source in the whole pipeline: Open Targets
already decomposes gene-disease evidence into datatype buckets (genetic
association, somatic mutation, animal model, literature, RNA expression,
etc.), which line up almost directly with our driver-vs-passenger evidence
tiers -- and it's structured data, not something an LLM has to infer from
prose.
"""

import requests

from src import config

_SEARCH_QUERY = """
query searchGene($q: String!) {
  search(queryString: $q, entityNames: ["target"]) {
    hits { id name entity }
  }
}
"""

_ASSOCIATIONS_QUERY = """
query targetAssociations($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    associatedDiseases(page: { index: 0, size: 15 }) {
      rows {
        disease { id name }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""


def _post(query: str, variables: dict) -> dict:
    resp = requests.post(
        config.OPEN_TARGETS_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def resolve_ensembl_id(gene_symbol: str) -> str | None:
    data = _post(_SEARCH_QUERY, {"q": gene_symbol})
    hits = data.get("data", {}).get("search", {}).get("hits", [])
    for hit in hits:
        if hit.get("entity") == "target":
            return hit["id"]
    return None


def get_genetic_associations(gene_symbol: str) -> list[dict]:
    """
    Returns per-disease evidence rows with Open Targets' own datatype
    breakdown, e.g. genetic_association, somatic_mutation, known_drug,
    affected_pathway, rna_expression, animal_model, literature.
    A gene with a high genetic_association score and a low rna_expression
    score is a strong driver candidate; the reverse pattern is a red flag
    for "passenger".
    """
    ensembl_id = resolve_ensembl_id(gene_symbol)
    if not ensembl_id:
        return []

    data = _post(_ASSOCIATIONS_QUERY, {"ensemblId": ensembl_id})
    target = data.get("data", {}).get("target") or {}
    rows = target.get("associatedDiseases", {}).get("rows", [])

    evidence = []
    for row in rows:
        evidence.append(
            {
                "gene": gene_symbol,
                "disease": row["disease"]["name"],
                "overall_score": row["score"],
                "datatype_scores": row.get("datatypeScores", []),
                "source": "Open Targets",
            }
        )
    return evidence
