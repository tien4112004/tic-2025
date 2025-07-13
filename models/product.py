from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from decimal import Decimal
from enum import Enum

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class SortBy(str, Enum):
    name = "name"
    price = "price"
    created_at = "created_at"
    popularity = "popularity"

class ProductResponse(BaseModel):
    id: str
    name: str
    price: Decimal
    image_url: HttpUrl
    description: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    sub_category: Optional[str] = None
    product_type: Optional[str] = None
    colour: Optional[str] = None
    in_stock: bool = True
    similarity_score: Optional[float] = None
    created_at: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: float
        }

class ProductFilters(BaseModel):
    search: Optional[str] = Field(None, description="Search query for product name/description")
    gender: Optional[str] = Field(None, description="Filter by gender")
    category: Optional[str] = Field(None, description="Filter by category")
    sub_category: Optional[str] = Field(None, description="Filter by subcategory")
    product_type: Optional[str] = Field(None, description="Filter by product type")
    colour: Optional[str] = Field(None, description="Filter by colour")
    min_price: Optional[Decimal] = Field(None, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, description="Maximum price filter")
    in_stock: Optional[bool] = Field(None, description="Filter by stock availability")
    sort_by: Optional[SortBy] = Field(SortBy.name, description="Sort field")
    sort_order: Optional[SortOrder] = Field(SortOrder.asc, description="Sort direction")
    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    pagination: PaginationMeta
    filters_applied: ProductFilters

class SearchRequest(BaseModel):
    limit: Optional[int] = 10
    threshold: Optional[float] = 0.7

class SearchResponse(BaseModel):
    products: List[ProductResponse]
    total_found: int
    search_time_ms: float