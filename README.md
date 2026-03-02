# OLS Open Science Research System

**An open-source, AI-powered research infrastructure for sociology, psychology, environmentalism, and neuroscience.**

Built by [Optimal Living Systems](https://optimallivingsystems.org) — a mutual aid nonprofit facilitating projects that help humanity.

---

## What This Is

A research system that combines a fine-tuned AI model with domain-specific knowledge bases to perform rigorous literature reviews, methodology analysis, evidence synthesis, and research gap identification across four scientific domains.

**Architecture:** One research-methodology model (Qwen 2.5 14B, QLoRA fine-tuned) + four domain-specific RAG collections in LanceDB, orchestrated by Kestra.

**Why one model instead of four?** Our domains deeply overlap (neuroscience ↔ psychology, sociology ↔ environmentalism). A single model trained on *how to do research* paired with domain-specific retrieval produces better cross-domain synthesis, costs 75% less compute, and updates instantly when new papers are added.

## Research Domains

| Domain | Focus Areas | OLS Project Alignment |
|--------|------------|----------------------|
| **Psychology** | Self-Determination Theory, intrinsic motivation, community psychology, well-being | PersonalLLM, OVNN |
| **Sociology** | Mutual aid, community organizing, commons governance, participatory democracy | CommunityLLM, DirectDemocracyLLM |
| **Environmentalism** | Degrowth, ecological economics, planetary boundaries, environmental justice | OVNN ecological dimensions |
| **Neuroscience** | Social neuroscience, motivation circuits, stress/resilience, decision-making | HBoK biological grounding |

## System Architecture

```
┌─────────────────────────────────────────────┐
│            KESTRA ORCHESTRATOR              │
│  (Schedules, triggers, monitors, logs)      │
└──────────┬─────────────────────┬────────────┘
           │                     │
     ┌─────▼──────┐       ┌─────▼──────┐
     │  DATA LAYER │       │MODEL LAYER │
     │             │       │            │
     │  LanceDB    │◄─────►│ Qwen 2.5   │
     │  4 domain   │       │ 14B QLoRA  │
     │  collections│       │ fine-tuned │
     │  + cross-   │       │ for research│
     │  domain idx │       │ methodology│
     │             │       │            │
     │  BGE-M3     │       │ Reranker   │
     │  embeddings │       │            │
     └─────────────┘       └────────────┘
           │
     ┌─────▼───────────────────────────┐
     │         DATA SOURCES            │
     │  OpenAlex · Semantic Scholar    │
     │  PubMed/PMC · PsyArXiv         │
     │  SocArXiv · EarthArXiv         │
     └────────────────────────────────-┘
```

## What the Model Learns

The fine-tuned model is trained on **research methodology**, not domain facts. It learns 8 skills:

1. **Paper Analysis** — Extract hypothesis, methodology, sample, findings, limitations
2. **Methodology Critique** — Identify confounds, sampling issues, statistical concerns
3. **Evidence Synthesis** — Synthesize findings across multiple studies
4. **Research Gap Identification** — Find unstudied areas and missing methodologies
5. **Statistical Reasoning** — Interpret effect sizes, p-values, regression tables
6. **Structured Data Extraction** — Pull consistent structured data from papers
7. **Tool Use Decisions** — Know when to search, retrieve, calculate, or clarify
8. **Citation-Grounded Response** — Never make unsupported claims, always cite sources

Domain knowledge comes from RAG at query time — updated instantly when new papers are added.

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Orchestration | [Kestra](https://kestra.io) | YAML-first, observable, plugin ecosystem |
| Vector Database | [LanceDB](https://lancedb.com) | Embedded, open source, Apache 2.0 |
| Embeddings | [BGE-M3](https://huggingface.co/BAAI/bge-m3) | Best quality/speed balance for academic text |
| Base Model | [Qwen 2.5 14B Instruct](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct) | Native tool calling, 128K context, Apache 2.0 |
| Fine-Tuning | [Unsloth](https://github.com/unslothai/unsloth) + QLoRA | 2-5x faster, lower memory |
| Data Sources | OpenAlex, Semantic Scholar, PubMed/PMC | Free, open, comprehensive |
| GPU (training) | RunPod (rented A100) | Cost-effective on-demand |
| GPU (inference) | Modal (serverless) | Pay-per-second, scales to zero |

## Project Status

- [x] Architecture design and planning
- [ ] Kestra deployment
- [ ] Data collection pipelines
- [ ] RAG infrastructure (LanceDB + BGE-M3)
- [ ] Training data generation
- [ ] Model fine-tuning
- [ ] Agent integration
- [ ] End-to-end research workflows
- [ ] Documentation and OSF registration

## Repository Structure

```
research-system/
├── docs/                  # Architecture, guides, methodology
├── kestra-flows/          # All Kestra workflow YAML files
│   ├── collection/        # Data collection from APIs
│   ├── processing/        # Chunking, embedding, indexing
│   ├── training/          # Training data gen + fine-tuning
│   ├── research/          # Literature review, analysis flows
│   └── maintenance/       # Backups, updates, monitoring
├── schemas/               # LanceDB, training data, eval schemas
├── prompts/               # Prompt templates for training data generation
├── evaluation/            # Test sets and evaluation results
├── scripts/               # Setup and utility scripts
└── data/                  # Data storage (not in git, see data/README.md)
```

## Open Science Commitment

This project is registered with the Center for Open Science. All methodology is pre-registered, all data pipelines are reproducible, and all results are published openly.

- **Code:** AGPL-3.0 (ensures derivatives stay open)
- **Documentation:** CC-BY-SA-4.0
- **Training Data:** CC-BY-4.0
- **Model Weights:** Apache 2.0

## Related OLS Projects

- [Human Body of Knowledge (HBoK)](https://github.com/optimal-living-systems/hbok) — Personal knowledge architecture
- [OVNN](https://github.com/optimal-living-systems/ovnn) — Optimal Value Neural Network
- [CommunityLLM](https://github.com/optimal-living-systems/communityllm) — Politically neutral community organizing AI
- [DirectDemocracyLLM](https://github.com/optimal-living-systems/direct-democracy-llm) — Participatory democracy tools

## Contributing

We welcome contributions from researchers, data scientists, librarians, information architects, and anyone passionate about open science. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Contact

- **Organization:** Optimal Living Systems (501(c)(3) nonprofit)
- **Email:** research@optimallivingsystems.org
- **Mission:** Building AI infrastructure that supports human autonomy rather than capital extraction.
