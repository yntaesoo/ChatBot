import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('langchain')

# Check all unique sources
data = collection.get()
sources = set()
for meta in data['metadatas']:
    if meta and 'source' in meta:
        sources.add(meta['source'])

print("Unique sources in DB:")
for s in sources:
    print(f"- {s}")

# Check specific dummy file chunks
dummy_chunks = [meta for meta in data['metadatas'] if meta and 'dummy' in meta.get('source', '')]
print(f"\nFound {len(dummy_chunks)} chunks for dummy files.")
