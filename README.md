# E-commerce Image Search API

A modern FastAPI-based e-commerce API with image search capabilities and comprehensive product management features.

## Features

- **Image Search**: Upload images to find similar products using vector similarity
- **Product Catalog**: Browse products with advanced filtering and search
- **Pagination**: Efficient pagination for large product catalogs
- **Sorting**: Multiple sorting options (name, price, date, popularity)
- **Filtering**: Filter by category, brand, price range, and stock status
- **Interactive Documentation**: Auto-generated API docs with Swagger UI

## API Endpoints

### Core Endpoints
- `GET /` - API root
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Products
- `GET /products` - List products with filters and pagination
- `GET /products/categories` - Get available categories
- `GET /products/brands` - Get available brands

### Image Search
- `POST /search/image` - Search products by image similarity

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/tien4112004/tic-2025.git
cd tic-2025
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python main.py
```

The API will be available at http://localhost:8000

## Usage Examples

### Browse Products
```bash
# Get all products (first page)
curl "http://localhost:8000/products"

# Search products
curl "http://localhost:8000/products?search=electronics"

# Filter by category and price
curl "http://localhost:8000/products?category=Electronics&min_price=50&max_price=200"

# Sort by price descending
curl "http://localhost:8000/products?sort_by=price&sort_order=desc"

# Pagination
curl "http://localhost:8000/products?page=2&page_size=10"
```

### Image Search
```bash
# Upload image for product search
curl -X POST "http://localhost:8000/search/image" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/image.jpg"
```

### Get Available Options
```bash
# Get categories
curl "http://localhost:8000/products/categories"

# Get brands
curl "http://localhost:8000/products/brands"
```

## API Parameters

### Product Filtering
- `search` - Search in product names and descriptions
- `category` - Filter by product category
- `brand` - Filter by brand name
- `min_price` - Minimum price filter
- `max_price` - Maximum price filter
- `in_stock` - Filter by stock availability (true/false)

### Sorting
- `sort_by` - Sort field: `name`, `price`, `created_at`, `popularity`
- `sort_order` - Sort direction: `asc`, `desc`

### Pagination
- `page` - Page number (1-based, default: 1)
- `page_size` - Items per page (1-100, default: 20)

## Project Structure

```
├── main.py                 # FastAPI application entry point
├── models/
│   ├── __init__.py
│   └── product.py         # Pydantic models and schemas
├── services/
│   ├── __init__.py
│   ├── image_search.py    # Image search logic
│   └── product_service.py # Product management logic
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── .gitignore           # Git ignore rules
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here
PINECONE_INDEX_NAME=product_images
ECOMMERCE_API_BASE_URL=https://your-ecommerce-api.com/api
ECOMMERCE_API_KEY=your_ecommerce_api_key_here
```

## Technology Stack

- **Framework**: FastAPI with async support
- **Vector Database**: Pinecone (for image search)
- **Image Processing**: Pillow
- **HTTP Client**: httpx
- **Validation**: Pydantic
- **Server**: Uvicorn with auto-reload

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License.