import http from 'k6/http';
import { check } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errors = new Rate('hydra_errors');
const successfulRequests = new Counter('hydra_success');
const gatewayLatency = new Trend('hydra_latency');

export const options = {
  // Staged concurrency to find the breaking point
  stages: [
    { duration: '10s', target: 10 },
    { duration: '20s', target: 25 },
    { duration: '20s', target: 50 },
    { duration: '20s', target: 100 },
    { duration: '20s', target: 200 },
    { duration: '10s', target: 0 },
  ],

  // Don't fail the test immediately, just observe the metrics for now
  thresholds: {
    http_req_failed: ['rate<0.01'],
    hydra_errors: ['rate<0.01'],
  },
};

// Use environment variables for secrets
const API_KEY = __ENV.MOCK_API;

export default function () {
  // Use host.docker.internal for Docker on Windows to reach the host's localhost
  const url = 'http://host.docker.internal:8000/chat';

  const res = http.post(
    url,
    JSON.stringify({
      prompt: 'Hello, this is a load test!',
      model: 'mock-llm',
      system_prompt: 'You are a load testing bot.',
      max_tokens: 50,
      model_temp: 1.1,
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${API_KEY}`,
      },
    }
  );

  const ok = check(res, {
    'status is 200': (r) => r.status === 200,
  });

  errors.add(!ok);
  if (ok) successfulRequests.add(1);

  gatewayLatency.add(res.timings.duration);
}
