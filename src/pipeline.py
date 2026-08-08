"""
End-to-end orchestration: gene + disease in, verdict + citations out.
This is the function both the CLI and the Lambda handler call -- keeping it
free of any AWS- or CLI-specific code makes it trivial to also run inside a
Step Functions state machine later if the pipeline grows (e.g. to fan out
tagging calls in parallel).
"""

from src import reasoning, tagging
from src.retrieval import open_targets, pubmed


def run_pipeline(gene: str, disease: str) -> dict:
    pmids = pubmed.search_pubmed(gene, disease)
    abstracts = pubmed.fetch_abstracts(pmids)

    tagged_evidence = []
    for article in abstracts:
        items = tagging.tag_abstract(gene, disease, article["abstract"], article["pmid"])
        tagged_evidence.extend(items)

    genetic_assoc_evidence = open_targets.get_genetic_associations(gene)

    verdict = reasoning.generate_verdict(gene, disease, tagged_evidence, genetic_assoc_evidence)
    verdict["gene"] = gene
    verdict["disease"] = disease
    verdict["num_articles_reviewed"] = len(abstracts)
    verdict["pmids_reviewed"] = pmids
    return verdict
