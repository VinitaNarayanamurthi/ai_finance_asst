
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


# Add parent directory to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file (dynamic path)
env_path = Path(__file__).resolve().parent.parent / ".env"
result = load_dotenv(str(env_path))

print(f"load_dotenv returned: {result}")

from ai_finance_asst.rag.loader_preprocessor import DocumentProcessor


class EmbeddingProcessor:
    """
    Process document chunks and create embeddings using OpenAI's text-embedding-3-small model.
    """
    
    def __init__(self, docs_path=None, embedding_model_name="text-embedding-3-large"):
        """
        Initialize the embedding processor.
        
        Args:
            docs_path: Optional path to docs folder
            embedding_model_name: OpenAI embedding model to use
        """
        # Initialize document processor
        self.processor = DocumentProcessor(docs_path=docs_path)
        self.chunks = self.processor.load_and_process_pdfs(verbose=False)
        
        # Get OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY") 
        
        # Initialize embedding model
        self.embedding_model = OpenAIEmbeddings(
            api_key=self.api_key,
            model=embedding_model_name
        )
        
        self.embeddings = None
    
    def create_embeddings(self):
        """
        Create embeddings for all chunks using text-embedding-3-large and store in vector db.
        
        Returns:
            List of embeddings (vectors)
        """
        texts = self.chunks
        print(f"Creating vector db for {len(texts)} chunks...")
        ids = [f"chunk_{i}" for i in range(len(texts))]

        #create vector store
        self.vector_store = Chroma(
        collection_name="financial_documents",
        embedding_function=self.embedding_model,
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )
        #add documents to vector store

        self.vector_store.add_documents(documents=texts, ids=ids)

    # @tool(response_format="content_and_artifact")
    def retrieve_context(self, query: str):
        """Retrieve information to help answer a query."""
        retrieved_docs = self.vector_store.similarity_search(query, k=2)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nContent: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs


    
if __name__ == "__main__":
    # Example usage
    docs_path = "docs"
    embedding_processor = EmbeddingProcessor(docs_path=docs_path)
    embedding_processor.create_embeddings()
    
    # Example retrieval
    query = "What is the financial outlook for 2024?"   
    serialized, retrieved_docs = embedding_processor.retrieve_context(query)
    print(f"\nRetrieved context for query: '{query}'")
    print(serialized)