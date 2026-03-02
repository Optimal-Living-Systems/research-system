# OLS Research System — Implementation Plan
## Single Research-Methodology Model + 4 Domain RAG Collections

**Date:** March 1, 2026
**Status:** ACTIVE BUILD PLAN
**GitHub Repo:** `optimal-living-systems/research-system` (to be created)

---

## PART 1: SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KESTRA ORCHESTRATOR                         │
│  (Schedules, triggers, monitors, retries, logs everything)         │
└──────────┬──────────────────────────────────────┬──────────────────┘
           │                                      │
     ┌─────▼──────┐                        ┌──────▼───────┐
     │  DATA LAYER │                        │ MODEL LAYER  │
     │             │                        │              │
     │ ┌─────────┐ │    query + context     │ ┌──────────┐ │
     │ │LanceDB  │ │ ──────────────────►    │ │ Qwen 2.5 │ │
     │ │         │ │                        │ │   14B     │ │
     │ │ 4 domain│ │    ◄──────────────     │ │ QLoRA    │ │
     │ │collections│      tool calls        │ │fine-tuned│ │
     │ │ + cross- │ │                        │ │  for     │ │
     │ │  domain  │ │                        │ │ research │ │
     │ └─────────┘ │                        │ │methodology│ │
     │             │                        │ └──────────┘ │
     │ ┌─────────┐ │                        │              │
     │ │BGE-M3   │ │                        │ ┌──────────┐ │
     │ │Embedding│ │                        │ │BGE-M3    │ │
     │ │Service  │ │                        │ │Reranker  │ │
     │ └─────────┘ │                        │ └──────────┘ │
     └─────────────┘                        └──────────────┘
           │
     ┌─────▼──────────────────────────────────────┐
     │              DATA SOURCES                   │
     │  OpenAlex │ Semantic Scholar │ PubMed/PMC   │
     │  PsyArXiv │ SocArXiv │ EarthArXiv │ bioRxiv│
     └─────────────────────────────────────────────┘
```

---

## PART 2: THE FINE-TUNED MODEL — What It Learns

### 2.1 What We Are NOT Teaching It

We are NOT teaching it sociology, psychology, environmentalism, or neuroscience facts. That knowledge comes from RAG at query time. The model does NOT need to "know" anything about your domains.

### 2.2 What We ARE Teaching It

We are teaching it to BE A RESEARCHER. Specifically, these 8 skills:

```
SKILL 1: PAPER ANALYSIS
  Input:  A paper (or section of a paper)
  Output: Structured extraction of hypothesis, methodology,
          sample, findings, limitations, effect sizes, p-values

SKILL 2: METHODOLOGY CRITIQUE
  Input:  A methods section
  Output: Identified strengths, weaknesses, confounds,
          sampling issues, statistical concerns, replication risk

SKILL 3: EVIDENCE SYNTHESIS
  Input:  Multiple paper summaries on one topic
  Output: Coherent synthesis identifying consensus, disagreement,
          strength of evidence, and confidence levels

SKILL 4: RESEARCH GAP IDENTIFICATION
  Input:  A body of literature summaries
  Output: What hasn't been studied, understudied populations,
          missing methodologies, unexplored intersections

SKILL 5: STATISTICAL REASONING
  Input:  Statistical tables, regression outputs, effect sizes
  Output: Plain-language interpretation, significance assessment,
          practical vs statistical significance distinction

SKILL 6: STRUCTURED DATA EXTRACTION
  Input:  Any paper content
  Output: Consistent JSON with fields like sample_size,
          study_type, effect_size, confidence_interval, etc.

SKILL 7: TOOL USE DECISIONS
  Input:  A research question
  Output: Correct tool calls — when to search databases,
          when to retrieve from RAG, when to calculate,
          when to ask for clarification

SKILL 8: CITATION-GROUNDED RESPONSE
  Input:  A question + retrieved context with sources
  Output: Answer that cites specific sources, never makes
          unsupported claims, flags uncertainty explicitly
```

### 2.3 Training Data Format

Every training example follows this structure (ChatML format for Qwen):

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a research methodology specialist. You analyze papers with rigorous scientific standards, extract structured data, and synthesize evidence across studies. You always ground claims in cited sources and flag uncertainty. You use tools when needed."
    },
    {
      "role": "user",
      "content": "[THE TASK — e.g., 'Analyze the methodology of this study...']"
    },
    {
      "role": "assistant",
      "content": "[THE IDEAL RESPONSE — structured, cited, rigorous]"
    }
  ]
}
```

For tool-use examples:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a research methodology specialist with access to tools: search_papers, retrieve_context, extract_data, calculate_effect_size."
    },
    {
      "role": "user",
      "content": "What does the literature say about intrinsic motivation and volunteer retention?"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "type": "function",
          "function": {
            "name": "search_papers",
            "arguments": "{\"query\": \"intrinsic motivation volunteer retention\", \"domains\": [\"psychology\", \"sociology\"], \"min_citations\": 10}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "content": "[Search results with paper metadata]"
    },
    {
      "role": "assistant",
      "content": "[Synthesized answer grounded in the retrieved papers]"
    }
  ]
}
```

### 2.4 Training Data Distribution (35,000 examples total)

| Skill | Count | % | Rationale |
|-------|-------|---|-----------|
| Paper Analysis | 8,000 | 23% | Core skill, needs many diverse examples |
| Methodology Critique | 5,000 | 14% | High value, moderate complexity |
| Evidence Synthesis | 5,000 | 14% | Critical for literature reviews |
| Research Gap ID | 3,000 | 9% | Harder to generate, fewer needed |
| Statistical Reasoning | 4,000 | 11% | Needs variety of stat methods |
| Structured Extraction | 4,000 | 11% | Needs consistent schema adherence |
| Tool Use Decisions | 3,500 | 10% | Critical for agent behavior |
| Citation-Grounded Response | 2,500 | 7% | Reinforced across other skills too |
| **Total** | **35,000** | **100%** | |

### 2.5 Training Data Generation Pipeline

This is the most important pipeline in the entire system. Here's exactly how to build each skill's training data:

#### STEP 1: Collect Source Papers (Kestra automated)

```
For each domain:
  → Query OpenAlex API for top-cited papers (last 20 years)
  → Filter: citation_count > 20, has_fulltext = true
  → Download full text from PMC OA or Unpaywall
  → Store as JSON: {doi, title, authors, year, journal, abstract, full_text, sections}
  → Target: 5,000 full-text papers per domain = 20,000 total
