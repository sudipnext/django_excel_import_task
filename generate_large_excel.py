import pandas as pd
import numpy as np
from faker import Faker
import random
import time
import argparse

# Constants for product data
AVAILABILITY_CHOICES = ['in_stock', 'out_of_stock', 'preorder']
CONDITION_CHOICES = ['new', 'used', 'refurbished']
GENDER_CHOICES = ['male', 'female', 'unisex']
MATERIALS = ['Wool', 'Synthetic', 'Silk', 'Cotton', 'Jute', 'Polyester', 'Viscose']
PATTERNS = ['Solid', 'Striped', 'Floral', 'Geometric', 'Abstract', 'Checkered']
COLORS = ['Red', 'Blue', 'Green', 'Yellow', 'Black', 'White', 'Gray', 'Beige', 'Brown', 'Purple']
PRODUCT_TYPES = ['Rug', 'Carpet', 'Floor Mat', 'Runner', 'Area Rug', 'Oriental Rug', 'Shag Rug']
SIZES = ['80x150', '120x170', '160x230', '200x290', '120x80', '300x400']
BRANDS = ['Morgenland', 'Rugvista', 'Esprit', 'Nourison', 'Safavieh', 'Persian-Rugs']
ITEM_GROUPS = ['ITEM0', 'ITEM1', 'ITEM2', 'ITEM3', 'ITEM4']

def create_random_product(fake, index):
    """Generate random product data with occasional missing fields"""
    
    # Base fields (required in your Django model)
    product = {
        'id': f"SKU{index:05d}",
        'title': fake.sentence(nb_words=4)[:-1],
        'price': f"{random.uniform(50, 500):.2f} EUR"
    }
    
    # Other fields with varying probability of being present
    if random.random() > 0.05:  # 5% chance of missing
        product['image_link'] = random.choice([
            fake.image_url(),
            f"https://placekitten.com/{random.randint(100, 999)}/{random.randint(50, 999)}",
            f"https://dummyimage.com/{random.randint(100, 999)}x{random.randint(100, 999)}",
            f"https://placeimg.com/{random.randint(100, 999)}/{random.randint(100, 999)}/any",
            f"https://www.lorempixel.com/{random.randint(100, 999)}/{random.randint(50, 999)}"
        ])
    
    if random.random() > 0.1:  # 10% chance of missing
        product['description'] = fake.paragraph()
    
    if random.random() > 0.08:  # 8% chance of missing
        product['link'] = fake.url()
    
    if random.random() > 0.15:  # 15% chance of missing
        product['sale_price'] = f"{random.uniform(40, 450):.2f} EUR"
    
    if random.random() > 0.2:  # 20% chance of missing
        product['shipping'] = "DE:0.00 EUR"
    
    if random.random() > 0.1:  # 10% chance of missing
        product['item_group_id'] = random.choice(ITEM_GROUPS)
    
    if random.random() > 0.07:  # 7% chance of missing
        product['availability'] = random.choice(AVAILABILITY_CHOICES)
    
    if random.random() > 0.3:  # 30% chance of missing
        num_images = random.randint(1, 3)
        additional_links = []
        for _ in range(num_images):
            img_url = random.choice([
                f"https://placekitten.com/{random.randint(100, 999)}/{random.randint(50, 999)}",
                f"https://dummyimage.com/{random.randint(100, 999)}x{random.randint(100, 999)}",
                f"https://placeimg.com/{random.randint(100, 999)}/{random.randint(100, 999)}/any",
                f"https://www.lorempixel.com/{random.randint(100, 999)}/{random.randint(50, 999)}"
            ])
            additional_links.append(img_url)
        product['additional_image_links'] = ','.join(additional_links)
    
    if random.random() > 0.12:  # 12% chance of missing
        product['brand'] = random.choice(BRANDS)
    
    if random.random() > 0.25:  # 25% chance of missing
        product['gtin'] = ''.join([str(random.randint(0, 9)) for _ in range(13)])
    
    if random.random() > 0.3:  # 30% chance of missing
        product['gender'] = random.choice(GENDER_CHOICES)
    
    if random.random() > 0.22:  # 22% chance of missing
        product['google_product_category'] = '598'  # Example category ID for rugs
    
    if random.random() > 0.2:  # 20% chance of missing
        product['product_type'] = random.choice(PRODUCT_TYPES)
    
    if random.random() > 0.18:  # 18% chance of missing
        product['material'] = random.choice(MATERIALS)
    
    if random.random() > 0.28:  # 28% chance of missing
        product['pattern'] = random.choice(PATTERNS)
    
    if random.random() > 0.15:  # 15% chance of missing
        product['color'] = random.choice(COLORS)
    
    # Dimensions with higher chance of missing
    if random.random() > 0.35:  # 35% chance of missing
        product['product_length'] = f"{random.randint(80, 300)} cm"
    
    if random.random() > 0.35:  # 35% chance of missing
        product['product_width'] = f"{random.randint(30, 200)} cm"
    
    if random.random() > 0.35:  # 35% chance of missing
        product['product_height'] = f"{random.randint(1, 10)} cm"
    
    if random.random() > 0.35:  # 35% chance of missing
        product['product_weight'] = f"{random.uniform(0.5, 15):.2f} kg"
    
    if random.random() > 0.25:  # 25% chance of missing
        product['size'] = random.choice(SIZES)
    
    if random.random() > 0.4:  # 40% chance of missing
        product['lifestyle_image_link'] = random.choice([
            f"https://placekitten.com/{random.randint(100, 999)}/{random.randint(50, 999)}",
            f"https://dummyimage.com/{random.randint(100, 999)}x{random.randint(100, 999)}",
            f"https://placeimg.com/{random.randint(100, 999)}/{random.randint(100, 999)}/any"
        ])
    
    if random.random() > 0.3:  # 30% chance of missing
        product['max_handling_time'] = random.randint(1, 10)
    
    if random.random() > 0.3:  # 30% chance of missing
        product['is_bundle'] = 'yes' if random.random() > 0.8 else 'no'
    
    if random.random() > 0.25:  # 25% chance of missing
        product['Model'] = f"Model-{random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
    
    if random.random() > 0.15:  # 15% chance of missing
        product['condition'] = random.choice(CONDITION_CHOICES)
    
    return product

