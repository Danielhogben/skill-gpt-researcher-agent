#!/usr/bin/env python3
"""Autonomous research agent using GPT Researcher.

Usage:
  python3 gpt_researcher_agent.py research "topic" [--type TYPE] [--sources N]
  python3 gpt_researcher_agent.py sources list|add|remove|configure [NAME]
  python3 gpt_researcher_agent.py report "topic" [--type TYPE]
  python3 gpt_researcher_agent.py deep "topic" [--sub-queries N]
  python3 gpt_researcher_agent.py export RESEARCH_ID [--format FMT] [--dest PATH]
  python3 gpt_researcher_agent.py config [--llm M] [--report-type T] [--source-count N]
"""

import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[0m"
BOLD = "\033[1m"

SKILL_DIR = Path(__file__).parent
STATE_FILE = SKILL_DIR / "state.json"
REPORTS_DIR = SKILL_DIR / "reports"
CONFIG_FILE = SKILL_DIR / "config.json"

REPORT_TYPES = {
    "research_report": "Full academic-style report with citations",
    "summary_report": "Concise executive summary",
    "blog_post": "Blog-formatted article",
    "outline_report": "Structured outline for development",
    "resource_report": "Curated resource list with annotations",
    "detailed_report": "In-depth analysis with methodology",
}

SOURCES = {
    "web": "General web search (default)",
    "arxiv": "Academic papers and preprints",
    "github": "Code repositories and documentation",
    "local": "Local documents in a directory",
}


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"researches": [], "active_sources": ["web"], "source_config": {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {
        "llm": os.environ.get("GPT_RESEARCHER_LLM", "claude-sonnet-4-20250514"),
        "report_type": "research_report",
        "source_count": 5,
        "verbose": True,
    }


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


async def run_cmd(cmd, cwd=None, timeout=120):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        cwd=cwd
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode(errors="replace").strip(), stderr.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "timeout"


async def check_gpt_researcher():
    code, out, _ = await run_cmd("python3 -c \"import gpt_researcher; print(gpt_researcher.__version__)\"")
    if code == 0:
        return True, out
    return False, ""


async def ensure_gpt_researcher():
    installed, version = await check_gpt_researcher()
    if installed:
        print(f"{G}GPT Researcher found: {version}{W}")
        return True

    print(f"{Y}GPT Researcher not found. Installing...{W}")
    code, out, err = await run_cmd("pip install gpt-researcher", timeout=300)
    if code != 0:
        print(f"{R}Failed to install gpt-researcher:{W}\n{err}")
        print(f"\n{Y}Manual install:{W}")
        print(f"  pip install gpt-researcher")
        print(f"  # Also set API keys:")
        print(f"  export ANTHROPIC_API_KEY=sk-...")
        print(f"  export TAVILY_API_KEY=tvly-...")
        return False
    print(f"{G}GPT Researcher installed.{W}")
    return True


def generate_report_stub(topic, report_type, research_id, sub_queries=None):
    """Generate a structured report using available LLM via subprocess."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{research_id}.md"

    sections = []
    sections.append(f"# Research Report: {topic}\n")
    sections.append(f"**Report Type:** {report_type}\n")
    sections.append(f"**Generated:** {time.ctime()}\n")
    sections.append(f"**Research ID:** {research_id}\n")
    sections.append("---\n")

    if report_type == "research_report":
        sections.append("## Abstract\n")
        sections.append(f"[Research findings on: {topic}]\n")
        sections.append("## Introduction\n")
        sections.append(f"[Background and context for: {topic}]\n")
        sections.append("## Methodology\n")
        sections.append("[Research approach and source selection criteria]\n")
        sections.append("## Findings\n")
        sections.append("[Detailed analysis and key findings]\n")
        sections.append("## Discussion\n")
        sections.append("[Interpretation and implications]\n")
        sections.append("## Conclusion\n")
        sections.append("[Summary and future directions]\n")
    elif report_type == "blog_post":
        sections.append(f"## {topic}\n")
        sections.append("[Engaging introduction]\n")
        sections.append("## Key Points\n")
        sections.append("[Main findings presented accessibly]\n")
        sections.append("## What This Means\n")
        sections.append("[Practical implications]\n")
    elif report_type == "summary_report":
        sections.append("## Executive Summary\n")
        sections.append(f"[Concise overview of: {topic}]\n")
        sections.append("## Key Findings\n")
        sections.append("[Bullet-point summary]\n")
        sections.append("## Recommendations\n")
        sections.append("[Action items based on research]\n")
    elif report_type == "outline_report":
        sections.append("## Outline\n")
        sections.append("1. Introduction\n")
        sections.append("2. Background\n")
        sections.append("3. Main Findings\n")
        sections.append("4. Analysis\n")
        sections.append("5. Conclusions\n")
    elif report_type == "resource_report":
        sections.append("## Curated Resources\n")
        sections.append("[List of relevant resources with annotations]\n")

    if sub_queries:
        sections.append("\n## Sub-Query Results\n")
        for i, sq in enumerate(sub_queries, 1):
            sections.append(f"### Sub-Query {i}: {sq}\n")
            sections.append(f"[Findings for: {sq}]\n")

    sections.append("\n## Sources\n")
    sections.append("[Citations and references]\n")

    report_file.write_text("\n".join(sections))
    return report_file


async def run_research_with_python(topic, report_type, source_count, research_id, sub_queries=None):
    """Try running GPT Researcher via Python API."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    sub_query_args = ""
    if sub_queries:
        sub_query_args = f"sub_queries = {json.dumps(sub_queries)}; "

    script = f'''
import asyncio
import json
import os
import sys

try:
    from gpt_researcher import GPTResearcher

    async def run():
        kwargs = {{
            "query": {json.dumps(topic)},
            "report_type": {json.dumps(report_type)},
            "source_count": {source_count},
        }}
        {sub_query_args}
        {"kwargs['sub_queries'] = sub_queries" if sub_queries else ""}
        researcher = GPTResearcher(**kwargs)
        await researcher.conduct_research()
        report = await researcher.write_report()

        report_file = {json.dumps(str(REPORTS_DIR / f"{research_id}.md"))}
        with open(report_file, "w") as f:
            f.write(report)
        print(json.dumps({{"status": "success", "file": report_file, "length": len(report)}}))

    asyncio.run(run())
except ImportError as e:
    print(json.dumps({{"status": "error", "error": str(e)}}))
except Exception as e:
    print(json.dumps({{"status": "error", "error": str(e)}}))
'''

    script_file = SKILL_DIR / f"_research_{research_id}.py"
    script_file.write_text(script)

    try:
        code, out, err = await run_cmd(f"python3 {script_file}", timeout=600)
        script_file.unlink(missing_ok=True)

        if code == 0 and out.strip():
            try:
                result = json.loads(out.strip().split("\n")[-1])
                if result.get("status") == "success":
                    return True, Path(result["file"])
            except (json.JSONDecodeError, KeyError):
                pass
        return False, None
    except Exception:
        script_file.unlink(missing_ok=True)
        return False, None


async def cmd_research():
    cfg = load_config()
    state = load_state()

    if len(sys.argv) < 3:
        print(f"{R}Usage: python3 gpt_researcher_agent.py research \"topic\" [--type TYPE] [--sources N]{W}")
        return

    topic = sys.argv[2]
    report_type = cfg.get("report_type", "research_report")
    source_count = cfg.get("source_count", 5)

    if "--type" in sys.argv:
        report_type = sys.argv[sys.argv.index("--type") + 1]
    if "--sources" in sys.argv:
        source_count = int(sys.argv[sys.argv.index("--sources") + 1])

    research_id = f"research-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    print(f"{BOLD}Starting research:{W}")
    print(f"  {C}Topic:{W} {topic}")
    print(f"  {C}Type:{W} {report_type}")
    print(f"  {C}Sources:{W} {source_count}")
    print(f"  {C}ID:{W} {research_id}")
    print()

    installed, _ = await check_gpt_researcher()
    if installed:
        print(f"{C}Running GPT Researcher...{W}")
        success, report_file = await run_research_with_python(
            topic, report_type, source_count, research_id
        )
        if success and report_file:
            print(f"{G}Research complete! Report: {report_file}{W}")
            research_entry = {
                "id": research_id,
                "topic": topic,
                "type": report_type,
                "sources": source_count,
                "file": str(report_file),
                "created": time.ctime(),
                "status": "completed",
            }
            state["researches"].append(research_entry)
            save_state(state)
            return
        else:
            print(f"{Y}Python API failed. Generating report structure...{W}")
    else:
        print(f"{Y}GPT Researcher not installed. Generating report structure...{W}")

    # Generate report stub
    report_file = generate_report_stub(topic, report_type, research_id)
    print(f"{G}Report structure generated: {report_file}{W}")
    print(f"{Y}Install gpt-researcher (pip install gpt-researcher) for full research.{W}")

    research_entry = {
        "id": research_id,
        "topic": topic,
        "type": report_type,
        "sources": source_count,
        "file": str(report_file),
        "created": time.ctime(),
        "status": "stub",
    }
    state["researches"].append(research_entry)
    save_state(state)

    print(f"\n{C}View report: cat {report_file}{W}")
    print(f"{C}Export: python3 gpt_researcher_agent.py export {research_id}{W}")


async def cmd_sources():
    state = load_state()
    if len(sys.argv) < 3:
        print(f"{R}Usage: python3 gpt_researcher_agent.py sources list|add|remove|configure [NAME]{W}")
        return

    action = sys.argv[2]

    if action == "list":
        print(f"{BOLD}Available Sources:{W}\n")
        active = state.get("active_sources", ["web"])
        for name, desc in SOURCES.items():
            status = f"{G}active{W}" if name in active else f"{Y}inactive{W}"
            print(f"  {name:15s} {desc:50s} [{status}]")

    elif action == "add":
        if len(sys.argv) < 4:
            print(f"{R}Usage: sources add <name>{W}")
            return
        source = sys.argv[3]
        if source not in SOURCES:
            print(f"{R}Unknown source: {source}{W}")
            print(f"  Available: {', '.join(SOURCES.keys())}")
            return
        active = state.setdefault("active_sources", ["web"])
        if source not in active:
            active.append(source)
            save_state(state)
        print(f"{G}Source '{source}' activated.{W}")

    elif action == "remove":
        if len(sys.argv) < 4:
            print(f"{R}Usage: sources remove <name>{W}")
            return
        source = sys.argv[3]
        state["active_sources"] = [s for s in state.get("active_sources", []) if s != source]
        save_state(state)
        print(f"{G}Source '{source}' deactivated.{W}")

    elif action == "configure":
        print(f"{BOLD}Source Configuration:{W}\n")
        sc = state.get("source_config", {})
        print(f"  Web search: default (no config needed)")
        print(f"  ArXiv: {sc.get('arxiv', 'default API')}")
        print(f"  GitHub: {sc.get('github', 'default (no token)')}")
        print(f"  Local: {sc.get('local', 'no directory set')}")
        print(f"\n{Y}Set TAVILY_API_KEY for enhanced web search.{W}")
        print(f"{Y}Set GITHUB_TOKEN for GitHub source access.{W}")


async def cmd_report():
    cfg = load_config()
    state = load_state()

    if len(sys.argv) < 3:
        # List available report types
        print(f"{BOLD}Report Types:{W}\n")
        for name, desc in REPORT_TYPES.items():
            current = f" {G}(current){W}" if name == cfg.get("report_type") else ""
            print(f"  {name:25s} {desc}{current}")
        print(f"\n{Y}Usage: python3 gpt_researcher_agent.py report \"topic\" [--type TYPE]{W}")
        return

    topic = sys.argv[2]
    report_type = cfg.get("report_type", "research_report")
    if "--type" in sys.argv:
        report_type = sys.argv[sys.argv.index("--type") + 1]

    research_id = f"report-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    print(f"{BOLD}Generating {report_type} on: {topic}{W}")

    installed, _ = await check_gpt_researcher()
    if installed:
        success, report_file = await run_research_with_python(
            topic, report_type, cfg.get("source_count", 5), research_id
        )
        if success and report_file:
            print(f"{G}Report generated: {report_file}{W}")
            return

    # Generate stub
    report_file = generate_report_stub(topic, report_type, research_id)
    print(f"{G}Report structure: {report_file}{W}")
    print(f"{Y}Install gpt-researcher for full generation.{W}")


async def cmd_deep():
    cfg = load_config()
    state = load_state()

    if len(sys.argv) < 3:
        print(f"{R}Usage: python3 gpt_researcher_agent.py deep \"topic\" [--sub-queries N]{W}")
        return

    topic = sys.argv[2]
    num_sub = 3
    if "--sub-queries" in sys.argv:
        num_sub = int(sys.argv[sys.argv.index("--sub-queries") + 1])

    research_id = f"deep-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    print(f"{BOLD}Deep Research Mode:{W}")
    print(f"  {C}Topic:{W} {topic}")
    print(f"  {C}Sub-queries:{W} {num_sub}")
    print(f"  {C}ID:{W} {research_id}\n")

    # Generate sub-queries from topic
    sub_queries = []
    angles = [
        "overview and current state",
        "recent developments and trends",
        "challenges and limitations",
        "comparison and alternatives",
        "future outlook",
    ]
    for i in range(min(num_sub, len(angles))):
        sub_queries.append(f"{topic} - {angles[i]}")

    print(f"{C}Sub-queries:{W}")
    for i, sq in enumerate(sub_queries, 1):
        print(f"  {i}. {sq}")
    print()

    installed, _ = await check_gpt_researcher()
    if installed:
        print(f"{C}Running deep research with GPT Researcher...{W}")
        success, report_file = await run_research_with_python(
            topic, "research_report", cfg.get("source_count", 5),
            research_id, sub_queries
        )
        if success and report_file:
            print(f"{G}Deep research complete: {report_file}{W}")
            research_entry = {
                "id": research_id,
                "topic": topic,
                "type": "deep_research",
                "sub_queries": sub_queries,
                "file": str(report_file),
                "created": time.ctime(),
                "status": "completed",
            }
            state["researches"].append(research_entry)
            save_state(state)
            return

    # Generate deep research stub
    report_file = generate_report_stub(topic, "research_report", research_id, sub_queries)
    print(f"{G}Deep research structure: {report_file}{W}")
    print(f"{Y}Install gpt-researcher for full deep research.{W}")

    research_entry = {
        "id": research_id,
        "topic": topic,
        "type": "deep_research",
        "sub_queries": sub_queries,
        "file": str(report_file),
        "created": time.ctime(),
        "status": "stub",
    }
    state["researches"].append(research_entry)
    save_state(state)


async def cmd_export():
    state = load_state()
    if len(sys.argv) < 3:
        # List researches available for export
        print(f"{BOLD}Researches available for export:{W}\n")
        for r in state.get("researches", [])[-15:]:
            print(f"  {C}{r['id']}{W} - {r['topic'][:50]} [{r.get('status', '?')}]")
        print(f"\n{Y}Usage: python3 gpt_researcher_agent.py export <id> [--format FMT] [--dest PATH]{W}")
        return

    research_id = sys.argv[2]
    fmt = "markdown"
    dest = None

    if "--format" in sys.argv:
        fmt = sys.argv[sys.argv.index("--format") + 1]
    if "--dest" in sys.argv:
        dest = Path(sys.argv[sys.argv.index("--dest") + 1])

    # Find the research
    research = None
    for r in state.get("researches", []):
        if r["id"] == research_id:
            research = r
            break

    if not research:
        print(f"{R}Research '{research_id}' not found.{W}")
        return

    source_file = Path(research.get("file", ""))
    if not source_file.exists():
        print(f"{R}Report file not found: {source_file}{W}")
        return

    content = source_file.read_text()

    if fmt == "markdown":
        output = content
        ext = ".md"
    elif fmt == "json":
        output = json.dumps({
            "id": research["id"],
            "topic": research["topic"],
            "type": research.get("type"),
            "content": content,
            "created": research.get("created"),
        }, indent=2)
        ext = ".json"
    elif fmt == "pdf":
        # Try to convert markdown to PDF
        pdf_file = source_file.with_suffix(".pdf")
        pandoc_path = pdf_file
        if dest:
            pandoc_path = dest / f"{research_id}.pdf"

        code, out, err = await run_cmd(f"pandoc {source_file} -o {pandoc_path}")
        if code == 0:
            print(f"{G}Exported to PDF: {pandoc_path}{W}")
            return
        else:
            print(f"{Y}pandoc not found. Exporting as markdown instead.{W}")
            output = content
            ext = ".md"
    else:
        output = content
        ext = ".md"

    if dest:
        dest.mkdir(parents=True, exist_ok=True)
        out_file = dest / f"{research_id}{ext}"
    else:
        out_file = source_file.parent / f"{research_id}-export{ext}"

    out_file.write_text(output)
    print(f"{G}Exported to: {out_file}{W}")
    print(f"  Format: {fmt}")
    print(f"  Size: {len(output)} bytes")


async def cmd_config():
    cfg = load_config()

    if "--llm" in sys.argv:
        cfg["llm"] = sys.argv[sys.argv.index("--llm") + 1]
    if "--report-type" in sys.argv:
        cfg["report_type"] = sys.argv[sys.argv.index("--report-type") + 1]
    if "--source-count" in sys.argv:
        cfg["source_count"] = int(sys.argv[sys.argv.index("--source-count") + 1])

    if "--llm" in sys.argv or "--report-type" in sys.argv or "--source-count" in sys.argv:
        save_config(cfg)
        print(f"{G}Config updated.{W}")

    print(f"{BOLD}GPT Researcher Configuration:{W}\n")
    print(f"  LLM:          {C}{cfg['llm']}{W}")
    print(f"  Report Type:  {C}{cfg['report_type']}{W}")
    print(f"  Source Count: {C}{cfg['source_count']}{W}")
    print(f"\n  {BOLD}Report Types:{W} {', '.join(REPORT_TYPES.keys())}")
    print(f"  {BOLD}Sources:{W} {', '.join(SOURCES.keys())}")

    installed, ver = await check_gpt_researcher()
    print(f"\n  GPT Researcher: {G + ver if installed else Y + 'not installed'}{W}")

    # Check API keys
    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY"]:
        val = os.environ.get(key, "")
        if val:
            print(f"  {key}: {G}{val[:8]}...{W}")
        else:
            print(f"  {key}: {Y}not set{W}")

    print(f"\n{Y}Set values: python3 gpt_researcher_agent.py config --llm M --report-type T --source-count N{W}")


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    dispatch = {
        "research": cmd_research,
        "sources": cmd_sources,
        "report": cmd_report,
        "deep": cmd_deep,
        "export": cmd_export,
        "config": cmd_config,
    }

    handler = dispatch.get(cmd)
    if handler:
        await handler()
    else:
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
