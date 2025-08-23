src/utils/metrics.py
from prometheus_client import Counter, Histogram

recall_latency_ms = Histogram(
    "recall_latency_ms", "Recall latency (ms)", buckets=(1,5,10,20,30,40,50,75,100,200)
)
ingest_counter = Counter("ingest_total", "Memories ingested")
reflect_counter = Counter("reflect_total", "Reflection runs")
compress_counter = Counter("compress_total", "Compression runs")