def generate_excel(num_rows=1000000, chunk_size=10000, output_file='large_product_data.xlsx'):
    """Generate a large Excel file with random product data"""
    
    fake = Faker()
    Faker.seed(42)  # For reproducibility
    random.seed(42)
    
    print(f"Generating {num_rows} rows of product data...")
    start_time = time.time()
    
    # Use ExcelWriter in append mode for large files
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for chunk_start in range(0, num_rows, chunk_size):
            chunk_end = min(chunk_start + chunk_size, num_rows)
            print(f"Generating rows {chunk_start} to {chunk_end}...")
            
            chunk_data = []
            for i in range(chunk_start, chunk_end):
                product = create_random_product(fake, i)
                chunk_data.append(product)
            
            df_chunk = pd.DataFrame(chunk_data)
            
            # First chunk creates the file, others append
            if chunk_start == 0:
                df_chunk.to_excel(writer, index=False, sheet_name='Products')
            else:
                # For Excel we need to manually handle appending
                # Get the current sheet
                sheet = writer.sheets['Products']
                
                # Write data without headers
                for r_idx, row in enumerate(df_chunk.values):
                    for c_idx, value in enumerate(row):
                        sheet.cell(row=r_idx + chunk_start + 2, column=c_idx + 1, value=value)
                        
            # Print progress
            elapsed = time.time() - start_time
            progress = (chunk_end / num_rows) * 100
            eta = (elapsed / (chunk_end - chunk_start)) * (num_rows - chunk_end)
            print(f"Progress: {progress:.1f}% complete, ETA: {eta:.1f} seconds")

    total_time = time.time() - start_time
    print(f"File generation complete! Total time: {total_time:.2f} seconds")
    print(f"Output saved to: {output_file}")

def generate_csv(num_rows=1000000, chunk_size=50000, output_file='large_product_data.csv'):
    """Generate a large CSV file with random product data (more efficient for very large datasets)"""
    
    fake = Faker()
    Faker.seed(42)  # For reproducibility
    random.seed(42)
    
    print(f"Generating {num_rows} rows of product data as CSV...")
    start_time = time.time()
    
    # Create first chunk with headers
    chunk_data = []
    for i in range(min(chunk_size, num_rows)):
        product = create_random_product(fake, i)
        chunk_data.append(product)
    
    df_chunk = pd.DataFrame(chunk_data)
    df_chunk.to_csv(output_file, index=False)
    
    # Append remaining chunks without headers
    for chunk_start in range(chunk_size, num_rows, chunk_size):
        chunk_end = min(chunk_start + chunk_size, num_rows)
        print(f"Generating rows {chunk_start} to {chunk_end}...")
        
        chunk_data = []
        for i in range(chunk_start, chunk_end):
            product = create_random_product(fake, i)
            chunk_data.append(product)
        
        df_chunk = pd.DataFrame(chunk_data)
        df_chunk.to_csv(output_file, mode='a', header=False, index=False)
        
        # Print progress
        elapsed = time.time() - start_time
        progress = (chunk_end / num_rows) * 100
        eta = (elapsed / (chunk_end - chunk_start)) * (num_rows - chunk_end)
        print(f"Progress: {progress:.1f}% complete, ETA: {eta:.1f} seconds")

    total_time = time.time() - start_time
    print(f"File generation complete! Total time: {total_time:.2f} seconds")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a large product dataset with missing values.')
    parser.add_argument('--rows', type=int, default=1000000, help='Number of rows to generate')
    parser.add_argument('--format', choices=['csv', 'excel'], default='csv', help='Output format (csv or excel)')
    parser.add_argument('--chunk-size', type=int, default=50000, help='Chunk size for processing')
    parser.add_argument('--output', type=str, default=None, help='Output file path')
    
    args = parser.parse_args()
    
    if args.format == 'csv':
        output_file = args.output or f'product_data_{args.rows}.csv'
        generate_csv(num_rows=args.rows, chunk_size=args.chunk_size, output_file=output_file)
    else:
        output_file = args.output or f'product_data_{args.rows}.xlsx'
        generate_excel(num_rows=args.rows, chunk_size=args.chunk_size, output_file=output_file)