```

#### STEP 2: Generate Training Examples (Kestra + Claude API)

For each paper, generate multiple training examples using Claude API:

**Prompt template for Paper Analysis examples:**
```
You are generating training data for a research AI.

Given this paper:
Title: {title}
Abstract: {abstract}
Methods: {methods_section}
Results: {results_section}

Generate a training example where:
- The USER asks to analyze this paper's methodology and findings
- The ASSISTANT provides a structured analysis covering:
  1. Research question/hypothesis
  2. Study design (RCT, observational, qualitative, etc.)
  3. Sample (size, demographics, recruitment)
  4. Key variables (independent, dependent, controls)
  5. Main findings with effect sizes
  6. Limitations
  7. Confidence assessment (high/medium/low)

Format as a JSON message pair. The ASSISTANT response should be
thorough but concise, in a consistent format.
```

**Prompt template for Methodology Critique examples:**
```
Given this methods section from a published paper:
{methods_section}

Generate a training example where:
- The USER asks to evaluate the methodology
- The ASSISTANT identifies:
  1. Strengths of the design
  2. Potential confounds or threats to validity
  3. Sampling concerns
  4. Statistical approach appropriateness
  5. Missing controls or comparisons
  6. Reproducibility assessment

Be specific and cite concrete issues, not generic complaints.
```

**Prompt template for Evidence Synthesis examples:**
```
Given these 3-5 paper summaries on a related topic:
{paper_summaries}

Generate a training example where:
- The USER asks to synthesize findings across these studies
- The ASSISTANT provides:
  1. Points of consensus
  2. Points of disagreement or inconsistency
  3. Methodological differences that explain disagreements
  4. Overall strength of evidence
  5. What a researcher should conclude
  6. Remaining questions
```

**Prompt template for Tool Use examples:**
```
Generate a training example where:
- The USER asks a research question: "{research_question}"
- The ASSISTANT must decide which tools to call:
  - search_papers(query, domains, filters)
  - retrieve_context(paper_ids, sections)
  - extract_data(paper_id, fields)
  - calculate_effect_size(data)
- Show the tool call, the simulated tool response, and
  the final answer grounded in the tool results.
```

#### STEP 3: Quality Filter (Semi-automated + Human Review)

```
For each generated example:
  1. Automated checks:
     - JSON valid?
     - Response length reasonable (200-2000 tokens)?
     - Contains specific claims (not just generic advice)?
     - Structured output matches schema?
     - No hallucinated citations?

  2. Human spot-check (you review 10% sample):
     - Is the analysis actually correct?
     - Would a researcher find this useful?
     - Is the methodology critique valid?
     - Are the tool calls appropriate?

  3. Filter out:
     - Generic/vague responses
     - Incorrect statistical interpretations
     - Examples that just paraphrase the abstract
     - Tool calls that don't make sense
```

#### STEP 4: Augmentation

```
  1. Create adversarial examples:
     - Papers with known retractions → model should flag concerns
     - Papers with p-hacking → model should identify
     - Studies with tiny samples → model should note limitation
     - Conflicting studies → model should acknowledge both sides

  2. Create multi-turn examples:
     - User asks follow-up questions
     - User challenges the model's analysis
     - User asks to go deeper on one aspect

  3. Create refusal examples:
     - Questions outside research scope → model redirects
     - Requests for medical/legal advice → model declines appropriately
     - Requests to fabricate citations → model refuses
