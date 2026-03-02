# Data Sources

## Primary Sources

### OpenAlex (Primary)
- **URL:** https://openalex.org
- **API:** https://api.openalex.org
- **Access:** Free, no key required (register email for polite pool)
- **Coverage:** 250M+ scholarly works, all disciplines
- **License:** CC0 (public domain)
- **Rate Limit:** 10 req/sec (polite pool), 1 req/sec (anonymous)
- **Use:** Abstracts, metadata, citation counts, concept tagging
- **Documentation:** https://docs.openalex.org

### Semantic Scholar
- **URL:** https://www.semanticscholar.org
- **API:** https://api.semanticscholar.org
- **Access:** Free API key (request at https://www.semanticscholar.org/product/api)
- **Coverage:** 200M+ papers, strong in CS/bio/social sciences
- **Rate Limit:** 1 req/sec (free), 10 req/sec (with key)
- **Use:** Supplementary metadata, citation graphs, influential citations
- **Documentation:** https://api.semanticscholar.org/api-docs/

### PubMed / PMC Open Access
- **URL:** https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/
- **Access:** Free, bulk download available
- **Coverage:** 8M+ full-text biomedical/life science articles
- **License:** Various (CC-BY, CC0, etc. — check per article)
- **Use:** Full-text papers for neuroscience and psychology
- **Documentation:** https://www.ncbi.nlm.nih.gov/home/develop/api/

### Preprint Servers
- **PsyArXiv:** https://psyarxiv.com (psychology preprints)
- **SocArXiv:** https://socopen.org (sociology/social science preprints)
- **EarthArXiv:** https://eartharxiv.org (earth/environment preprints)
- **bioRxiv:** https://www.biorxiv.org (biology/neuroscience preprints)
- **Access:** All free, most CC-BY
- **Use:** Latest research before journal publication

### Unpaywall
- **URL:** https://unpaywall.org
- **API:** https://api.unpaywall.org
- **Access:** Free (register email)
- **Use:** Resolve DOIs to open access full-text URLs
- **Documentation:** https://unpaywall.org/products/api

## Excluded Sources

| Source | Reason |
|--------|--------|
| Sci-Hub | Legal risk incompatible with Open Science nonprofit status |
| Web of Science | Proprietary, expensive, data not redistributable |
| Scopus | Proprietary, expensive, restrictive API terms |

## Data Collection Ethics

- We only collect openly licensed or public domain content
- We respect API rate limits and use polite pool headers
- We do not redistribute full-text papers (only metadata and our derived analyses)
- We track and remove retracted papers
- All collection methods are documented and reproducible
