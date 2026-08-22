---
company: cross-company (kit-first — primary buyers: mascir, ensias-um5-lab)
repo: mlops-research-starter
stack: [Python, scikit-learn, FastAPI, Docker, GitHub Actions, CycloneDX]
timebox: "MVP: 1 weekend — wrap one published model, reproduce + serve. Full: 4 weeks — eval suite, model card, demo video."
dataset: "one published model (MAScIR/ENSIAS-adjacent paper preferred; else a public checkpoint)"
status: demo-ready
---
# MLOps research starter: reproducible + served wrapper for research code

## Why this project exists (the thinking)

Start from the observed evidence, not from a technology: applied-AI labs chronically produce research code that only runs on the PhD student's laptop — and their own internship documents say so in writing (mission bullets for *dataset preprocessing* and *real-time implementation* are engineering pain wearing a research costume). MAScIR's need is identical (every report and patent filing requires re-running experiments), and ENSIAS labs live on reproducibility by definition — it's the currency of every thesis they supervise.

So the question wasn't "what project sounds impressive" but "what artifact proves I remove this specific, self-declared pain?" Wrapping *one published model* in DVC + MLflow + FastAPI is the smallest honest answer: it takes someone else's research output and makes it versioned, seeded, re-runnable with one command, and callable over HTTP. It demonstrates a *discipline*, applied to *their kind of artifact*.

## What you actually learn by building it

A course in what separates engineers from notebook coders: **reproducibility**. You internalize why seeds matter (run twice, get different metrics — fix it), why data and models must be versioned like code, why environments get pinned, why an experiment without lineage is a rumor. Serving via an API forces the model-to-production gap — serialization, latency, input validation. Permanent skills: you'll run your own PFE experiments inside this structure from day one, which is how a 6-month internship produces a defensible report instead of orphaned notebooks.

## Its real value beyond the CV

- **For any lab**: a drop-in template — "put your model here, get reproducibility and serving for free." Labs genuinely adopt such starters.
- **For you**: the chassis of the PFE itself, whatever topic you land.
- **Honest ceiling**: the wrapped model isn't novel research; the value is the infrastructure pattern, not the science — which is why the research tier also gets the RAG kit (usefulness) alongside this (discipline).

## Why buyers care
[[companies/mascir]] and [[companies/ensias-um5-lab]] — gap evidence in each briefing's "What they need" section. Cluster 2 of [[00-Gap-Map]]: one build covering the whole research tier. (Historically also aimed at Ai Movement — that company is now ethics-excluded; see [[companies/aim-um6p]].)

## MVP scope
- Pick one public model checkpoint from a paper (MAScIR/ENSIAS-adjacent preferred) → DVC-tracked data+model → MLflow run → FastAPI `/predict` → Docker.

## Full scope
- Eval suite (seeded, CI-run), model card, one-command `make reproduce`, 90-sec EN demo video, GitHub Actions badge.

## Demo script
1. `make reproduce` — identical metrics twice (seed control). 2. `curl /predict` on a sample. 3. MLflow UI shows run lineage. 4. Model card page. 5. "This is what I'd bring to the lab's codebase in week one."

## CV bullets
- Implemented typed `researchops` 0.1.0 protocols, immutable run manifests, deterministic fixture reproduction, hash-verified artifacts, and atomic promotion.
- Packaged the reusable orchestration layer as a wheel with a recorded SHA-256 and CycloneDX SBOM; real MVTec performance remains unpublished.
