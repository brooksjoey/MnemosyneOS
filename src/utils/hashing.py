src/utils/hashing.py
import hashlib, json

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_json(obj) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"))

def stable_hash_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()