# ============================================================
# FINANCIAL MULTI-AGENT ORCHESTRATOR WITH GUARDRAILS
# ============================================================

from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

import sys
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
import os

# Add parent directory to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file (dynamic path)
env_path = Path(__file__).resolve().parent.parent / ".env"
result = load_dotenv(str(env_path))

print(f"load_dotenv returned: {result}")

# Get API key with validation
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment. Please set it in .env or export it.")

# ============================================================
# SHARED STATE
# ============================================================

class FinancialState(TypedDict, total=False):
    user_input: str
    agents_to_run: List[str]

    blocked: bool
    guardrail_reason: str

    qa_response: str
    portfolio_analysis: str
    market_analysis: str
    goal_plan: str
    news_summary: str
    tax_guidance: str

    errors: List[str]
    final_response: str

# ============================================================
#  RETRY + BACKOFF WRAPPER
# ============================================================

def with_retry(fn, retries=3, base_delay=1):
    def wrapper(state):
        for attempt in range(retries):
            try:
                return fn(state)
            except (TimeoutError, ConnectionError) as e:
                if attempt == retries - 1:
                    raise
                sleep_time = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(sleep_time)
            except Exception:
                raise
    return wrapper

# ============================================================
#  DEFINE TOOLS (ONE PER AGENT)
# ============================================================

@tool
def finance_qa_tool(question: str) -> str:
    """Answer financial Q&A questions with expert insights."""
    return f"Finance Answer: {question}"

@tool
def portfolio_analysis_tool(details: str) -> str:
    """Analyze portfolio risk metrics, allocation, and diversification."""
    return "Portfolio risk metrics and allocation evaluated."

@tool
def market_analysis_tool(topic: str) -> str:
    """Analyze market trends, volatility, and macroeconomic signals."""
    return "Market volatility, trends, and macro signals analyzed."

@tool
def goal_planning_tool(context: str) -> str:
    """Create structured retirement and wealth-building roadmaps."""
    return "Structured retirement and wealth-building roadmap created."

@tool
def news_synth_tool(topic: str) -> str:
    """Synthesize and summarize latest financial news."""
    return "Latest financial news synthesized."

@tool
def tax_education_tool(query: str) -> str:
    """Explain tax optimization strategies and implications."""
    return "Explained tax optimization strategies and implications."

# ============================================================
#  BUILD TOOL-CALLING AGENTS
# ============================================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

def build_executor(system_prompt, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}\n\n{agent_scratchpad}")
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)

qa_executor = build_executor("You are a finance Q&A expert.", [finance_qa_tool])
portfolio_executor = build_executor("You are a portfolio analyst.", [portfolio_analysis_tool])
market_executor = build_executor("You are a market analyst.", [market_analysis_tool])
goal_executor = build_executor("You are a financial planner.", [goal_planning_tool])
news_executor = build_executor("You are a financial news analyst.", [news_synth_tool])
tax_executor = build_executor("You are a tax education specialist.", [tax_education_tool])

# ============================================================
#  GUARDRAILS LAYER
# ============================================================

FORBIDDEN_PATTERNS = [
    "guarantee profit",
    "insider trading",
    "hide income",
    "tax evasion",
    "100% safe investment",
    "double my money instantly"
]

def guardrail_node(state: FinancialState):
    user_input = state["user_input"].lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in user_input:
            return {
                "blocked": True,
                "guardrail_reason": "Request violates financial compliance policies."
            }
    # Optional: LLM classification for complex queries
    response = llm.invoke([HumanMessage(content=f"""
        Classify query as SAFE, UNSAFE, or NEEDS_DISCLAIMER:
        {state['user_input']}
    """)])
    label = response.content.strip().upper()
    if "UNSAFE" in label:
        return {"blocked": True, "guardrail_reason": "Request classified as unsafe."}
    if "NEEDS_DISCLAIMER" in label:
        return {"blocked": False, "guardrail_reason": "Educational guidance only."}
    return {"blocked": False}

