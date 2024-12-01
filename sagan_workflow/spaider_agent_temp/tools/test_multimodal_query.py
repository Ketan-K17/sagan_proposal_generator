from multimodal_query import NomicVisionQuerier

# Initialize the querier
querier = NomicVisionQuerier()

# Query the vector database
results = querier.multimodal_vectordb_query(
    persist_dir="C:/UniLu/Spaider/sagan/SAW_code_21_11_2024/SAW_code_plus_db-main/ingest_data/astroai2",
    query="Show me comparison of Computational Density Per Watt of State-of-the-art Rad-Hard Processors",
    k=5,
)

# Print the results (structured output)
print(results)

# Optionally save results to a JSON file
import json
with open("query_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)
