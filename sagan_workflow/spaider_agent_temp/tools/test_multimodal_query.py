import json
import sys
import os
from multimodal_query import NomicVisionQuerier
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VECTOR_DB_PATHS

# Initialize the querier
querier = NomicVisionQuerier()

# Query the vector database
results = querier.multimodal_vectordb_query(
    persist_dir=VECTOR_DB_PATHS['astro_ai2'],
    query="Show me comparison of Computational Density Per Watt of State-of-the-art Rad-Hard Processors",
    k=5,
)

# Print the results (structured output)
print(results)

# Optionally save results to a JSON file
with open("query_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)
