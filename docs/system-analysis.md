# OLS Open Science Research Lab — AI Research System Architecture Analysis

**Date:** March 1, 2026
**Prepared for:** Executive Director, Optimal Living Systems
**Domains:** Sociology, Psychology, Environmentalism, Neuroscience

---

## EXECUTIVE SUMMARY

You're proposing to build a multi-model AI research system composed of fine-tuned 14B reasoning models, RAG pipelines, and autonomous agents — orchestrated through Kestra and built using coding agents (Codex, Claude Code, Qwen 3 Coder). This analysis rates every critical decision point 1-10 and provides concrete recommendations.

**Core architecture recommendation:** Don't fine-tune 4 separate domain models. Fine-tune ONE research-methodology model + build 4 domain-specific RAG knowledge bases. This saves 75% of your fine-tuning compute while delivering better results because your domains (psychology ↔ neuroscience, sociology ↔ environmentalism) deeply overlap.

---

## 1. BASE MODEL SELECTION (Rating: 9/10 importance)

The 14B parameter class is the sweet spot — large enough for serious reasoning, small enough to fine-tune on a single GPU and run inference affordably. Here are your real options as of early 2026:

### Top Picks

| Model | Reasoning | Tool Use | Fine-Tune Ecosystem | Open Science Fit | Overall |
|-------|-----------|----------|---------------------|------------------|---------|
| **Qwen 2.5 14B Instruct** | 9/10 | 9/10 | 9/10 | 8/10 | **9/10** ★ |
| **Qwen 3 14B** | 9/10 | 9/10 | 8/10 | 8/10 | **8.5/10** |
| **DeepSeek-R1-Distill-Qwen-14B** | 10/10 | 5/10 | 7/10 | 9/10 | **7.5/10** |
| **Mistral Nemo 12B** | 7/10 | 8/10 | 8/10 | 7/10 | **7/10** |
| **Phi-4 14B** | 8/10 | 6/10 | 6/10 | 6/10 | **6.5/10** |

### My Recommendation: Qwen 2.5 14B as primary

**Why Qwen 2.5 14B wins:**
- Native tool/function calling built into the architecture (critical for agents)
- Thinking/reasoning mode available
- Massive fine-tuning community — Unsloth, Axolotl, LLaMA-Factory all have first-class support
- Apache 2.0 license — perfect for Open Science
- 128K context window — essential for research papers (most are 15-40 pages)
- Strong structured output (JSON, citations, data extraction)

**Why NOT DeepSeek-R1-Distill despite better raw reasoning:**
- Tool calling is bolted on, not native — fine-tuning for tool use is fragile
- The "thinking" tokens eat into your context window
- Less community support for fine-tuning modifications
- You need tool use MORE than you need raw reasoning for a research system

**Why Qwen 3 14B is close second:**
- Newer, potentially better, but the fine-tuning ecosystem is still maturing
- If you start building in April/May 2026, Qwen 3 ecosystem may be mature enough
- Monitor this — could become the pick by the time you're ready to train

### Rating: 9/10 — Model selection is the single most impactful decision. Get this right and everything downstream works better.

---

## 2. FINE-TUNING STRATEGY (Rating: 10/10 importance)

This is where I have the strongest opinion. Your notes mention fine-tuning separate models for "industry" and "economics" and presumably each research domain. **I strongly recommend against this.**

### The Two Approaches

**Approach A: Multiple Domain-Specific Fine-Tunes (What you described)**
- Fine-tune Model-Sociology, Model-Psychology, Model-Environment, Model-Neuroscience
- Each model is an expert in one domain
- Rating: 4/10

**Approach B: Single Research-Methodology Fine-Tune + Domain RAG (What I recommend)**
- Fine-tune ONE model to be exceptional at *research methodology*
- Teach it: how to read papers, extract findings, evaluate methodology, synthesize across studies, identify gaps, handle statistical reasoning, understand experimental design
- Then give it domain knowledge via RAG at inference time
- Rating: 9/10

### Why Approach B is Superior

1. **Your domains overlap massively.** Neuroscience papers cite psychology constantly. Environmental sociology IS sociology + environmentalism. A neuroscience paper on stress responses is also a psychology paper. Separate models can't cross-reference.

2. **Research methodology is domain-agnostic.** A well-designed RCT follows the same principles whether it's studying CBT outcomes (psychology) or pesticide exposure (environment). Teaching the model to BE a researcher is more valuable than teaching it domain facts.

