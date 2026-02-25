"""
News Synthesizer Agent using Alpha Vantage News & Sentiment API
This agent uses Alpha Vantage API to fetch the latest financial news, market updates,
and sentiment analysis for stocks and topics.
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
from datetime import datetime, timedelta

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
# ALPHA VANTAGE NEWS & SENTIMENT API TOOLS
# ============================================================

@tool
def get_news_sentiment(tickers: str = None, topics: str = None, limit: int = 50) -> str:
    """Get latest financial news with sentiment analysis. Provide tickers (e.g., 'AAPL,MSFT') or topics (e.g., 'technology,earnings')."""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": alpha_vantage_api_key,
            "limit": limit
        }
        
        if tickers:
            params["tickers"] = tickers
        if topics:
            params["topics"] = topics
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "feed" in data and data["feed"]:
            articles = data["feed"][:10]
            result = f"Latest financial news ({len(articles)} articles"
            if tickers:
                result += f" for {tickers}"
            if topics:
                result += f" about {topics}"
            result += "):\n\n"
            
            for i, article in enumerate(articles, 1):
                result += f"{i}. {article['title']}\n"
                result += f"   Source: {article['source']}\n"
                result += f"   Published: {article['time_published']}\n"
                result += f"   Summary: {article['summary'][:250]}...\n"
                
                # Sentiment scores
                if 'overall_sentiment_score' in article:
                    score = float(article['overall_sentiment_score'])
                    label = article.get('overall_sentiment_label', 'Neutral')
                    result += f"   Sentiment: {label} (score: {score:.3f})\n"
                
                # Ticker sentiment if available
                if 'ticker_sentiment' in article and article['ticker_sentiment']:
                    result += f"   Ticker Sentiments: "
                    ticker_sents = article['ticker_sentiment'][:3]
                    for ts in ticker_sents:
                        result += f"{ts['ticker']}({ts['ticker_sentiment_label']}) "
                    result += "\n"
                
                result += f"   URL: {article['url']}\n\n"
            
            return result
        else:
            return f"Unable to fetch news. Error: {data.get('Note', data.get('Information', 'Unknown error'))}"
    
    except Exception as e:
        return f"Error fetching news sentiment: {str(e)}"

@tool
def get_market_news_feed(topics: str = "financial_markets") -> str:
    """Get general market news feed. Topics: blockchain, earnings, ipo, mergers_and_acquisitions, financial_markets, economy_fiscal, economy_monetary, economy_macro, energy_transportation, finance, life_sciences, manufacturing, real_estate, retail_wholesale, technology."""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "topics": topics,
            "apikey": alpha_vantage_api_key,
            "limit": 50,
            "sort": "LATEST"
        }
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "feed" in data and data["feed"]:
            articles = data["feed"][:10]
            result = f"Market news for topic '{topics}' ({len(articles)} articles):\n\n"
            
            for i, article in enumerate(articles, 1):
                result += f"{i}. {article['title']}\n"
                result += f"   Source: {article['source']}\n"
                result += f"   Published: {article['time_published']}\n"
                result += f"   Summary: {article['summary'][:250]}...\n"
                
                if 'overall_sentiment_score' in article:
                    score = float(article['overall_sentiment_score'])
                    label = article.get('overall_sentiment_label', 'Neutral')
                    result += f"   Sentiment: {label} (score: {score:.3f})\n"
                
                result += f"   URL: {article['url']}\n\n"
            
            return result
        else:
            return f"Unable to fetch market news. Error: {data.get('Note', data.get('Information', 'Unknown error'))}"
    
    except Exception as e:
        return f"Error fetching market news: {str(e)}"

@tool
def get_stock_news(symbol: str, limit: int = 20) -> str:
    """Get news specifically about a stock symbol with sentiment analysis."""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": alpha_vantage_api_key,
            "limit": limit,
            "sort": "LATEST"
        }
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "feed" in data and data["feed"]:
            articles = data["feed"][:10]
            result = f"News for {symbol} ({len(articles)} articles):\n\n"
            
            for i, article in enumerate(articles, 1):
                result += f"{i}. {article['title']}\n"
                result += f"   Source: {article['source']}\n"
                result += f"   Published: {article['time_published']}\n"
                result += f"   Summary: {article['summary'][:250]}...\n"
                
                # Overall sentiment
                if 'overall_sentiment_score' in article:
                    score = float(article['overall_sentiment_score'])
                    label = article.get('overall_sentiment_label', 'Neutral')
                    result += f"   Overall Sentiment: {label} (score: {score:.3f})\n"
                
                # Stock-specific sentiment
                if 'ticker_sentiment' in article:
                    for ts in article['ticker_sentiment']:
                        if ts['ticker'] == symbol:
                            result += f"   {symbol} Sentiment: {ts['ticker_sentiment_label']} (score: {ts['ticker_sentiment_score']})\n"
                            result += f"   Relevance: {ts['relevance_score']}\n"
                            break
                
                result += f"   URL: {article['url']}\n\n"
            
            return result
        else:
            return f"Unable to fetch news for {symbol}. Error: {data.get('Note', data.get('Information', 'Unknown error'))}"
    
    except Exception as e:
        return f"Error fetching stock news: {str(e)}"

@tool
def get_sector_news(topics: str = "technology") -> str:
    """Get news for specific sectors. Topics: technology, energy_transportation, finance, life_sciences, manufacturing, real_estate, retail_wholesale."""
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "topics": topics,
            "apikey": alpha_vantage_api_key,
            "limit": 50,
            "sort": "LATEST"
        }
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "feed" in data and data["feed"]:
            articles = data["feed"][:10]
            result = f"Sector news for '{topics}' ({len(articles)} articles):\n\n"
            
            for i, article in enumerate(articles, 1):
                result += f"{i}. {article['title']}\n"
                result += f"   Source: {article['source']}\n"
                result += f"   Published: {article['time_published']}\n"
                result += f"   Summary: {article['summary'][:250]}...\n"
                
                if 'overall_sentiment_score' in article:
                    score = float(article['overall_sentiment_score'])
                    label = article.get('overall_sentiment_label', 'Neutral')
                    result += f"   Sentiment: {label} (score: {score:.3f})\n"
                
                # Show relevant tickers
                if 'ticker_sentiment' in article and article['ticker_sentiment']:
                    result += f"   Related stocks: "
                    tickers = [ts['ticker'] for ts in article['ticker_sentiment'][:5]]
                    result += ", ".join(tickers) + "\n"
                
                result += f"   URL: {article['url']}\n\n"
            
            return result
        else:
            return f"Unable to fetch sector news. Error: {data.get('Note', data.get('Information', 'Unknown error'))}"
    
    except Exception as e:
        return f"Error fetching sector news: {str(e)}"

# ============================================================
# BUILD NEWS SYNTHESIZER AGENT EXECUTOR
# ============================================================

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

# All Alpha Vantage News & Sentiment API tools available to the agent
news_tools = [
    get_news_sentiment,
    get_market_news_feed,
    get_stock_news,
    get_sector_news
]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a financial news analyst and synthesizer. Use the Alpha Vantage News & Sentiment API tools
    to fetch the latest financial news, market updates, and sentiment analysis.

    Available tools:
    - get_news_sentiment: Get news with sentiment for specific tickers or topics
    - get_market_news_feed: Get general market news by topic (financial_markets, economy, technology, etc.)
    - get_stock_news: Get news specifically about a stock symbol with sentiment
    - get_sector_news: Get news for specific sectors (technology, finance, energy, etc.)

    Choose ONE tool that best matches the user's request — do not call all tools for every query.
    Use get_stock_news when the user asks about a specific stock.
    Use get_sector_news when the user asks about a sector.
    Use get_market_news_feed for general market news.
    Use get_news_sentiment only when you need combined ticker + topic filtering.
    If a tool returns a rate-limit or error message, do not retry — report what is available instead.
    Synthesize and summarize the results, highlighting key trends, sentiment, and important developments."""),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, news_tools, prompt)
news_executor = AgentExecutor(
    agent=agent,
    tools=news_tools,
    verbose=False,
    max_iterations=10,
    handle_parsing_errors=True,
)

# ============================================================
# STANDALONE TESTING
# ============================================================

if __name__ == "__main__":
    # Test the news synthesizer agent
    test_query = "What are the latest headlines about Apple stock?"
    
    print(f"\nTesting News Synthesizer Agent with query: '{test_query}'\n")
    
    result = news_executor.invoke({"input": test_query})
    
    print("\n" + "="*60)
    print("AGENT RESPONSE:")
    print("="*60)
    print(result["output"])
