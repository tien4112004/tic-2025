import os
import httpx
import math
from typing import List, Tuple, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.product import ProductResponse, ProductFilters, ProductListResponse, PaginationMeta, SortBy, SortOrder
from database.connection import Product, ProductImage, AsyncSessionLocal

class ProductService:
    def __init__(self):
        self.api_base_url = os.getenv("ECOMMERCE_API_BASE_URL", "")
        self.api_key = os.getenv("ECOMMERCE_API_KEY", "")
    
    async def get_products_by_ids(self, product_ids: List[str]) -> List[ProductResponse]:
        async with AsyncSessionLocal() as session:
            # Query products by product_id
            stmt = (
                select(Product, ProductImage.image_url)
                .outerjoin(ProductImage, (Product.id == ProductImage.product_id) & (ProductImage.is_primary == True))
                .where(Product.product_id.in_(product_ids))
            )
            result = await session.execute(stmt)
            rows = result.all()
            
            products = []
            for i, (product, image_url) in enumerate(rows):
                similarity_score = 0.95 - (i * 0.05) if i < len(product_ids) else 0.5
                
                product_response = ProductResponse(
                    id=product.product_id,
                    name=product.product_title,
                    price=product.price,
                    image_url=image_url or "https://example.com/placeholder.jpg",
                    description=product.description,
                    category=product.category,
                    gender=product.gender,
                    sub_category=product.sub_category,
                    product_type=product.product_type,
                    colour=product.colour,
                    in_stock=product.in_stock,
                    similarity_score=similarity_score,
                    created_at=product.created_at.isoformat() if product.created_at else None
                )
                products.append(product_response)
            
            return products
    
    async def get_products(self, filters: ProductFilters) -> ProductListResponse:
        async with AsyncSessionLocal() as session:
            # Build the base query
            query = (
                select(Product, ProductImage.image_url)
                .outerjoin(ProductImage, (Product.id == ProductImage.product_id) & (ProductImage.is_primary == True))
            )
            
            # Apply filters
            conditions = []
            
            if filters.search:
                search_term = f"%{filters.search.lower()}%"
                conditions.append(
                    or_(
                        func.lower(Product.product_title).like(search_term),
                        func.lower(Product.description).like(search_term)
                    )
                )
            
            if filters.gender:
                conditions.append(Product.gender == filters.gender)
            
            if filters.category:
                conditions.append(Product.category == filters.category)
            
            if filters.sub_category:
                conditions.append(Product.sub_category == filters.sub_category)
            
            if filters.product_type:
                conditions.append(Product.product_type == filters.product_type)
            
            if filters.colour:
                conditions.append(Product.colour == filters.colour)
            
            if filters.min_price is not None:
                conditions.append(Product.price >= filters.min_price)
            
            if filters.max_price is not None:
                conditions.append(Product.price <= filters.max_price)
            
            if filters.in_stock is not None:
                conditions.append(Product.in_stock == filters.in_stock)
            
            # Apply all conditions
            if conditions:
                query = query.where(*conditions)
            
            # Apply sorting
            if filters.sort_by == SortBy.name:
                order_col = Product.product_title
            elif filters.sort_by == SortBy.price:
                order_col = Product.price
            elif filters.sort_by == SortBy.created_at:
                order_col = Product.created_at
            else:  # popularity - use created_at as fallback
                order_col = Product.created_at
            
            if filters.sort_order == SortOrder.desc:
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())
            
            # Get total count for pagination
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total_items = total_result.scalar()
            
            # Apply pagination
            offset = (filters.page - 1) * filters.page_size
            query = query.offset(offset).limit(filters.page_size)
            
            # Execute query
            result = await session.execute(query)
            rows = result.all()
            
            # Convert to ProductResponse objects
            products = []
            for product, image_url in rows:
                product_response = ProductResponse(
                    id=product.product_id,
                    name=product.product_title,
                    price=product.price,
                    image_url=image_url or "https://example.com/placeholder.jpg",
                    description=product.description,
                    category=product.category,
                    gender=product.gender,
                    sub_category=product.sub_category,
                    product_type=product.product_type,
                    colour=product.colour,
                    in_stock=product.in_stock,
                    created_at=product.created_at.isoformat() if product.created_at else None
                )
                products.append(product_response)
            
            # Calculate pagination metadata
            total_pages = math.ceil(total_items / filters.page_size)
            pagination = PaginationMeta(
                page=filters.page,
                page_size=filters.page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_next=filters.page < total_pages,
                has_previous=filters.page > 1
            )
            
            return ProductListResponse(
                products=products,
                pagination=pagination,
                filters_applied=filters
            )
    
    async def get_available_filters(self) -> dict:
        """Get available filter options from database"""
        async with AsyncSessionLocal() as session:
            # Get distinct values for filter options
            genders_result = await session.execute(select(Product.gender).distinct().where(Product.gender.isnot(None)))
            categories_result = await session.execute(select(Product.category).distinct().where(Product.category.isnot(None)))
            sub_categories_result = await session.execute(select(Product.sub_category).distinct().where(Product.sub_category.isnot(None)))
            product_types_result = await session.execute(select(Product.product_type).distinct().where(Product.product_type.isnot(None)))
            colours_result = await session.execute(select(Product.colour).distinct().where(Product.colour.isnot(None)))
            
            return {
                "genders": sorted([g[0] for g in genders_result.all() if g[0]]),
                "categories": sorted([c[0] for c in categories_result.all() if c[0]]),
                "subcategories": sorted([sc[0] for sc in sub_categories_result.all() if sc[0]]),
                "product_types": sorted([pt[0] for pt in product_types_result.all() if pt[0]]),
                "colours": sorted([co[0] for co in colours_result.all() if co[0]])
            }
    
    async def _fetch_from_api(self, product_ids: List[str]) -> List[ProductResponse]:
        # Placeholder for actual API integration
        # This will make HTTP requests to your existing e-commerce API
        if not self.api_base_url:
            return []
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            
            try:
                response = await client.get(
                    f"{self.api_base_url}/products",
                    params={"ids": ",".join(product_ids)},
                    headers=headers
                )
                response.raise_for_status()
                
                # Parse response and convert to ProductResponse objects
                # This depends on your existing API structure
                return []
                
            except Exception as e:
                print(f"Error fetching products from API: {e}")
                return []