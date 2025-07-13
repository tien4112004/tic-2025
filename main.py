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
import math

from models.product import (
    ProductResponse, 
    ProductListResponse, 
    ProductFilters, 
    PaginationMeta,
    SortBy, 
    SortOrder
)
from models.errors import ErrorResponse, ValidationErrorResponse, ErrorDetail
from services.image_search_service import ImageSearchService
from services.product_service import ProductService
from services.exceptions import APIError, ValidationError, InvalidImageError, NotFoundError
from main_ml_service import MultiModalSearchService

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
ml_search_service = MultiModalSearchService()

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
        # Get regular database search results
        db_result = await product_service.get_products(filters)
        
        # If there's a search query, also perform ML text search
        if search and search.strip():
            try:
                logger.info(f"Performing ML text search for query: {search}")
                # Get ML search results (product IDs)
                ml_product_ids = ml_search_service.search_by_text(search, top_k=10)
                
                if ml_product_ids:
                    # Get product details for ML results
                    ml_products = await product_service.get_products_by_ids(ml_product_ids)
                    
                    # Apply the same filters to ML results (except search)
                    filtered_ml_products = _apply_filters_to_products(ml_products, filters)
                    
                    # Merge results: prioritize ML results, then add unique DB results
                    merged_products = _merge_search_results(filtered_ml_products, db_result.products)
                    
                    # Apply pagination to merged results
                    paginated_products, updated_pagination = _paginate_merged_results(
                        merged_products, filters.page, filters.page_size
                    )
                    
                    logger.info(f"Merged search results: {len(paginated_products)} products")
                    return ProductListResponse(
                        products=paginated_products,
                        pagination=updated_pagination,
                        filters_applied=filters
                    )
                else:
                    logger.info("No ML search results found, returning database results only")
            except Exception as ml_error:
                logger.error(f"ML search failed, falling back to database search: {ml_error}")
        
        return db_result
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

# Helper functions for merging search results
def _apply_filters_to_products(products: List[ProductResponse], filters: ProductFilters) -> List[ProductResponse]:
    """Apply filters to a list of products (excluding search filter)"""
    filtered_products = []
    
    for product in products:
        # Apply filters
        if filters.gender and product.gender != filters.gender:
            continue
        if filters.category and product.category != filters.category:
            continue
        if filters.sub_category and product.sub_category != filters.sub_category:
            continue
        if filters.product_type and product.product_type != filters.product_type:
            continue
        if filters.colour and product.colour != filters.colour:
            continue
        if filters.min_price is not None and product.price < filters.min_price:
            continue
        if filters.max_price is not None and product.price > filters.max_price:
            continue
        if filters.in_stock is not None and product.in_stock != filters.in_stock:
            continue
        
        filtered_products.append(product)
    
    return filtered_products

def _merge_search_results(ml_products: List[ProductResponse], db_products: List[ProductResponse]) -> List[ProductResponse]:
    """Merge ML search results with database search results, prioritizing ML results"""
    # Create a set of ML product IDs for quick lookup
    ml_product_ids = {product.id for product in ml_products}
    
    # Start with ML products (they have similarity scores)
    merged_products = ml_products.copy()
    
    # Add database products that are not already in ML results
    for db_product in db_products:
        if db_product.id not in ml_product_ids:
            # Set a lower similarity score for database-only results
            db_product.similarity_score = 0.3
            merged_products.append(db_product)
    
    # Sort by similarity score (descending) to prioritize ML results
    merged_products.sort(key=lambda x: x.similarity_score or 0, reverse=True)
    
    return merged_products

def _paginate_merged_results(products: List[ProductResponse], page: int, page_size: int) -> tuple[List[ProductResponse], PaginationMeta]:
    """Apply pagination to merged results and return pagination metadata"""
    total_items = len(products)
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get page of products
    paginated_products = products[offset:offset + page_size]
    
    # Create pagination metadata
    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    
    return paginated_products, pagination

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)