# Sentinel AI

**Sentinel AI** is a Runtime Security Platform that protects enterprise AI applications by sitting between applications and any Large Language Model (LLM). Rather than acting as a chatbot or prompt filter, Sentinel provides a model-agnostic security, governance, observability, and policy enforcement layer for AI systems.

It enables organizations to securely integrate with providers such as OpenAI, Anthropic, Google Gemini, Azure OpenAI, Amazon Bedrock, Vertex AI, and self-hosted models while enforcing security controls before, during, and after every AI interaction.

---

## Why Sentinel AI?

As organizations rapidly adopt Generative AI, traditional application security is no longer enough. AI introduces entirely new attack vectors including prompt injection, jailbreak attempts, sensitive data leakage, malicious RAG documents, policy violations, and model manipulation.

Sentinel is designed to become the runtime security layer for enterprise AI applications, providing continuous inspection, threat detection, governance, and enforcement without requiring changes to the underlying model.

---

# Core Capabilities

### Runtime AI Security

- Prompt Injection Detection
- Jailbreak Detection
- Input Security Analysis
- Output Security Analysis
- Runtime Threat Detection Engine
- Policy Enforcement Engine
- AI Runtime Middleware
- Session-aware Security Analysis

---

### RAG Shield Pipeline

Sentinel secures Retrieval-Augmented Generation (RAG) systems before documents are ingested into vector databases.

The pipeline:

- Extracts content from multiple document formats
- Detects hidden prompt injections
- Removes zero-width characters
- Detects Unicode homoglyph attacks
- Normalizes hidden formatting
- Detects encoded instructions
- Separates legitimate knowledge from embedded AI instructions
- Sanitizes malicious content
- Quarantines dangerous documents before chunking or vectorization

This prevents poisoned knowledge bases before retrieval ever occurs.

---

### Security Governance

- Policy-based AI request validation
- Security rule enforcement
- Enterprise audit logging
- Runtime decision tracking
- Threat visibility
- Multi-tenant architecture

---

### AI Observability

Sentinel provides visibility into AI runtime behavior by tracking:

- AI requests
- Security decisions
- Threat detections
- Policy violations
- Runtime events
- Security metrics

The goal is to provide observability for AI systems similar to how Datadog provides observability for cloud infrastructure.

---

## Current Features

- Prompt Injection Detection
- Jailbreak Detection
- Runtime AI Security Middleware
- Input & Output Inspection
- Threat Detection Engine
- Policy Enforcement
- Audit Logging
- Multi-tenant SaaS Foundation
- Session-aware Security Concepts
- RAG Shield Pipeline

---

# Technology Stack

- React
- TypeScript
- Vite
- Tailwind CSS

---

# Getting Started

## Requirements

- Node.js 18+

Install dependencies

```bash
npm install
```

Start the development server

```bash
npm run dev
```

Open the URL displayed by Vite (typically `http://localhost:5173`).

---

# Production Build

```bash
npm run build
npm run preview
```

The project builds into a static `dist/` directory which can be deployed to platforms such as:

- Vercel
- Netlify
- GitHub Pages
- Cloudflare Pages

---

# Project Structure

```
src/
│
├── components/
│   ├── Dashboard
│   ├── Prompt Injection Demo
│   ├── Jailbreak Detection
│   ├── Runtime Security
│   ├── Risk Meter
│   ├── Threat Analysis
│   └── Shared UI Components
│
├── hooks/
│   ├── useCountUp.ts
│   └── useSentinelAPI.ts
│
├── lib/
│   ├── detectors.ts
│   ├── sampleData.ts
│   └── types.ts
│
├── App.tsx
├── main.tsx
└── index.css
```

---

# Security Philosophy

Sentinel is designed around a simple principle:

**Every interaction with an LLM should pass through a dedicated security layer.**

Instead of trusting model providers to solve AI security, Sentinel independently inspects requests and responses, applies enterprise policies, detects attacks, and records every decision for governance and compliance.

This makes the platform model-agnostic and portable across any AI provider.

---

# Vision

Sentinel aims to become the security infrastructure layer for enterprise AI, providing organizations with the same level of protection, governance, and visibility that platforms like CrowdStrike, Cloudflare, and Datadog provide for traditional cloud environments.

Rather than replacing existing AI models, Sentinel enables enterprises to use them securely at scale through centralized runtime protection, policy enforcement, threat intelligence, and AI observability.

---

# Roadmap

Future capabilities include:

- Advanced AI Threat Intelligence
- AI Security Posture Management
- AI Agent Runtime Protection
- Cross-Model Risk Correlation
- AI Incident Investigation
- Enterprise Compliance Reporting
- Adaptive Policy Engine
- Real-time AI Risk Scoring
- AI Security Analytics
- Continuous AI Runtime Monitoring

---

# License

This project is intended as the foundation of **Sentinel AI**, an enterprise AI Runtime Security Platform.
