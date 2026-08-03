# 🚀 HydraServe (AI Gateway & Control Plane)

HydraServe is a production-grade **AI Gateway and Control Plane** designed to route, orchestrate, and observe LLM workloads across multiple providers (OpenAI, Gemini). 

It abstracts away the complexities of interacting with disparate AI models, providing a unified compute layer with built-in intelligent routing, enterprise-grade rate limiting, observability, and fallback logic.

## 🌟 The Problem it Solves
Companies are moving beyond simple chatbots to production agentic systems. You can't just duct-tape API calls to LLM providers; you need a robust infrastructure layer. 

HydraServe acts as a control plane that provides:
- **Intelligent Routing & Fallback Logic:** Never fail a request due to an OpenAI or Anthropic outage. HydraServe seamlessly routes between providers.
- **Observability & Telemetry:** Full visibility into token usage, latency, and cache hit rates via Prometheus, Grafana, OpenTelemetry, and Langfuse.
- **Semantic & Exact Caching:** Powered by Redis to drastically reduce latency and API costs for repeated queries.
- **Enterprise Governance:** API key management, project-based usage tracking, and dynamic rate-limiting (Token Bucket algorithm).

## 🏗️ Architecture & Tech Stack

### Control Plane (Backend)
- **Framework:** FastAPI (Python) for asynchronous, high-throughput request handling.
- **Database:** PostgreSQL (asyncpg, SQLAlchemy) for user governance, project tracking, and API keys.
- **Caching & Rate Limiting:** Redis for ultra-low latency exact-match caching and distributed rate limiting.
- **Observability:** Prometheus (Metrics), Grafana (Dashboards), OpenTelemetry (Tracing), Langfuse (LLM Tracing).

### Management Console (Frontend)
- **Framework:** React 19, TypeScript, Vite.
- **Styling:** TailwindCSS, shadcn/ui, dark-mode native.
- **Analytics:** Recharts for dynamic time-series metrics (Token trends, latency, usage).
- **State Management:** TanStack Query for robust data fetching and caching.

## ⚡ Core Features

1. **Unified LLM Gateway:** One API endpoint (`/chat`) that routes requests to any provider.
2. **Resilience (Fallbacks):** If a primary provider (e.g., Anthropic) is rate-limited or down, HydraServe instantly falls back to an alternative (e.g., OpenAI).
3. **Advanced Rate Limiting:** Dynamic rate limits per-user and per-project to prevent abuse and enforce cost policies.
4. **Instant Caching:** Identical prompts hit the Redis cache, returning responses in < 5ms and costing $0.00 in LLM API fees.
5. **Developer Dashboard:** A premium React dashboard to manage API keys, track token usage across projects, and view live latency metrics.

## 🚦 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL
- Redis
- API Keys for your preferred LLM providers (OpenAI, Groq, etc.)

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/hydraserve.git
cd hydraserve

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the gateway
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📈 Roadmap (Next Iterations)
- **gRPC Support:** For ultra-low latency microservice communication.
- **Semantic Caching:** Integrating VectorDBs to cache conceptually similar queries, not just exact string matches.
- **MCP Gateway Integration:** Centralized tool management for multi-agent workflows.

---
