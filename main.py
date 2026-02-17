from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import CrossEncoder
from sklearn.decomposition import PCA
import numpy as np
import asyncio
import random
app = FastAPI()

# --- LOAD SYSTEMS ---
print("--- SYSTEMS ONLINE ---")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2", model_kwargs={'device': 'cpu'})
reranker = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2', max_length=512)
vector_store = FAISS.load_local("faiss_gpt4_index", embeddings, allow_dangerous_deserialization=True)
llm = ChatOllama(model="phi4-mini-custom", temperature=0.1)

# --- MAP PRE-CALCULATION ---
n_total = vector_store.index.ntotal
all_vectors = vector_store.index.reconstruct_n(0, n_total)
pca = PCA(n_components=3)
pca.fit(all_vectors)
map_coords = pca.transform(all_vectors).tolist() 

docstore = vector_store.docstore
index_to_id = vector_store.index_to_docstore_id
all_docs_text = []
for i in range(n_total):
    doc = docstore.search(index_to_id[i])
    all_docs_text.append(doc.page_content[:150] + "...")

@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

@app.get("/api/map-data")
async def get_map_data():
    return {"coords": map_coords, "texts": all_docs_text}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            query = data

            # --- STEP 1: INITIALIZATION ---
            await websocket.send_json({"type": "log", "message": "Searching vector space."})
            
            # Send the Query Coordinate (Red Star)
            query_vec = embeddings.embed_query(query)
            query_proj = pca.transform([query_vec])[0].tolist()
            await websocket.send_json({
                "type": "map_update", 
                "step": "query", 
                "coords": query_proj
            })
            await asyncio.sleep(0.5)

            # --- STEP 2: SCANNING EFFECT (The "Matrix" lines) ---
            await websocket.send_json({"type": "log", "message": "[SYSTEM] SCANNING INDEX 0x1A..."})
            
            # Fake scanning effect: rapid fire log of "Checking Vector ID..."
            for _ in range(5):
                fake_id = f"0x{random.randint(1000,9999)}"
                fake_score = random.random()
                await websocket.send_json({"type": "log", "message": f"   > CHECKING VECTOR {fake_id} // SIMILARITY: {fake_score:.4f}"})
                await asyncio.sleep(0.1) # Fast scroll

            # --- STEP 3: RETRIEVAL (Yellow Candidates) ---
            docs = vector_store.similarity_search(query, k=20)
            
            # Find indices for visual map
            retrieved_indices = []
            for d in docs:
                try:
                    snippet = d.page_content[:150] + "..."
                    idx = all_docs_text.index(snippet)
                    retrieved_indices.append(idx)
                except: continue

            await websocket.send_json({
                "type": "map_update", 
                "step": "retrieval", 
                "indices": retrieved_indices
            })
            
            await websocket.send_json({"type": "log", "message": f"[RESULT] 20 CANDIDATES IDENTIFIED."})
            
            # List the candidates in the log
            for i, d in enumerate(docs[:3]): # Just show top 3 to not spam too hard
                await websocket.send_json({"type": "log", "message": f"   > CANDIDATE {i+1}: {d.page_content[:40]}..."})
            
            await asyncio.sleep(1.5) 

            # --- STEP 4: RERANKING (The One-by-One Reveal) ---
            await websocket.send_json({"type": "log", "message": "[FILTER] ENGAGING CROSS-ENCODER..."})
            
            pairs = [[query, doc.page_content] for doc in docs]
            scores = reranker.predict(pairs)
            scored_docs = sorted(list(zip(scores, docs)), key=lambda x: x[0], reverse=True)[:5]
            top_docs = [doc for score, doc in scored_docs]
            
            # Identify the final "Green" indices
            top_indices = []
            for d in top_docs:
                try:
                    snippet = d.page_content[:150] + "..."
                    idx = all_docs_text.index(snippet)
                    top_indices.append(idx)
                except: continue

            # REVEAL LOOP: Turn them green one by one
            current_green_list = []
            for idx in top_indices:
                current_green_list.append(idx)
                # Send update to turn this specific set green
                await websocket.send_json({
                    "type": "map_update", 
                    "step": "rerank", 
                    "indices": current_green_list 
                })
                # Log the lock-on
                await websocket.send_json({"type": "log", "message": f"   > VERIFIED SOURCE ID: {idx} [LOCKED]"})
                await asyncio.sleep(2) # 0.8s pause between each green dot reveal

            await websocket.send_json({"type": "log", "message": "[COMPLETE] RELEVANCE FILTERING FINISHED."})
            await asyncio.sleep(1)

            # --- STEP 5: GENERATION ---
            await websocket.send_json({"type": "log", "message": "[PROCESS] PROCESSING ANSWER..."})
            
            context = "\n".join([d.page_content for d in top_docs])
            template = "[INST] Context: {context} \n\n Question: {question} \n\n Answer: [/INST]"
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | llm | StrOutputParser()
            
            full_answer = ""
            async for chunk in chain.astream({"context": context, "question": query}):
                full_answer += chunk
                await websocket.send_json({"type": "token", "content": chunk})
            
            await websocket.send_json({"type": "done"})

    except Exception as e:
        print(f"Error: {e}")

app.mount("/static", StaticFiles(directory="static"), name="static")
