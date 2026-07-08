# Contributing to Sentinel AI

First off, thank you for considering contributing to Sentinel AI! It's people like you that make building secure, enterprise-grade AI applications possible. 


Sentinel AI is an interactive AI runtime security platform, and we welcome contributions across the board—whether it's adding new threat detection rules, improving our LangGraph RAG pipeline, fixing UI bugs, or writing documentation.

## Table of Contents

* [Code of Conduct](#code-of-conduct)
* [Getting Started](#getting-started)
* [How to Contribute](#how-to-contribute)
    * [Reporting Bugs](#reporting-bugs)
    * [Suggesting Enhancements](#suggesting-enhancements)
    * [Pull Requests](#pull-requests)
* [Development Workflow](#development-workflow)
* [Styleguides](#styleguides)

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to **[Insert Your Contact Email Here]**.

## Getting Started

Sentinel AI consists of a React/TypeScript frontend (Vite) and a Python/FastAPI backend. 

### Prerequisites

* **Node.js**: v18 or higher (for the frontend)
* **Python**: 3.9 or higher (for the backend and AI agents)
* **Git**

### Local Setup

1.  **Fork and clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Sentinel-AI.git](https://github.com/YOUR_USERNAME/Sentinel-AI.git)
    cd Sentinel-AI
    ```

2.  **Set up the Frontend:**
    ```bash
    npm install
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173`.

3.  **Set up the Backend (FastAPI):**
    Navigate to the `backend` directory (adjust path if necessary) and set up your virtual environment:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the [Issue Tracker](https://github.com/shresthgoel77-png/Sentinel-AI/issues) to see if the problem has already been reported. If not, open a new issue and include:
* A clear and descriptive title.
* Exact steps to reproduce the problem.
* Expected behavior vs. actual behavior.
* Your environment (OS, Node version, Python version, Browser).

### Suggesting Enhancements

We are always looking to expand our threat detection engine and policy enforcement capabilities. If you have an idea:
* Open an issue tagged as `enhancement`.
* Explain the use case (e.g., a new type of prompt injection or a UI feature for the Risk Meter).
* Provide examples of how it should work or look.

### Pull Requests

1.  **Create a new branch** for your feature or bugfix:
    ```bash
    git checkout -b feature/your-feature-name
    ```
    *(Use `bugfix/`, `feature/`, or `docs/` prefixes).*
2.  **Make your changes**, ensuring you follow our styleguides.
3.  **Test your changes** locally. Ensure both the frontend dashboard and backend pipelines are functioning correctly.
4.  **Commit your changes** using clear, descriptive commit messages.
5.  **Push to your fork** and submit a Pull Request to the `main` branch of the Sentinel AI repository.
6.  **Link the PR** to any relevant open issues.

## Development Workflow

* **Security First:** Since this is a security platform, ensure your contributions do not introduce new vulnerabilities. Never commit hardcoded secrets or API keys.
* **Keep it Modular:** When adding new UI components, place them in the appropriate `src/components/` subfolder (e.g., `Dashboard`, `Threat Analysis`).
* **Update Documentation:** If you are adding a new detector to `lib/detectors.ts` or modifying the RAG Shield Pipeline, please update the `README.md` and inline documentation accordingly.

## Styleguides

### Commit Messages
* Use the present tense ("Add feature" not "Added feature").
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
* Reference issues and pull requests liberally.

### TypeScript / React (Frontend)
* We use standard modern React practices (Functional components, Hooks).
* Use Tailwind CSS for styling. Avoid writing custom CSS in `index.css` unless absolutely necessary.
* Ensure proper type definitions for any new data structures in `lib/types.ts`.

### Python (Backend / AI Stack)
* Follow PEP 8 guidelines.
* Use type hints wherever possible.
* When interacting with LangChain or LangGraph, ensure your chains are properly isolated and testable.

Thank you for helping us secure enterprise AI!
