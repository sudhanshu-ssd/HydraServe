from prometheus_client import Counter,Histogram,Gauge,make_asgi_app


REQUESTS_TOTAL = Counter(
    "hydraserve_requests_total",
    "Total API requests",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "hydraserve_request_latency_seconds",
    "Request latency",
    ["endpoint"]
)

CACHE_HITS = Counter(
    "hydraserve_cache_hits_total",
    "Total cache hits"
)

CACHE_MISSES = Counter(
    "hydraserve_cache_misses_total",
    "Total cache misses"
)

PROVIDER_LATENCY = Histogram(
    "provider_latency_seconds",
    "LLM latency",
    ["provider","model"]
)


TOKENS_USED = Counter(
    "hydraserve_tokens_total",
    "Total LLM tokens",
    ["model","type"]
)

RATE_LIMIT_REJECTED = Counter(
    "hydraserve_rate_limit_rejections_total",
    "Rejected requests"
)

PROVIDER_ERRORS = Counter(
    "hydraserve_provider_errors_total",
    "LLM provider failures",
    ["provider"]
)

FALLBACK_TOTAL = Counter(
    "hydraserve_fallback_total",
    "Fallback invocations",
    ["from_provider","to_provider"]
)