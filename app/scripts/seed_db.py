import asyncio
import random
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.product import Product

# Sample data: auto‑parts with diverse attributes
SAMPLE_PRODUCTS = [
    {
        "name": "Ceramic Brake Pads - Front",
        "description": "Premium ceramic pads for quiet, low-dust braking.",
        "price": 49.99,
        "category": "Brakes",
        "brand": "AutoStop",
        "inventory_count": 120,
        "image_urls": ["https://via.placeholder.com/150?text=BrakePads"],
        "attributes": {"material": "ceramic", "warranty_years": 2},
    },
    {
        "name": "HID Headlight Bulb - 9006",
        "description": "High-intensity discharge bulb with 6000K color temperature.",
        "price": 89.95,
        "category": "Lighting",
        "brand": "LumenX",
        "inventory_count": 45,
        "image_urls": ["https://via.placeholder.com/150?text=Headlight"],
        "attributes": {"base_type": "9006", "kelvin": 6000, "voltage": 12},
    },
    {
        "name": "Oil Filter - Synthetic",
        "description": "High-efficiency synthetic media for extended oil change intervals.",
        "price": 12.50,
        "category": "Engine",
        "brand": "EcoFilter",
        "inventory_count": 300,
        "image_urls": ["https://via.placeholder.com/150?text=OilFilter"],
        "attributes": {"thread_size": "3/4-16", "anti_drain_valve": True},
    },
    {
        "name": "All-Weather Floor Mats - Set of 4",
        "description": "Heavy-duty rubber mats with deep channels for mud and snow.",
        "price": 65.00,
        "category": "Interior",
        "brand": "MatGuard",
        "inventory_count": 80,
        "image_urls": ["https://via.placeholder.com/150?text=FloorMats"],
        "attributes": {"color": "black", "material": "rubber", "fits": "sedan"},
    },
    {
        "name": "Windshield Wiper Blades - 24 inch",
        "description": "Beam style wiper blades with dual rubber compound.",
        "price": 24.99,
        "category": "Exterior",
        "brand": "ClearView",
        "inventory_count": 200,
        "image_urls": ["https://via.placeholder.com/150?text=Wiper"],
        "attributes": {"size": 24, "type": "beam", "adapter": "push-button"},
    },
    {
        "name": "Engine Air Filter",
        "description": "OEM-grade air filter with advanced filtration media.",
        "price": 18.75,
        "category": "Engine",
        "brand": "AirFlow",
        "inventory_count": 150,
        "image_urls": ["https://via.placeholder.com/150?text=AirFilter"],
        "attributes": {"shape": "rectangular", "height_mm": 45},
    },
    {
        "name": "Spark Plug - Iridium",
        "description": "Iridium-tipped plug for better ignition and longevity.",
        "price": 8.99,
        "category": "Engine",
        "brand": "IgnitePro",
        "inventory_count": 500,
        "image_urls": ["https://via.placeholder.com/150?text=SparkPlug"],
        "attributes": {"gap_mm": 1.1, "heat_range": 6, "terminal": "stud"},
    },
    {
        "name": "5W-30 Synthetic Motor Oil - 5 Quart",
        "description": "Full synthetic oil designed for modern engines.",
        "price": 36.50,
        "category": "Fluids",
        "brand": "LubeTech",
        "inventory_count": 210,
        "image_urls": ["https://via.placeholder.com/150?text=MotorOil"],
        "attributes": {"viscosity": "5W-30", "api_rating": "SP", "volume_qt": 5},
    },
    {
        "name": "Brake Fluid - DOT 4",
        "description": "High-boiling point brake fluid for performance applications.",
        "price": 14.25,
        "category": "Brakes",
        "brand": "StoppingPower",
        "inventory_count": 180,
        "image_urls": ["https://via.placeholder.com/150?text=BrakeFluid"],
        "attributes": {"dot_rating": 4, "boiling_point_c": 260},
    },
    {
        "name": "LED Tail Light Assembly",
        "description": "Plug-and-play LED tail light with sequential turn signals.",
        "price": 115.00,
        "category": "Lighting",
        "brand": "OptiLite",
        "inventory_count": 30,
        "image_urls": ["https://via.placeholder.com/150?text=TailLight"],
        "attributes": {"led_type": "SMD", "voltage": 12, "dimmable": False},
    },
]

# Generate extra 10 products dynamically
CATEGORIES = ["Brakes", "Engine", "Lighting", "Interior", "Exterior", "Fluids", "Electrical"]
BRANDS = ["AutoStop", "LumenX", "EcoFilter", "MatGuard", "ClearView", "AirFlow", "IgnitePro", "LubeTech", "StoppingPower", "OptiLite"]

for i in range(10):
    cat = random.choice(CATEGORIES)
    brand = random.choice(BRANDS)
    SAMPLE_PRODUCTS.append({
        "name": f"Generic {cat} Part {i+1}",
        "description": f"Replacement part for {cat} systems. Quality guaranteed.",
        "price": round(random.uniform(10.0, 120.0), 2),
        "category": cat,
        "brand": brand,
        "inventory_count": random.randint(10, 500),
        "image_urls": [f"https://via.placeholder.com/150?text={cat}{i+1}"],
        "attributes": {
            "type": "generic",
            "sku_suffix": f"G{i:03d}",
            "estimated_delivery_days": random.randint(1, 5),
        },
    })

async def seed():
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[Product],
    )
    
    # Clear existing products (only in development)
    if settings.app_env == "development":
        await Product.delete_all()
        print("Cleared existing products (development environment).")
    
    # Insert sample products
    products = [Product(**data) for data in SAMPLE_PRODUCTS]
    await Product.insert_many(products)
    print(f"Seeded {len(products)} products.")
    
    # Create text index for full‑text search (preparing for Step 3)
    await Product.create_indexes()
    print("Text index created.")

if __name__ == "__main__":
    asyncio.run(seed())