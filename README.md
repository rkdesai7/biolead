# BioLead — driver vs. passenger gene agent (local prototype)

Given a gene symbol and a disease/phenotype, this pipeline gathers literature and
genetic-association evidence, tags each piece of evidence by causal-strength tier, and
asks an LLM to produce a weighted, citation-backed verdict: `driver`, `passenger`, or
`uncertain`.

This is a local-only prototype meant for iterating on the reasoning and testing against
known genes. See the accompanying diagram for how to move it to AWS once it's validated.

## Pipeline

1. **Retrieval** (`src/retrieval/`) — pulls PubMed abstracts mentioning the gene and
   disease (NCBI E-utilities) and structured genetic-association scores from the Open
   Targets Platform.
2. **Tagging** (`src/tagging.py`) — an LLM call classifies each relevant sentence in the
   abstracts into an evidence tier (genetic association, functional perturbation,
   Mendelian randomization, expression correlation, pathway context, or irrelevant).
3. **Reasoning** (`src/reasoning.py`) — aggregates tier counts with weights that favor
   causal evidence over correlation, then asks the LLM for a chain-of-thought verdict
   that must cite PMIDs for every claim.

`src/pipeline.py` wires these together into a single `run_pipeline(gene, disease)` call.

## Running it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export NCBI_EMAIL=you@example.com   # NCBI requires a contact email
python cli.py IL13 "atopic dermatitis"
```

This prints the full verdict JSON: `verdict`, `confidence`, `reasoning` (with PMID
citations), `tier_counts`, `weighted_score`, and the list of PMIDs reviewed.

## Demo UI

A Streamlit front end (`app.py`) wraps `run_pipeline()` for a live demo — gene and disease
inputs, a verdict badge, the evidence tier breakdown, and clickable PMID links that open the
source article on PubMed in a new tab. It's a UI layer only; it doesn't change any pipeline
logic.

```bash
pip install -r requirements-app.txt
export ANTHROPIC_API_KEY=sk-ant-...
export NCBI_EMAIL=you@example.com
streamlit run app.py
```

Opens at `http://localhost:8501`. A query takes ~1-2 minutes end to end, so the spinner is
expected to sit for a bit — that's the tagging loop working through each abstract, not a bug.

## Using a local model for tagging (optional)

The tagging step (`src/tagging.py`) — classifying evidence sentences into tiers — is the
high-volume part of the pipeline (one call per abstract), so it's the natural place to swap
in a cheap local model instead of paying per-token for every run. The reasoning/verdict step
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
3. Run as usual — `ANTHROPIC_API_KEY` is still required for the reasoning step:
   ```bash
   python cli.py IL13 "atopic dermatitis"
   ```

Both backends share the exact same prompt and tier schema, so switching `TAGGING_BACKEND`
back to `anthropic` gives you a direct point of comparison. **Validate before trusting it**:
smaller local models tend to find the right sentence but pick an adjacent tier (e.g.
`pathway_context` instead of `expression_correlation`) more often than Claude does. Run the
same gene through both backends and diff the `tier` assignments before relying on the local
path for anything that feeds a real verdict. Each tagged item is stamped with
`tagging_backend` so you can tell which backend produced it when comparing runs.

## Tuning before you trust it

- **Tier weights** live at the top of `src/reasoning.py`. They're a reasonable starting
  point, not tuned — adjust them against real cases.
- **Validation set**: before presenting, run a handful of well-documented driver genes
  (e.g. FLG in atopic dermatitis) and correlation-only genes through `cli.py` and check
  the verdicts against the known answer. This also tells you if the tagging step
  (`src/tagging.py`) is classifying evidence sentences correctly — spot-check a few.
- **NCBI rate limits**: unauthenticated E-utilities calls are throttled hard. Get a free
  NCBI API key and set `NCBI_API_KEY` to raise the limit to 10 req/s.
- **GeneCards**: it has no public API, so genetic-association evidence comes from Open
  Targets instead, which returns the same kind of evidence as structured datatype scores
  rather than something that needs scraping.

## What this doesn't do yet

- No caching — every run re-queries PubMed, Open Targets, and Claude from scratch.
- No persistence, no API layer, no concurrency — it's a single sequential script.
- No gold-standard accuracy report — that's on you to build once the tier weights feel
  right (see "Tuning before you trust it" above).
