# ============================================================
# FINANCIAL MULTI-AGENT ORCHESTRATOR WITH GUARDRAILS
# ============================================================
import sys
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
import os

from typing import TypedDict, List

# Add project root to path BEFORE importing agent modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(str(env_path))

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment. Please set it in .env or export it.")

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage

from agent.finance_qa_agent import qa_executor
from agent.portfolio_agent import portfolio_executor
from agent.market_analysis_agent import market_executor
from agent.news_synthesizer_agent import news_executor

# ============================================================
# SHARED STATE
# ============================================================

class FinancialState(TypedDict, total=False):
    user_input: str
    chat_history: List[BaseMessage]
    agents_to_run: List[str]

    blocked: bool
    guardrail_reason: str

    qa_response: str
    portfolio_analysis: str
    market_analysis: str
    news_summary: str

    errors: List[str]
    final_response: str

# ============================================================
# RETRY + BACKOFF WRAPPER
# ============================================================

def with_retry(fn, retries=3, base_delay=1):
    def wrapper(state):
        for attempt in range(retries):
            try:
                return fn(state)
            except (TimeoutError, ConnectionError):
                if attempt == retries - 1:
                    raise
                time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.5))
            except Exception:
                raise
    return wrapper

# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

# ============================================================
# GUARDRAILS LAYER
# ============================================================

FORBIDDEN_PATTERNS = [
    "guarantee profit",
    "insider trading",
    "hide income",
    "tax evasion",
    "100% safe investment",
    "double my money instantly",
]

def guardrail_node(state: FinancialState):
    user_input = state["user_input"].lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in user_input:
            return {
                "blocked": True,
                "guardrail_reason": "Request violates financial compliance policies.",
            }

    # Build context so follow-up queries ("explain more", "elaborate") are
    # evaluated with the conversation history, not in isolation.
    messages = list(state.get("chat_history") or [])
    messages.append(HumanMessage(content=f"""You are a financial compliance guardrail.
Classify the LATEST user message as exactly one of: SAFE, UNSAFE, or NEEDS_DISCLAIMER.

- SAFE            : normal finance questions, follow-ups, elaborations, greetings
- NEEDS_DISCLAIMER: speculative advice, predictions, or opinion-heavy requests
- UNSAFE          : requests that promote illegal activity (fraud, insider trading, tax evasion)

Respond with ONLY the single label word. No explanation, no punctuation.

Latest message: {state['user_input']}"""))

    response = llm.invoke(messages)
    # Take only the first word to guard against verbose responses
    label = response.content.strip().upper().split()[0] if response.content.strip() else "SAFE"

    if label == "UNSAFE":
        return {"blocked": True, "guardrail_reason": "Request classified as unsafe."}
    if label == "NEEDS_DISCLAIMER":
        return {"blocked": False, "guardrail_reason": "Educational guidance only — not financial advice."}
    return {"blocked": False}

def guardrail_route(state: FinancialState):
    return "blocked" if state.get("blocked") else "allowed"

def blocked_node(state: FinancialState):
    return {
        "final_response":
            f"⚠️ Request cannot be processed.\nReason: {state.get('guardrail_reason', 'Policy violation')}"
    }

# ============================================================
# SAFE AGENT EXECUTION WRAPPER
# ============================================================

def safe_agent_node(executor, output_key):
    @with_retry
    def node(state: FinancialState):
        try:
            result = executor.invoke({
                "input": state["user_input"],
                "chat_history": state.get("chat_history", []),
            })
            return {output_key: result["output"]}
        except Exception as e:
            error_msg = f"{output_key} failed: {str(e)}"
            return {
                output_key: f"{output_key} temporarily unavailable.",
                "errors": state.get("errors", []) + [error_msg],
            }
    return node

qa_node = safe_agent_node(qa_executor, "qa_response")
portfolio_node = safe_agent_node(portfolio_executor, "portfolio_analysis")
market_node = safe_agent_node(market_executor, "market_analysis")
news_node = safe_agent_node(news_executor, "news_summary")

# ============================================================
# PLANNER NODE WITH FALLBACK
# ============================================================

