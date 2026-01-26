# Data Ingestion & Processing
import os
import re
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """
    Process PDF documents: load, clean, chunk, and create contextual embeddings.
    """
    
    def __init__(self, docs_path=None, chunk_size=1000, chunk_overlap=200):
        """
        Initialize the document processor.
        
        Args:
            docs_path: Path to docs folder. If None, uses project root/docs
            chunk_size: Size of each text chunk
            chunk_overlap: Overlap between chunks for context preservation
        """
        if docs_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.docs_path = os.path.join(project_root, "docs")
        else:
            self.docs_path = docs_path
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " "],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # Store chunks with metadata
        self.chunks = []
    
    def create_contextual_embedding(self, chunk_data):
        """
        Combine content with metadata context for embedding.
        
        Args:
            chunk_data: Dictionary with 'content' and 'metadata' keys
            
        Returns:
            String with contextual information and content
        """
        content = chunk_data["content"]
        metadata = chunk_data["metadata"]
        
        contextual_text = f"Source: {metadata['source']} Page: {metadata['page']} Chunk: {metadata['chunk_index']}/{metadata['total_chunks']} Content:{content}"
        
        return contextual_text
    
    def clean_text(self, text):
        """
        Clean and preprocess text.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove newlines within paragraphs
        RE_EXCESS_NEWLINE = re.compile(r"\n(?=[ a-z])")
        cleaned_text = RE_EXCESS_NEWLINE.sub("", text)
        
        # Remove multiple consecutive newlines
        cleaned_text = re.sub(r"\n+", " ", cleaned_text)
        
        # Remove multiple consecutive spaces
        cleaned_text = re.sub(r" +", " ", cleaned_text).strip()
        
        # Fix hyphenated words
        cleaned_text = re.sub(r"([a-z])-([a-z])", r"\1\2", cleaned_text)
        
        return cleaned_text
    
    def process_document(self, doc):
        """
        Process a single document into chunks with metadata.
        
        Args:
            doc: LangChain document object
            
        Returns:
            Number of chunks created
        """
        # Extract metadata
        source = doc.metadata.get('source', 'unknown')
        page = doc.metadata.get('page', 0)
        
        # Clean text
        cleaned_text = self.clean_text(doc.page_content)
        
        # Split into chunks
        chunks = self.text_splitter.split_text(cleaned_text)
        
        # Create chunks with preserved metadata and contextual embeddings
        for chunk_index, chunk in enumerate(chunks):
            chunk_metadata = {
                "source": source,
                "page": page,
                "chunk_index": chunk_index,
                "total_chunks": len(chunks),
            }
            
            chunk_data = {
                "content": chunk,
                "metadata": chunk_metadata,
                "contextual_text": self.create_contextual_embedding({
                    "content": chunk,
                    "metadata": chunk_metadata
                })
            }
            
            self.chunks.append(chunk_data)
        
        return len(chunks)
    
    def load_and_process_pdfs(self, verbose=True):
        """
        Load all PDFs from docs_path and process them.
        
        Args:
            verbose: Print processing information
            
        Returns:
            List of chunks with metadata and contextual text
        """
        pdf_files = list(Path(self.docs_path).glob("*.pdf"))
        
        if verbose:
            print(f"Loading {len(pdf_files)} documents from {self.docs_path}\n")
        
        for pdf_file in pdf_files:
            loader = PyPDFLoader(str(pdf_file))
            docs = loader.load()
            
            if verbose:
                print(f"Loading {len(docs)} pages from {pdf_file.name}")
            
            for doc in docs:
                chunks_count = self.process_document(doc)
                if verbose:
                    print(f" {doc.metadata['source']}: {chunks_count} chunks created")
        
        if verbose:
            print(f"\nTotal chunks: {len(self.chunks)}")
        
        return self.chunks
    
    def get_chunks(self):
        """Get all processed chunks."""
        return self.chunks
    
    def clear_chunks(self):
        """Clear stored chunks."""
        self.chunks = []


# Example usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    chunks = processor.load_and_process_pdfs()
    
    # Access chunks
    print(f"\nFirst chunk content preview: {chunks[0]['content'][:100]}...")
