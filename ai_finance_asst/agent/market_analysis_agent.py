"""
Market Analysis Agent using Alpha Vantage API
This agent uses Alpha Vantage API to fetch real-time market data, stock prices,
and provide market trend analysis.
"""

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import json

# Add parent directory to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file (dynamic path)
env_path = Path(__file__).resolve().parent.parent / ".env"
result = load_dotenv(str(env_path))

print(f"load_dotenv returned: {result}")

# Get API keys with validation
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment. Please set it in .env or export it.")

alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
if not alpha_vantage_api_key:
    print("Warning: ALPHA_VANTAGE_API_KEY not found. Using demo key (rate limited).")
    alpha_vantage_api_key = "demo"

# ============================================================
# ALPHA VANTAGE API TOOLS
# ============================================================

@tool
def get_stock_quote(symbol: str) -> str:
    """Get real-time stock quote for a given symbol (e.g., AAPL, MSFT, GOOGL)."""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={alpha_vantage_api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            result = f"""
Stock Quote for {symbol}:
- Price: ${quote.get('05. price', 'N/A')}
- Change: {quote.get('09. change', 'N/A')} ({quote.get('10. change percent', 'N/A')})
- Volume: {quote.get('06. volume', 'N/A')}
- Previous Close: ${quote.get('08. previous close', 'N/A')}
- Trading Day: {quote.get('07. latest trading day', 'N/A')}
"""
            return result
        else:
            return f"Unable to fetch quote for {symbol}. Error: {data.get('Note', data.get('Error Message', 'Unknown error'))}"
    except Exception as e:
        return f"Error fetching stock quote: {str(e)}"

@tool
def get_stock_intraday(symbol: str, interval: str = "5min") -> str:
    """Get intraday time series data for a stock. Interval options: 1min, 5min, 15min, 30min, 60min."""
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={alpha_vantage_api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        time_series_key = f"Time Series ({interval})"
        
        if time_series_key in data:
            time_series = data[time_series_key]
            # Get the latest 5 data points
            latest_data = list(time_series.items())[:5]
            
            result = f"Intraday data for {symbol} ({interval} interval):\n\n"
            for timestamp, values in latest_data:
                result += f"{timestamp}: Open=${values['1. open']}, High=${values['2. high']}, Low=${values['3. low']}, Close=${values['4. close']}, Volume={values['5. volume']}\n"
            
            return result
        else:
            return f"Unable to fetch intraday data for {symbol}. Error: {data.get('Note', data.get('Error Message', 'Unknown error'))}"
    except Exception as e:
        return f"Error fetching intraday data: {str(e)}"

@tool
def get_stock_daily(symbol: str) -> str:
    """Get daily time series data for a stock (last 100 days)."""
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={alpha_vantage_api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            # Get the latest 10 data points
            latest_data = list(time_series.items())[:10]
            
            result = f"Daily data for {symbol} (last 10 days):\n\n"
            for date, values in latest_data:
                result += f"{date}: Open=${values['1. open']}, High=${values['2. high']}, Low=${values['3. low']}, Close=${values['4. close']}, Volume={values['5. volume']}\n"
            
            return result
        else:
            return f"Unable to fetch daily data for {symbol}. Error: {data.get('Note', data.get('Error Message', 'Unknown error'))}"
    except Exception as e:
        return f"Error fetching daily data: {str(e)}"

@tool
def search_symbol(keywords: str) -> str:
    """Search for stock symbols by company name or keywords."""
    try:
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={keywords}&apikey={alpha_vantage_api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "bestMatches" in data and data["bestMatches"]:
            matches = data["bestMatches"][:5]  # Top 5 matches
            result = f"Symbol search results for '{keywords}':\n\n"
            for match in matches:
                result += f"- {match['1. symbol']}: {match['2. name']} ({match['3. type']}, {match['4. region']})\n"
            return result
        else:
            return f"No matches found for '{keywords}'."
    except Exception as e:
        return f"Error searching symbols: {str(e)}"

@tool
def get_company_overview(symbol: str) -> str:
    """Get comprehensive company overview including fundamentals, financials, and key metrics."""
    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={alpha_vantage_api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data and "Symbol" in data:
            result = f"""
Company Overview for {data.get('Name', symbol)} ({symbol}):

Basic Information:
- Sector: {data.get('Sector', 'N/A')}
- Industry: {data.get('Industry', 'N/A')}
- Market Cap: ${data.get('MarketCapitalization', 'N/A')}
- Exchange: {data.get('Exchange', 'N/A')}

Valuation Metrics:
- P/E Ratio: {data.get('PERatio', 'N/A')}
- EPS: ${data.get('EPS', 'N/A')}
- Beta: {data.get('Beta', 'N/A')}
- 52 Week High: ${data.get('52WeekHigh', 'N/A')}
- 52 Week Low: ${data.get('52WeekLow', 'N/A')}

Dividends:
- Dividend Yield: {data.get('DividendYield', 'N/A')}
- Dividend Per Share: ${data.get('DividendPerShare', 'N/A')}

Profitability:
- Profit Margin: {data.get('ProfitMargin', 'N/A')}
- Operating Margin: {data.get('OperatingMarginTTM', 'N/A')}
- ROE: {data.get('ReturnOnEquityTTM', 'N/A')}
- ROA: {data.get('ReturnOnAssetsTTM', 'N/A')}

Description:
{data.get('Description', 'N/A')[:500]}...
"""
            return result
        else:
            return f"Unable to fetch company overview for {symbol}. Error: {data.get('Note', data.get('Error Message', 'Unknown error'))}"
    except Exception as e:
        return f"Error fetching company overview: {str(e)}"

# ============================================================
# BUILD MARKET ANALYSIS AGENT EXECUTOR
# ============================================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

# All Alpha Vantage tools available to the agent
market_tools = [
    get_stock_quote,
    get_stock_intraday,
    get_stock_daily,
    search_symbol,
    get_company_overview
]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a market analysis expert. Use the Alpha Vantage API tools to fetch real-time market data, 
    stock prices, company information, and market trends. 
    
    Available tools:
    - get_stock_quote: Get current price and basic quote information
    - get_stock_intraday: Get intraday price data (5min, 15min, etc.)
    - get_stock_daily: Get daily historical price data
    - search_symbol: Search for stock symbols by company name
    - get_company_overview: Get comprehensive company fundamentals and metrics
    
    Always provide data-driven insights and explain market trends based on the retrieved data.
    When asked about a company, first search for its symbol if not provided, then fetch relevant data."""),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, market_tools, prompt)
market_executor = AgentExecutor(
    agent=agent, 
    tools=market_tools, 
    verbose=False, 
    max_iterations=20
)

# ============================================================
# STANDALONE TESTING
# ============================================================

if __name__ == "__main__":
    # Test the market analysis agent
    test_query = "What's the current price and performance of Apple stock?"
    
    print(f"\nTesting Market Analysis Agent with query: '{test_query}'\n")
    
    result = market_executor.invoke({"input": test_query})
    
    print("\n" + "="*60)
    print("AGENT RESPONSE:")
    print("="*60)
    print(result["output"])
