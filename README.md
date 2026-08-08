# BioLead (local prototype)

This is an easy to use agent that allows drug and cosmetic developers to streamline their search in identifying whether significant genetic biomarkers are actually causal of disease/phenotype instead of just covariant.

Given a gene symbol and a disease/phenotype, this pipeline gathers literature and
genetic-association evidence from PubMed and Open Targets, identifies what each piece of evidence supports, and
asks an LLM to produce a weighteed and citation-backed verdict: 

- `driver`: the gene plays a role in inducing the phenotype
- `passenger`: differences in gene activity are a symptom of the phenotype
- `uncertain`: inconclusive evidence

Currently, this is a local-only prototype, but `pipeline.py` can be used for seamless deployment in the cloud (see the accompanying diagram).

## Pipeline

1. **Retrieval** (`src/retrieval/`): Scrapes both PubMed abstracts mentioning the gene and
   disease using NCBI E-utilities. and genetic-association scores from the Open
   Targets Platform.
2. **Tagging** (`src/tagging.py`): An LLM call classifies each sentence in the PubMed
   abstracts into an evidence tier (genetic association, functional perturbation,
   Mendelian randomization, expression correlation, pathway context, or irrelevant).
3. **Reasoning** (`src/reasoning.py`): Aggregates tier counts with weights that favor
   causal evidence over correlation, then uses an LLM for a chain-of-thought classification
   that must cite PMIDs for every claim.

To Run in Terminal:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export NCBI_EMAIL=you@example.com   # NCBI requires a contact email
python cli.py IL13 "atopic dermatitis"
```

This prints the full verdict JSON: `verdict`, `confidence`, `reasoning` (with PMID
citations), `tier_counts`, `weighted_score`, and the list of PMIDs reviewed.

## Demo UI

A Streamlit front end (`app.py`) provides a live UI. This includes gene and disease
inputs, a verdict badge, the evidence tier breakdown, and clickable PMID's linking out to a
source article on PubMed in a new tab.

To run:

```bash
pip install -r requirements-app.txt
export ANTHROPIC_API_KEY=sk-ant-...
export NCBI_EMAIL=you@example.com
streamlit run app.py
```

Opens at `http://localhost:8501`. An average query takes ~1-2 minutes end to end, so the spinner is
expected to sit for a bit.

## Using a local model for tagging (optional)

A local model can be swapped in the tagging step (`src/tagging.py`) to save token usage.
(`src/reasoning.py`) stays on Claude regardless of this setting, since it's the one call per
run that has to weigh conflicting evidence and produce trustworthy chain-of-thought.

1. Install [Ollama](https://ollama.com) and pull a model, e.g.:
   ```bash
   ollama pull qwen3:8b
   ```
2. Point the pipeline at it:
   ```bash
   export TAGGING_BACKEND=ollama
   export OLLAMA_MODEL=qwen3:8b        # optional, this is the default
   export OLLAMA_HOST=http://localhost:11434   # optional, this is the default
   ```
3. Run as usual:
   ```bash
   python cli.py IL13 "atopic dermatitis"
   ```

## Tuning

- **Tier weights** lat the top of `src/reasoning.py` can be adjusted
- **NCBI rate limits**: Get a free NCBI API key and set `NCBI_API_KEY` to raise the limit to 10 req/s.

## Future Improvements

- Cache results for popular targets
- Implement ground truth
- Transfer to a virtual machine to run heavier models locally (eliminating token cost altogether)
- Integrate other literature
