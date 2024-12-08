import chromadb
import os
from config import VECTOR_DB_PATHS

def check_db():
    db_path = VECTOR_DB_PATHS['astro_ai2']
    
    print(f"Checking database at: {db_path}")
    print(f"Path exists: {os.path.exists(db_path)}")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        print(f"\nFound collections: {len(collections)}")
        
        for collection in collections:
            print(f"\nCollection: {collection.name}")
            print(f"Count: {collection.count()}")
            
            # Try to peek at the data
            try:
                peek = collection.peek()
                print(f"Sample data available: {bool(peek)}")
            except Exception as e:
                print(f"Error peeking collection: {e}")
                
    except Exception as e:
        print(f"Error accessing database: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    check_db() 