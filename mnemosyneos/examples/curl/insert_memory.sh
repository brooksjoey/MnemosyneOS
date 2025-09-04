#!/usr/bin/env bash
curl -X POST http://127.0.0.1:8208/memories -d '{"text":"hello"}' -H "Content-Type: application/json"