```

---

## PART 3: THE 4 DOMAIN RAG COLLECTIONS

### 3.1 LanceDB Schema

Each domain collection uses the same schema:

```python
# Schema for each domain collection in LanceDB
{
    "id": "string",              # unique identifier (DOI or generated)
    "doi": "string",             # Digital Object Identifier
    "title": "string",           # paper title
    "authors": "string",         # comma-separated author names
    "year": "int",               # publication year
    "journal": "string",         # journal name
    "citation_count": "int",     # citation count (updated periodically)
    "study_type": "string",      # RCT, observational, meta-analysis, qualitative, review, theoretical
    "abstract": "string",        # full abstract text
    "chunk_type": "string",      # abstract, introduction, methods, results, discussion, summary
    "chunk_text": "string",      # the actual text content
    "vector": "vector[1024]",    # BGE-M3 embedding
    "domains": "list[string]",   # can appear in multiple domains
    "keywords": "list[string]",  # extracted keywords
    "methodology_tags": "list[string]",  # e.g., ["longitudinal", "survey", "n>1000"]
    "open_access": "bool",       # is full text freely available?
    "source": "string",          # openalex, semantic_scholar, pubmed, preprint
    "collected_date": "string",  # when we collected this
    "quality_score": "float"     # computed quality metric (citations/year + journal impact)
}
```

### 3.2 Collection Specifications

#### COLLECTION 1: `psychology_papers`

**Scope & Boundaries:**
- Self-Determination Theory (SDT) — PRIORITY: every paper by Deci, Ryan, and collaborators
- Intrinsic/extrinsic motivation
- Community psychology
- Well-being and flourishing research
- Behavioral change and habit formation
- Social psychology of cooperation and prosocial behavior
- Positive psychology (but critically evaluated)

**Excluded:** Clinical psychology (unless community-based), psychopharmacology, abnormal psychology (unless relevant to well-being frameworks)

**Key API Queries for OpenAlex:**
```
concepts: "Self-Determination Theory" OR "intrinsic motivation"
concepts: "community psychology" OR "mutual aid"
concepts: "prosocial behavior" OR "cooperation"
concepts: "well-being" OR "flourishing" OR "eudaimonia"
concepts: "behavioral change" AND NOT "pharmacological"
filter: cited_by_count > 15, publication_year > 2004
```

**Priority Journals:**
- Journal of Personality and Social Psychology
- Motivation and Emotion
- Basic and Applied Social Psychology
- Journal of Community Psychology
- American Journal of Community Psychology
- Self and Identity
- Psychological Bulletin (review articles)

**Target Volume:**
- 80,000 abstracts + metadata
- 8,000 full-text papers (high-citation subset)
- ~200,000 chunks after processing

**OLS Mission Alignment:** DIRECT. SDT is the theoretical backbone of PersonalLLM, OVNN dimensions (autonomy, competence, relatedness), and intrinsic motivation mapping.

---

#### COLLECTION 2: `sociology_papers`

**Scope & Boundaries:**
- Mutual aid and community organizing
- Social movements and collective action
- Commons governance and shared resources
- Inequality, social stratification, and justice
- Institutional analysis and organizational sociology
- Community resilience and social capital
- Democratic participation and civic engagement
- Cooperative economics and alternative institutions

**Excluded:** Pure demography (unless tied to inequality), historical sociology before 1950 (unless foundational), cultural studies without empirical grounding

**Key API Queries for OpenAlex:**
```
concepts: "mutual aid" OR "community organizing"
concepts: "social movements" OR "collective action"
concepts: "commons governance" OR "common pool resources"
concepts: "social capital" OR "community resilience"
concepts: "participatory democracy" OR "direct democracy"
concepts: "cooperative" OR "cooperative economics"
concepts: "social inequality" OR "social stratification"
filter: cited_by_count > 10, publication_year > 2000
```

**Priority Journals:**
- American Sociological Review
- Social Forces
- American Journal of Sociology
- Annual Review of Sociology
- Mobilization (social movements)
- Community Development Journal
- Journal of Civil Society

**Priority Authors/Works:**
- Elinor Ostrom (commons governance) — foundational
- Peter Kropotkin → modern mutual aid researchers
- Robert Putnam (social capital)
- Theda Skocpol (civic engagement)
- Erik Olin Wright (real utopias)

**Target Volume:**
- 60,000 abstracts + metadata
- 6,000 full-text papers
- ~150,000 chunks after processing

**OLS Mission Alignment:** DIRECT. Community organizing IS the OLS mission. CommunityLLM draws directly from this literature. DirectDemocracyLLM needs participatory democracy research.

---

#### COLLECTION 3: `environmentalism_papers`

**Scope & Boundaries:**
- Degrowth economics and post-growth theory
- Ecological economics (distinct from environmental economics)
- Sustainability science and planetary boundaries
- Environmental justice and equity
- Climate change social dimensions (adaptation, policy, behavior)
- Commons-based natural resource management
- Agroecology and food sovereignty
- Circular economy and resource throughput

**Excluded:** Pure climate modeling (physics), industrial ecology focused solely on corporate optimization, carbon market financialization

**Key API Queries for OpenAlex:**
```
concepts: "degrowth" OR "post-growth"
concepts: "ecological economics" OR "steady-state economy"
concepts: "planetary boundaries" OR "sustainability science"
concepts: "environmental justice" OR "climate justice"
concepts: "commons" AND "natural resources"
concepts: "agroecology" OR "food sovereignty"
concepts: "resource throughput" OR "material flow"
filter: cited_by_count > 10, publication_year > 2005
```

**Priority Journals:**
- Ecological Economics
- Sustainability Science
- Nature Climate Change (social dimensions)
- Ecology and Society
- Environmental Science & Policy
- Journal of Cleaner Production
- Futures (degrowth scenarios)

**Priority Authors/Works:**
- Jason Hickel (degrowth)
- Kate Raworth (doughnut economics)
- Johan Rockström (planetary boundaries)
- Giorgos Kallis (degrowth economics)
- Tim Jackson (prosperity without growth)
- Elinor Ostrom (commons — shared with sociology)

**Target Volume:**
- 50,000 abstracts + metadata
- 5,000 full-text papers
- ~120,000 chunks after processing

**OLS Mission Alignment:** DIRECT. OVNN's ecological_impact dimension, resource_throughput scoring, and the moneyless society framework all draw from degrowth and ecological economics.

---

#### COLLECTION 4: `neuroscience_papers`

**Scope & Boundaries:**
- Social neuroscience (neural basis of cooperation, empathy, trust)
- Reward systems and motivation neuroscience (dopamine, intrinsic motivation circuits)
- Stress, resilience, and neuroplasticity
- Decision-making neuroscience (especially collective/social decisions)
- Neuroscience of well-being and flourishing
- Embodied cognition relevant to HBoK physical layer
- Sleep, exercise, nutrition neuroscience (HBoK body systems)

**Excluded:** Purely clinical neuroscience (Alzheimer's, Parkinson's, etc.), computational neuroscience (unless applied to decision-making), neuroimaging methodology papers (unless groundbreaking)

**Key API Queries for OpenAlex:**
```
concepts: "social neuroscience" OR "social cognition"
concepts: "reward system" AND "motivation"
concepts: "intrinsic motivation" AND ("neural" OR "brain" OR "fMRI")
concepts: "stress" AND "resilience" AND "neuroscience"
concepts: "decision making" AND "neuroscience" AND "social"
concepts: "well-being" AND ("neural" OR "brain")
concepts: "exercise" AND "brain" AND "cognition"
filter: cited_by_count > 20, publication_year > 2005
```

**Priority Journals:**
- Nature Neuroscience
- Social Cognitive and Affective Neuroscience (SCAN)
- NeuroImage
- Cerebral Cortex
- PNAS (neuroscience articles)
- Trends in Cognitive Sciences
- Frontiers in Human Neuroscience

**Target Volume:**
- 40,000 abstracts + metadata
- 4,000 full-text papers
- ~100,000 chunks after processing

**OLS Mission Alignment:** SUPPORTING. Provides biological grounding for SDT, validates HBoK body-mind connections, informs OVNN health dimension.

---

#### COLLECTION 5: `cross_domain_index`

This is NOT a separate paper collection. It's an INDEX that maps concepts across the four domain collections.

```python
# Cross-domain index schema
{
    "concept": "string",           # e.g., "intrinsic motivation"
    "domains_present": "list[string]",  # ["psychology", "neuroscience", "sociology"]
    "paper_ids_by_domain": {
        "psychology": ["doi1", "doi2"],
        "neuroscience": ["doi3"],
        "sociology": ["doi4", "doi5"]
    },
    "description": "string",       # how this concept appears across domains
    "vector": "vector[1024]",      # embedding of the concept description
    "related_concepts": "list[string]",  # linked concepts
    "ols_relevance": "string"      # which OLS project this concept serves
}
```

**Priority Cross-Domain Concepts to Seed:**

| Concept | Psychology | Sociology | Environment | Neuroscience |
|---------|-----------|-----------|-------------|--------------|
| Intrinsic motivation | SDT theory | Volunteer retention | Pro-environmental behavior | Reward circuitry |
| Autonomy | SDT autonomy need | Self-governance | Energy democracy | Prefrontal decision-making |
| Cooperation | Prosocial behavior | Collective action | Commons management | Neural basis of trust |
| Well-being | Eudaimonia | Social determinants | Ecological well-being | Neural correlates |
| Community resilience | Community psych | Social capital | Climate adaptation | Stress buffering |
| Behavioral change | Habit formation | Social norms | Sustainability behavior | Neuroplasticity |
| Equity/Justice | Fairness perception | Social inequality | Environmental justice | Inequity aversion |
| Commons | Shared resources psych | Ostrom's principles | Natural resource commons | Shared neural representations |

**Build Process:**
1. After all 4 domain collections are populated
2. Extract top 500 keywords from each collection
3. Find keywords appearing in 2+ collections
4. Use Claude API to generate concept descriptions showing cross-domain connections
5. Embed and store in LanceDB

---

### 3.3 Chunking Strategy (Critical Detail)

**DO NOT chunk by fixed token count.** Academic papers have natural structure.

```
For each full-text paper:

  CHUNK 1: "paper_summary"
    = title + abstract + extracted key findings
    Purpose: High-level retrieval for broad queries
    Typical size: 300-500 tokens

  CHUNK 2: "introduction"
    = Introduction / Background section
    Purpose: Context, research question, literature positioning
    Typical size: 500-1500 tokens
    If >1500 tokens: split at paragraph boundaries

  CHUNK 3: "methods"
    = Methods / Materials section
    Purpose: Study design, sample, procedures, measures
    Typical size: 500-2000 tokens
    If >2000 tokens: split into "methods_design" + "methods_measures" + "methods_analysis"

  CHUNK 4: "results"
    = Results section
    Purpose: Findings, statistics, tables
    Typical size: 500-2000 tokens
    If >2000 tokens: split by sub-study or hypothesis

  CHUNK 5: "discussion"
    = Discussion / Conclusion section
    Purpose: Interpretation, implications, limitations
    Typical size: 500-1500 tokens
    If >1500 tokens: split into "discussion_interpretation" + "discussion_limitations"

  ALL CHUNKS carry full metadata:
    {doi, title, authors, year, journal, chunk_type}
