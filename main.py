from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Optional
import os
from dotenv import load_dotenv
from decimal import Decimal

from models.product import (
    ProductResponse, 
    ProductListResponse, 
    ProductFilters, 
    SortBy, 
    SortOrder
)
from services.image_search import ImageSearchService
from services.product_service import ProductService

load_dotenv()

app = FastAPI(
    title="E-commerce Image Search API",
    description="API for searching products using image similarity and browsing products with filters",
    version="1.0.0"
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

@app.get("/products", response_model=ProductListResponse)
async def get_products(
    search: Optional[str] = Query(None, description="Search query for product name/description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
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
        category=category,
        brand=brand,
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
    return {
        "categories": ["Electronics", "Clothing", "Home & Garden", "Books", "Sports", "Beauty"]
    }

@app.get("/products/brands")
async def get_brands():
    return {
        "brands": ["TechCorp", "FashionPlus", "HomeStyle", "BookWorld", "SportMax", "BeautyBest"]
    }

@app.post("/search/image", response_model=List[ProductResponse])
async def search_by_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        
        product_ids = await image_search_service.search_similar_products(contents)
        
        products = await product_service.get_products_by_ids(product_ids)
        
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)