3. **Domain knowledge changes constantly.** New papers every day. Fine-tuned knowledge is frozen at training time. RAG knowledge updates instantly when you add new papers to your vector database.

4. **Cost and maintenance.** Fine-tuning once costs ~$50-200 on rented GPUs. Fine-tuning four models is 4x that, plus you maintain four separate model versions, four evaluation pipelines, four deployment configs.

5. **Kestra orchestration is cleaner.** One model endpoint, four RAG collections. Much simpler workflow YAML than routing to four different model endpoints.

### What the Fine-Tune Should Teach

Your training dataset should contain examples that teach the model:

- **Paper analysis:** Given a paper, extract hypothesis, methodology, sample size, findings, limitations, p-values, effect sizes
- **Methodology critique:** Identify confounds, sampling bias, statistical errors, reproducibility issues
- **Evidence synthesis:** Given multiple papers on a topic, synthesize findings, identify consensus vs. disagreement
- **Research gap identification:** Given a body of literature, identify what hasn't been studied
- **Statistical reasoning:** Interpret regression tables, meta-analysis forest plots, Bayesian posteriors
- **Citation handling:** Proper APA/academic citation generation and fact-grounding
- **Structured output:** Consistent JSON/structured responses for downstream processing
- **Tool use patterns:** When to search, when to retrieve, when to calculate, when to visualize

### Rating: 10/10 — This decision determines whether you build something that works or something that's expensive and fragile.

---

## 3. DATASET CONSTRUCTION (Rating: 9/10 importance)

### Sources for Training Data

| Source | Quality | Access | Volume | Legal/Ethical | Rating |
|--------|---------|--------|--------|---------------|--------|
| **Semantic Scholar API** | 9/10 | Free API | Millions of abstracts | Open | **9/10** ★ |
| **OpenAlex** | 8/10 | Fully open | 250M+ works | CC0 | **9/10** ★ |
| **PubMed/PMC Open Access** | 10/10 | Free | 8M+ full texts | Open | **9/10** ★ |
| **CORE** | 7/10 | Free API | 300M+ metadata | Open | **8/10** |
| **arXiv** | 8/10 | Free bulk | Millions | Open | **7/10** (less relevant for your fields) |
| **Unpaywall** | 7/10 | Free API | OA link resolver | Open | **8/10** |
| **PsyArXiv/SocArXiv** | 9/10 | Free | Thousands of preprints | Open | **8/10** |
| **Sci-Hub** | 10/10 | Legal gray area | Everything | ⚠️ AVOID | **2/10** (legal risk for Open Science org) |

### Dataset Construction Pipeline (Kestra-Orchestrated)

**Phase 1 — Raw Collection (Weeks 1-3)**
- Pull abstracts + metadata from OpenAlex and Semantic Scholar for your four domains
- Pull full-text PDFs from PMC Open Access Subset
- Pull preprints from PsyArXiv, SocArXiv, EarthArXiv
- Store everything in structured format (JSON lines)
- Kestra handles scheduling, retries, rate limiting

**Phase 2 — Processing & Cleaning (Weeks 3-5)**
- Extract text from PDFs (use `marker` or `nougat` for academic PDFs — much better than basic extractors)
- Chunk papers into sections (Abstract, Methods, Results, Discussion)
- Generate metadata: domain tags, methodology type, sample size, year, citation count
- Quality filter: remove retracted papers, predatory journal papers, papers below citation threshold

**Phase 3 — Training Example Generation (Weeks 5-8)**
- This is the critical step. You need to generate instruction-following examples.
- Use Claude API (or similar) to generate high-quality Q&A pairs FROM your collected papers
- Example formats:
  - "Analyze this methodology section and identify potential confounds" → [model answer]
  - "Given these three abstracts on [topic], synthesize the key findings" → [model answer]
  - "Extract all statistical findings from this results section in structured JSON" → [model answer]
  - "What research gaps exist based on this literature review?" → [model answer]
- Target: 10,000-35,000 high-quality examples (aligns with your CommunityLLM target of 35K)
- Human verification gate: You review a sample of generated examples for quality

**Phase 4 — Augmentation (Weeks 8-10)**
- Generate adversarial examples (papers with methodological flaws for the model to catch)
- Create multi-paper synthesis examples
- Add tool-use examples (model deciding to search, retrieve, or calculate)
- Create structured output examples (consistent JSON schemas)

