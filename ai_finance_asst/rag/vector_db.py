import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Add parent directory to path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from .env file
load_dotenv()

from ai_finance_asst.rag.embedding import EmbeddingProcessor


class ChromaVectorDB:
    """
    Wrapper class to manage Chroma vector database for storing and querying embeddings.
    """
    
    def __init__(self, db_path="./chroma_db", collection_name="financial_documents"):
        """
        Initialize Chroma vector database.
        
        Args:
            db_path: Path where Chroma database will be stored
            collection_name: Name of the collection to store embeddings
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize Chroma client (persistent)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        print(f"Chroma Vector DB initialized")
        print(f"  Collection: {collection_name}")
        print(f"  Database path: {db_path}")
    
    def add_embeddings(self, chunks_with_embeddings):
        """
        Add chunks with embeddings to the Chroma collection.
        
        Args:
            chunks_with_embeddings: List of dicts with 'content', 'metadata', and 'embedding'
        """
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks_with_embeddings):
            ids.append(f"doc_{i}")
            embeddings.append(chunk['embedding'])
            documents.append(chunk['contextual_text'])
            metadatas.append(chunk['metadata'])
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f" Added {len(ids)} embeddings to Chroma collection")
        print(f"  Total documents in collection: {self.collection.count()}")
    
    def query(self, query_embedding, n_results=5):
        """
        Query the vector database using an embedding.
        
        Args:
            query_embedding: Embedding vector for the query
            n_results: Number of results to return
            
        Returns:
            Dictionary with search results
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
    
    def query_by_text(self, query_text, embedding_processor, n_results=5):
        """
        Query the database using text (embeds it first).
        
        Args:
            query_text: Text query to search for
            embedding_processor: EmbeddingProcessor instance to embed the query
            n_results: Number of results to return
            
        Returns:
            Dictionary with search results
        """
        # Embed the query
        query_embedding = embedding_processor.embed_query(query_text)
        
        # Query the collection
        results = self.query(query_embedding, n_results=n_results)
        
        return results
    
    def get_collection_stats(self):
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection info
        """
        stats = {
            "collection_name": self.collection_name,
            "total_documents": self.collection.count(),
            "metadata": self.collection.metadata
        }
        return stats
    
    def delete_collection(self):
        """
        Delete the entire collection.
        """
        self.client.delete_collection(name=self.collection_name)
        print(f"✓ Deleted collection: {self.collection_name}")
    
    def clear_collection(self):
        """
        Clear all documents from the collection.
        """
        # Get all IDs in collection
        all_data = self.collection.get()
        if all_data['ids']:
            self.collection.delete(ids=all_data['ids'])
            print(f"✓ Cleared all documents from collection")


if __name__ == "__main__":
    # Example usage
    
    # Step 1: Create embeddings
    print("Step 1: Creating embeddings...\n")
    docs_path = "docs"
    embedding_processor = EmbeddingProcessor(docs_path=docs_path)
    embedding_processor.create_embeddings()
    chunks_with_embeddings = embedding_processor.get_chunks_with_embeddings()
    
    # Step 2: Initialize Chroma vector DB
    print("\nStep 2: Initializing Chroma Vector DB...\n")
    vector_db = ChromaVectorDB(
        db_path="./chroma_db",
        collection_name="financial_documents"
    )
    
    # Step 3: Add embeddings to Chroma
    print("\nStep 3: Adding embeddings to Chroma...\n")
    vector_db.add_embeddings(chunks_with_embeddings)
    
    # Step 4: Get collection stats
    print("\nStep 4: Collection statistics:\n")
    stats = vector_db.get_collection_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Step 5: Query the database
    print("\nStep 5: Querying the database...\n")
    query_text = "What is the financial strategy?"
    results = vector_db.query_by_text(query_text, embedding_processor, n_results=3)
    
    print(f"\nTop 3 results for query: '{query_text}'")
    for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
        print(f"\nResult {i+1} (distance: {distance:.4f}):")
        print(f"  {doc[:200]}...")
