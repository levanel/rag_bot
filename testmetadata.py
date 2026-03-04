import fitz  # PyMuPDF
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer

# 1. Initialize Qdrant and your Embedding Model
client = QdrantClient(":memory:") 
collection_name = "financial_documents"

if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

encoder = SentenceTransformer('all-MiniLM-L6-v2') 

def process_and_ingest_pdf(pdf_path, image_output_dir):
    """
    Extracts tables using PyMuPDF, takes high-res screenshots, 
    formats as Markdown, and ingests into Qdrant.
    """
    if not os.path.exists(image_output_dir):
        os.makedirs(image_output_dir)

    points = []
    
    # Open the document with PyMuPDF
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            
            # FIX 1: Pass parameters directly to PyMuPDF. 
            # Using strategy="text" and snap tolerances to bridge massive gaps.
            tables = page.find_tables(
                strategy="text", 
                snap_x_tolerance=15, 
                snap_y_tolerance=15
            )
            
            # FIX 2: Keep everything nested inside this loop!
            for table_index, table in enumerate(tables):
                text_chunk = table.to_markdown()
                
                if not text_chunk.strip():
                    continue
                
                # 2. Capture High-Res Screenshot using Bounding Box
                image_filename = f"page_{page_num + 1}_table_{table_index + 1}.png"
                image_path = os.path.join(image_output_dir, image_filename)
                
                # The Matrix(4, 4) acts like a multiplier for crisp frontend viewing
                zoom_matrix = fitz.Matrix(4, 4)
                
                # get_pixmap takes a picture of the page. 'clip' restricts it to the table's exact coordinates.
                pix = page.get_pixmap(matrix=zoom_matrix, clip=table.bbox)
                pix.save(image_path)
                
                # 3. Vectorize the Markdown text chunk
                vector = encoder.encode(text_chunk).tolist()
                
                # 4. Assemble Payload
                payload = {
                    "source_file": os.path.basename(pdf_path),
                    "page_number": page_num + 1,
                    "chunk_type": "table",
                    "text_content": text_chunk,
                    "image_path": image_path 
                }
                
                # Create a Qdrant point
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()), 
                        vector=vector, 
                        payload=payload
                    )
                )
                print(f"Processed table {table_index + 1} on page {page_num + 1}")

    # 5. Ingest into Qdrant
    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"Successfully ingested {len(points)} table chunks into Qdrant.")
    else:
        print("No tables found to ingest.")

# --- Execution ---
process_and_ingest_pdf("test.pdf", "frontend/public/table_images")