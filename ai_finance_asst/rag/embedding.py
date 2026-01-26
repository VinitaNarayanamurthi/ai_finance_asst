import os
import sys
import getpass
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# Add parent directory to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
load_dotenv()

from ai_finance_asst.rag.loader_preprocessor import DocumentProcessor


class EmbeddingProcessor:
    """
    Process document chunks and create embeddings using OpenAI's text-embedding-3-small model.
    """
    
    def __init__(self, docs_path=None, embedding_model_name="text-embedding-3-small"):
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
    
    def get_contextual_texts(self):
        """
        Extract all contextual texts from chunks.
        
        Returns:
            List of contextual text strings
        """
        contextual_texts = [chunk['contextual_text'] for chunk in self.chunks]
        return contextual_texts
    
    def create_embeddings(self):
        """
        Create embeddings for all chunks using text-embedding-3-small.
        
        Returns:
            List of embeddings (vectors)
        """
        texts = self.get_contextual_texts()
        print(f"Creating embeddings for {len(texts)} chunks...")
        
        self.embeddings = self.embedding_model.embed_documents(texts)
        
        print(f" Embeddings created successfully")
        print(f"  Embedding dimension: {len(self.embeddings[0])}")
        
        return self.embeddings
    
    def get_chunks_with_embeddings(self):
        """
        Get chunks paired with their embeddings.
        
        Returns:
            List of dictionaries with chunk data and embeddings
        """
        if self.embeddings is None:
            raise ValueError("Embeddings not created yet. Call create_embeddings() first.")
        
        chunks_with_embeddings = []
        for i, chunk in enumerate(self.chunks):
            chunks_with_embeddings.append({
                "content": chunk["content"],
                "metadata": chunk["metadata"],
                "contextual_text": chunk["contextual_text"],
                "embedding": self.embeddings[i]
            })
        
        return chunks_with_embeddings
    
    def embed_query(self, query):
        """
        Embed a query string.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector for the query
        """
        return self.embedding_model.embed_query(query)
    
if __name__ == "__main__":
    # Example usage
    docs_path = "docs"
    embedding_processor = EmbeddingProcessor(docs_path=docs_path)
    embedding_processor.create_embeddings()
    chunks_with_embeddings = embedding_processor.get_chunks_with_embeddings()
    
    print(f"\nSample chunk with embedding:")
    print(f"Content: {chunks_with_embeddings[0]['content']}")
    print(f"Metadata: {chunks_with_embeddings[0]['metadata']}")
    print(f"Contextual Text: {chunks_with_embeddings[0]['contextual_text']}")
    print(f"Embedding (first 5 values): {chunks_with_embeddings[0]['embedding'][:5]}")