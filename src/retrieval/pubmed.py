"""
Retrieves candidate evidence articles from PubMed via NCBI E-utilities.
This is the "evidence article" step of the pipeline -- it does not decide
anything about driver/passenger status, it just gathers raw text.
"""

import xml.etree.ElementTree as ET

import requests

from src import config

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def _base_params():
    params = {"tool": config.NCBI_TOOL, "email": config.NCBI_EMAIL}
    if config.NCBI_API_KEY:
        params["api_key"] = config.NCBI_API_KEY
    return params


def search_pubmed(gene: str, disease: str, max_results: int | None = None) -> list[str]:
    """Return a list of PMIDs mentioning both the gene and the disease/phenotype."""
    query = f"({gene}[Title/Abstract]) AND ({disease}[Title/Abstract])"
    params = {
        **_base_params(),
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results or config.MAX_PUBMED_RESULTS,
    }
    resp = requests.get(ESEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])


def fetch_abstracts(pmids: list[str]) -> list[dict]:
    """Fetch title + abstract text for a batch of PMIDs."""
    if not pmids:
        return []
    params = {
        **_base_params(),
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }
    resp = requests.get(EFETCH_URL, params=params, timeout=20)
    resp.raise_for_status()
    return _parse_pubmed_xml(resp.text)


def _parse_pubmed_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    articles = []
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//PMID")
        pmid = pmid_el.text if pmid_el is not None else None

        title_el = art.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""

        abstract_parts = art.findall(".//AbstractText")
        abstract = " ".join("".join(p.itertext()) for p in abstract_parts)

        if pmid and abstract:
            articles.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                }
            )
    return articles
