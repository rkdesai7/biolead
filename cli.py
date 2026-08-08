"""
Local CLI for local testing of the pipeline.
Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python cli.py IL13 "atopic dermatitis"
"""

import argparse
import json

from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="BioLead driver-vs-passenger gene agent")
    parser.add_argument("gene", help="Gene symbol, e.g. IL13")
    parser.add_argument("disease", help="Disease or phenotype name, e.g. 'atopic dermatitis'")
    args = parser.parse_args()

    result = run_pipeline(args.gene, args.disease)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
