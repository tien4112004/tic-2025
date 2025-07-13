import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, Boolean, DECIMAL, Text, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
import uuid

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ecommerce_user:ecommerce_password@localhost:5432/ecommerce_db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()

# SQLAlchemy models
class Product(Base):
    __tablename__ = "products"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(String(50), unique=True, nullable=False)
    gender = Column(String(20))
    category = Column(String(100), nullable=False)
    sub_category = Column(String(100))
    product_type = Column(String(100))
    colour = Column(String(50))
    usage = Column(String(50))
    product_title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    brand = Column(String(100))
    in_stock = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))
    image_url = Column(String(1000), nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Create tables (for development)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)