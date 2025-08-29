"""
M.6.2 — Web Content Summarization Module
PURPOSE: Summarize web content before ingesting into memory, using extractive or LLM-based methods.
INPUTS: content (str), method (str: 'extractive' or 'llm'), max_length (int)
ACTIONS:
  1. Summarize content using the selected method.
  2. Return summary for downstream ingest.
OUTPUT/STATE: Summarized content
ROLLBACK: N/A (stateless)
QUICKTEST: python -m memory.M.6.2_web_summarize --test
"""

from typing import Optional
import re

# Stub for LLM summarization (replace with real LLM call in production)
def llm_summarize(text: str, max_length: int = 512) -> str:
    return text[:max_length] + ("..." if len(text) > max_length else "")

# Simple extractive summarizer: take first N sentences
def extractive_summarize(text: str, max_length: int = 512) -> str:
    sentences = re.split(r'(?<=[.!?]) +', text)
    summary = ''
    for s in sentences:
        if len(summary) + len(s) > max_length:
            break
        summary += s + ' '
    return summary.strip()

def summarize_content(content: str, method: str = 'extractive', max_length: int = 512) -> str:
    if method == 'llm':
        return llm_summarize(content, max_length)
    else:
        return extractive_summarize(content, max_length)

def quicktest():
    text = "This is sentence one. This is sentence two. This is sentence three."
    s1 = summarize_content(text, 'extractive', 30)
    s2 = summarize_content(text, 'llm', 30)
    assert s1 and s2
    print("M.6.2 quicktest passed.")

if __name__ == "__main__":
    quicktest()
