#!/usr/bin/env python3
import sys
import os
# ensure project root is on sys.path so imports work when run as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from knowledge_base_manager import KnowledgeBase

KB_PATH = 'knowledge_base'
kb = KnowledgeBase(knowledge_base_path=KB_PATH)
processed_folders = 0
for root, dirs, files in os.walk(KB_PATH):
    pdfs = [f for f in files if f.lower().endswith('.pdf')]
    if not pdfs:
        continue
    rel = os.path.relpath(root, KB_PATH)
    collection = rel if rel != '.' else None
    print(f'Processing folder: {root} -> collection: {collection}')
    kb.load_documents_from_folder(root, collection_name=collection)
    processed_folders += 1

print('\nFinished. Processed folders:', processed_folders)
print('KB stats:', kb.get_stats())

# Sample verification query against 'springworks' if present
query = "How do I verify a candidate's employment and references?"
col = 'springworks'
if os.path.isdir(os.path.join(KB_PATH, col)):
    ctx = kb.search(query, n_results=5, collection_name=col)
    print('\nTop matches for collection springworks:')
    for i,c in enumerate(ctx,1):
        print(f"{i}) {c.get('metadata',{}).get('source')} - distance={c.get('distance')}")
        print(c.get('content')[:300].replace('\n',' '))
        print('---')
else:
    print('\nNo springworks collection found; skipping sample query.')