```

**For abstract-only papers** (no full text available):

```
  CHUNK 1: "paper_summary"
    = title + abstract
    Typical size: 200-400 tokens
    Still valuable for broad synthesis queries
```

### 3.4 Embedding Pipeline

```
Input: chunk_text (string)
  ↓
BGE-M3 model (running on GPU or CPU)
  ↓
Output: 1024-dimensional float vector
  ↓
Store in LanceDB with all metadata fields
```

**BGE-M3 configuration:**
- Model: `BAAI/bge-m3`
- Max input length: 8192 tokens (handles long chunks)
- Output: dense embedding (1024d) — use dense for primary search
- Also supports sparse (lexical) and colbert (multi-vector) — use sparse for hybrid search
- Normalize embeddings for cosine similarity

**Batch processing:**
- Process 32-64 chunks per batch on GPU
- ~500 chunks/second on A100, ~50 chunks/second on CPU
- Total embedding time for 570,000 chunks:
  - GPU: ~20 minutes
  - CPU: ~3 hours

---

## PART 4: KESTRA FLOW ARCHITECTURE

### 4.1 Namespace Organization

```
ols-research/
├── collection/
│   ├── collect-openalex          # pull papers from OpenAlex
│   ├── collect-semantic-scholar  # pull from Semantic Scholar
│   ├── collect-pubmed-oa         # pull from PubMed OA
│   └── collect-preprints         # pull from PsyArXiv, SocArXiv, etc.
│
├── processing/
│   ├── extract-pdf-text          # PDF → structured text
│   ├── chunk-papers              # text → chunks with metadata
│   ├── generate-embeddings       # chunks → BGE-M3 vectors
│   ├── quality-filter            # remove low-quality papers
│   └── index-to-lancedb          # upsert to LanceDB collections
│
├── training/
│   ├── generate-training-data    # create instruction examples via Claude API
│   ├── validate-training-data    # quality checks + human review queue
│   ├── prepare-dataset           # format for QLoRA training
│   ├── run-fine-tune             # trigger training on GPU server
│   └── evaluate-model            # benchmark on held-out test set
│
├── research/
│   ├── literature-review         # end-to-end research pipeline
│   ├── paper-analysis            # analyze single paper
│   ├── methodology-audit         # critique a study's methods
│   ├── trend-analysis            # track trends over time
│   └── cross-domain-synthesis    # synthesize across domains
│
└── maintenance/
    ├── update-citation-counts    # refresh citation data monthly
    ├── check-retractions         # flag retracted papers
    ├── backup-lancedb            # backup vector database
    └── monitor-quality           # track retrieval quality metrics
```

### 4.2 Core Kestra Flows (YAML)

#### Flow 1: Collect from OpenAlex

```yaml
id: collect-openalex
namespace: ols-research.collection
description: "Pull new papers from OpenAlex API for all 4 domains"

triggers:
  - id: weekly-schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 2 * * 0"  # Every Sunday at 2 AM

inputs:
  - id: domains
    type: JSON
    defaults: |
      {
        "psychology": [
          "self-determination theory",
          "intrinsic motivation",
          "community psychology",
          "prosocial behavior",
          "well-being flourishing"
        ],
        "sociology": [
          "mutual aid",
          "community organizing",
          "collective action",
          "commons governance",
          "participatory democracy"
        ],
        "environmentalism": [
          "degrowth",
          "ecological economics",
          "planetary boundaries",
          "environmental justice",
          "agroecology"
        ],
        "neuroscience": [
          "social neuroscience",
          "reward motivation brain",
          "intrinsic motivation neural",
          "decision making social neuroscience",
          "resilience neuroscience"
        ]
      }

