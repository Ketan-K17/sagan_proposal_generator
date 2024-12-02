import os
import torch
import fitz  # PyMuPDF
from transformers import AutoModel, AutoTokenizer
from langchain_community.vectorstores import Chroma
from langchain.embeddings.base import Embeddings
from typing import List, Dict, Union
from PIL import Image
import io


class NomicVisionQuerier(Embeddings):
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1"):
        print(f"Loading model {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        self.images_dir = "retrieved_images"
        os.makedirs(self.images_dir, exist_ok=True)

    def search_similar(self, persist_dir: str, query: str, k: int = 5) -> Dict[str, List[Dict[str, Union[str, List[str]]]]]:
        try:
            vector_store = Chroma(persist_directory=persist_dir, embedding_function=self)
            results = vector_store.similarity_search_with_relevance_scores(query, k=k)
            print(f"Raw Tool Results: {results}")

            formatted_results = []
            for doc, score_dict in results:
                score = score_dict.get('relevance', 0) if isinstance(score_dict, dict) else score_dict
                metadata = doc.metadata
                content = doc.page_content
                source = metadata.get("source", "Unknown source")
                page_num = metadata.get("page", 0)
                images = self.extract_images_from_pdf(source, page_num)
                formatted_results.append({"content": content, "images": images, "score": score})

            return {"Results": formatted_results}
        except Exception as e:
            print(f"Error in search_similar: {e}")
            raise

    def extract_images_from_pdf(self, pdf_path: str, page_num: int) -> List[str]:
        """Extract images from a specific page of a PDF and save them."""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num - 1]  # Convert to 0-based index
            image_list = page.get_images()
            saved_images = []

            for img_idx, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Generate unique filename
                    image_filename = f"{os.path.basename(pdf_path)}_page{page_num}_img{img_idx}.png"
                    image_path = os.path.join(self.images_dir, image_filename)

                    # Save image
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)

                    saved_images.append(image_path)
                except Exception as e:
                    print(f"Error extracting image {img_idx}: {str(e)}")

            return saved_images
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            return []

    def embed_query(self, query: str) -> List[float]:
        """Generate embeddings for query text."""
        inputs = self.tokenizer(query, return_tensors="pt", padding=True, truncation=True)
        if self.device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

        return embedding[0].tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Required by Langchain but not used for querying."""
        return [self.embed_query(text) for text in texts]

    def multimodal_vectordb_query(
        self, persist_dir: str, query: str, k: int = 5
    ) -> Dict[str, List[Dict[str, Union[str, List[str]]]]]:
        """Search for similar items and return results in section_answers schema."""
        vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=self,
        )

        print(f"\nProcessing query: {query}\n")

        results = vector_store.similarity_search_with_relevance_scores(query, k=k)

        if not results:
            print("No results found.")
            return {"Results": []}

        formatted_results = []

        for doc, score in results:
            metadata = doc.metadata
            content = doc.page_content
            source = metadata.get("source", "Unknown source")
            page_num = metadata.get("page", 0)

            # Extract images
            images = self.extract_images_from_pdf(source, page_num)

            # Format the result to match section_answers schema
            formatted_results.append({
                "content": content,
                "images": images,
            })

        return {"Results": formatted_results}