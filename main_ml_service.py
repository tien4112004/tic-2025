# main_ml_service.py
# This file contains all the core logic for Person 2's tasks.
# VERSION 13: Replaced googletrans with deep-translator to resolve dependency conflicts.

import csv
import os
import time
from io import BytesIO
from typing import List

# --- CHANGE: Import a new, more stable translator library ---
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from PIL import Image
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

# --- Main Service Class ---
# Person 1 can import this class directly into their FastAPI application.

class MultiModalSearchService:
    """
    A service class that handles initializing ML models and performing
    multimodal (image and text) searches using Pinecone.
    """
    def __init__(self):
        """
        Initializes the Pinecone connection and loads the ML model.
        This is called once when the service is created.
        """
        print("--> Initializing MultiModalSearchService...")
        # --- Configuration ---
        load_dotenv()
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = "hackathon-fashion-search"
        self.model_name = 'clip-ViT-B-32'
        
        # --- Initialize connections ---
        self.pc: Pinecone = None
        self.pinecone_index = None
        self.model = None
        # --- CHANGE: Added a translator instance from the new library ---
        self.translator = GoogleTranslator(source='auto', target='en')
        self._initialize_services()
        print("--> Service initialized successfully.")

    def _initialize_services(self):
        """Private method to set up Pinecone and the model."""
        # 1. Initialize Pinecone
        print("    -> Step 1: Initializing Pinecone client...")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        print("        Pinecone client initialized.")

        # 2. Connect to or create the index
        print(f"    -> Step 2: Checking for index '{self.pinecone_index_name}'...")
        if self.pinecone_index_name not in self.pc.list_indexes().names():
            print(f"        Index not found. Creating new serverless index '{self.pinecone_index_name}'...")
            self.pc.create_index(
                name=self.pinecone_index_name,
                dimension=512,
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            print("        Waiting for index to be ready...")
            time.sleep(10)
            print("        Index created successfully.")
        else:
            print(f"        Index '{self.pinecone_index_name}' already exists.")

        self.pinecone_index = self.pc.Index(self.pinecone_index_name)
        print("        Successfully connected to index.")
        print("        Index Stats:", self.pinecone_index.describe_index_stats())

        # 3. Load the Sentence Transformer (CLIP) model
        print(f"    -> Step 3: Loading ML model '{self.model_name}' (this may take a moment)...")
        self.model = SentenceTransformer(self.model_name)
        print("        Model loaded into memory.")

    # --- Search Functions ---

    def search_by_image(self, image_file: BytesIO, top_k: int = 5) -> List[str]:
        """
        Takes an image file (as bytes), converts it to a vector, and queries Pinecone.
        """
        if not self.pinecone_index or not self.model:
            print("ERROR: Service not fully initialized.")
            return []
        try:
            print(f"\n[STARTING IMAGE SEARCH] for top {top_k} products.")
            img = Image.open(image_file).convert("RGB")
            query_vector = self.model.encode(img).tolist()
            query_results = self.pinecone_index.query(
                vector=query_vector, top_k=top_k, include_metadata=False
            )
            product_ids = [match['id'] for match in query_results['matches']]
            print(f"  -> Found matches: {product_ids}")
            print("[IMAGE SEARCH COMPLETE]")
            return product_ids
        except Exception as e:
            print(f"An error occurred during image search: {e}")
            return []

    def search_by_text(self, text_query: str, top_k: int = 5) -> List[str]:
        """
        Takes a text query, translates it to English, converts it to a vector, 
        and queries the image index.
        """
        if not self.pinecone_index or not self.model:
            print("ERROR: Service not fully initialized.")
            return []
        try:
            print(f"\n[STARTING TEXT SEARCH] for: '{text_query}'")
            
            # --- CHANGE: Use the new translator library ---
            translated_query = text_query
            try:
                # The new library handles detection and translation in one simple step
                translated_query = self.translator.translate(text_query)
                print(f"    -> Translated query to English: '{translated_query}'")
            except Exception as e:
                print(f"    -> Warning: Could not translate text. Using original query. Error: {e}")

            print("  -> Generating vector for query text...")
            query_vector = self.model.encode(translated_query).tolist()
            
            print("  -> Querying Pinecone index...")
            query_results = self.pinecone_index.query(
                vector=query_vector, top_k=top_k, include_metadata=False
            )
            product_ids = [match['id'] for match in query_results['matches']]
            print(f"  -> Found matches: {product_ids}")
            print("[TEXT SEARCH COMPLETE]")
            return product_ids
        except Exception as e:
            print(f"An error occurred during text search: {e}")
            return []

# --- Indexing Function (to be run offline, not part of the live service) ---

def index_products_from_csv(service: MultiModalSearchService, csv_file_path: str, base_images_path: str):
    """
    Utility function to index products. This should be run separately and not as part of the API.
    """
    pinecone_index = service.pinecone_index
    model = service.model
    
    print(f"\n[STARTING INDEXING PROCESS]")
    print("--> Checking for already indexed products...")
    existing_ids = set(pinecone_index.list())
    print(f"    Found {len(existing_ids)} existing products.")

    batch_size = 64
    vectors_to_upsert = []

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        all_rows = list(csv.DictReader(f))
        rows_to_process = [row for row in all_rows if os.path.splitext(row['Image'])[0] not in existing_ids]
        
        total_to_process = len(rows_to_process)
        if total_to_process == 0:
            print("All products are already indexed.")
            return
        print(f"{total_to_process} new products to be indexed.")

        for i, row in enumerate(rows_to_process):
            if (i + 1) % 25 == 0:
                print(f"  -> Progress: Processing new image {i + 1}/{total_to_process}...")
            
            try:
                category = row['Category']
                gender = row['Gender']
                image_filename = row['Image']
                product_id = os.path.splitext(image_filename)[0]

                image_path = os.path.join(
                    base_images_path, category, gender, 'Images', 'images_with_product_ids', image_filename
                )
                
                if not os.path.exists(image_path): continue

                img = Image.open(image_path).convert("RGB")
                embedding = model.encode(img).tolist()
                vectors_to_upsert.append((product_id, embedding))

                if len(vectors_to_upsert) >= batch_size:
                    pinecone_index.upsert(vectors=vectors_to_upsert)
                    vectors_to_upsert = []
            except Exception as e:
                print(f"ERROR processing row {row}: {e}")


    if vectors_to_upsert:
        pinecone_index.upsert(vectors=vectors_to_upsert)

    print("\n[INDEXING COMPLETE]")
    print("Final Index Stats:", pinecone_index.describe_index_stats())


# --- Main Execution Block (Example of how to use the service) ---
if __name__ == '__main__':
    
    print("--- DEMONSTRATING SERVICE USAGE ---")
    
    search_service = MultiModalSearchService()
    
    # UNCOMMENT THE LINES BELOW TO RUN INDEXING
    # print("\n--- Starting offline indexing task ---")
    # path_to_your_csv = "fashion_data/fashion.csv" 
    # path_to_your_images_folder = "fashion_data"
    # index_products_from_csv(search_service, path_to_your_csv, path_to_your_images_folder)
    # print("--- Offline indexing task finished ---")

    print("\n--- Running a test text search in Vietnamese ---")
    search_query = "áo sơ mi màu xanh cho nam"
    text_search_results = search_service.search_by_text(search_query, top_k=3)
    print(f"Top 3 results for '{search_query}': {text_search_results}")
    print("------------------------------------")
