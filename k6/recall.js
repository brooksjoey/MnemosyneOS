k6/recall.js
import http from 'k6/http';
import { sleep } from 'k6';
import { Trend } from 'k6/metrics';
let t = new Trend('recall_latency');

export let options = { vus: 100, duration: '30s' };

export default function () {
  const url = 'http://localhost:8000/recall?query=project%20notes&k=5';
  const params = { headers: { Authorization: 'Bearer dev-key-123' } };
  let res = http.get(url, params);
  t.add(res.timings.duration);
  if (res.status !== 200) { console.error(res.status, res.body); }
  sleep(0.1);
}