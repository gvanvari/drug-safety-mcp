# Drug Safety Intelligence MCP - MVP Specification

## Overview

A Model Context Protocol (MCP) server that provides intelligent drug safety analysis by integrating three key resources:

1. **FDA API** - Real-time adverse event & recall data
2. **SQLite Cache** - Local data persistence & rate-limiting optimization
3. **Reference Data (JSON)** - Pre-loaded drug information for validation
4. **OpenAI API** - Intelligent summarization & insights generation

---

## Problem Statement

When researching medication safety, users face:

- ❌ Overwhelming raw FDA adverse event data
- ❌ No clear summary of safety concerns
- ❌ Manual parsing of complex data
- ❌ Risk of repeated API calls

---

## Solution: Three MCP Tools

### **Tool 1: `drug_safety_profile`**

Returns comprehensive safety analysis for a given drug.

**Input:**

```json
{
  "drug_name": "Ibuprofen"
}
```

**Process:**

1. Validate drug name against reference data
2. Check SQLite cache (24-hour TTL)
3. If not cached, query FDA API for:
   - Adverse events (last 2 years)
   - Active recalls
   - Demographic breakdown
4. Call OpenAI to generate intelligent summary
5. Store result in cache
6. Return structured response

**Output:**

```json
{
  "drug_name": "Ibuprofen",
  "safety_score": 78,
  "summary": "Ibuprofen commonly causes gastrointestinal issues, especially in patients over 65. Most events are mild-to-moderate. No serious safety trends detected in 2024.",
  "adverse_events_count": 15432,
  "top_side_effects": ["Nausea", "Stomach pain", "Headache"],
  "high_risk_demographics": ["Elderly (65+)", "Patients with GI history"],
  "active_recalls": 0,
  "data_freshness": "3 hours old (cached)",
  "cached": true
}
```

---

### **Tool 2: `check_drug_recalls`**

Quick recall status check.

**Input:**

```json
{
  "drug_name": "Aspirin"
}
```

**Output:**

```json
{
  "drug_name": "Aspirin",
  "recalls": [],
  "status": "No active recalls"
}
```

---

### **Tool 3: `compare_drug_safety`**

Compare safety profiles of 2-3 drugs.

**Input:**

```json
{
  "drugs": ["Ibuprofen", "Naproxen", "Acetaminophen"]
}
```

**Output:**

```json
{
  "comparison": [
    {
      "drug_name": "Ibuprofen",
      "safety_score": 78,
      "top_concern": "GI issues in elderly"
    },
    {
      "drug_name": "Naproxen",
      "safety_score": 71,
      "top_concern": "Cardiovascular risk in long-term use"
    },
    {
      "drug_name": "Acetaminophen",
      "safety_score": 82,
      "top_concern": "Liver toxicity with overdose"
    }
  ],
  "recommendation": "Acetaminophen has best safety profile. Ibuprofen good for short-term use. Avoid Naproxen for cardiovascular patients."
}
```

---

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ (MCP Request)
       ↓
┌─────────────────────────┐
│   MCP Server            │
│  (FastMCP)              │
└──────┬────────────────┬─┘
       │                │
       ↓                ↓
   ┌────────────┐  ┌──────────────────┐
   │ SQLite     │  │  Service Layer   │
   │ Cache      │  │ (models, tools)  │
   └────────────┘  └────┬─────────┬───┘
                         │         │
                    ┌────↓──┐  ┌──↓─────────┐
                    │ FDA   │  │  OpenAI    │
                    │ API   │  │  API       │
                    └───────┘  └────────────┘
                         │
                    ┌────↓──────┐
                    │ Reference │
                    │ Data (JSON)│
                    └────────────┘
```

---

## Resources Used (3 resources for recruiter impression)

| Resource           | Purpose                                   | Why It Matters                       |
| ------------------ | ----------------------------------------- | ------------------------------------ |
| **FDA API**        | Authoritative adverse event & recall data | Real-world integration               |
| **SQLite Cache**   | Local persistence + rate-limiting         | Shows optimization thinking          |
| **Reference Data** | Pre-loaded drugs for validation           | Intelligent design + data efficiency |
| **OpenAI API**     | Intelligent summarization                 | LLM integration showcase             |

---

## Tech Stack

- **Framework:** FastMCP (MCP SDK for Python)
- **Validation:** Pydantic (strict type safety)
- **Database:** SQLite (built-in, no external deps)
- **API Clients:** `httpx` (FDA API), `openai` (GPT-4)
- **Data Format:** JSON reference data
- **Python Version:** 3.10+

---

## Key Features

✅ **Rate-Limit Aware** — Caching prevents hammering FDA API  
✅ **Error Handling** — Graceful failures, meaningful error messages  
✅ **Pydantic Validation** — Strict input/output types  
✅ **Multi-Resource Integration** — Shows full-stack thinking  
✅ **AI-Powered Insights** — Demonstrates LLM orchestration  
✅ **Production-Ready** — Error handling, logging, timeouts

---

## MVP Timeline (3-4 hours)

| Phase                       | Time   | Tasks                                             |
| --------------------------- | ------ | ------------------------------------------------- |
| **1. Setup**                | 30 min | Project structure, dependencies, MCP boilerplate  |
| **2. Models & Services**    | 45 min | Pydantic models, cache service, FDA service       |
| **3. Reference Data**       | 20 min | Create drugs_reference.json with ~50 common drugs |
| **4. Tools Implementation** | 60 min | Implement 3 MCP tools, integrate OpenAI           |
| **5. Testing & Polish**     | 25 min | Error handling, testing, documentation            |

---

## Files Structure

```
drug_safety_mcp/
├── src/
│   ├── server.py              # Main MCP server entry point
│   ├── models.py              # Pydantic models
│   ├── fda_service.py         # FDA API integration
│   ├── cache_service.py       # SQLite caching layer
│   ├── ai_service.py          # OpenAI integration
│   └── reference_data.py      # Reference data loader
├── data/
│   ├── drugs_reference.json   # Pre-loaded drug data
│   └── cache.db               # SQLite (created at runtime)
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # Usage guide
└── MVP.md                    # This file
```

---

## Recruiter Impression Checklist

- ✅ Understands MCP architecture (multiple tools, resource orchestration)
- ✅ Real API integration (FDA + OpenAI)
- ✅ Data persistence (SQLite)
- ✅ Type safety (Pydantic)
- ✅ Performance optimization (caching)
- ✅ Error handling & validation
- ✅ LLM integration (shows AI knowledge)
- ✅ Clear problem-solving approach

---

## Next Steps (Post-MVP)

- Add drug interaction checker
- Implement user preferences/saved searches
- Add web UI dashboard
- Deploy to cloud (Vercel, Railway)
- Add authentication for production use