### Rating: 9/10 — Dataset quality determines fine-tune quality. "Garbage in, garbage out" is the iron law.

---

## 4. RAG ARCHITECTURE (Rating: 8/10 importance)

### Vector Database Selection

| Database | Self-Hosted | Cost | Performance | Kestra Integration | Rating |
|----------|-------------|------|-------------|-------------------|--------|
| **LanceDB** | Yes | Free/OSS | Excellent | File-based, easy | **9/10** ★ |
| **Qdrant** | Yes | Free/OSS | Excellent | REST API | **8/10** |
| **ChromaDB** | Yes | Free/OSS | Good | Python native | **7/10** |
| **Weaviate** | Yes | Free/OSS | Excellent | REST API | **7/10** |
| **Pinecone** | No (cloud) | Paid | Excellent | REST API | **5/10** (vendor lock-in) |

### My Recommendation: LanceDB

You're already planning to use LanceDB for OVNN. Keep the stack unified. LanceDB advantages for your case:
- Runs embedded (no separate server to manage)
- Stores on disk in Lance columnar format — handles millions of vectors
- Supports hybrid search (vector + keyword) out of the box
- Native Python, easy Kestra integration via Python tasks
- Multi-modal: can store and index images, tables from papers alongside text
- Zero cost, Apache 2.0 license

### RAG Pipeline Design

```
[User Query]
    ↓
[Query Analyzer] — Fine-tuned model determines:
    - Which domain collection(s) to search
    - What type of search (semantic, keyword, hybrid)
    - Whether to decompose into sub-queries
    ↓
[Retriever] — LanceDB hybrid search across domain collections:
    - sociology_papers (embeddings + metadata)
    - psychology_papers
    - environment_papers
    - neuroscience_papers
    - cross_domain_index (shared concepts)
    ↓
[Re-Ranker] — Cross-encoder reranking of top-K results
    - Use a small cross-encoder model (e.g., bge-reranker)
    - Filters by recency, citation count, methodology quality
    ↓
[Context Assembly] — Formats retrieved chunks with citations
    ↓
[Fine-Tuned 14B Model] — Generates research-grounded response
    ↓
[Citation Validator] — Verifies claims are actually supported by retrieved sources
```

### Embedding Model Selection

| Model | Dimensions | Quality | Speed | Rating |
|-------|-----------|---------|-------|--------|
| **BGE-M3** | 1024 | 9/10 | Fast | **9/10** ★ |
| **E5-Mistral-7B** | 4096 | 10/10 | Slow | **7/10** (overkill) |
| **Nomic-Embed-v2** | 768 | 8/10 | Fast | **8/10** |
| **all-MiniLM-L6-v2** | 384 | 6/10 | Very fast | **5/10** (too low quality for research) |

**Recommendation: BGE-M3.** Best balance of quality and speed for academic text. Handles long passages well. Open source.

### Chunking Strategy for Academic Papers

This matters more than people think. Bad chunking = bad retrieval = bad answers.

- **DO NOT** chunk by fixed token count (destroys context)
- **DO** chunk by paper section (Abstract, Introduction, Methods, Results, Discussion, each as one chunk)
- **DO** keep metadata attached to each chunk: paper title, authors, year, journal, DOI, section name
- **DO** create a "paper summary" chunk that combines abstract + key findings for high-level queries
- **DO** create cross-reference chunks linking papers that cite each other
- Optimal chunk size: 512-1024 tokens per section chunk, with 128-token overlap

### Rating: 8/10 — RAG is what makes domain knowledge dynamic and current. It's the difference between a static model and a living research system.

---

## 5. AGENT SYSTEM DESIGN (Rating: 8/10 importance)

### Agent Framework Selection

| Framework | No-Code Friendly | Tool Ecosystem | Kestra Integration | Maturity | Rating |
|-----------|-----------------|----------------|-------------------|----------|--------|
| **LangGraph** | 4/10 | 9/10 | Good (Python tasks) | 8/10 | **7/10** |
| **CrewAI** | 7/10 | 7/10 | Good (Python tasks) | 7/10 | **7/10** |
| **Haystack** | 6/10 | 8/10 | Good (Python tasks) | 9/10 | **8/10** ★ |
| **DSPy** | 3/10 | 6/10 | Moderate | 7/10 | **5/10** |
| **Custom (Kestra-native)** | 9/10 | Varies | Perfect | N/A | **7/10** |

