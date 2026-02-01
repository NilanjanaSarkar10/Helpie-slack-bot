from knowledge_base_manager import KnowledgeBase
from llama_ai import LlamaAI
import os

KB_PATH='knowledge_base'
COL='springworks'

print('Loading existing knowledge base...')
kb = KnowledgeBase(knowledge_base_path=KB_PATH)

# 1) Tag untagged documents
untagged = 0
for m in kb.metadatas:
    if not m.get('collection'):
        m['collection'] = COL
        untagged += 1
if untagged:
    kb._save_index()
print(f'Tagged {untagged} previously untagged metadata entries as "{COL}"')

# 2) Reindex with tuned chunking
print('Reindexing with chunk_size=300, overlap=50...')

# Create a fresh KB instance to re-build index
new_kb = KnowledgeBase(knowledge_base_path=KB_PATH)

# Bind a custom chunking function
def custom_chunk(self, text: str, chunk_size: int = 300, overlap: int = 50):
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    if step <= 0:
        step = max(1, chunk_size)
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks if chunks else [text]

new_kb._chunk_text = custom_chunk.__get__(new_kb, KnowledgeBase)

# Clear and reload springworks folder
new_kb.clear()
new_kb.load_documents_from_folder(os.path.join(KB_PATH, COL), collection_name=COL)
print('Reindex done. Stats:', new_kb.get_stats())

# 3) Sample verification query
query = "How do I verify a candidate's employment and reference?"
print('\nSample Query:', query)
context = new_kb.search(query, n_results=3, collection_name=COL)
print('\nTop 3 KB matches:')
for i, ctx in enumerate(context, 1):
    src = ctx.get('metadata', {}).get('source')
    dist = ctx.get('distance')
    print(f'{i}) source={src}, distance={dist:.4f}')
    print(ctx.get('content')[:400].strip())
    print('---')

# Generate LLM response
ll = LlamaAI()
resp = ll.generate_response(query=query, context=context, user_id='tester', use_history=False)
print('\nLLM Response:\n')
print(resp)
