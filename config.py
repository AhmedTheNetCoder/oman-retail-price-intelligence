"""
Configuration for Oman Retail Price Intelligence System
"""

from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ASSETS_DIR = BASE_DIR / "assets"

# Create directories
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "prices.db"

# Retailers Configuration
RETAILERS = {
    "lulu": {
        "name": "Lulu Hypermarket",
        "base_url": "https://www.luluhypermarket.com/en-om",
        "currency": "OMR"
    },
    "carrefour": {
        "name": "Carrefour Oman",
        "base_url": "https://www.carrefourkuwait.com/mafkwt/en/",
        "currency": "OMR"
    },
    "sultan_center": {
        "name": "Sultan Center",
        "base_url": "https://www.sultancenter.com",
        "currency": "OMR"
    },
    "nesto": {
        "name": "Nesto Hypermarket",
        "base_url": "https://www.nestogroup.com",
        "currency": "OMR"
    }
}

# Product Categories
CATEGORIES = [
    "Rice & Grains",
    "Cooking Oil",
    "Dairy & Eggs",
    "Beverages",
    "Snacks",
    "Personal Care",
    "Cleaning",
    "Baby Products"
]

# Scraping Settings
REQUEST_DELAY = 2.0  # seconds between requests
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Analysis Settings
PRICE_CHANGE_THRESHOLD = 0.05  # 5% change is significant
INFLATION_BASKET_ITEMS = [
    "Basmati Rice 5kg",
    "Sunflower Oil 1.5L",
    "Fresh Milk 1L",
    "Eggs 30pcs",
    "Mineral Water 1.5L 6pack",
    "White Bread",
    "Chicken Whole",
    "Tomatoes 1kg",
    "Onions 1kg",
    "Sugar 1kg"
]