### My Recommendation: Haystack + Kestra Hybrid

Here's the key insight: **Kestra IS an agent orchestrator.** Its flow-based execution, conditional branching, retry logic, and plugin ecosystem mean you can build research agents directly in Kestra YAML without learning a Python agent framework.

**Use Kestra for macro-orchestration:**
- "Run a literature review on Topic X" → Kestra flow that calls search → retrieve → analyze → synthesize
- Scheduling, monitoring, error handling, logging all built in
- You can build this in YAML, not code

**Use Haystack for micro-pipelines within Kestra tasks:**
- Document processing pipeline (PDF → chunks → embeddings → LanceDB)
- RAG query pipeline (query → retrieve → rerank → generate)
- Haystack has the best academic/research document processing of any framework
- Each Haystack pipeline is called as a Python task within a Kestra flow

### Agent Roles for Research System

1. **Search Agent** — Given a research question, formulates search queries, calls Semantic Scholar/OpenAlex APIs, filters results by relevance, recency, citation count
2. **Retrieval Agent** — Searches your local LanceDB collections, performs hybrid search, reranks results
3. **Analysis Agent** — Your fine-tuned 14B model analyzing retrieved papers for methodology, findings, gaps
4. **Synthesis Agent** — Combines analyses from multiple papers into coherent literature reviews
5. **Fact-Check Agent** — Cross-references claims against source material, flags unsupported statements
6. **Data Extraction Agent** — Pulls structured data from papers (sample sizes, effect sizes, p-values) into databases

### Rating: 8/10 — The agent layer is what turns a model + data into a usable research system. But start simple — you can always add agents later.

---

## 6. KESTRA ORCHESTRATION (Rating: 10/10 importance)

This is your superpower. Kestra is genuinely underutilized in the AI/ML space and you're right that it's a game-changer. Here's how to maximize it:

### Kestra Flow Architecture

```
LEVEL 1: Data Collection Flows (automated, scheduled)
├── flow: collect-openalex         (weekly, pulls new papers)
├── flow: collect-semantic-scholar (weekly, pulls new papers)
├── flow: collect-pubmed-oa        (weekly, pulls new OA papers)
├── flow: collect-preprints        (daily, PsyArXiv/SocArXiv/EarthArXiv)
└── flow: collect-rss-feeds        (daily, journal RSS feeds)

LEVEL 2: Processing Flows (triggered by collection)
├── flow: process-pdfs             (extract text, chunk, embed)
├── flow: quality-filter           (remove low-quality, retracted)
├── flow: metadata-enrichment      (add citation counts, domain tags)
└── flow: index-to-lancedb        (upsert embeddings to vector DB)

LEVEL 3: Fine-Tuning Flows (manual trigger)
├── flow: generate-training-data   (create instruction examples from papers)
├── flow: validate-training-data   (human-in-the-loop quality check)
├── flow: run-fine-tune            (execute QLoRA training on GPU server)
└── flow: evaluate-model           (benchmark against test set)

LEVEL 4: Research Flows (on-demand or scheduled)
├── flow: literature-review        (full pipeline: search → retrieve → analyze → synthesize)
├── flow: methodology-audit        (analyze a paper's methodology)
├── flow: trend-analysis           (track research trends over time in a domain)
├── flow: gap-analysis             (identify unstudied areas in a topic)
└── flow: data-extraction          (pull structured data from paper set)

LEVEL 5: Maintenance Flows (scheduled)
├── flow: update-embeddings        (re-embed with newer model if upgraded)
├── flow: prune-database           (remove outdated/retracted papers)
├── flow: backup-lancedb           (backup vector database)
└── flow: monitor-model-drift      (track model performance over time)
```

### Why Kestra is Perfect for This

1. **YAML-first** — You write flows in YAML, not Python. This matches your no-code constraint.
2. **Plugin ecosystem** — Python script tasks, HTTP requests, file handling, scheduling all built in.
3. **Observability** — Every flow execution is logged, timed, and debuggable in the UI.
4. **Error handling** — Built-in retry, timeout, error notification. Critical for long-running GPU jobs.
5. **Triggers** — Schedule flows, trigger on file upload, trigger on webhook, chain flows together.
6. **Secrets management** — API keys for Semantic Scholar, GPU providers stored securely.
7. **Namespace organization** — Organize flows by domain (sociology, psychology, etc.)
8. **Scalability** — Can distribute across workers as your system grows.