def guardrail_route(state: FinancialState):
    return "blocked" if state.get("blocked") else "allowed"

def blocked_node(state: FinancialState):
    return {
        "final_response":
        f"⚠️ Request cannot be processed.\nReason: {state.get('guardrail_reason','Policy violation')}"
    }

# ============================================================
# SAFE AGENT EXECUTION WRAPPER
# ============================================================

def safe_agent_node(executor, output_key):
    @with_retry
    def node(state: FinancialState):
        try:
            result = executor.invoke({"input": state["user_input"]})
            return {output_key: result["output"]}
        except Exception as e:
            error_msg = f"{output_key} failed: {str(e)}"
            return {
                output_key: f"{output_key} temporarily unavailable.",
                "errors": state.get("errors", []) + [error_msg]
            }
    return node

qa_node = safe_agent_node(qa_executor, "qa_response")
portfolio_node = safe_agent_node(portfolio_executor, "portfolio_analysis")
market_node = safe_agent_node(market_executor, "market_analysis")
goal_node = safe_agent_node(goal_executor, "goal_plan")
news_node = safe_agent_node(news_executor, "news_summary")
tax_node = safe_agent_node(tax_executor, "tax_guidance")

# ============================================================
#  PLANNER NODE WITH FALLBACK
# ============================================================

@with_retry
def planner_node(state: FinancialState):
    try:
        response = llm.invoke([HumanMessage(content=f"""
            Return JSON list of agents to run: qa, portfolio, market, goal, news, tax
            User input: {state['user_input']}
        """)])
        agents = json.loads(response.content)
        if not isinstance(agents, list):
            raise ValueError("Planner did not return a list")
        return {"agents_to_run": agents}
    except Exception as e:
        return {"agents_to_run": ["qa"], "errors": [f"Planner fallback: {str(e)}"]}

def route_agents(state: FinancialState):
    return state["agents_to_run"]

# ============================================================
# AGGREGATOR
# ============================================================

def aggregator_node(state: FinancialState):
    outputs = []
    for key in [
        "qa_response",
        "portfolio_analysis",
        "market_analysis",
        "goal_plan",
        "news_summary",
        "tax_guidance"
    ]:
        if key in state:
            outputs.append(state[key])
    if not outputs:
        return {"final_response": "System temporarily unavailable."}
    return {"final_response": "\n\n".join(outputs)}

# ============================================================
# BUILD LANGGRAPH DAG
# ============================================================

graph = StateGraph(FinancialState)

graph.add_node("guardrail", guardrail_node)
graph.add_node("blocked", blocked_node)
graph.add_node("planner", planner_node)
graph.add_node("qa", qa_node)
graph.add_node("portfolio", portfolio_node)
graph.add_node("market", market_node)
graph.add_node("goal", goal_node)
graph.add_node("news", news_node)
graph.add_node("tax", tax_node)
graph.add_node("aggregator", aggregator_node)

graph.set_entry_point("guardrail")

graph.add_conditional_edges("guardrail", guardrail_route, {"blocked": "blocked", "allowed": "planner"})
graph.add_edge("blocked", END)

graph.add_conditional_edges("planner", route_agents, {
    "qa": "qa",
    "portfolio": "portfolio",
    "market": "market",
    "goal": "goal",
    "news": "news",
    "tax": "tax",
})

for node in ["qa", "portfolio", "market", "goal", "news", "tax"]:
    graph.add_edge(node, "aggregator")

graph.add_edge("aggregator", END)

app = graph.compile()

# ============================================================
# EXAMPLE RUN
# ============================================================

if __name__ == "__main__":
    result = app.invoke({
        "user_input": "Analyze my portfolio and explain tax impact under current market conditions"
    })

    print("\nFINAL RESPONSE:\n")
    print(result["final_response"])

    if "errors" in result:
        print("\nERRORS CAPTURED:\n")
        for e in result["errors"]:
            print("-", e)
