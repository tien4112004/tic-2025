# image_search.py (Person 1's file)

import io
from typing import List

from PIL import Image

# --- CHANGE: Import your service class ---
from main_ml_service import MultiModalSearchService

# --- CHANGE: Create one instance of the service when the app starts ---
# The ML models and Pinecone connection will be loaded once here.
search_service = MultiModalSearchService()


class ImageSearchService:
    def __init__(self):
        # The __init__ can be empty now, as the service is already initialized globally.
        pass
    
    async def search_similar_products(self, image_bytes: bytes, limit: int = 10) -> List[str]:
        # Validate the image can be opened
        try:
            image_file = io.BytesIO(image_bytes)
            image = Image.open(image_file)
            image.verify()
            # Reset cursor after verify
            image_file.seek(0)
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
        
        # --- CHANGE: Replace placeholder with a call to your real service method ---
        product_ids = search_service.search_by_image(image_file=image_file, top_k=limit)
        
        return product_ids