### Kestra + GPU Servers

Kestra can trigger fine-tuning jobs on remote GPU servers via:
- SSH tasks (run training scripts on rented GPU boxes)
- HTTP tasks (call GPU provider APIs like RunPod, Lambda, Vast.ai)
- Python tasks that use paramiko/fabric to remote-execute

The flow handles: spin up GPU → upload data → run training → download model → spin down GPU → notify you.

### Rating: 10/10 — Kestra is not just helpful, it's the backbone. Every other component connects through it. Invest heavily in learning Kestra flow patterns.

---

## 7. GPU INFRASTRUCTURE (Rating: 7/10 importance)

### What You Need

**For Fine-Tuning (QLoRA on 14B model):**
- Minimum: 1x A100 40GB (~$1.50/hr on Vast.ai)
- Recommended: 1x A100 80GB (~$2.00/hr) or 1x H100 80GB (~$3.00/hr)
- Training time: 10-20 hours for 35K examples with QLoRA
- Estimated cost per fine-tune run: $30-60

**For Inference (serving the fine-tuned model):**
- Minimum: 1x RTX 4090 24GB (with 4-bit quantization)
- Recommended: 1x A100 40GB or L40S for full precision
- Can run on CPU with llama.cpp if speed isn't critical (for batch processing)
- Monthly cost: $50-150/month for a small always-on server, or per-use with serverless

**For Embedding Generation:**
- Can run on CPU (BGE-M3 is small enough)
- GPU speeds it up 10-50x for bulk processing
- Share the inference GPU or use a cheap T4 ($0.30/hr)

### GPU Provider Comparison

| Provider | Price/hr (A100 80GB) | Kestra Integration | Reliability | Rating |
|----------|---------------------|-------------------|-------------|--------|
| **Vast.ai** | $1.50-2.50 | API available | Variable | **7/10** |
| **RunPod** | $2.00-2.80 | Good API | Good | **8/10** ★ |
| **Lambda Labs** | $2.50 | SSH | Excellent | **8/10** |
| **Together.ai** | Pay per token | REST API | Excellent | **7/10** (fine-tune API) |
| **Modal** | Pay per second | Python SDK | Excellent | **8/10** (serverless) |

### My Recommendation: RunPod for fine-tuning, Modal for inference

- **RunPod**: Rent GPU pods on-demand for fine-tuning. Kestra triggers pod creation → training → shutdown.
- **Modal**: Serverless GPU inference. Pay only when your model is being queried. Perfect for a research system that isn't 24/7.
- **Alternative**: If you want simplicity, Together.ai has a fine-tuning API where you just upload data and they handle everything. Less control but much easier.

### Total Estimated Costs

| Component | One-Time | Monthly (ongoing) |
|-----------|----------|-------------------|
| Fine-tuning (1 model, QLoRA) | $50-100 | $0 (one-time) |
| Inference server (Modal serverless) | $0 | $30-100 |
| Embedding generation | $10-20 | $5-10 |
| LanceDB storage | $0 (self-hosted) | $0 |
| Kestra (self-hosted) | $0 | $5-20 (small VPS) |
| API costs (Semantic Scholar, etc.) | $0 (free tiers) | $0 |
| **Total** | **$60-120** | **$35-130/month** |

### Rating: 7/10 — Important but not the hardest problem. GPU rental is commoditized. The real challenge is everything else.

---

## 8. CODING AGENT STRATEGY (Rating: 7/10 importance)

You mentioned Codex, Claude Code, and Qwen 3 Coder. Here's how to use each:

### Role Assignment

| Agent | Best For | Limitation | Rating |
|-------|----------|-----------|--------|
| **Claude Code** | Architecture, complex logic, documentation, Kestra YAML, system design | Cost per token | **9/10** ★ |
| **Codex (OpenAI)** | Quick code generation, boilerplate, simple scripts | Less nuanced reasoning | **7/10** |
| **Qwen 3 Coder** | Self-hosted, private, iterative coding, running locally | Needs GPU to run | **7/10** |

### My Recommendation: Claude Code as primary, Qwen 3 Coder as local assistant

