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
- Sensitive data leakage in model responses
- Malicious RAG documents poisoned before ingestion
- Policy violations and model manipulation

Sentinel is designed to become the **runtime security layer** for enterprise AI applications — providing continuous inspection, threat detection, governance, and enforcement without requiring changes to the underlying model.

---
## Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=ts,react,js,python,redis" />
</p>

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS |
| **Backend** | Python, FastAPI, Redis |
| **AI Stack** | LangChain, LangGraph, RAG Pipeline |

---

## Features

The frontend ships with an interactive demo that makes these capabilities tangible for contributors and users.

| Feature | What it does |
|---------|--------------|
| **Deep Prompt Analysis** | Inspects raw strings and uploaded documents for injection patterns in real time |
| **Data Leak Prevention** | Scans model output for API keys, credentials, PII, and confidential markers |
| **Jailbreak Detection** | Screens incoming prompts for known manipulation and override patterns |
| **Threat Dashboard** | Tracks total scans, safe requests, and threats blocked across the session |
| **RAG Shield Pipeline** | Sanitizes documents before they enter a vector database |

### Deep Prompt Analysis

The Core Engine is the heart of the live demo. Paste a payload or upload a file, then watch the pipeline terminal stream analysis stages as Sentinel classifies risk.

<p align="center">
  <img src="docs/images/core-analyzer.png" alt="Sentinel AI Core Engine — Deep Prompt Analysis interface with payload input and live terminal" width="900" />
</p>

### Flagged Interaction

When a suspicious prompt is submitted, Sentinel streams live pipeline logs to the terminal, assigns a **risk score**, and returns a classification with execution details. In this example, a jailbreak attempt scores **95/100** and is blocked.

<p align="center">
  <img src="docs/images/flagged-interaction.png" alt="Sentinel AI flagged jailbreak prompt with risk score 95/100, HIGH classification, and live pipeline logs" width="900" />
</p>

### Threat Dashboard

The System Analytics panel tracks session-level metrics — threats neutralized, verified safe requests, and overall threat ratio — updating in real time as scans complete.

<p align="center">
  <img src="docs/images/threat-dashboard.png" alt="Sentinel AI System Analytics dashboard showing threats neutralized, verified safe, and threat ratio" width="900" />
</p>

---

## Core Capabilities

### Runtime AI Security

- Prompt injection detection
- Jailbreak detection
- Input and output security analysis
- Runtime threat detection engine
- Policy enforcement engine
- AI runtime middleware
- Session-aware security analysis

### RAG Shield Pipeline

Sentinel secures retrieval-augmented generation (RAG) systems **before** documents are ingested into vector databases:

- Extracts content from multiple document formats
- Detects hidden prompt injections and encoded instructions
- Removes zero-width characters and Unicode homoglyph attacks
- Normalizes hidden formatting
- Separates legitimate knowledge from embedded AI instructions
- Sanitizes malicious content and quarantines dangerous documents

This prevents poisoned knowledge bases before retrieval ever occurs.

### Security Governance

- Policy-based AI request validation
- Security rule enforcement
- Enterprise audit logging
- Runtime decision tracking
- Threat visibility
- Multi-tenant architecture

### AI Observability

Sentinel provides visibility into AI runtime behavior by tracking requests, security decisions, threat detections, policy violations, and runtime events — similar to how Datadog provides observability for cloud infrastructure.

---

## Getting Started

### Requirements

- **Node.js** 18+ (frontend)
- **Python** 3.9+ (backend, optional for live analysis)
- **Git**

### Frontend (interactive demo)

```bash
npm install
npm run dev
```

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

```bash
npm run build
npm run preview
```

The project builds into a static `dist/` directory deployable to Vercel, Netlify, GitHub Pages, or Cloudflare Pages.

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
- Continuous AI runtime monitoring

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup, development workflow, and style guidelines.

---

## License

This project is intended as the foundation of **Sentinel AI**, an enterprise AI runtime security platform.