tasks:
  - id: fetch-papers
    type: io.kestra.plugin.scripts.python.Script
    description: "Query OpenAlex API for each domain and concept"
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install requests
    outputFiles:
      - "*.jsonl"
    script: |
      import requests
      import json
      import time
      import os

      domains = json.loads('{{ inputs.domains }}')
      base_url = "https://api.openalex.org/works"

      # Polite pool - add your email for faster rate limits
      headers = {"mailto": "research@optimallivingsystems.org"}

      for domain, concepts in domains.items():
          output_file = f"{domain}_papers.jsonl"
          paper_count = 0

          with open(output_file, 'w') as f:
              for concept in concepts:
                  params = {
                      "search": concept,
                      "filter": "cited_by_count:>10,publication_year:>2004,has_abstract:true",
                      "sort": "cited_by_count:desc",
                      "per_page": 200,
                      "page": 1
                  }

                  while params["page"] <= 5:  # Max 1000 papers per concept
                      response = requests.get(base_url, params=params, headers=headers)
                      if response.status_code != 200:
                          break

                      data = response.json()
                      results = data.get("results", [])
                      if not results:
                          break

                      for work in results:
                          paper = {
                              "id": work.get("id", ""),
                              "doi": work.get("doi", ""),
                              "title": work.get("title", ""),
                              "authors": [a.get("author", {}).get("display_name", "")
                                         for a in work.get("authorships", [])[:10]],
                              "year": work.get("publication_year"),
                              "journal": work.get("primary_location", {}).get("source", {}).get("display_name", ""),
                              "citation_count": work.get("cited_by_count", 0),
                              "abstract": work.get("abstract_inverted_index", {}),
                              "open_access": work.get("open_access", {}).get("is_oa", False),
                              "oa_url": work.get("open_access", {}).get("oa_url", ""),
                              "concepts": [c.get("display_name", "") for c in work.get("concepts", [])[:10]],
                              "domain": domain,
                              "search_concept": concept,
                              "collected_date": time.strftime("%Y-%m-%d")
                          }

                          # Reconstruct abstract from inverted index
                          if isinstance(paper["abstract"], dict) and paper["abstract"]:
                              words = {}
                              for word, positions in paper["abstract"].items():
                                  for pos in positions:
                                      words[pos] = word
                              paper["abstract"] = " ".join(words[k] for k in sorted(words.keys()))

                          f.write(json.dumps(paper) + "\n")
                          paper_count += 1

                      params["page"] += 1
                      time.sleep(0.1)  # Rate limiting

          print(f"Collected {paper_count} papers for {domain}")

  - id: store-raw-data
    type: io.kestra.plugin.core.storage.LocalFiles
    description: "Store collected papers for processing pipeline"
    inputs:
      psychology_papers: "{{ outputs['fetch-papers'].outputFiles['psychology_papers.jsonl'] }}"
      sociology_papers: "{{ outputs['fetch-papers'].outputFiles['sociology_papers.jsonl'] }}"
      environmentalism_papers: "{{ outputs['fetch-papers'].outputFiles['environmentalism_papers.jsonl'] }}"
      neuroscience_papers: "{{ outputs['fetch-papers'].outputFiles['neuroscience_papers.jsonl'] }}"

  - id: trigger-processing
    type: io.kestra.plugin.core.flow.Flow
    description: "Trigger the processing pipeline"
    namespace: ols-research.processing
    flowId: chunk-and-embed
    wait: false
```

#### Flow 2: Chunk Papers and Generate Embeddings

```yaml
id: chunk-and-embed
namespace: ols-research.processing
description: "Chunk papers by section, generate BGE-M3 embeddings, store in LanceDB"

inputs:
  - id: domain
    type: STRING
    description: "Which domain to process"
  - id: input_file
    type: FILE
    description: "JSONL file of collected papers"

tasks:
  - id: process-and-embed
    type: io.kestra.plugin.scripts.python.Script
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install lancedb sentence-transformers pyarrow
    script: |
      import json
      import lancedb
      from sentence_transformers import SentenceTransformer
      import pyarrow as pa

      domain = "{{ inputs.domain }}"

      # Load embedding model
      print("Loading BGE-M3 embedding model...")
      model = SentenceTransformer("BAAI/bge-m3")

      # Connect to LanceDB
      db = lancedb.connect("/data/lancedb")

      # Read papers
      papers = []
      with open("{{ inputs.input_file }}", 'r') as f:
          for line in f:
              papers.append(json.loads(line))

      print(f"Processing {len(papers)} papers for {domain}")

      # Chunk and embed
      chunks = []
      for paper in papers:
          # Create paper_summary chunk (always)
          summary_text = f"{paper['title']}. {paper.get('abstract', '')}"
          if summary_text.strip():
              chunks.append({
                  "id": f"{paper.get('doi', paper['id'])}_summary",
                  "doi": paper.get("doi", ""),
                  "title": paper["title"],
                  "authors": ", ".join(paper.get("authors", [])),
                  "year": paper.get("year", 0),
                  "journal": paper.get("journal", ""),
                  "citation_count": paper.get("citation_count", 0),
                  "chunk_type": "paper_summary",
                  "chunk_text": summary_text,
                  "domain": domain,
                  "keywords": paper.get("concepts", []),
                  "open_access": paper.get("open_access", False),
                  "source": "openalex"
              })

      # Batch embed
      print(f"Embedding {len(chunks)} chunks...")
      texts = [c["chunk_text"] for c in chunks]
      embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

      for i, chunk in enumerate(chunks):
          chunk["vector"] = embeddings[i].tolist()

      # Upsert to LanceDB
      table_name = f"{domain}_papers"
      if table_name in db.table_names():
          table = db.open_table(table_name)
          table.add(chunks)
      else:
          table = db.create_table(table_name, chunks)

      print(f"Stored {len(chunks)} chunks in {table_name}")
      print(f"Total rows in {table_name}: {len(table)}")
```

#### Flow 3: Generate Training Data

```yaml
id: generate-training-data
namespace: ols-research.training
description: "Generate fine-tuning examples from collected papers using Claude API"

inputs:
  - id: skill_type
    type: STRING
    description: "Which skill to generate examples for"
    defaults: "paper_analysis"
    enum:
      - paper_analysis
      - methodology_critique
      - evidence_synthesis
      - research_gap
      - statistical_reasoning
      - structured_extraction
      - tool_use
      - citation_grounded
  - id: num_examples
    type: INT
    description: "How many examples to generate"
    defaults: 100
  - id: domain
    type: STRING
    defaults: "psychology"

