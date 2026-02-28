

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import importlib.util



portfolio_insights = [ 'total_portfolio_value', 'total_invested', 'total_gain_loss',
'asset_type_allocation', 'top_performers',  'diversification', 'chart_paths']

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


# Load portfolio analyzer module dynamically
def _load_portfolio_analyzer():
    """Dynamically load the portfolio analyzer module."""
    analyzer_path = Path(__file__).resolve().parent.parent / "tools" / "portfolio_analyzer.py"
    if not analyzer_path.exists():
        raise FileNotFoundError(f"Portfolio analyzer not found at: {analyzer_path}")
    
    spec = importlib.util.spec_from_file_location("portfolio_analyzer", str(analyzer_path))
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)
    return module


portfolio_analyzer_module = _load_portfolio_analyzer()

@tool
def portfolio_analysis_tool(file_path: str = None) -> str:
    """Analyze portfolio risk metrics, allocation, and diversification using actual portfolio analyzer."""
    if portfolio_analyzer_module is None:
        return "Portfolio analyzer module unavailable."
    
    try:
        # Resolve the file path
        resolved_path = None
        
        if file_path:
            # Try the provided path first
            p = Path(file_path)
            if p.exists():
                resolved_path = str(p)
        
        # If not found, look in tools directory
        if not resolved_path:
            tools_dir = Path(__file__).resolve().parent.parent / "tools"
            sample_files = list(tools_dir.glob("sample_*.xlsx"))
            if sample_files:
                resolved_path = str(sample_files[0])
                file_path = resolved_path
        
        if not resolved_path:
            return "No portfolio file found. Please provide a valid file path or ensure sample_portfolio.xlsx exists in tools directory."
        
        # Verify file exists before calling analyzer
        if not Path(resolved_path).exists():
            return f"Portfolio file not found: {resolved_path}"
        
        # Run the analyzer
        output_dir = Path(__file__).resolve().parent.parent / "analysis_output"
        output_dir.mkdir(exist_ok=True)
        
        results = portfolio_analyzer_module.analyze_portfolio(file_path= resolved_path, output_dir= str(output_dir))
        summary = f"Portfolio Analysis Results:\n"
        for k, v in results.items():
            if k in portfolio_insights:
                summary += f"{k}: {v}\n"

        return summary
        
    except Exception as e:
        return f"Portfolio analysis error: {str(e)}"
    
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

def build_executor(system_prompt, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=10, handle_parsing_errors=True)

portfolio_executor = build_executor(
    "You are a portfolio analyst. You MUST use the portfolio_analysis_tool to analyze any portfolio file. "
    "Always call the tool with the file path from the user query. Never say you cannot access files. "
    "When the tool returns chart paths, always include the full file paths in your response so the user can open them. "
    ,
    [portfolio_analysis_tool]
)

if __name__ == "__main__":
    result = portfolio_executor.invoke({
        "input": "Analyze my portfolio from C:\\Users\\vinit\\Documents\\agentic_ai\\capstone_project\\ai_finance_asst\\tools\\sample_portfolio.xlsx and give me insights  and also dsplay charts"
    })
 
    print("\nFINAL RESPONSE:\n")
    print(result)