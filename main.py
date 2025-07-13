from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
from typing import List, Optional
import os
import logging
from dotenv import load_dotenv
from decimal import Decimal

from models.product import (
    ProductResponse, 
    ProductListResponse, 
    ProductFilters, 
    SortBy, 
    SortOrder
)
from models.errors import ErrorResponse, ValidationErrorResponse, ErrorDetail
from services.image_search_service import ImageSearchService
from services.product_service import ProductService
from services.exceptions import APIError, ValidationError, InvalidImageError, NotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="E-commerce Image Search API",
    description="API for searching products using image similarity and browsing products with filters",
    version="1.0.0"
)

# Global exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    logger.error(f"API Error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            code=error["type"]
        ).dict())
    
    response = ValidationErrorResponse(
        message="Invalid request parameters",
        details=errors
    )
    
    logger.warning(f"Validation Error: {response.dict()}")
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            status_code=500
        ).dict()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_search_service = ImageSearchService()
product_service = ProductService()

@app.get("/")
async def root():
    return {"message": "E-commerce Image Search API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/services/status")
async def get_services_status():
    """Get the status of all services including visual search."""
    from datetime import datetime
    try:
        search_status = image_search_service.get_search_service_status()
        logger.info("Service status requested")
        return {
            "api_status": "healthy",
            "visual_search": search_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return {
            "api_status": "healthy",
            "visual_search": {"error": str(e)},
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/products", response_model=ProductListResponse)
async def get_products(
    search: Optional[str] = Query(None, description="Search query for product name/description"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sub_category: Optional[str] = Query(None, description="Filter by subcategory"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    colour: Optional[str] = Query(None, description="Filter by colour"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    sort_by: SortBy = Query(SortBy.name, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.asc, description="Sort direction"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    filters = ProductFilters(
        search=search,
        gender=gender,
        category=category,
        sub_category=sub_category,
        product_type=product_type,
        colour=colour,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    try:
        result = await product_service.get_products(filters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@app.get("/products/categories")
async def get_categories():
    filters = await product_service.get_available_filters()
    return {"categories": filters["categories"]}

@app.get("/products/genders")
async def get_genders():
    filters = await product_service.get_available_filters()
    return {"genders": filters["genders"]}

@app.get("/products/subcategories")
async def get_subcategories():
    filters = await product_service.get_available_filters()
    return {"subcategories": filters["subcategories"]}

@app.get("/products/product-types")
async def get_product_types():
    filters = await product_service.get_available_filters()
    return {"product_types": filters["product_types"]}

@app.get("/products/colours")
async def get_colours():
    filters = await product_service.get_available_filters()
    return {"colours": filters["colours"]}

@app.post("/search/image", response_model=List[ProductResponse])
async def search_by_image(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise InvalidImageError("File must be an image (JPEG, PNG, GIF, etc.)")
    
    # Validate file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise InvalidImageError("Image file too large. Maximum size is 10MB.")
    
    try:
        contents = await file.read()
        
        # Validate file is not empty
        if not contents:
            raise InvalidImageError("Image file is empty")
        
        logger.info(f"Processing image search for file: {file.filename}, size: {len(contents)} bytes")
        
        product_ids = await image_search_service.search_similar_products(contents)
        
        if not product_ids:
            logger.info("No similar products found")
            return []
        
        products = await product_service.get_products_by_ids(product_ids)
        
        logger.info(f"Found {len(products)} similar products")
        return products
        
    except InvalidImageError:
        raise
    except ValueError as e:
        raise InvalidImageError(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in image search: {str(e)}", exc_info=True)
        raise APIError(
            status_code=500,
            message="Image search service is temporarily unavailable",
            error_code="SEARCH_ERROR"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)