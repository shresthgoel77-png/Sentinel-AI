# Sentinel AI

**Sentinel AI** is a runtime security platform that protects enterprise AI applications by sitting between your app and any large language model (LLM). Rather than acting as a chatbot or simple prompt filter, Sentinel provides a model-agnostic layer for security, governance, observability, and policy enforcement.

<p align="center">
  <img src="docs/images/hero-dashboard.png" alt="Sentinel AI dashboard — AI Shield protecting systems from data leaks and jailbreak attacks" width="900" />
</p>

<p align="center">
  <em>The live interactive demo dashboard — scan stats, threat counters, and one-click access to security demos.</em>
</p>

It enables organizations to securely integrate with providers such as OpenAI, Anthropic, Google Gemini, Azure OpenAI, Amazon Bedrock, Vertex AI, Ollama, and self-hosted models — enforcing security controls before, during, and after every AI interaction.

---

## Why Sentinel AI?

As organizations rapidly adopt generative AI, traditional application security is no longer enough. AI introduces entirely new attack vectors:

- Prompt injection and jailbreak attempts
- Sensitive data leakage (PII, credentials) in model responses (Data Loss Prevention)
- Malicious RAG documents poisoned before ingestion
- Policy violations and multi-tenant isolation breaches
- **Operational Intelligence & SOC gaps:** Lack of live traffic streaming, persistent Multi-Tenancy control, and async webhook alerting.

Sentinel is designed to become the **runtime security layer** for enterprise AI applications — providing continuous inspection, threat detection, governance, multi-tenant policy enforcement, and egress masking without requiring changes to the underlying model.

---
## Technology Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=ts,react,js,python,redis,postgres" />
</p>

| Layer | Technologies |
|-------|-------------|
| **Frontend (SaaS Shell)** | React, TypeScript, Vite, Tailwind CSS, Recharts, Lucide-React, OGL (DarkVeil Shader) |
| **Backend (Gateway)** | Python, FastAPI (Async Loop & BackgroundTasks), SQLAlchemy, Alembic, OpenAI SDK |
| **Infrastructure** | PostgreSQL (State/Tenants/Incidents), Redis (aioredis, Edge-Caching, Rate Limiting) |
| **AI Security Stack** | LangChain, LangGraph (State Machine), RAG Pipeline |

---

## Features & Supported Providers

The frontend ships with an interactive demo while the Backend functions as a production OpenAI-compatible API Gateway. Supported providers currently include **OpenAI (gpt, o1 models)**, **Anthropic (claude)**, and **Google Gemini** via a dynamic Adapter Design Pattern routing.

| Feature | What it does (Current Capabilities) |
|---------|--------------|
| **OpenAI-Compatible Gateway** | Intercepts `/v1/chat/completions` natively injecting Tenant and Application contexts, providing drop-in security. |
| **Pre-Execution Security Pipeline** | Distributed LangGraph nodes (`analyze_semantics`, `detect_heuristics`, `evaluate_harm`) intercept threats in real-time. |
| **Egress Data Masking (DLP)** | Post-execution string parsing via `Sanitizer.py` automatically redacts API keys, credentials, and PII migrating out of the LLM. |
| **Multi-Tenant Policies** | Custom Risk limits and features per organization dynamically evaluated from PostgreSQL (e.g., `evaluate_policies()`). |
| **Non-Blocking Telemetry & SOC** | FastAPI BackgroundTasks (`write_incident_background`) persist Gateway logs and dispatch Webhook/Slack alerts without impacting LLM latency. |

### Deep Prompt Analysis & API Endpoints

The Core Engine analyzes incoming vectors using a cyclical LangGraph State Machine. You can hit the API via real-time endpoints (e.g., `/api/analyze-prompt`, `/api/analyze-document`) or via the UI. 

If a prompt exceeds a **risk score of 70**, the `ThreatState` halts the LangGraph and immediately blocks the payload with an HTTP `403`.

<p align="center">
  <img src="docs/images/core-analyzer.png" alt="Sentinel AI Core Engine — Deep Prompt Analysis interface with payload input and live terminal" width="900" />
</p>

### Flagged Interaction & Current Security Features

When a suspicious prompt is submitted through the `/v1/chat/completions` API or the UI, Sentinel streams live pipeline logs, assigns a **risk score**, and returns a classification. A jailbreak attempt scoring above the Tenant's authorized policy threshold will trigger a block.

<p align="center">
  <img src="docs/images/flagged-interaction.png" alt="Sentinel AI flagged jailbreak prompt with risk score 95/100, HIGH classification, and live pipeline logs" width="900" />
</p>

### Threat Dashboard

The System Analytics panel grabs persistent logs from PostgreSQL and tracks metrics — threats neutralized, latency, provider split, and overall token consumption — updating dynamically via Recharts. The Dashboard features comprehensive management across:
- **Applications & Keys:** Generate and manage secure API keys tied directly to Postgres.
- **Policy Studio & Test Bench:** Toggle policies (`PATCH /v1/policies/{id}/toggle`) and run the Simulator against the `DocumentSanitizer` graph model.
- **Incident Queue:** Perform forensic previews of trapped anomalous API transactions and resolve them.
- **Audit & Reports:** Export complete `AuditLog` row geometries to CSV.

<p align="center">
  <img src="docs/images/threat-dashboard.png" alt="Sentinel AI System Analytics dashboard showing threats neutralized, verified safe, and threat ratio" width="900" />
</p>

---

## Core Capabilities

### Runtime AI Security
- **End-to-End Execution Lifecycle:** `HTTPBearer` intercepts -> Policy Materialization bounds checking -> LangGraph Engine Handoff -> Adapter Invocation Bridge -> Post-Execution Egress checks -> Telemetry Offloading.
- Prompt injection & Jailbreak detection algorithms.
- Input and output security analysis with PII/Credential filtering.
- Extensible Gateway Design (Open/Closed Principle) routing through abstract classes, keeping the core vendor-agnostic.

