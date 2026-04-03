# Internshala Autonomous Hiring Agent

An intelligent, autonomous hiring pipeline capable of parsing, scoring, and evaluating 1,000+ candidates at scale. Built as a modular microservices architecture.

---

## Architecture Overview
┌─────────────────────────────────────────────────────────────┐
│                    HIRING AGENT PIPELINE                     │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  DOM Inject  │───▶│  Intelligence│───▶│  Anti-Cheat  │  │
│  │  (Collector) │    │  (Scorer)    │    │  (Validator) │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│          │                  │                   │           │
│          ▼                  ▼                   ▼           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PostgreSQL State Store                   │  │
│  │  candidates | scores | flags | audit_log              │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                               │
│                            ▼                               │
│              ┌─────────────────────────┐                   │
│              │  Local Vector Embeddings│                   │
│              │  (all-MiniLM-L6-v2)     │                   │
│              └─────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
### Components

| Service | File | Responsibility |
|---|---|---|
| **Intelligence Module** | `intelligence.py` | Parses CSV, cleans data, scores & tiers candidates |
| **Anti-Cheat Module** | `anti_cheat.py` | Semantic similarity + timing analysis to detect AI-generated answers |
| **Scraper Probe** | `scraper_test.py` | Documents bot-protection encountered on target platform |

---

## Why DOM Injection Instead of Scraping

Platforms like Internshala deploy **Google reCAPTCHA v3**, Cloudflare edge WAFs, and IP rate-limiting on all authenticated endpoints. `scraper_test.py` documents this failure in production.

The production design therefore uses a **browser extension (DOM injection)** approach:
- The agent runs as a content script inside a real, authenticated Chrome session
- It reads candidate data directly from the rendered DOM — no HTTP scraping required
- All bot-detection is bypassed because the requests originate from a genuine browser with valid session cookies

---

## Scoring Algorithm

Each candidate starts at a base score of **50/100**. Adjustments:

| Signal | Delta |
|---|---|
| GitHub profile present | +10 |
| Code block in answer (per block, max +30) | +15 |
| Inline code reference | +5 |
| Missing GitHub link | -20 |
| AI boilerplate phrase (per phrase, max -30) | -8 |
| Answer < 20 words | -10 |
| Answer empty / < 5 words | -25 |
| Missing email | -10 |

### Tier Classification

| Tier | Score Range |
|---|---|
| **Fast-Track** | ≥ 70 |
| **Standard** | 45 – 69 |
| **Review** | 25 – 44 |
| **Reject** | < 25 |

---

## Anti-Cheat Design

Two independent checks run per candidate:

1. **Semantic Similarity** — Encodes the answer and a known AI-generated baseline using `all-MiniLM-L6-v2`. Cosine similarity > 80% triggers a flag.
2. **Timing Analysis** — If a response of > 50 words was submitted in under 60 seconds, it is flagged as an impossibly fast human response.

Both checks run locally — no external API calls, no data leaves the machine.

---

## PostgreSQL State Schema (Production)
```sql
CREATE TABLE candidates (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE,
    github        TEXT,
    raw_answer    TEXT,
    score         NUMERIC(5,2),
    tier          TEXT,
    ai_flagged    BOOLEAN DEFAULT FALSE,
    timing_flagged BOOLEAN DEFAULT FALSE,
    processed_at  TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Quick Start
```bash
# Clone and set up
git clone https://github.com/YOUR_USERNAME/internshala-hiring-agent.git
cd internshala-hiring-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the intelligence (scoring) module
python intelligence.py

# Run the anti-cheat module
python anti_cheat.py

# Run the scraper probe (documents bot-protection)
python scraper_test.py
```

---

## Tech Stack

- **Python 3.11+**
- **pandas** — data ingestion & cleaning
- **sentence-transformers** — local vector embeddings (`all-MiniLM-L6-v2`)
- **scikit-learn** — cosine similarity
- **numpy** — numerical operations
- **requests** — HTTP probing
- **PostgreSQL** *(production)* — persistent state store

---

## License

MIT