#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge_base_manager import KnowledgeBase

KB_PATH = 'knowledge_base'

# Remove the existing index to start fresh
index_path = os.path.join(KB_PATH, 'kb_index.pkl')
embeddings_path = os.path.join(KB_PATH, 'embeddings.npy')
metadata_path = os.path.join(KB_PATH, 'metadata.pkl')

for fpath in [index_path, embeddings_path, metadata_path]:
    if os.path.exists(fpath):
        os.remove(fpath)
        print(f'Removed {fpath}')

# Reload and rebuild index with TXT files only
kb = KnowledgeBase(knowledge_base_path=KB_PATH)
kb.load_documents_from_folder(os.path.join(KB_PATH, 'springworks'), collection_name='springworks')
print('\nReindex complete.')
print('KB stats:', kb.get_stats())

# Test query
from llama_ai import LlamaAI

query = "How do I verify a candidate's employment and references?"
ctx = kb.search(query, n_results=3, collection_name='springworks')
print('\nTop KB matches:')
for i, c in enumerate(ctx, 1):
    print(f"{i}) {c.get('metadata',{}).get('source')} - distance={c.get('distance')}")
    print(c.get('content')[:300].replace('\n', ' '))
    print('---')

print('\nGenerating LLM response (mixed KB + fallback)...')
ll = LlamaAI()
resp = ll.generate_response(query=query, context=ctx, user_id='test', use_history=False)
print('\nLLM Response:\n')
print(resp)
