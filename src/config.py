"""
Central configuration. All values come from environment variables so the
same code runs unchanged locally, in a container, or as a Lambda function.
In AWS, set these as Lambda environment variables (encrypt ANTHROPIC_API_KEY
with a KMS key or, better, pull it from Secrets Manager at cold start -- see
README for the Secrets Manager variant).
"""

import os

#LLM: reasoning step (always Claude)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# --- LLM: tagging step (swappable backend) ---
# "anthropic" uses the same Claude client as the reasoning step.
# "ollama" uses a local model (e.g. Qwen3) via a local Ollama server -- much
# cheaper for the high-volume tagging step, at some cost to tier-labeling
# accuracy. Validate a sample against the anthropic backend before trusting
# it for a real run (see README).
TAGGING_BACKEND = os.environ.get("TAGGING_BACKEND", "anthropic")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "60"))

# --- NCBI E-utilities ---
# NCBI asks for an identifying email + tool name, and will rate-limit you
# harder if you don't provide an api_key. Get a free key from your NCBI
# account settings and set it as NCBI_API_KEY to raise the limit to 10 req/s.
NCBI_API_KEY = os.environ.get("NCBI_API_KEY")
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "your-email@example.com")
NCBI_TOOL = "biolead-agent"

MAX_PUBMED_RESULTS = int(os.environ.get("MAX_PUBMED_RESULTS", "15"))

# --- Open Targets ---
OPEN_TARGETS_GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