tasks:
  - id: sample-papers
    type: io.kestra.plugin.scripts.python.Script
    description: "Sample papers from LanceDB for example generation"
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install lancedb
    outputFiles:
      - "sampled_papers.jsonl"
    script: |
      import lancedb
      import json
      import random

      db = lancedb.connect("/data/lancedb")
      domain = "{{ inputs.domain }}"
      num = int("{{ inputs.num_examples }}")

      table = db.open_table(f"{domain}_papers")
      # Sample high-quality papers (high citation count)
      results = table.search().limit(num * 3).to_list()
      sampled = random.sample(results, min(num, len(results)))

      with open("sampled_papers.jsonl", 'w') as f:
          for paper in sampled:
              f.write(json.dumps({
                  "title": paper["title"],
                  "abstract": paper["chunk_text"],
                  "doi": paper["doi"],
                  "year": paper["year"],
                  "journal": paper["journal"]
              }) + "\n")

      print(f"Sampled {len(sampled)} papers")

  - id: generate-examples
    type: io.kestra.plugin.scripts.python.Script
    description: "Call Claude API to generate training examples"
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install anthropic
    env:
      ANTHROPIC_API_KEY: "{{ secret('ANTHROPIC_API_KEY') }}"
    outputFiles:
      - "training_examples.jsonl"
    script: |
      import anthropic
      import json
      import time

      client = anthropic.Anthropic()
      skill = "{{ inputs.skill_type }}"

      # Load prompt templates per skill type
      PROMPTS = {
          "paper_analysis": """Given this paper:
      Title: {title}
      Abstract: {abstract}

      Generate a training example as JSON with "messages" array:
      1. system message: "You are a research methodology specialist..."
      2. user message asking to analyze this paper
      3. assistant message with structured analysis covering:
         hypothesis, study design, sample, key variables, findings, limitations, confidence

      Return ONLY valid JSON, no markdown.""",

          "methodology_critique": """Given this paper:
      Title: {title}
      Abstract: {abstract}

      Generate a training example as JSON with "messages" array:
      1. system message
      2. user asking to critique the methodology
      3. assistant identifying: strengths, confounds, sampling issues,
         statistical concerns, missing controls, reproducibility

      Return ONLY valid JSON, no markdown.""",

          # ... additional prompt templates for each skill
      }

      papers = []
      with open("{{ outputs['sample-papers'].outputFiles['sampled_papers.jsonl'] }}", 'r') as f:
          for line in f:
              papers.append(json.loads(line))

      examples = []
      for i, paper in enumerate(papers):
          prompt = PROMPTS.get(skill, PROMPTS["paper_analysis"]).format(
              title=paper["title"],
              abstract=paper["abstract"]
          )

          try:
              response = client.messages.create(
                  model="claude-sonnet-4-5-20250514",
                  max_tokens=2000,
                  messages=[{"role": "user", "content": prompt}]
              )
              result = response.content[0].text

              # Validate JSON
              example = json.loads(result)
              if "messages" in example and len(example["messages"]) >= 3:
                  example["metadata"] = {
                      "source_doi": paper["doi"],
                      "skill": skill,
                      "generated_from": paper["title"]
                  }
                  examples.append(example)

          except Exception as e:
              print(f"Error on paper {i}: {e}")

          time.sleep(0.5)  # Rate limiting

          if (i + 1) % 10 == 0:
              print(f"Generated {len(examples)}/{i+1} examples")

      with open("training_examples.jsonl", 'w') as f:
          for ex in examples:
              f.write(json.dumps(ex) + "\n")

      print(f"Successfully generated {len(examples)} training examples")
```

#### Flow 4: Run Fine-Tune on GPU Server

```yaml
id: run-fine-tune
namespace: ols-research.training
description: "Execute QLoRA fine-tuning on rented GPU server"

inputs:
  - id: gpu_provider
    type: STRING
    defaults: "runpod"
  - id: training_data
    type: FILE
    description: "JSONL training dataset"
  - id: base_model
    type: STRING
    defaults: "Qwen/Qwen2.5-14B-Instruct"
  - id: lora_rank
    type: INT
    defaults: 64
  - id: epochs
    type: INT
    defaults: 2
  - id: learning_rate
    type: STRING
    defaults: "2e-4"

tasks:
  - id: setup-gpu-server
    type: io.kestra.plugin.scripts.python.Script
    description: "Provision GPU server and upload training data"
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install paramiko scp
    env:
      RUNPOD_API_KEY: "{{ secret('RUNPOD_API_KEY') }}"
      GPU_SSH_KEY: "{{ secret('GPU_SSH_KEY') }}"
    script: |
      # This script provisions a RunPod instance,
      # uploads training data, and starts training.
      #
      # The actual training script uses Unsloth:
      #
      # from unsloth import FastLanguageModel
      # model, tokenizer = FastLanguageModel.from_pretrained(
      #     model_name = "Qwen/Qwen2.5-14B-Instruct",
      #     max_seq_length = 4096,
      #     dtype = None,  # auto-detect
      #     load_in_4bit = True,
      # )
      # model = FastLanguageModel.get_peft_model(
      #     model, r = 64, target_modules = [...],
      #     lora_alpha = 128, lora_dropout = 0,
      # )
      # ... training loop with SFTTrainer ...

      print("GPU provisioning flow - implement with your GPU provider's API")
      print("See /docs/gpu-setup.md for step-by-step instructions")

  - id: notify-complete
    type: io.kestra.plugin.notifications.slack.SlackIncomingWebhook
    description: "Notify when training completes"
    url: "{{ secret('SLACK_WEBHOOK') }}"
    payload: |
      {"text": "Fine-tuning complete! Model: {{ inputs.base_model }}, Epochs: {{ inputs.epochs }}"}
```

#### Flow 5: Literature Review (End-to-End Research Pipeline)

```yaml
id: literature-review
namespace: ols-research.research
description: "End-to-end literature review: search → retrieve → analyze → synthesize"

inputs:
  - id: research_question
    type: STRING
    description: "The research question to investigate"
  - id: domains
    type: ARRAY
    itemType: STRING
    defaults: ["psychology", "sociology", "environmentalism", "neuroscience"]
  - id: max_papers
    type: INT
    defaults: 20
  - id: output_format
    type: STRING
    defaults: "markdown"
    enum:
      - markdown
      - json
      - both

