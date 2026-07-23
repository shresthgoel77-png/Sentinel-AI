# Sentinel AI

**Sentinel AI** is a runtime security platform that protects enterprise AI applications by sitting between your app and any large language model (LLM). Rather than acting as a chatbot or simple prompt filter, Sentinel provides a model-agnostic layer for security, governance, observability, and policy enforcement.

<p align="center">
  <img src="docs/images/hero-dashboard.png" alt="Sentinel AI dashboard — AI Shield protecting systems from data leaks and jailbreak attacks" width="900" />
</p>

<p align="center">
  <em>The live interactive demo dashboard — scan stats, threat counters, and one-click access to security demos.</em>
</p>

It enables organizations to securely integrate with providers such as OpenAI, Anthropic, Google Gemini, Azure OpenAI, Amazon Bedrock, Vertex AI, and self-hosted models — enforcing security controls before, during, and after every AI interaction.

---

## Why Sentinel AI?

As organizations rapidly adopt generative AI, traditional application security is no longer enough. AI introduces entirely new attack vectors:

- Prompt injection and jailbreak attempts
- Sensitive data leakage (PII, credentials) in model responses
- Malicious RAG documents poisoned before ingestion
- Policy violations and multi-tenant isolation breaches

Sentinel is designed to become the **runtime security layer** for enterprise AI applications — providing continuous inspection, threat detection, governance, multi-tenant policy enforcement, and egress masking without requiring changes to the underlying model.

---
## Technology Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=ts,react,js,python,redis,postgres" />
</p>

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS, OGL (DarkVeil Shader) |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic, OpenAI SDK |
| **Infrastructure** | PostgreSQL (State/Tenants/Logs), Upstash Redis (Caching/Realtime PubSub) |
| **AI Stack** | LangChain, LangGraph, RAG Pipeline |

---

## Features & Supported Providers

The frontend ships with an interactive demo while the Backend functions as a production OpenAI-compatible API Gateway. Supported providers currently include **OpenAI (gpt, o1 models)** and **Anthropic (claude)** via dynamic routing.

| Feature | What it does (Current Capabilities) |
|---------|--------------|
| **OpenAI-Compatible Gateway** | Intercepts `/v1/chat/completions` providing drop-in security for existing apps |
| **Deep Prompt Analysis** | Inspects raw strings and uploaded documents for injection patterns in real time |
| **Egress Data Masking** | Automatically redacts API keys, credentials, and PII migrating out of the LLM |
| **Multi-Tenant Policies** | Custom Risk limits and features per organization, managed by PostgreSQL |
| **Threat Dashboard** | Persistent Audit Logs track total scans, safe requests, tokens used, and threats blocked |

### Deep Prompt Analysis & API Endpoints

The Core Engine analyzes incoming vectors. You can hit the API via real-time endpoints (e.g. `/api/analyze-prompt`, `/api/analyze-document`) or via the UI.

<p align="center">
  <img src="docs/images/core-analyzer.png" alt="Sentinel AI Core Engine — Deep Prompt Analysis interface with payload input and live terminal" width="900" />
</p>

### Flagged Interaction & Current Security Features

When a suspicious prompt is submitted through the `/v1/chat/completions` API or the UI, Sentinel streams live pipeline logs, assigns a **risk score**, and returns a classification. A jailbreak attempt scoring above the Tenant's authorized policy threshold will trigger a `403/Block`.

<p align="center">
  <img src="docs/images/flagged-interaction.png" alt="Sentinel AI flagged jailbreak prompt with risk score 95/100, HIGH classification, and live pipeline logs" width="900" />
</p>

### Threat Dashboard

The System Analytics panel grabs persistent logs from PostgreSQL and tracks metrics — threats neutralized, latency, provider split, and overall token consumption — updating dynamically.

<p align="center">
  <img src="docs/images/threat-dashboard.png" alt="Sentinel AI System Analytics dashboard showing threats neutralized, verified safe, and threat ratio" width="900" />
</p>

---

## Core Capabilities

### Runtime AI Security

- Prompt injection & Jailbreak detection algorithms
- Input and output security analysis with PII/Credential filtering
- Runtime threat detection engine routing Anthropic/OpenAI
- Persistent Multi-Tenant Policy enforcement engine

### RAG Shield Pipeline

Sentinel secures retrieval-augmented generation (RAG) systems **before** documents are ingested into vector databases:

- Extracts content from multiple document formats
- Detects hidden prompt injections and encoded instructions
- Removes zero-width characters and normalizes hidden formatting

This prevents poisoned knowledge bases before retrieval ever occurs.

### Security Governance

- Policy-based AI request validation mapping limits directly to SQLite/Postgres
- Security rule enforcement via LangGraph middleware
- Enterprise audit logging parsing tokens, latency, and endpoints
- Threat visibility and runtime decision tracking

### AI Observability

Sentinel provides visibility into AI runtime behavior by tracking requests, security decisions, threat detections, policy violations, and runtime events — completely decoupled from the provider.

---

## Getting Started: Setup & Installation

### Requirements

- **Node.js** 18+ (frontend)
- **Python** 3.9+ (backend)
- **Git** & **Docker** (optional, for Postgres)

### Environment Variables & Database/Redis Setup

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Fill out your `OPENAI_API_KEY` and `REDIS_URL`. Start your local PostgreSQL instance (or use the configured default SQLite fallback via `database.py`).
3. (Optional) Run `docker-compose up -d` to spin up a local PostgreSQL container.

### Running the Frontend & Backend

**Frontend (interactive UI):**
```bash
npm install
npm run dev
```
Open `http://localhost:5173`.

Open the URL displayed by Vite (typically `http://localhost:5173`).

### Backend (live Core Engine)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
set GOOGLE_API_KEY=your-key  # Windows
uvicorn main:app --reload
```

The React app connects to the backend at `http://127.0.0.1:8000`.

### Production build
=======
**Backend (live Core Engine & Gateway):**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
alembic upgrade head         # Run DB migrations
uvicorn main:app --reload
```
The React app connects to the backend at `http://127.0.0.1:8000`.

### Production Deployment Instructions

**Frontend Build:**
```bash
npm run build
npm run preview
```
The project builds into a static `dist/` directory deployable to Vercel, Netlify, or GH Pages.

The project builds into a static `dist/` directory deployable to Vercel, Netlify, GitHub Pages, or Cloudflare Pages.
=======
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
=======
│   ├── DarkVeil.tsx          # OGL-powered Background visual layer
│   ├── CombinedDashboard.tsx # Threat analytics dashboard
│   └── …                     # Shared UI components
├── hooks/
│   ├── useSentinelAPI.ts     # Backend API integration
│   └── useCountUp.ts
├── lib/
│   ├── detectors.ts          # Client-side pattern rules
│   ├── sampleData.ts
│   └── types.ts
├── App.tsx
├── main.tsx
└── index.css

backend/
├── main.py                   # FastAPI gateway
├── graph.py                  # LangGraph threat pipeline
=======
├── main.py                   # FastAPI gateway & endpoints
├── database/                 # SQLAlchemy schemas (models) and sqlite engine
├── providers/                # OpenAI/Anthropic SDK abstractions
├── alembic/                  # Database migration management
├── graph.py                  # LangGraph threat pipeline
├── redis_client.py           # Upstash Realtime connection wrapper
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
- AI security analytics
- Real-time AI risk scoring
- Continuous AI runtime monitoring

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, development workflow, and style guidelines.

---

## License

This project is intended as the foundation of **Sentinel AI**, an enterprise AI runtime security platform.
