# Data Ingestion & Processing
import os
import re
from pathlib import Path

from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser
from langchain_text_splitters import RecursiveCharacterTextSplitter


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


def process_document(doc):
    """
    Process a single document:
    - Clean text
    - Create chunks
    - Preserve metadata (source, page, section)
    """
    
    # Extract metadata
    source = doc.metadata.get('source', 'unknown')
    page = doc.metadata.get('page', 0)
    
    # Clean text
    RE_EXCESS_NEWLINE = re.compile(r"\n(?=[ a-z])")
    cleaned_text = RE_EXCESS_NEWLINE.sub("", doc.page_content)
    
    # Split into chunks
    chunks = text_splitter.split_text(cleaned_text)
    
    # Create chunks with preserved metadata
    for chunk_index, chunk in enumerate(chunks):
        chunk_metadata = {
            "source": source,
            "page": page,
            "chunk_index": chunk_index,
            "total_chunks": len(chunks),
        }
        
        all_chunks_with_metadata.append({
            "content": chunk,
            "metadata": chunk_metadata
        })
    
    return len(chunks)


# Load all PDFs
loader = GenericLoader(
    blob_loader=FileSystemBlobLoader(
        path=docs_path,
        glob="*.pdf",
    ),
    blob_parser=PyPDFParser(),
)

docs = loader.load()

# Process each document independently
print(f"Loading {len(docs)} documents from {docs_path}\n")
for doc in docs:
    chunks_count = process_document(doc)
    print(f"✓ {doc.metadata['source']}: {chunks_count} chunks created")

print(f"\n✓ Total chunks: {len(all_chunks_with_metadata)}")
