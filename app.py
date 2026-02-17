import chainlit as cl
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import CrossEncoder
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import numpy as np
import io
import asyncio
import random
from langchain_huggingface import HuggingFaceEmbeddings
# --- 1. SYSTEM BOOT SEQUENCE ---
print("--- INITIATING NEURAL LINK ---")
print("[SYSTEM] Loading Embedding Matrix (CPU)...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'}
)

print("[SYSTEM] Calibrating Cross-Encoder Reranker...")
reranker = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2', max_length=512)

print("[SYSTEM] Accessing Vector Archive (FAISS)...")
vector_store = FAISS.load_local(
    "faiss_gpt4_index", 
    embeddings, 
    allow_dangerous_deserialization=True
)

print("[SYSTEM] Waking Mistral-7B Nexus...")
llm = ChatOllama(model="phi4-mini-custom", temperature=0.1)

# Prompt
template = """[INST] You are an expert scholar of provided context. 
Answer the question based ONLY on the provided Context.

Context:
{context}

Question: 
{question} 
[/INST]"""
prompt = ChatPromptTemplate.from_template(template)


# --- SCI-FI VISUALIZATION FUNCTION ---
def plot_sci_fi_network(query, all_docs, top_docs_indices, embedding_model):
    """
    Generates a 'holographic' style network graph.
    """
    plt.style.use('dark_background') # Sci-fi look
    
    # 1. Get embeddings & Reduce to 2D
    query_vec = embedding_model.embed_query(query)
    doc_vecs = embedding_model.embed_documents([d.page_content for d in all_docs])
    all_vecs = np.array([query_vec] + doc_vecs)
    
    pca = PCA(n_components=2)
    reduced_vecs = pca.fit_transform(all_vecs)
    
    # Separate coordinates
    qx, qy = reduced_vecs[0]
    dx, dy = reduced_vecs[1:, 0], reduced_vecs[1:, 1]

    fig, ax = plt.subplots(figsize=(10, 7))
    # Turn off axes for a cleaner 'interface' look
    ax.axis('off')
    
    # Faint background grid
    ax.grid(True, color='#00ffff', linestyle=':', linewidth=0.5, alpha=0.2)

    # 2. Plot "Background Noise" (Unselected Docs) - Faint Blue Hexagons
    ax.scatter(dx, dy, c='#0088ff', marker='h', s=80, alpha=0.3, label='Latent Data Nodes')

    # 3. Plot Query Protocol (Red Star with Glow)
    # Outer glow
    ax.scatter(qx, qy, c='#ff0000', marker='*', s=500, alpha=0.2)
    # Inner core
    ax.scatter(qx, qy, c='#ff3333', marker='*', s=250, edgecolors='white', linewidth=1, label='Active Query Protocol')
    ax.text(qx+0.05, qy+0.05, f"[QUERY-ORIGIN]\nCoords: {qx:.2f}, {qy:.2f}", color='red', fontsize=8)

    # 4. Plot & Connect Top Reranked Docs (Bright Cyan/Green with connections)
    for i in top_docs_indices:
        # The actual doc coordinate (offset by 1 because index 0 is query)
        doc_x, doc_y = reduced_vecs[i+1]
        
        # Draw glowing connection line from Query to Doc
        ax.plot([qx, doc_x], [qy, doc_y], color='#00ffff', linestyle='-', linewidth=1.5, alpha=0.6)
        
        # Draw the Node (Bright Green Hexagon)
        ax.scatter(doc_x, doc_y, c='#00ff88', marker='h', s=180, edgecolors='#ffffff', linewidth=1)
        
        # Add fake technical ID annotation
        fake_id = f"VEC-{random.randint(100,999)}-{chr(random.randint(65,90))}"
        ax.text(doc_x+0.03, doc_y+0.03, f"[{fake_id}]\nRel: High", color='#00ff88', fontsize=7)

    plt.title(">> NEURAL VECTOR SPACE TRIANGULATION <<", color='#00ffff', fontsize=12, pad=20)
    
    # Save to stream
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', facecolor='black', edgecolor='none', bbox_inches='tight')
    img_buf.seek(0)
    plt.close()
    return img_buf

@cl.on_chat_start
async def start():
    await cl.Message(content="**Elden Ring Archive Interface Initialized.**\nReady for query input...").send()

@cl.on_message
async def main(message: cl.Message):
    
    # --- DRAMATIC SEQUENCE START ---
    
    # STEP 1: Retrieval (With artificial delay)
    async with cl.Step(name="[1/3] Initializing Vector Sweep...", type="tool") as step:
        # Do the actual work instantly
        raw_docs = vector_store.similarity_search(message.content, k=15)
        step.output = f"Sweep complete. Detected {len(raw_docs)} latent data points."
        # DRAMATIC PAUSE
        await asyncio.sleep(2.5)

    # STEP 2: Reranking (With artificial delay)
    async with cl.Step(name="[2/3] Engaging Cross-Encoder Rerank Protocols...", type="tool") as step:
        # Do the actual work instantly
        pairs = [[message.content, doc.page_content] for doc in raw_docs]
        scores = reranker.predict(pairs)
        scored_docs = sorted(list(zip(scores, raw_docs)), key=lambda x: x[0], reverse=True)
        
        # Keep top 5, but also keep track of their original indices for plotting
        top_docs_with_indices = []
        for i, (score, doc) in enumerate(scored_docs):
            if i < 5:
                 # Find where this doc was in the original raw_docs list
                original_index = raw_docs.index(doc)
                top_docs_with_indices.append((doc, original_index))

        top_docs = [t[0] for t in top_docs_with_indices]
        top_indices = [t[1] for t in top_docs_with_indices]

        step.output = f"Reranking complete. Isolated top {len(top_docs)} high-relevance nodes."
        # DRAMATIC PAUSE
        await asyncio.sleep(2.5)

    # STEP 3: Visualization (With artificial delay)
    async with cl.Step(name="[3/3] Generating Neural Network Topology Map...", type="tool") as step:
        # Do the work
        img_stream = plot_sci_fi_network(message.content, raw_docs, top_indices, embeddings)
        
        image = cl.Image(
            name="neural_map",
            content=img_stream.getvalue(),
            display="inline"
        )
        step.elements = [image]
        step.output = "Topology visualized. Establishing connection to Mistral Nexus."
        # DRAMATIC PAUSE (Longer for the map effect)
        await asyncio.sleep(3.5)

    # --- MISTRAL GENERATION ---
    
    # Prepare context & elements
    source_elements = [image] # Add map to final answer
    context_text = ""
    for i, doc in enumerate(top_docs):
        context_text += f"\n\n-- Source Node {i+1} --\n{doc.page_content}"
        source_elements.append(
            cl.Text(content=doc.page_content, name=f"Node {i+1} Data", display="side")
        )

    chain = prompt | llm | StrOutputParser()
    inputs = {"context": context_text, "question": message.content}

    # Create the message bubble WITH the cool map and sources already attached
    msg = cl.Message(content="", elements=source_elements)
    await msg.send()
    
    # Stream the answer slowly
    async for chunk in chain.astream(inputs):
        await msg.stream_token(chunk)
    
    await msg.update()
