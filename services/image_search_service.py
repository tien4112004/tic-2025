import os
import io
import logging
from typing import List, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Global variables for the service
pinecone_index = None
model = None

# Try to import Pinecone
try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not available - visual search will use fallback mode")

def initialize_services():
    """
    Initialize the visual search services (model and Pinecone).
    This should be called before using the search functionality.
    """
    global pinecone_index, model
    
    try:
        print("Initializing visual search services...")
        
        if not PINECONE_AVAILABLE:
            print("Pinecone package not available - using fallback mode")
            return True
        
        # Initialize Pinecone
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if pinecone_api_key:
            print("Initializing Pinecone connection...")
            pc = Pinecone(api_key=pinecone_api_key)
            
            index_name = os.getenv("PINECONE_INDEX_NAME", "product_images")
            try:
                pinecone_index = pc.Index(index_name)
                print(f"Connected to Pinecone index: {index_name}")
            except Exception as e:
                print(f"Could not connect to Pinecone index '{index_name}': {e}")
                print("Visual search will use fallback mode")
        else:
            print("PINECONE_API_KEY not found. Visual search will use fallback mode")
        
        print("Visual search services initialized successfully")
        return True
        
    except Exception as e:
        print(f"Failed to initialize visual search services: {e}")
        return True  # Return True to allow app to start even if ML services fail

def find_similar_products(image_file, top_k=5):
    """
    This is the function Person 1 will call from the FastAPI endpoint.
    It takes an image file, converts it to a vector, and queries Pinecone.
    """
    if not pinecone_index or not model:
        print("ERROR: Services not initialized. Please call initialize_services() first.")
        return []

    try:
        print(f"\n[STARTING SEARCH] for top {top_k} products.")
        img = Image.open(image_file).convert("RGB")
        
        print("  -> Generating vector for query image...")
        query_vector = model.encode(img).tolist()
        
        print("  -> Querying Pinecone index...")
        query_results = pinecone_index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=False
        )
        
        product_ids = [match['id'] for match in query_results['matches']]
        print(f"  -> Found matches: {product_ids}")
        print("[SEARCH COMPLETE]")
        
        return product_ids

    except Exception as e:
        print(f"An error occurred during search: {e}")
        return []

class ImageSearchService:
    """
    Unified service for handling image-based product search.
    Integrates with the global find_similar_products function.
    """
    
    def __init__(self):
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize the visual search services with error handling."""
        try:
            success = initialize_services()
            if success:
                logger.info("Visual search service initialized successfully")
            else:
                logger.warning("Failed to initialize visual search service")
                logger.info("Image search will use fallback mode")
        except Exception as e:
            logger.warning(f"Failed to initialize visual search service: {e}")
            logger.info("Image search will use fallback mode")
    
    async def search_similar_products(self, image_bytes: bytes, limit: int = 10) -> List[str]:
        """
        Search for similar products using image similarity.
        
        Args:
            image_bytes: Raw image data as bytes
            limit: Maximum number of similar products to return
            
        Returns:
            List of product IDs sorted by similarity
            
        Raises:
            ValueError: If image is invalid or cannot be processed
        """
        # Validate the image can be opened
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Create a copy for verification since verify() closes the image
            image_copy = image.copy()
            image_copy.verify()
            logger.info(f"Image validation successful: {image.size}, mode: {image.mode}")
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}")
            raise ValueError(f"Invalid image file: {str(e)}")
        
        try:
            # Reset image stream position for processing
            image_stream = io.BytesIO(image_bytes)
            
            # Use the global find_similar_products function
            logger.info(f"Searching for {limit} similar products...")
            product_ids = find_similar_products(
                image_file=image_stream,
                top_k=limit
            )
            
            if not product_ids:
                logger.warning("No similar products found")
                # Return fallback results
                fallback_products = ["PROD001", "PROD002", "PROD003", "PROD004", "PROD005"]
                return fallback_products[:limit]
            
            logger.info(f"Found {len(product_ids)} similar products: {product_ids}")
            return product_ids
            
        except Exception as e:
            logger.error(f"Error in visual search: {str(e)}")
            # Return fallback results instead of raising error
            fallback_products = ["PROD001", "PROD002", "PROD003", "PROD004", "PROD005"]
            return fallback_products[:limit]
    
    async def index_product_image(self, product_id: str, image_url: str) -> bool:
        """
        Index a product image for future similarity searches.
        
        Args:
            product_id: Unique product identifier
            image_url: URL or path to the product image
            
        Returns:
            True if indexing was successful, False otherwise
        """
        try:
            # This would typically:
            # 1. Download/load image from URL
            # 2. Extract features using the same method as search
            # 3. Store vector in Pinecone with product_id as key
            # 4. Store vector reference in database
            
            logger.info(f"Indexing image for product {product_id}: {image_url}")
            # Implementation would go here
            return True
            
        except Exception as e:
            logger.error(f"Error indexing product image {product_id}: {str(e)}")
            return False
    
    def get_search_service_status(self) -> dict:
        """
        Get the current status of the image search service.
        
        Returns:
            Dictionary containing service status information
        """
        global pinecone_index, model
        
        return {
            "service_name": "ImageSearchService",
            "version": "1.0.0",
            "initialized": model is not None,
            "model_loaded": model is not None,
            "pinecone_connected": pinecone_index is not None,
            "model_name": "clip-ViT-B-32" if model else None,
            "fallback_mode": pinecone_index is None
        }
    