- **Claude Code** for: Writing Kestra flow YAML, designing system architecture, building Haystack pipelines, creating documentation for GitHub repos, complex debugging
- **Qwen 3 Coder** for: Running locally on your inference GPU, quick iterations, private code that shouldn't leave your machine, testing and modification loops
- **Codex** for: If you're already in VS Code / GitHub ecosystem, use it for boilerplate and simple scripts

### GitHub Workflow with Coding Agents

```
1. Claude Code designs the component (architecture + initial code)
2. Push to GitHub branch
3. Qwen 3 Coder (local) iterates on it, runs tests
4. Push updates to branch
5. Claude Code reviews, suggests improvements
6. Merge to main
7. Kestra pulls latest from GitHub for deployment
```

### Rating: 7/10 — Coding agents accelerate development massively but they're tools, not substitutes for understanding what you're building. You still need to understand the system design.

---

## 9. DOMAIN SPECIALIZATION STRATEGY (Rating: 8/10 importance)

### Your Four Research Domains — How They Connect

```
                    NEUROSCIENCE
                   /            \
          neural basis of      brain-environment
          social behavior      interactions
                /                    \
        PSYCHOLOGY -------- ENVIRONMENTALISM
          social psych \      / environmental
          well-being    \    /  justice
                    \    \  /    /
                     SOCIOLOGY
```

**These domains are deeply interconnected.** This is why one fine-tuned model + domain RAG beats four separate models.

### Domain-Specific RAG Collections

For each domain, you need curated knowledge bases:

**Sociology Collection:**
- Key journals: American Sociological Review, Social Forces, Annual Review of Sociology
- Focus areas: social movements, mutual aid, community organizing, inequality, institutional analysis
- Key databases: ICPSR (quantitative social science data), GSS (General Social Survey)
- Estimated papers: 50,000-100,000 abstracts, 5,000-10,000 full texts
- Rating: 8/10 relevance to OLS mission

**Psychology Collection:**
- Key journals: Psychological Bulletin, Journal of Personality and Social Psychology, Motivation and Emotion
- Focus areas: Self-Determination Theory, intrinsic motivation, well-being, community psychology, behavioral change
- Key databases: APA PsycINFO (via OpenAlex for open access), PsyArXiv preprints
- Estimated papers: 50,000-100,000 abstracts, 5,000-10,000 full texts
- SDT-specific sub-collection: every paper by Deci, Ryan, and collaborators
- Rating: 10/10 relevance to OLS mission (SDT is foundational)

**Environmentalism Collection:**
- Key journals: Nature Climate Change, Environmental Science & Technology, Ecology and Society
- Focus areas: degrowth, ecological economics, sustainability science, environmental justice, commons governance
- Key databases: Web of Science (via OpenAlex), EarthArXiv preprints
- Estimated papers: 30,000-50,000 abstracts, 3,000-5,000 full texts
- Rating: 9/10 relevance to OLS mission

**Neuroscience Collection:**
- Key journals: Nature Neuroscience, PNAS, NeuroImage, Social Cognitive and Affective Neuroscience
- Focus areas: social neuroscience, reward systems, motivation circuitry, stress/resilience neurobiology, decision-making
- Key databases: PubMed/PMC (richest source), bioRxiv preprints
- Estimated papers: 30,000-50,000 abstracts, 5,000-10,000 full texts (PubMed has great OA coverage)
- Rating: 7/10 relevance to OLS mission (foundational but less directly operational)

### Cross-Domain Index

Create a fifth collection that indexes concepts appearing across domains:
- "intrinsic motivation" → papers from psychology, neuroscience, sociology
- "community resilience" → papers from sociology, environmentalism, psychology
- "commons governance" → papers from sociology, environmentalism, economics
- This enables cross-domain synthesis, which is where the most valuable insights live

### Rating: 8/10 — Domain structure determines what questions your system can answer. The cross-domain index is what makes this more than just a search engine.

---

## 10. FINE-TUNING METHODOLOGY (Rating: 8/10 importance)

### QLoRA Configuration

For a 14B model, QLoRA is the only sensible choice on rented GPUs:

| Parameter | Recommended Value | Why |
|-----------|-------------------|-----|
| **Quantization** | 4-bit NF4 | Standard for QLoRA, minimal quality loss |
| **LoRA rank (r)** | 64 | Good balance for research tasks; 32 might undershoot |
| **LoRA alpha** | 128 | 2x rank is standard |
| **LoRA target modules** | All linear layers | Better than just attention for instruction-following |
| **Learning rate** | 2e-4 | Standard for QLoRA |
| **Batch size** | 4 (with gradient accumulation 4) | Effective batch 16 |
| **Epochs** | 2-3 | More risks overfitting on 35K examples |
| **Max sequence length** | 4096-8192 | Needs to fit paper sections + response |
| **Optimizer** | Paged AdamW 8-bit | Memory efficient |

