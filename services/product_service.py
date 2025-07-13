import os
import httpx
import math
from typing import List, Tuple
from decimal import Decimal
from datetime import datetime

from models.product import ProductResponse, ProductFilters, ProductListResponse, PaginationMeta, SortBy, SortOrder

class ProductService:
    def __init__(self):
        self.api_base_url = os.getenv("ECOMMERCE_API_BASE_URL", "")
        self.api_key = os.getenv("ECOMMERCE_API_KEY", "")
        self._mock_products = self._generate_mock_products()
    
    async def get_products_by_ids(self, product_ids: List[str]) -> List[ProductResponse]:
        # Mock implementation for now - replace with actual API calls
        mock_products = []
        
        genders = ["Men", "Women", "Unisex"]
        categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Sports", "Beauty"]
        sub_categories = ["Smartphones", "T-Shirts", "Furniture", "Fiction", "Fitness", "Skincare"]
        product_types = ["Gadget", "Apparel", "Accessory", "Book", "Equipment", "Cosmetic"]
        colours = ["Black", "White", "Blue", "Red", "Green", "Gray"]
        
        for i, product_id in enumerate(product_ids):
            product = ProductResponse(
                id=product_id,
                name=f"Product {product_id}",
                price=Decimal("29.99"),
                image_url="https://example.com/product.jpg",
                description=f"Description for {product_id}",
                category=categories[i % len(categories)],
                gender=genders[i % len(genders)],
                sub_category=sub_categories[i % len(sub_categories)],
                product_type=product_types[i % len(product_types)],
                colour=colours[i % len(colours)],
                in_stock=True,
                similarity_score=0.95 - (i * 0.05)
            )
            mock_products.append(product)
        
        return mock_products
    
    async def get_products(self, filters: ProductFilters) -> ProductListResponse:
        # Filter products based on criteria
        filtered_products = self._filter_products(self._mock_products, filters)
        
        # Calculate pagination
        total_items = len(filtered_products)
        total_pages = math.ceil(total_items / filters.page_size)
        start_idx = (filters.page - 1) * filters.page_size
        end_idx = start_idx + filters.page_size
        
        # Get page slice
        page_products = filtered_products[start_idx:end_idx]
        
        # Create pagination metadata
        pagination = PaginationMeta(
            page=filters.page,
            page_size=filters.page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=filters.page < total_pages,
            has_previous=filters.page > 1
        )
        
        return ProductListResponse(
            products=page_products,
            pagination=pagination,
            filters_applied=filters
        )
    
    def _filter_products(self, products: List[ProductResponse], filters: ProductFilters) -> List[ProductResponse]:
        filtered = products.copy()
        
        # Search filter
        if filters.search:
            search_term = filters.search.lower()
            filtered = [
                p for p in filtered 
                if search_term in p.name.lower() or 
                   (p.description and search_term in p.description.lower())
            ]
        
        # Gender filter
        if filters.gender:
            filtered = [p for p in filtered if p.gender == filters.gender]
        
        # Category filter
        if filters.category:
            filtered = [p for p in filtered if p.category == filters.category]
        
        # Sub-category filter
        if filters.sub_category:
            filtered = [p for p in filtered if p.sub_category == filters.sub_category]
        
        # Product type filter
        if filters.product_type:
            filtered = [p for p in filtered if p.product_type == filters.product_type]
        
        # Colour filter
        if filters.colour:
            filtered = [p for p in filtered if p.colour == filters.colour]
        
        # Price filters
        if filters.min_price is not None:
            filtered = [p for p in filtered if p.price >= filters.min_price]
        
        if filters.max_price is not None:
            filtered = [p for p in filtered if p.price <= filters.max_price]
        
        # Stock filter
        if filters.in_stock is not None:
            filtered = [p for p in filtered if p.in_stock == filters.in_stock]
        
        # Sort products
        filtered = self._sort_products(filtered, filters.sort_by, filters.sort_order)
        
        return filtered
    
    def _sort_products(self, products: List[ProductResponse], sort_by: SortBy, sort_order: SortOrder) -> List[ProductResponse]:
        reverse = sort_order == SortOrder.desc
        
        if sort_by == SortBy.name:
            return sorted(products, key=lambda p: p.name.lower(), reverse=reverse)
        elif sort_by == SortBy.price:
            return sorted(products, key=lambda p: p.price, reverse=reverse)
        elif sort_by == SortBy.created_at:
            return sorted(products, key=lambda p: p.created_at or "", reverse=reverse)
        elif sort_by == SortBy.popularity:
            # Mock popularity sorting by product ID
            return sorted(products, key=lambda p: p.id, reverse=reverse)
        
        return products
    
    def _generate_mock_products(self) -> List[ProductResponse]:
        categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Sports", "Beauty"]
        genders = ["Men", "Women", "Unisex"]
        sub_categories = ["Smartphones", "T-Shirts", "Furniture", "Fiction", "Fitness", "Skincare"]
        product_types = ["Gadget", "Apparel", "Accessory", "Book", "Equipment", "Cosmetic"]
        colours = ["Black", "White", "Blue", "Red", "Green", "Gray"]
        
        products = []
        for i in range(1, 101):  # Generate 100 mock products
            product = ProductResponse(
                id=f"prod_{i:03d}",
                name=f"Product {i}",
                price=Decimal(str(round(10 + (i * 2.5), 2))),
                image_url=f"https://example.com/product_{i}.jpg",
                description=f"High quality product {i} with excellent features and performance",
                category=categories[i % len(categories)],
                gender=genders[i % len(genders)],
                sub_category=sub_categories[i % len(sub_categories)],
                product_type=product_types[i % len(product_types)],
                colour=colours[i % len(colours)],
                in_stock=i % 7 != 0,  # Some products out of stock
                created_at=f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T10:00:00Z"
            )
            products.append(product)
        
        return products
    
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