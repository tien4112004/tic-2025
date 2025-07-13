-- Sample data for testing
-- Insert sample products with multiple images

-- Insert sample products
INSERT INTO products (product_id, gender, category, sub_category, product_type, colour, usage, product_title, description, price, brand, in_stock) VALUES
('PROD001', 'Men', 'Apparel', 'Topwear', 'Shirts', 'Blue', 'Casual', 'Men''s Blue Casual Shirt', 'Comfortable cotton casual shirt perfect for everyday wear', 29.99, 'FashionPlus', true),
('PROD002', 'Women', 'Apparel', 'Topwear', 'Tops', 'Red', 'Party', 'Women''s Red Party Top', 'Elegant red top perfect for party occasions', 45.99, 'StyleCorp', true),
('PROD003', 'Men', 'Footwear', 'Shoes', 'Sneakers', 'White', 'Sports', 'Men''s White Sports Sneakers', 'High-performance sports sneakers with advanced cushioning', 89.99, 'SportMax', true),
('PROD004', 'Women', 'Electronics', 'Mobile', 'Smartphone', 'Black', 'Work', 'Smartphone Pro X', 'Latest smartphone with advanced features and excellent camera', 699.99, 'TechCorp', true),
('PROD005', 'Unisex', 'Home & Garden', 'Decor', 'Lamp', 'Gold', 'Home', 'Designer Gold Table Lamp', 'Modern designer table lamp with adjustable brightness', 159.99, 'HomeStyle', true),
('PROD006', 'Men', 'Apparel', 'Bottomwear', 'Jeans', 'Blue', 'Casual', 'Men''s Blue Denim Jeans', 'Classic blue denim jeans with comfortable fit', 65.99, 'FashionPlus', true),
('PROD007', 'Women', 'Beauty', 'Skincare', 'Moisturizer', 'White', 'Daily', 'Daily Hydrating Moisturizer', 'Lightweight moisturizer for all skin types', 24.99, 'BeautyBest', true),
('PROD008', 'Kids', 'Toys', 'Educational', 'Building Blocks', 'Multicolor', 'Play', 'Educational Building Blocks Set', 'Creative building blocks for developing motor skills', 19.99, 'KidsWorld', true),
('PROD009', 'Men', 'Accessories', 'Watches', 'Smartwatch', 'Black', 'Sports', 'Sports Smartwatch Pro', 'Advanced fitness tracking smartwatch with GPS', 249.99, 'TechCorp', false),
('PROD010', 'Women', 'Footwear', 'Heels', 'Stilettos', 'Black', 'Formal', 'Classic Black Stiletto Heels', 'Elegant black stiletto heels for formal occasions', 79.99, 'StyleCorp', true);

-- Insert multiple images for each product
INSERT INTO product_images (product_id, image_url, is_primary) VALUES
-- PROD001 images
((SELECT id FROM products WHERE product_id = 'PROD001'), 'https://example.com/images/prod001_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD001'), 'https://example.com/images/prod001_side.jpg', false),
((SELECT id FROM products WHERE product_id = 'PROD001'), 'https://example.com/images/prod001_back.jpg', false),

-- PROD002 images
((SELECT id FROM products WHERE product_id = 'PROD002'), 'https://example.com/images/prod002_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD002'), 'https://example.com/images/prod002_detail.jpg', false),

-- PROD003 images
((SELECT id FROM products WHERE product_id = 'PROD003'), 'https://example.com/images/prod003_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD003'), 'https://example.com/images/prod003_side.jpg', false),
((SELECT id FROM products WHERE product_id = 'PROD003'), 'https://example.com/images/prod003_sole.jpg', false),

-- PROD004 images
((SELECT id FROM products WHERE product_id = 'PROD004'), 'https://example.com/images/prod004_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD004'), 'https://example.com/images/prod004_back.jpg', false),

-- PROD005 images
((SELECT id FROM products WHERE product_id = 'PROD005'), 'https://example.com/images/prod005_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD005'), 'https://example.com/images/prod005_lit.jpg', false),

-- PROD006 images
((SELECT id FROM products WHERE product_id = 'PROD006'), 'https://example.com/images/prod006_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD006'), 'https://example.com/images/prod006_detail.jpg', false),

-- PROD007 images
((SELECT id FROM products WHERE product_id = 'PROD007'), 'https://example.com/images/prod007_main.jpg', true),

-- PROD008 images
((SELECT id FROM products WHERE product_id = 'PROD008'), 'https://example.com/images/prod008_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD008'), 'https://example.com/images/prod008_built.jpg', false),

-- PROD009 images
((SELECT id FROM products WHERE product_id = 'PROD009'), 'https://example.com/images/prod009_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD009'), 'https://example.com/images/prod009_strap.jpg', false),

-- PROD010 images
((SELECT id FROM products WHERE product_id = 'PROD010'), 'https://example.com/images/prod010_main.jpg', true),
((SELECT id FROM products WHERE product_id = 'PROD010'), 'https://example.com/images/prod010_side.jpg', false);