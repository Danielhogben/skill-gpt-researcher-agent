---
name: gpt-researcher-agent
description: >
  Autonomous research agent using GPT Researcher. Run deep research on any topic,
  generate structured reports (papers, blogs, summaries), manage sources, and
  export results as PDF/Markdown/JSON.
  Use when: "research topic," "gpt researcher," "deep research," "generate report,"
  "research sources," "research paper," "blog post research."
version: 1.0.0
author: user
metadata:
  hermes:
    tags: [research, gpt-researcher, reports, sources, automation]
    category: productivity
    requires_toolsets: [terminal]
allowed-tools: Bash(python3:*) Bash(pip:*) Bash(curl:*) Read Write
---

# GPT Researcher Agent

Autonomous research agent using [GPT Researcher](https://github.com/assafelovic/gpt-researcher) — an AI agent that conducts comprehensive research across multiple sources and generates structured reports.

## Commands

### Run research

```bash
python3 gpt_researcher_agent.py research "What are the latest advances in quantum computing?"
python3 gpt_researcher_agent.py research "Compare Rust vs Go for systems programming" --type report
python3 gpt_researcher_agent.py research "History of Linux kernel development" --sources 10
```

Conduct research on a topic. Searches web, academic, and code sources, then generates a structured report.

### Manage sources

```bash
python3 gpt_researcher_agent.py sources list
python3 gpt_researcher_agent.py sources add arxiv
python3 gpt_researcher_agent.py sources add github
python3 gpt_researcher_agent.py sources remove <name>
python3 gpt_researcher_agent.py sources configure
```

Configure which sources GPT Researcher uses: web search, arXiv, GitHub, local documents.

### Generate reports

```bash
python3 gpt_researcher_agent.py report "topic" --type research_report
python3 gpt_researcher_agent.py report "topic" --type blog_post
python3 gpt_researcher_agent.py report "topic" --type summary_report
python3 gpt_researcher_agent.py report "topic" --type outline_report
```

Generate specific report types from research data.

### Deep research mode

```bash
python3 gpt_researcher_agent.py deep "Analyze the current state of AGI safety research"
python3 gpt_researcher_agent.py deep "Compare container orchestration solutions" --sub-queries 5
```

Deep research mode: breaks the topic into sub-queries, researches each independently, then synthesizes findings.

### Export results

```bash
python3 gpt_researcher_agent.py export <research-id>
python3 gpt_researcher_agent.py export <research-id> --format markdown
python3 gpt_researcher_agent.py export <research-id> --format pdf
python3 gpt_researcher_agent.py export <research-id> --format json
python3 gpt_researcher_agent.py export <research-id> --dest /path/to/output
```

Export research results in various formats.

### Configure settings

```bash
python3 gpt_researcher_agent.py config
python3 gpt_researcher_agent.py config --llm claude-sonnet-4-20250514
python3 gpt_researcher_agent.py config --report-type research_report
python3 gpt_researcher_agent.py config --source-count 10
```

View or update configuration (LLM provider, report type, source count, etc.).

## Report Types

| Type | Description |
|------|-------------|
| `research_report` | Full academic-style research report with citations |
| `summary_report` | Concise executive summary |
| `blog_post` | Blog-formatted article with engaging structure |
| `outline_report` | Structured outline for further development |
| `resource_report` | Curated list of resources with annotations |

## Sources

- **Web** — general web search (default)
- **ArXiv** — academic papers and preprints
- **GitHub** — code repositories and documentation
- **Local** — local documents in a specified directory

## Workflow

### Quick research

1. Run: `python3 gpt_researcher_agent.py research "your topic here"`
2. Report is generated and saved to the `reports/` directory
3. Export: `python3 gpt_researcher_agent.py export <id> --format markdown`

### Deep research

1. Run: `python3 gpt_researcher_agent.py deep "complex topic" --sub-queries 5`
2. Monitor sub-query progress in the output
3. Final synthesized report combines all findings

## Configuration

Set environment variables:
- `ANTHROPIC_API_KEY` for Claude models
- `OPENAI_API_KEY` for GPT models
- `TAVILY_API_KEY` for enhanced web search (optional)

## Notes

- GPT Researcher requires Python 3.10+ and an LLM API key
- First run will install dependencies via pip
- Reports include source citations and references
- Deep research mode takes longer but produces more thorough analysis
- The `reports/` directory stores all generated reports
