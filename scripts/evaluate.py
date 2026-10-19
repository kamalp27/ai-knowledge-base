#!/usr/bin/env python
"""CLI Evaluation Entrypoint for AI Knowledge Base RAG Evaluation Suite.

Usage:
    python scripts/evaluate.py
    python scripts/evaluate.py --use-real-embeddings
    python scripts/evaluate.py --output evaluations/reports/custom_eval.json
"""
import os
import sys

# Ensure repository root is on sys.path
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.rag.evaluation.cli import main

if __name__ == "__main__":
    main()
