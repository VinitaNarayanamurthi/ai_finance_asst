"""Portfolio Analyzer Agent wrapper

Provides a LangChain Tool that runs the local `tools/portfolio_analyzer.py` script
and a helper to forward the analysis summary and chart paths to an LLM for a
concise executive summary.

Usage examples:

from langchain.chat_models import ChatOpenAI
from agent.portfolio_agent import create_portfolio_tool, summarize_with_llm

tool, analyze_func = create_portfolio_tool()
# call tool.func("path/to/file.xlsx") or use LangChain agent

llm = ChatOpenAI(temperature=0.2)
result_text = analyze_func("../sample_portfolio_data.xlsx")
summary = summarize_with_llm(llm, result_text)
print(summary)
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from langchain.agents import Tool


def _load_analyzer_module() -> Any:
    """Dynamically load the local portfolio_analyzer.py module.

    Looks for the module at ../tools/portfolio_analyzer.py relative to this file.
    """
    tools_path = Path(__file__).resolve().parents[1] / "tools" / "portfolio_analyzer.py"
    if not tools_path.exists():
        raise FileNotFoundError(f"Portfolio analyzer not found at: {tools_path}")

    spec = importlib.util.spec_from_file_location("portfolio_analyzer", str(tools_path))
    module = importlib.util.module_from_spec(spec)  # type: ignore
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)
    return module


def _format_results(results: Dict[str, Any]) -> str:
    """Turn analysis results dict into a human-readable summary string."""
    out = []
    out.append("Portfolio Analysis Summary:\n")
    out.append(f"Sheets found: {results.get('sheets_found', [])}\n")
    out.append(f"Number of holdings: {results.get('num_holdings', 'N/A')}")
    out.append(f"Total portfolio value: {results.get('total_portfolio_value', 0):,.2f}")
    if results.get('total_invested') is not None:
        out.append(f"Total invested (cost basis): {results.get('total_invested', 0):,.2f}")
    if results.get('total_gain_loss') is not None:
        out.append(f"Total gain/loss: {results.get('total_gain_loss', 0):,.2f}")
        out.append(f"Total return %: {results.get('total_return_pct', 0):+.2f}%")

    div = results.get('diversification', {})
    if div:
        out.append("\nDiversification:")
        out.append(f"  HHI: {div.get('herfindahl_index')}")
        out.append(f"  Effective # holdings: {div.get('effective_num_holdings')}")
        out.append(f"  Top5 concentration: {div.get('top5_concentration')}%")

    if results.get('top_performers'):
        out.append("\nTop performers (ticker, %):")
        for t in results['top_performers']:
            out.append(f"  {t[0]}: {t[1]:+.2f}%")

    # Charts
    charts = results.get('chart_paths', {})
    if charts:
        out.append("\nCharts generated:")
        for name, path in charts.items():
            out.append(f"  {name}: {path}")

    return "\n".join(out)


def create_portfolio_tool() -> Tuple[Tool, Any]:
    """Create a LangChain Tool wrapping the local analyzer.

    Returns (Tool, analyze_func) where analyze_func(file_path, output_dir="charts")
    can be called directly for programmatic use.
    """
    module = _load_analyzer_module()

    def analyze_wrapper(file_path: str, output_dir: str = "charts") -> str:
        """Run the analyzer and return a text summary. Also returns chart paths."""
        # Use the analyzer function from the module
        results = module.analyze_portfolio(file_path, output_dir)
        # Ensure JSON-serializable
        try:
            _ = json.dumps(results)
        except Exception:
            # Convert non-serializable items to strings
            for k, v in list(results.items()):
                try:
                    json.dumps(v)
                except Exception:
                    results[k] = str(v)

        summary = _format_results(results)
        # include raw results as JSON at the end for LLM
        summary += "\n\nRAW_RESULTS_JSON:\n" + json.dumps(results, indent=2)
        return summary

    tool = Tool(
        name="portfolio_analyzer",
        func=analyze_wrapper,
        description=(
            "Analyze a portfolio Excel/CSV file and return a summary + paths to generated charts. "
            "Call with a file path string. Returns a text summary with RAW_RESULTS_JSON appended."
        ),
    )

    return tool, analyze_wrapper


def summarize_with_llm(llm: Any, analysis_text: str, max_tokens: int = 512) -> str:
    """Send the analysis text to an LLM and return the LLM's concise executive summary.

    This function attempts common LangChain LLM interfaces:
    - If `llm` is callable, calls `llm(analysis_prompt)`
    - If `llm` has `predict`, uses `llm.predict(prompt)`
    - If `llm` has `generate`, uses `llm.generate([prompt])` and extracts text

    If the LLM call fails, returns the raw analysis_text.
    """
    prompt = (
        "You are a financial analyst. Read the portfolio analysis and charts list below, "
        "then provide a concise executive summary (3-6 sentences) and 3 action items for the portfolio owner.\n\n"
        "Analysis:\n" + analysis_text
    )

    try:
        # common LangChain Chat model usage
        if hasattr(llm, "predict"):
            return llm.predict(prompt)
        if callable(llm):
            return llm(prompt)
        if hasattr(llm, "generate"):
            gen = llm.generate([prompt])
            # gen may be a ChatResult; try to extract content
            try:
                return gen.generations[0][0].text
            except Exception:
                return str(gen)
    except Exception as e:
        return f"LLM call failed: {e}\n\nOriginal analysis:\n{analysis_text}"

    # Fallback
    return analysis_text


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run portfolio analyzer tool and optionally call an LLM")
    parser.add_argument("file", help="Path to portfolio file (xlsx/csv)")
    parser.add_argument("--out", default="charts", help="Output directory for charts")
    parser.add_argument("--llm", action="store_true", help="If present, attempt to call an LLM (requires LangChain LLM in environment)")
    args = parser.parse_args()

    tool, analyze = create_portfolio_tool()
    text = analyze(args.file, args.out)
    print(text)

    if args.llm:
        try:
            # try to construct a simple ChatOpenAI if available
            from langchain.chat_models import ChatOpenAI

            llm = ChatOpenAI(temperature=0.2)
            print("\n=== LLM SUMMARY ===\n")
            print(summarize_with_llm(llm, text))
        except Exception as e:
            print(f"Could not run LLM: {e}")
