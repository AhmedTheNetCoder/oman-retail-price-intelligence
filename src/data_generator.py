"""
Sample Data Generator
Creates realistic Oman retail price data for demonstration.
In production, this would be replaced with actual web scraping.
"""

import random
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
import sys
sys.path.append(str(__file__).rsplit('\\', 2)[0])

from config import DATABASE_PATH, RETAILERS, CATEGORIES

# Realistic Oman product data with typical OMR prices
PRODUCTS = {
    "Rice & Grains": [
        {"name": "India Gate Basmati Rice 5kg", "base_price": 4.500, "unit": "5kg"},
        {"name": "Daawat Basmati Rice 5kg", "base_price": 4.200, "unit": "5kg"},
        {"name": "Tilda Basmati Rice 5kg", "base_price": 5.100, "unit": "5kg"},
        {"name": "Abu Kass Basmati Rice 5kg", "base_price": 3.900, "unit": "5kg"},
        {"name": "Spaghetti Pasta 500g", "base_price": 0.450, "unit": "500g"},
        {"name": "Penne Pasta 500g", "base_price": 0.480, "unit": "500g"},
    ],
    "Cooking Oil": [
        {"name": "Sunflower Oil 1.5L", "base_price": 1.850, "unit": "1.5L"},
        {"name": "Sunflower Oil 5L", "base_price": 5.200, "unit": "5L"},
        {"name": "Olive Oil Extra Virgin 500ml", "base_price": 3.450, "unit": "500ml"},
        {"name": "Corn Oil 1.5L", "base_price": 1.950, "unit": "1.5L"},
        {"name": "Vegetable Oil 1.5L", "base_price": 1.650, "unit": "1.5L"},
    ],
    "Dairy & Eggs": [
        {"name": "Fresh Milk Full Cream 1L", "base_price": 0.550, "unit": "1L"},
        {"name": "Fresh Milk Low Fat 1L", "base_price": 0.580, "unit": "1L"},
        {"name": "Eggs Large 30pcs", "base_price": 1.850, "unit": "30pcs"},
        {"name": "Eggs Medium 30pcs", "base_price": 1.650, "unit": "30pcs"},
        {"name": "Cheddar Cheese 200g", "base_price": 1.250, "unit": "200g"},
        {"name": "Labneh 500g", "base_price": 1.100, "unit": "500g"},
        {"name": "Greek Yogurt 500g", "base_price": 1.350, "unit": "500g"},
    ],
    "Beverages": [
        {"name": "Mineral Water 1.5L 6pack", "base_price": 0.850, "unit": "6x1.5L"},
        {"name": "Pepsi 2.25L", "base_price": 0.650, "unit": "2.25L"},
        {"name": "Coca Cola 2.25L", "base_price": 0.680, "unit": "2.25L"},
        {"name": "Orange Juice 1L", "base_price": 1.150, "unit": "1L"},
        {"name": "Apple Juice 1L", "base_price": 1.200, "unit": "1L"},
        {"name": "Red Bull 250ml 4pack", "base_price": 2.800, "unit": "4x250ml"},
    ],
    "Snacks": [
        {"name": "Lays Chips 170g", "base_price": 0.750, "unit": "170g"},
        {"name": "Pringles Original 165g", "base_price": 1.100, "unit": "165g"},
        {"name": "Oreo Cookies 137g", "base_price": 0.650, "unit": "137g"},
        {"name": "KitKat 4 Finger", "base_price": 0.350, "unit": "1pc"},
        {"name": "Mixed Nuts 500g", "base_price": 3.500, "unit": "500g"},
    ],
    "Personal Care": [
        {"name": "Dove Soap Bar 135g", "base_price": 0.550, "unit": "135g"},
        {"name": "Head Shoulders Shampoo 400ml", "base_price": 2.850, "unit": "400ml"},
        {"name": "Colgate Toothpaste 125ml", "base_price": 0.950, "unit": "125ml"},
        {"name": "Dettol Handwash 200ml", "base_price": 1.100, "unit": "200ml"},
        {"name": "Nivea Body Lotion 400ml", "base_price": 2.450, "unit": "400ml"},
    ],
    "Cleaning": [
        {"name": "Tide Detergent 2.5kg", "base_price": 3.250, "unit": "2.5kg"},
        {"name": "Ariel Detergent 2.5kg", "base_price": 3.450, "unit": "2.5kg"},
        {"name": "Fairy Dish Soap 750ml", "base_price": 1.350, "unit": "750ml"},
        {"name": "Dettol Floor Cleaner 1L", "base_price": 1.650, "unit": "1L"},
        {"name": "Tissue Box 150 sheets", "base_price": 0.450, "unit": "150sheets"},
    ],
    "Baby Products": [
        {"name": "Pampers Diapers Size 4 64pcs", "base_price": 6.500, "unit": "64pcs"},
        {"name": "Huggies Diapers Size 4 60pcs", "base_price": 6.200, "unit": "60pcs"},
        {"name": "Baby Wipes 72pcs", "base_price": 0.850, "unit": "72pcs"},
        {"name": "Baby Formula S26 400g", "base_price": 4.850, "unit": "400g"},
        {"name": "Cerelac Baby Cereal 400g", "base_price": 2.150, "unit": "400g"},
    ],
}


def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Prices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            retailer TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'OMR',
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Price alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            retailer TEXT,
            old_price REAL,
            new_price REAL,
            change_pct REAL,
            alert_type TEXT,
            date TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully")


def generate_sample_data(days: int = 30):
    """Generate sample price data for the past N days."""
    init_database()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM prices")
    cursor.execute("DELETE FROM products")
    conn.commit()

    product_id = 1
    retailers = list(RETAILERS.keys())

    for category, products in PRODUCTS.items():
        for product in products:
            # Insert product
            cursor.execute(
                "INSERT INTO products (id, name, category, unit) VALUES (?, ?, ?, ?)",
                (product_id, product["name"], category, product["unit"])
            )

            # Generate prices for each retailer over time
            base_price = product["base_price"]

            for retailer in retailers:
                # Each retailer has slightly different base price
                retailer_base = base_price * random.uniform(0.95, 1.08)

                for day_offset in range(days, -1, -1):
                    date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")

                    # Price varies slightly day to day
                    daily_variation = random.uniform(-0.02, 0.02)

                    # Occasional promotions (10% chance)
                    if random.random() < 0.10:
                        promotion = random.uniform(-0.15, -0.05)  # 5-15% discount
                    else:
                        promotion = 0

                    # Slight upward trend (inflation simulation)
                    inflation = (days - day_offset) * 0.0003  # ~0.03% per day

                    final_price = retailer_base * (1 + daily_variation + promotion + inflation)
                    final_price = round(max(final_price, 0.100), 3)  # Min 100 baisa

                    cursor.execute(
                        "INSERT INTO prices (product_id, retailer, price, date) VALUES (?, ?, ?, ?)",
                        (product_id, retailer, final_price, date)
                    )

            product_id += 1

    conn.commit()

    # Count records
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM prices")
    price_count = cursor.fetchone()[0]

    conn.close()

    print(f"Generated {product_count} products")
    print(f"Generated {price_count} price records")
    print(f"Data covers {days + 1} days across {len(retailers)} retailers")

    return {"products": product_count, "prices": price_count}


if __name__ == "__main__":
    generate_sample_data(30)
