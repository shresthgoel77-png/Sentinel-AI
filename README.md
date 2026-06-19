# AI Shield

An interactive hackathon demo of two AI safety concepts — **data leakage prevention** and
**jailbreak detection** — built with **React + TypeScript + Vite + Tailwind CSS**.

Everything runs client-side. Detection is rule-based pattern matching (regex) over a small
simulated "AI response" generator — there's no backend and no real model call, by design,
so judges can interact with it instantly and understand exactly how the detection works.

## What's inside

- **Hero** — problem statement + two demo entry points.
- **Data Leak Prevention demo** — type a prompt, see a simulated raw AI response scanned for
  API keys, passwords, tokens, and confidential phrases, with a redacted "what the user
  actually sees" view.
- **Jailbreak Detection demo** — type a prompt, see it scanned for instruction-override and
  manipulation patterns, with matches highlighted inline.
- **Live status bar + combined dashboard** — every demo run updates shared stats (blocked /
  detected / safe) with animated counters, like a small SOC console.
- **Attack simulation** — a fixed side-by-side "without AI Shield" vs "with AI Shield" comparison.
- **Architecture diagram** — hoverable nodes showing how the two detectors sit in front of the model.
- **Why This Matters** — a short section aimed at judges.

## Getting started

Requires [Node.js](https://nodejs.org/) 18+.

```bash
npm install
npm run dev
```

Then open the URL Vite prints (usually `http://localhost:5173`).

## Building for production

```bash
npm run build
npm run preview
```

`npm run build` outputs a static `dist/` folder you can deploy anywhere (Vercel, Netlify,
GitHub Pages, etc.) — it's plain static HTML/CSS/JS, no server required.

## Project structure

```
src/
  components/        UI sections (Hero, demos, dashboard, architecture, etc.)
  lib/
    detectors.ts      Rule-based scanning engine (the "AI Shield" logic)
    sampleData.ts      Sample prompts shown as quick-try buttons
    types.ts           Shared TypeScript types
  hooks/
    useCountUp.ts      Animated counter hook for the dashboard
  App.tsx              Top-level layout + shared stats state
  main.tsx             React entry point
  index.css            Tailwind + global styles
```

## Customizing the detection rules

All pattern matching lives in `src/lib/detectors.ts`:

- `DATA_LEAK_RULES` — regex patterns for the data leak scanner (API keys, passwords, tokens, etc).
- `JAILBREAK_RULES` — regex patterns for the jailbreak scanner (instruction overrides, role
  manipulation, etc).
- `simulateRawAIResponse()` — the canned "what would an unprotected model say" generator used by
  the data leak demo. All secrets it returns are obviously fake placeholder values.

Add or tweak entries in either rules array to extend what the demo can catch.