@with_retry
def planner_node(state: FinancialState):
    try:
        response = llm.invoke([HumanMessage(content=f"""
You are a financial query router. Analyze the user's QUESTION (ignore any system context in brackets) \
and return ONLY a JSON array of agent names to run.

Agents and their strict use cases:
- "qa"        : general finance concepts, definitions, investment principles, how-to explanations,
                document-based knowledge — only when NOT asking about a specific company or ticker.
                (e.g. "What is dollar-cost averaging?", "Explain the difference between stocks and bonds")
- "portfolio" : user explicitly asks to analyse THEIR portfolio, allocation, diversification,
                or portfolio performance. Only use when the question is clearly about the user's
                own portfolio holdings — NOT just because a portfolio file appears in context.
- "market"    : anything involving a SPECIFIC named company or stock ticker — prices, quotes,
                historical data, fundamentals, valuation metrics, sector, P/E ratio, EPS, market cap, etc.
                If a company name or ticker appears in the question, use "market".
                (e.g. "What is AAPL's price?", "Key valuation metrics for Microsoft", "IBM's P/E ratio")
- "news"      : financial news, headlines, sentiment, sector news
                (e.g. "Latest news on Tesla", "Market sentiment today", "Tech sector headlines")

Rules:
- Route on the USER'S INTENT, not on incidental context like file paths or profile info in brackets.
- If a SPECIFIC company or ticker is mentioned, prefer "market" over "qa" even for metric/concept questions.
- Use "qa" only for general, company-agnostic finance knowledge questions.
- Only include agents genuinely needed — do not bundle agents unnecessarily.
- Return ONLY a valid JSON array, no explanation, no markdown.

User input: {state['user_input']}

Examples:
  "What is asset allocation?" → ["qa"]
  "Analyse my portfolio risk" → ["portfolio"]
  "What is AAPL's price today?" → ["market"]
  "Latest tech news and AAPL price" → ["news", "market"]
        """)])

        content = response.content.strip()
        if not content:
            return {"agents_to_run": ["qa"], "errors": ["Planner returned empty response"]}

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        agents = json.loads(content)
        if not isinstance(agents, list) or not agents:
            raise ValueError("Planner did not return a non-empty list")

        valid = {"qa", "portfolio", "market", "news"}
        agents = [a for a in agents if a in valid] or ["qa"]
        return {"agents_to_run": agents}

    except json.JSONDecodeError as e:
        return {"agents_to_run": ["qa"], "errors": [f"Planner JSON error: {str(e)}"]}
    except Exception as e:
        return {"agents_to_run": ["qa"], "errors": [f"Planner fallback: {str(e)}"]}

def route_agents(state: FinancialState):
    return state["agents_to_run"]

# ============================================================
# AGGREGATOR WITH LLM SYNTHESIS
# ============================================================

def aggregator_node(state: FinancialState):
    label_map = {
        "qa_response":        "Financial Q&A",
        "portfolio_analysis": "Portfolio Analysis",
        "market_analysis":    "Market Analysis",
        "news_summary":       "News Summary",
    }
    outputs = {
        label: state[key]
        for key, label in label_map.items()
        if key in state and state.get(key)
    }

    if not outputs:
        return {"final_response": "System temporarily unavailable. Please try again."}

    # Single agent — return directly, no extra LLM call
    if len(outputs) == 1:
        return {"final_response": list(outputs.values())[0]}

    # Multiple agents — synthesize into one coherent response
    combined = "\n\n".join(f"### {label}\n{content}" for label, content in outputs.items())
    synthesis = llm.invoke([HumanMessage(content=f"""You are a financial assistant. Multiple specialized agents produced the outputs below.
Synthesize them into a single, well-structured, coherent response. Eliminate redundancy,
preserve all key facts, and organize with clear headings where appropriate.

{combined}

Provide a unified, professional response:""")])
    return {"final_response": synthesis.content}

# ============================================================
# BUILD LANGGRAPH DAG
# ============================================================

graph = StateGraph(FinancialState)

graph.add_node("guardrail",  guardrail_node)
graph.add_node("blocked",    blocked_node)
graph.add_node("planner",    planner_node)
graph.add_node("qa",         qa_node)
graph.add_node("portfolio",  portfolio_node)
graph.add_node("market",     market_node)
graph.add_node("news",       news_node)
graph.add_node("aggregator", aggregator_node)

graph.set_entry_point("guardrail")

graph.add_conditional_edges(
    "guardrail", guardrail_route,
    {"blocked": "blocked", "allowed": "planner"}
)
graph.add_edge("blocked", END)

graph.add_conditional_edges(
    "planner", route_agents,
    {"qa": "qa", "portfolio": "portfolio", "market": "market", "news": "news"}
)

for node in ["qa", "portfolio", "market", "news"]:
    graph.add_edge(node, "aggregator")

graph.add_edge("aggregator", END)

orchestrator_app = graph.compile()

# ============================================================
# STANDALONE TESTING
# ============================================================

if __name__ == "__main__":
    result = orchestrator_app.invoke({
        "user_input": "What are the key concepts I should understand about diversification and asset allocation?",
        "chat_history": [],
    })

    print("\nFINAL RESPONSE:\n")
    print(result["final_response"])

    if "errors" in result:
        print("\nERRORS CAPTURED:\n")
        for e in result["errors"]:
            print("-", e)