### RAG Shield Pipeline
Sentinel secures retrieval-augmented generation (RAG) systems **before** documents are ingested into vector databases:
- Extracts content from multiple document formats.
- Detects hidden prompt injections and encoded instructions.
- Removes zero-width characters and normalizes hidden formatting.

### Security Governance
- Policy-based AI request validation mapping limits directly to Postgres.
- Security rule enforcement via LangGraph middleware.
- Enterprise audit logging parsing tokens, latency, and endpoints.

### AI Observability
Sentinel provides visibility into AI runtime behavior by tracking requests, security decisions, threat detections, and policy violations. Using FastAPI BackgroundTasks, observability side-effects never block the primary proxy execution loop.

---

## Getting Started: Setup & Installation

### Requirements
- **Node.js** 18+ (frontend)
- **Python** 3.9+ (backend)
- **Git** & **Docker** (Required for PostgreSQL & Redis)

### Environment Variables

**Backend (`/backend/.env`):**
```dotenv
DATABASE_URL=postgresql://user:password@localhost:5432/sentinel
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
JWT_SECRET_KEY=generate_a_secure_random_key_here

# Provider request retries (optional, exponential backoff).  Defaults shown.
PROVIDER_RETRY_MAX_ATTEMPTS=3
PROVIDER_RETRY_INITIAL_BACKOFF=1.0
PROVIDER_RETRY_MAX_BACKOFF=30.0
```

### Frontend (`/.env`):
```
VITE_API_URL=http://localhost:8000/v1
```

### Running Locally (Mac/Linux)
1. Boot Database & Redis (Docker):
```
docker run --name sentinel-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:16
docker run --name sentinel-redis -p 6379:6379 -d redis
```
2. Backend (Live Core Engine & Gateway):
```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head         # Run DB migrations
uvicorn main:app --reload --port 8000
```
3. Frontend (Interactive UI):
```
npm install
npm run dev
```
Open `http://localhost:5173`

### Running Locally (Windows 11)
1. We have created specialized scripts to ensure safe initialization on Windows. Ensure Docker Desktop is running.
2. Open PowerShell in the project root and run Step A to boot DBs, apply Alembic migrations, and launch Uvicorn:
   ```powershell
   .\launch.ps1

3. Open a second PowerShell window and run Step B to boot the React frontend:
```
.\launch-frontend.ps1
```
(Fallback: If Docker is unavailable, install PostgreSQL 16 locally and Redis via WSL Ubuntu terminal.)


### Production Deployment Instructions

**Frontend Build:**
```bash
npm run build
npm run preview
```

The project builds into a static `dist/` directory deployable to Vercel, Netlify, GitHub Pages, or Cloudflare Pages.

**Backend Deployment:**
Ensure your production `.env` securely hosts your production `DATABASE_URL` (Postgres recommended) and `REDIS_URL`. Use Gunicorn as the process manager around Uvicorn, and deploy to AWS, Render, or Railway.

---

## Project Structure

```
src/
├── components/
│   ├── CoreAnalyzer.tsx      # Deep prompt & file analysis UI
│   ├── CombinedDashboard.tsx # Threat analytics dashboard
│   ├── DataLeakDemo.tsx      # Data leak prevention demo
│   ├── JailbreakDemo.tsx     # Jailbreak detection demo
│   ├── RiskMeter.tsx         # Risk score visualization
│   ├── DarkVeil.tsx          # OGL-powered Background visual layer
│   └── …                     # Shared UI components
├── hooks/
│   ├── useSentinelAPI.ts     # Backend API integration
│   └── useCountUp.ts
├── lib/
│   ├── detectors.ts          # Client-side pattern rules
│   ├── sampleData.ts         # Mock data separated from execution states
│   └── types.ts
├── App.tsx
├── main.tsx
└── index.css

backend/
├── main.py                   # FastAPI gateway & endpoints (Async Event Loop)
├── database/                 # SQLAlchemy schemas (models.py) and DB engines
├── providers/                # OpenAI/Anthropic SDK abstractions (Adapter Pattern)
├── alembic/                  # Database migration management
├── graph.py                  # LangGraph threat pipeline & StateGraph logic
├── policy_engine.py          # Policy Materialization & dependency injection
├── redis_client.py           # aioredis connection wrapper & rate limiting
├── extractor.py              # Document extraction
└── …

docs/
└── images/                   # README screenshots
```

---

## Security Philosophy

> **Every interaction with an LLM should pass through a dedicated security layer.**

Instead of trusting model providers to solve AI security, Sentinel independently inspects requests and responses, applies enterprise policies, detects attacks, and records every decision for governance and compliance. This makes the platform model-agnostic and portable across any AI provider.

---

## Vision

Sentinel aims to become the security infrastructure layer for enterprise AI — providing the same level of protection, governance, and visibility that platforms like CrowdStrike, Cloudflare, and Datadog provide for traditional cloud environments.

Rather than replacing existing AI models, Sentinel enables enterprises to use them securely at scale through centralized runtime protection, policy enforcement, threat intelligence, and AI observability.

---

## Roadmap

- Advanced AI threat intelligence
- AI security posture management
- AI agent runtime protection
- Cross-model risk correlation
- AI incident investigation
- Enterprise compliance reporting
- Adaptive policy engine
- Real-time AI risk scoring
- Continuous AI runtime monitoring

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, development workflow, and style guidelines.

---

## License

This project is intended as the foundation of **Sentinel AI**, an enterprise AI runtime security platform.
See [LICENSE](LICENSE) 
