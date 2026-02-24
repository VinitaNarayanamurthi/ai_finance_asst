"""
Finance Q&A Agent using RAG (Retrieval-Augmented Generation)
This agent uses vector_store_embedding.py to retrieve relevant context from financial documents
and answer user questions with expert insights.
"""

from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import importlib.util

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
# LOAD RAG MODULE DYNAMICALLY
# ============================================================

def _load_rag_module():
    """Dynamically load the vector_store_embedding module."""
    rag_path = Path(__file__).resolve().parent.parent / "rag" / "vector_store_embedding.py"
    if not rag_path.exists():
        raise FileNotFoundError(f"RAG module not found at: {rag_path}")
    
    spec = importlib.util.spec_from_file_location("vector_store_embedding", str(rag_path))
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)
    return module

try:
    rag_module = _load_rag_module()
    # Initialize the embedding processor once
    docs_path = Path(__file__).resolve().parent.parent.parent / "docs"
    embedding_processor = rag_module.EmbeddingProcessor(docs_path=str(docs_path))
    # The vector store will load from persist_directory if it exists
    print("RAG module loaded successfully")
except Exception as e:
    print(f"Warning: Could not load RAG module: {e}")
    rag_module = None
    embedding_processor = None

# ============================================================
# FINANCE Q&A TOOL
# ============================================================

@tool
def finance_qa_tool(question: str) -> str:
    """Answer financial Q&A questions with expert insights using RAG."""
    if rag_module is None or embedding_processor is None:
        return "Finance Q&A module unavailable. Please ensure the RAG system is properly initialized."
    
    try:
        # Retrieve relevant context from vector store
        context, retrieved_docs = embedding_processor.retrieve_context(question)
        
        # Format response with context and sources
        if not retrieved_docs:
            return "No relevant information found in the knowledge base for this question."
        
        response = f"Based on financial documents:\n\n{context}\n\n"
        response += f"Retrieved {len(retrieved_docs)} relevant document(s)."
        
        return response
    
    except Exception as e:
        return f"Finance Q&A error: {str(e)}"

# ============================================================
# BUILD Q&A AGENT EXECUTOR
# ============================================================
    
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a financial Q&A expert. Use the finance_qa_tool to retrieve relevant information 
    from financial documents to answer user questions. Provide comprehensive, accurate answers based on 
    the retrieved context. Always cite the sources when answering."""),
    ("human", "{input}\n\n{agent_scratchpad}")
])

agent = create_openai_tools_agent(llm, [finance_qa_tool], prompt)
qa_executor = AgentExecutor(
    agent=agent, 
    tools=[finance_qa_tool], 
    verbose=False, 
    max_iterations=20
)

# ============================================================
# STANDALONE TESTING
# ============================================================

if __name__ == "__main__":
    # Test the Q&A agent
    test_query = "What are the key financial trends for 2024?"
    
    print(f"\nTesting Finance Q&A Agent with query: '{test_query}'\n")
    
    result = qa_executor.invoke({"input": test_query})
    
    print("\n" + "="*60)
    print("AGENT RESPONSE:")
    print("="*60)
    print(result["output"])