tasks:
  - id: search-and-retrieve
    type: io.kestra.plugin.scripts.python.Script
    description: "Search LanceDB collections for relevant papers"
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install lancedb sentence-transformers
    outputFiles:
      - "retrieved_papers.json"
    script: |
      import lancedb
      from sentence_transformers import SentenceTransformer
      import json

      question = "{{ inputs.research_question }}"
      domains = {{ inputs.domains }}
      max_papers = int("{{ inputs.max_papers }}")

      model = SentenceTransformer("BAAI/bge-m3")
      query_embedding = model.encode(question)

      db = lancedb.connect("/data/lancedb")
      all_results = []

      for domain in domains:
          table_name = f"{domain}_papers"
          if table_name not in db.table_names():
              continue

          table = db.open_table(table_name)
          results = table.search(query_embedding).limit(max_papers // len(domains)).to_list()

          for r in results:
              r["search_domain"] = domain
              r.pop("vector", None)  # Don't pass embeddings downstream
              all_results.append(r)

      # Sort by relevance (distance) and deduplicate by DOI
      seen_dois = set()
      unique_results = []
      for r in sorted(all_results, key=lambda x: x.get("_distance", 999)):
          doi = r.get("doi", "")
          if doi and doi in seen_dois:
              continue
          seen_dois.add(doi)
          unique_results.append(r)

      with open("retrieved_papers.json", 'w') as f:
          json.dump(unique_results[:max_papers], f, indent=2, default=str)

      print(f"Retrieved {len(unique_results[:max_papers])} unique papers across {len(domains)} domains")

  - id: analyze-and-synthesize
    type: io.kestra.plugin.scripts.python.Script
    description: "Use fine-tuned model to analyze and synthesize findings"
    containerImage: python:3.11-slim
    beforeCommands:
      - pip install requests
    env:
      MODEL_API_URL: "{{ secret('MODEL_API_URL') }}"
    outputFiles:
      - "literature_review.*"
    script: |
      import json
      import requests

      question = "{{ inputs.research_question }}"

      with open("{{ outputs['search-and-retrieve'].outputFiles['retrieved_papers.json'] }}", 'r') as f:
          papers = json.load(f)

      # Format context for the model
      context = "\n\n".join([
          f"[{i+1}] {p['title']} ({p.get('year', 'n.d.')}). {p.get('journal', '')}.\n"
          f"   {p.get('chunk_text', p.get('abstract', ''))}"
          for i, p in enumerate(papers)
      ])

      # Call fine-tuned model
      prompt = f"""Research Question: {question}

      Retrieved Literature:
      {context}

      Please provide a comprehensive literature review that:
      1. Synthesizes findings across these studies
      2. Identifies points of consensus and disagreement
      3. Notes methodological strengths and limitations
      4. Identifies research gaps
      5. Provides a confidence assessment for key conclusions
      6. Cites sources using [N] notation

      Focus on evidence quality and cross-domain connections."""

      # This calls your fine-tuned model's API endpoint
      response = requests.post(
          "{{ secret('MODEL_API_URL') }}/v1/chat/completions",
          json={
              "model": "ols-research-v1",
              "messages": [
                  {"role": "system", "content": "You are a research methodology specialist."},
                  {"role": "user", "content": prompt}
              ],
              "max_tokens": 4000,
              "temperature": 0.3
          }
      )

      result = response.json()
      review_text = result["choices"][0]["message"]["content"]

      # Save as markdown
      with open("literature_review.md", 'w') as f:
          f.write(f"# Literature Review: {question}\n\n")
          f.write(f"*Generated by OLS Research System*\n")
          f.write(f"*Papers analyzed: {len(papers)}*\n\n")
          f.write(review_text)
          f.write("\n\n---\n\n## References\n\n")
          for i, p in enumerate(papers):
              f.write(f"[{i+1}] {', '.join(p.get('authors', '').split(', ')[:3])} "
                     f"({p.get('year', 'n.d.')}). {p['title']}. "
                     f"*{p.get('journal', '')}*. {p.get('doi', '')}\n\n")

      print(f"Literature review generated: {len(review_text)} characters")
```

---

## PART 5: BUILD SEQUENCE (Week-by-Week)

### Phase 1: Foundation (Weeks 1-2)

```
□ Deploy Kestra on VPS (Docker Compose)
□ Create GitHub repo: optimal-living-systems/research-system
□ Obtain API keys:
  □ OpenAlex (free, just register email)
  □ Semantic Scholar (free API key)
  □ Anthropic API (for training data generation)
  □ RunPod or Modal (for GPU)
□ Set up Kestra secrets for all API keys
□ Create namespace structure in Kestra
□ Write README.md for the GitHub repo
□ Install LanceDB on Kestra server
□ Test BGE-M3 model loading (CPU is fine for now)
```

### Phase 2: Data Collection (Weeks 3-4)

```
□ Deploy collect-openalex flow
□ Run initial collection for psychology domain (start with SDT)
□ Verify data quality — spot check 50 papers
□ Expand to all 4 domains
□ Deploy collect-semantic-scholar flow (supplementary)
□ Deploy collect-pubmed-oa flow (for full texts)
□ Total target: 230,000 abstracts collected
□ Document collection methodology for OSF
```

### Phase 3: Processing Pipeline (Weeks 5-6)

```
□ Deploy chunk-and-embed flow
□ Process psychology papers first (test end-to-end)
□ Verify LanceDB queries return relevant results
□ Process remaining 3 domains
□ Build quality-filter flow (remove low-citation, retracted)
□ Test basic RAG: ask question → get relevant papers
□ Total target: 570,000 chunks embedded in LanceDB
```

### Phase 4: RAG Testing (Week 7)

```
□ Build simple query interface (can be a Python script or Kestra flow)
□ Test 50 research questions across all domains
□ Measure retrieval relevance (are the right papers coming back?)
□ Tune search parameters (top-K, reranking, hybrid vs pure vector)
□ Build cross-domain index
□ Test cross-domain queries
□ Document RAG performance baseline
```

### Phase 5: Training Data Generation (Weeks 8-10)

```
□ Deploy generate-training-data flow
□ Generate 500 paper_analysis examples → human review quality
□ If quality good: scale to 8,000 paper_analysis examples
□ Generate all 8 skill types (see distribution in Part 2)
□ Run automated quality filters
□ Human review 10% sample (~3,500 examples)
□ Create held-out test set (1,000 examples, never train on these)
□ Total target: 35,000 verified training examples
```

### Phase 6: Fine-Tuning (Weeks 11-12)

```
□ Prepare dataset in ChatML format
□ Rent A100 80GB on RunPod
□ Install Unsloth + dependencies on GPU server
□ Run QLoRA training (estimated 10-20 hours)
□ Evaluate on held-out test set
□ Compare to base Qwen 2.5 14B (measure improvement)
□ If results unsatisfactory: adjust data, retrain
□ Merge LoRA weights → publish to Hugging Face
□ Deploy for inference (Modal serverless or dedicated GPU)
```

### Phase 7: Integration (Weeks 13-16)

```
□ Deploy literature-review flow (end-to-end)
□ Deploy paper-analysis flow
□ Deploy methodology-audit flow
□ Build cross-domain-synthesis flow
□ Test full system with 20 real research questions
□ Measure end-to-end quality
□ Write documentation for all flows
□ Publish methodology on OSF
□ Write blog post / announcement
```

---

## PART 6: GITHUB REPOSITORY STRUCTURE

```
optimal-living-systems/research-system/
│
├── README.md                    # Project overview, mission, how to contribute
├── LICENSE                      # AGPL-3.0 for code
├── CONTRIBUTING.md              # How to contribute
│
├── docs/
│   ├── architecture.md          # System architecture (this document)
│   ├── data-sources.md          # Where data comes from, access methods
│   ├── rag-design.md            # RAG collection schemas, chunking strategy
│   ├── fine-tuning.md           # Model selection, training methodology
│   ├── evaluation.md            # How we measure quality
│   ├── gpu-setup.md             # Step-by-step GPU rental guide
│   └── kestra-setup.md          # Kestra deployment instructions
│
├── kestra-flows/
│   ├── collection/
│   │   ├── collect-openalex.yml
│   │   ├── collect-semantic-scholar.yml
│   │   ├── collect-pubmed-oa.yml
│   │   └── collect-preprints.yml
│   ├── processing/
│   │   ├── chunk-and-embed.yml
│   │   ├── quality-filter.yml
│   │   └── index-to-lancedb.yml
│   ├── training/
│   │   ├── generate-training-data.yml
│   │   ├── validate-training-data.yml
│   │   ├── run-fine-tune.yml
│   │   └── evaluate-model.yml
│   ├── research/
│   │   ├── literature-review.yml
│   │   ├── paper-analysis.yml
│   │   ├── methodology-audit.yml
│   │   └── cross-domain-synthesis.yml
│   └── maintenance/
│       ├── update-citations.yml
│       ├── check-retractions.yml
│       └── backup-lancedb.yml
│
├── schemas/
│   ├── paper-chunk.json         # LanceDB chunk schema
│   ├── training-example.json    # Training data schema
│   ├── cross-domain-index.json  # Cross-domain concept schema
│   └── evaluation-result.json   # Eval output schema
│
├── prompts/
│   ├── paper-analysis.txt       # Prompt template for generating paper analysis training data
│   ├── methodology-critique.txt
│   ├── evidence-synthesis.txt
│   ├── research-gap.txt
│   ├── statistical-reasoning.txt
│   ├── structured-extraction.txt
│   ├── tool-use.txt
│   └── citation-grounded.txt
│
├── evaluation/
│   ├── test-questions.jsonl     # Held-out test set
│   ├── baseline-results.json    # Base model performance
│   ├── finetuned-results.json   # Fine-tuned model performance
│   └── eval-report.md           # Human-readable evaluation report
│
├── scripts/
│   ├── setup-lancedb.py         # Initialize LanceDB collections
│   ├── test-rag.py              # Quick RAG test script
│   ├── format-training-data.py  # Convert to ChatML format
│   └── merge-lora.py            # Merge LoRA weights for deployment
│
└── data/
    ├── .gitkeep                 # Data stored on server, not in git
    └── README.md                # Explains data storage location
```

---

## PART 7: COST ESTIMATE (DETAILED)

| Item | One-Time | Monthly | Notes |
|------|----------|---------|-------|
| **Kestra VPS** | $0 | $10-20 | Small VPS (2 CPU, 4GB RAM), Hetzner or DigitalOcean |
| **LanceDB storage VPS** | $0 | $20-40 | Need disk space for vectors (~50GB), can share with Kestra |
| **OpenAlex API** | $0 | $0 | Free, unlimited with polite pool |
| **Semantic Scholar API** | $0 | $0 | Free tier: 100 req/5min |
| **Claude API (training data gen)** | $100-300 | $0 | 35K examples × ~2K tokens × Sonnet pricing |
| **GPU: Fine-tuning (RunPod A100)** | $40-80 | $0 | ~20 hours × $2-4/hr, one-time per training run |
| **GPU: Inference (Modal)** | $0 | $30-100 | Pay per second, depends on usage |
| **BGE-M3 embedding** | $0 | $0 | Runs on CPU on Kestra VPS |
| **Domain (optional)** | $12/yr | $0 | research.optimallivingsystems.org |
| **GitHub** | $0 | $0 | Public repo, free |
| **OSF registration** | $0 | $0 | Free |
| **TOTAL** | **$150-400** | **$60-160** | |

---

## PART 8: SUCCESS METRICS

How you know this is working:

| Metric | Baseline (no fine-tune) | Target (with fine-tune) | How to Measure |
|--------|------------------------|------------------------|----------------|
| Paper analysis accuracy | ~70% | >90% | Compare to human analysis on 100 papers |
| Methodology critique validity | ~60% | >85% | Expert review of 50 critiques |
| Synthesis coherence | ~65% | >85% | Human rating 1-5 scale on 30 syntheses |
| Tool use correctness | ~50% | >80% | Automated check on 200 test queries |
| Citation accuracy | ~75% | >95% | Verify claims match cited sources |
| Hallucination rate | ~15% | <3% | Check unsupported claims in 100 responses |
| Cross-domain connection quality | ~40% | >75% | Expert rating on 30 cross-domain queries |
| End-to-end lit review usefulness | ~50% | >80% | Would a researcher use this? (human eval) |