### Fine-Tuning Tool

| Tool | Ease of Use | Quality | Kestra Integration | Rating |
|------|-------------|---------|-------------------|--------|
| **Unsloth** | 9/10 | 9/10 | Script-based | **9/10** ★ |
| **Axolotl** | 7/10 | 9/10 | YAML config | **8/10** |
| **LLaMA-Factory** | 8/10 | 8/10 | Web UI + CLI | **7/10** |
| **Together.ai API** | 10/10 | 7/10 | REST API | **7/10** |
| **Hugging Face AutoTrain** | 9/10 | 7/10 | CLI/API | **6/10** |

**Recommendation: Unsloth.** 2-5x faster than standard training, significantly lower memory usage, actively maintained, excellent Qwen support. Kestra can trigger an Unsloth training script via SSH on your GPU server.

### Evaluation Strategy

You need to know if your fine-tune actually worked. Evaluation benchmarks:

1. **Paper Analysis Accuracy** — Give it papers it hasn't seen, compare extracted findings to ground truth
2. **Methodology Critique** — Present papers with known flaws, check if model identifies them
3. **Synthesis Quality** — Multi-paper synthesis compared to human-written literature reviews
4. **Tool Use Correctness** — Does it call the right tools at the right time?
5. **Structured Output Compliance** — Does it follow your JSON schema consistently?
6. **Hallucination Rate** — Does it make claims not supported by retrieved sources?

Create a held-out test set of 500-1000 examples for evaluation. **Never train on your test set.**

### Rating: 8/10 — QLoRA is mature and well-understood. The real skill is in evaluation — knowing whether your model actually improved.

---

## 11. TIMELINE & PHASING (Rating: 9/10 importance)

### Realistic Build Schedule

| Week | Phase | Deliverables | Dependencies |
|------|-------|-------------|--------------|
| **1-2** | Foundation | Kestra instance deployed, GitHub repos created, project structure defined, API keys obtained | VPS for Kestra |
| **3-4** | Data Collection Flows | Kestra flows for OpenAlex, Semantic Scholar, PubMed OA automated collection | Kestra running |
| **5-6** | Processing Pipeline | PDF extraction, chunking, embedding pipeline in Kestra | Collection flows working |
| **7-8** | RAG Infrastructure | LanceDB setup, 4 domain collections populated, basic search working | Processing pipeline done |
| **9-10** | Training Data Generation | Generate 35K instruction examples using Claude API + collected papers | RAG populated |
| **11-12** | Human Verification | Review and filter training examples, create test set | Training data generated |
| **13-14** | Fine-Tuning | QLoRA training on Qwen 2.5 14B using Unsloth, evaluation | GPU rental, training data verified |
| **15-16** | Agent Assembly | Build research agents (search, retrieve, analyze, synthesize) | Fine-tuned model working |
| **17-18** | Integration & Testing | End-to-end testing, Kestra flow for full research pipeline | All components working |
| **19-20** | Documentation & Launch | GitHub documentation, public release of methodology, blog posts | System tested |

**Total: ~5 months from start to functional research system.**

### Critical Path Risks

| Risk | Impact | Likelihood | Mitigation | Rating |
|------|--------|-----------|------------|--------|
| Training data quality too low | High | Medium | Human verification gate, iterative improvement | 7/10 |
| Fine-tuned model hallucinates | High | Medium | Citation validation agent, RAG grounding | 8/10 |
| PDF extraction fails on many papers | Medium | High | Use `marker` library, have fallback to abstract-only | 6/10 |
| GPU costs exceed budget | Low | Low | QLoRA is cheap, use spot instances | 3/10 |
| Kestra learning curve | Medium | Medium | Start with simple flows, build complexity gradually | 5/10 |
| Model can't do cross-domain synthesis | Medium | Low | Cross-domain index + training examples | 4/10 |
| Scope creep (trying to do too much) | High | HIGH | **Biggest risk.** Stay disciplined. One model, then iterate. | 9/10 |

### Rating: 9/10 — A clear timeline with phases is the difference between shipping and perpetual "almost done."

