"""
M.5.6 — L5 Voice Adapter Module
PURPOSE: Provide a voice interface for the memory system, enabling speech-to-text ingestion and spoken recall.
INPUTS: Microphone audio (for ingest), text query (for recall)
ACTIONS:
  1. Capture voice input and transcribe to text (stub: input()).
  2. Ingest transcribed text as an event.
  3. Optionally, recall and speak results (stub: print()).
OUTPUT/STATE: Voice-driven memory interaction
ROLLBACK: N/A (interface only)
QUICKTEST: python -m memory.M.5.6_l5_voice_adapter --test
"""

from .M.5.4_l5_api_adapter import memory_api

def voice_ingest():
    # Stub: Replace input() with real speech-to-text in production
    print("[VOICE] Speak now (type for demo): ", end="")
    text = input()
    if text:
        memory_api("ingest", {"event_type": "voice", "content": text, "metadata": {"source": "mic"}})
        print("[VOICE] Ingested.")
    else:
        print("[VOICE] No input.")

def voice_recall():
    print("[VOICE] Query (type for demo): ", end="")
    query = input()
    if query:
        result = memory_api("recall", {"query": query, "limit": 3})
        print("[VOICE] Recall:")
        for item in result.get("result", []):
            print("-", item.get("content", "[no content]"))
    else:
        print("[VOICE] No query.")

def quicktest():
    print("[VOICE] Quicktest: (skipped, interactive)")

if __name__ == "__main__":
    print("[VOICE] Demo: Ingest then recall.")
    voice_ingest()
    voice_recall()
