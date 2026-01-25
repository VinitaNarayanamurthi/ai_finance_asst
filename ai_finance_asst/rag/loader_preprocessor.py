# Data Ingestion & Processing
import os
import re
from pathlib import Path

from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader



# Dynamic path to docs folder
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
docs_path = os.path.join(project_root, "docs")

# Initialize text splitter (shared configuration)
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " "],
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# Store chunks with metadata
all_chunks_with_metadata = []


def create_contextual_embedding(chunk_data):
    """
    Combine content with metadata context for embedding.
    Creates contextual text that includes source, page, and chunk information.
    """
    content = chunk_data["content"]
    metadata = chunk_data["metadata"]
    
    contextual_text = f"""Source: {metadata['source']} Page: {metadata['page']} Chunk: {metadata['chunk_index']}/{metadata['total_chunks']} Content:{content}"""
    
    return contextual_text


def process_document(doc):
    """
    Process a single document:
    - Clean text
    - Create chunks
    - Preserve metadata (source, page, section)
    - Create contextual embeddings
    """
    
    # Extract metadata
    source = doc.metadata.get('source', 'unknown')
    page = doc.metadata.get('page', 0)
    
    # Clean text: remove excess newlines and multiple spaces
    RE_EXCESS_NEWLINE = re.compile(r"\n(?=[ a-z])")
    cleaned_text = RE_EXCESS_NEWLINE.sub("", doc.page_content)
    
    # Remove multiple consecutive newlines, replace with single space
    cleaned_text = re.sub(r"\n+", " ", cleaned_text)
    
    # Remove multiple consecutive spaces
    cleaned_text = re.sub(r" +", " ", cleaned_text).strip()
    
    # Fix hyphenated words (um-brellas → umbrellas)
    cleaned_text = re.sub(r"([a-z])-([a-z])", r"\1\2", cleaned_text)
    
    # Split into chunks
    chunks = text_splitter.split_text(cleaned_text)
    
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
        }
        
        # Create contextual embedding text
        chunk_data["contextual_text"] = create_contextual_embedding(chunk_data)
        
        all_chunks_with_metadata.append(chunk_data)
    
    return len(chunks)




# Load individual PDFs with GenericLoader
for pdf_file in Path(docs_path).glob("*.pdf"):
    loader = PyPDFLoader(str(pdf_file))
    docs = loader.load()


    print(f"Loading {len(docs)} pages from {docs_path}\\{pdf_file.name}\n")
    for doc in docs:
        chunks_count = process_document(doc)
        print(f"✓ {doc.metadata['source']}: {chunks_count} chunks created")

print(f"\n✓ Total chunks: {len(all_chunks_with_metadata)}")
