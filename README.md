# 🏥 Drug Safety Intelligence MCP

> Intelligent drug safety analysis powered by FDA data, AI insights, and Model Context Protocol

---

## 📸 Screenshots

<!-- Add screenshots here -->

```
[Web UI Screenshot]
[Console UI Screenshot]
[MCP Tools in Action]
```

---

## ✨ Features

```
┌─────────────────────────────────────────────────┐
│         AI Assistant (Claude, ChatGPT)          │
└────────────────┬────────────────────────────────┘
                 │ MCP Protocol
┌────────────────▼────────────────────────────────┐
│       Drug Safety Intelligence MCP Server       │
├─────────────────────────────────────────────────┤
│  🔧 Tools Available:                            │
│    • drug_safety_profile                        │
│    • check_drug_recalls                         │
│    • compare_drug_safety                        │
├─────────────────────────────────────────────────┤
│  📊 Data Sources:                               │
│    • FDA Adverse Events API                     │
│    • FDA Recalls/Enforcement API                │
│    • OpenAI GPT-3.5 Turbo                       │
│    • SQLite Cache (24hr TTL)                    │
└─────────────────────────────────────────────────┘
```

### 🔧 MCP Tools

- **`drug_safety_profile`** - Comprehensive safety analysis with AI insights
- **`check_drug_recalls`** - Active FDA recalls and classifications
- **`compare_drug_safety`** - Side-by-side comparison of 2-3 drugs

### 🚀 Technical Capabilities

- ⚡ **Smart Caching** - SQLite-based with 24-hour TTL for performance
- 🎯 **AI-Powered Summaries** - GPT-5-nano generates patient-friendly insights
- 📊 **Real-time FDA Data** - Live adverse events and recall information
- 🛡️ **Type Safety** - Pydantic validation for all inputs/outputs
- ⏱️ **Rate Limiting** - Respects FDA API limits (60 req/min)

### 💻 User Interfaces

- **Web UI (Gradio)** - Interactive dashboard with natural language queries
- **Console CLI** - Terminal-based interface with REPL mode
- **MCP Integration** - Direct integration with AI assistants like Claude

---

## 🎭 Example Usage

### In Claude Desktop (MCP)

### In Claude Desktop (MCP)

```
"Tell me about Ibuprofen's safety"
→ Calls drug_safety_profile("Ibuprofen")
→ Returns AI analysis, side effects, adverse events, recalls

"Compare Aspirin, Ibuprofen, and Acetaminophen"
→ Calls compare_drug_safety([...])
→ Returns comparison table with AI recommendation
```

### Web UI

```bash
python run_web_ui.py
# Open http://localhost:7860
# Ask: "Tell me about Metformin's safety"
```

### Console CLI

```bash
python run_console.py
🏥 > safety Ibuprofen
🏥 > compare Aspirin Ibuprofen Naproxen
🏥 > ask "Is Lisinopril safe?"
```

---

## 📦 Installation & Setup

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run

**MCP Server:**

```bash
python src/mcp_server.py
```

**Web UI:**

```bash
python run_web_ui.py
```

**Console:**

```bash
python run_console.py
```

---

## ⚙️ Configuration

Environment variables in `.env`:

```bash
OPENAI_API_KEY=your_key_here          # Required for AI summaries
FDA_API_URL=https://api.fda.gov/drug  # Default FDA API
CACHE_DB_PATH=data/cache.db           # Cache database location
CACHE_TTL_HOURS=24                    # Cache validity period
LOG_LEVEL=INFO                        # Logging level
```

---

## 🙏 Acknowledgments

- **FDA OpenFDA API** for public drug safety data
- **Model Context Protocol** by Anthropic
- **OpenAI** for AI-powered summaries