---

## 12. OPEN SCIENCE ALIGNMENT (Rating: 9/10 importance)

### Licensing

| Component | Recommended License | Why |
|-----------|-------------------|-----|
| Fine-tuned model weights | Apache 2.0 | Matches Qwen's license, maximum openness |
| Training dataset | CC-BY-4.0 | Standard for research datasets |
| Code/pipelines | AGPL-3.0 | Ensures derivatives stay open (stronger than MIT/Apache for infrastructure) |
| Documentation | CC-BY-SA-4.0 | Open but requires attribution |
| Kestra flows | Apache 2.0 | Match Kestra's own license |

### Center for Open Science Integration

- Register the project on OSF (Open Science Framework)
- Pre-register your research methodology before building
- Use OSF for dataset hosting (free, DOI-assigned)
- This gives academic credibility to OLS's research infrastructure

### Reproducibility Requirements

- All Kestra flows committed to GitHub (anyone can replicate the pipeline)
- Training data generation scripts fully documented
- Model training configs (hyperparameters, hardware) logged
- Evaluation results published with statistical significance tests
- Version control on model checkpoints

### Rating: 9/10 — Open Science isn't just ethical alignment, it's strategic. It builds trust, attracts collaborators, and differentiates OLS from corporate AI research.

---

## 13. WHAT TO BUILD FIRST (Priority Order)

**Start with the simplest useful thing, then iterate.**

1. **Week 1:** Kestra + OpenAlex data collection for SDT psychology papers (your strongest domain)
2. **Week 2-3:** LanceDB + BGE-M3 embeddings for collected papers
3. **Week 4:** Basic RAG pipeline — ask questions, get answers grounded in papers
4. **Week 5-6:** Expand to all four domains
5. **Week 7-10:** Generate training data, fine-tune
6. **Week 11+:** Add agents, cross-domain synthesis, full research workflows

**DO NOT try to build everything at once.** Get RAG working first. That alone is enormously valuable even without fine-tuning. Then fine-tune to make it better. Then add agents to make it automated.

---

## OVERALL SYSTEM RATINGS SUMMARY

| Aspect | Rating | Notes |
|--------|--------|-------|
| Base model choice (Qwen 2.5 14B) | 9/10 | Best balance of reasoning, tool use, and community support |
| Single model + domain RAG strategy | 9/10 | Much better than multiple domain models |
| Dataset sources (OpenAlex, Semantic Scholar, PMC) | 9/10 | Comprehensive and legally clean |
| LanceDB for vector storage | 9/10 | Aligned with OVNN plans, open source, embedded |
| Kestra as orchestration backbone | 10/10 | Perfect fit, your biggest competitive advantage |
| QLoRA with Unsloth | 9/10 | Proven, cost-effective, well-supported |
| Agent design (Haystack + Kestra hybrid) | 8/10 | Start simple, add complexity as needed |
| GPU strategy (RunPod + Modal) | 7/10 | Adequate and cost-effective |
| Coding agent strategy (Claude Code primary) | 8/10 | Use Claude Code for design, Qwen for iteration |
| Timeline (5 months) | 7/10 | Ambitious but achievable if disciplined |
| Open Science alignment | 9/10 | Strategic advantage, not just ethics |
| Cross-domain research capability | 8/10 | The cross-domain index is the secret weapon |
| **Overall System Feasibility** | **8.5/10** | Highly achievable with disciplined execution |

---

## KEY WARNINGS

1. **Do NOT fine-tune four separate models.** This is the single biggest mistake you could make. One research-methodology model + four RAG collections.

2. **Do NOT skip evaluation.** A fine-tuned model that hallucinates is worse than no fine-tuning at all. Build evaluation into every phase.

3. **Do NOT start with agents.** Get RAG working first. RAG alone is 80% of the value. Agents are optimization on top.

4. **Do NOT use Sci-Hub data.** As an Open Science nonprofit, you need to be above reproach on data sourcing. OpenAlex + PMC OA gives you more than enough.

5. **Do NOT try to process all papers.** Start with high-impact, highly-cited papers in each domain. Quality over quantity. 10,000 excellent papers beats 500,000 mediocre ones.

6. **WATCH for scope creep.** You have OLS, CommunityLLM, HBoK, OVNN, DirectDemocracyLLM, and now a research system. Each is a full-time project. This research system should SERVE the other projects, not become a fifth standalone initiative.
