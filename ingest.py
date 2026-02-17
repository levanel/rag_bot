import os
import pymupdf4llm
from langchain_text_splitters import MarkdownTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- CONFIGURATION ---
PDF_PATH = "gpt4.pdf" # Make sure your PDF is named this
INDEX_OUTPUT_DIR = "faiss_gpt4_index"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

def main():
    # 1. CONVERT PDF TO MARKDOWN (Fixes spacing & layout)
    print(f"--- [1/4] Parsing {PDF_PATH} to Markdown ---")
    
    # This function extracts text + tables and fixes the "M a r i k a" kerning issues
    md_text = pymupdf4llm.to_markdown(PDF_PATH)
    
    # DEBUG: Save the raw markdown so you can check if it looks good
    with open("debug_text.md", "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"   > Debug file saved to 'debug_text.md'. Check this if answers feel weird.")

    # 2. SPLIT TEXT (Markdown Aware)
    print("--- [2/4] Splitting Text into Chunks ---")
    
    # We use MarkdownTextSplitter to keep headers (# Header) attached to their paragraphs
    text_splitter = MarkdownTextSplitter(
        chunk_size=1000,  # 1000 chars is a good balance for Lore
        chunk_overlap=100 # Overlap ensures context isn't cut in the middle of a sentence
    )
    
    chunks = text_splitter.create_documents([md_text])
    print(f"   > Created {len(chunks)} knowledge chunks.")

    # 3. INITIALIZE EMBEDDINGS
    print("--- [3/4] Loading Embedding Model ---")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'} # Force CPU to match your app setup
    )

    # 4. CREATE & SAVE VECTOR STORE
    print("--- [4/4] Vectorizing & Indexing ---")
    
    # This does the heavy lifting: Text -> Numbers -> Index
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    vector_store.save_local(INDEX_OUTPUT_DIR)
    
    print(f"\n>>> SUCCESS. Index saved to folder: '{INDEX_OUTPUT_DIR}'")
    print(">>> You can now run 'uvicorn main:app --reload'")

if __name__ == "__main__":
    main()