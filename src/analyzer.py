"""
Price Analyzer Module
Analyzes retail prices across Oman stores and generates insights.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sys
sys.path.append(str(__file__).rsplit('\\', 2)[0])

from config import DATABASE_PATH, RETAILERS, PRICE_CHANGE_THRESHOLD


class PriceAnalyzer:
    """Analyzes retail price data across Oman stores."""

    def __init__(self):
        self.db_path = DATABASE_PATH

    def _query(self, sql: str, params: tuple = ()) -> List[tuple]:
        """Execute a query and return results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()

    def get_current_prices(self, product_name: str = None) -> List[Dict]:
        """Get the most recent prices for all or specific products."""
        if product_name:
            sql = """
                SELECT p.name, p.category, pr.retailer, pr.price, pr.date
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE p.name LIKE ?
                AND pr.date = (SELECT MAX(date) FROM prices)
                ORDER BY pr.price
            """
            results = self._query(sql, (f"%{product_name}%",))
        else:
            sql = """
                SELECT p.name, p.category, pr.retailer, pr.price, pr.date
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.date = (SELECT MAX(date) FROM prices)
                ORDER BY p.category, p.name, pr.price
            """
            results = self._query(sql)

        return [
            {
                "product": r[0],
                "category": r[1],
                "retailer": RETAILERS.get(r[2], {}).get("name", r[2]),
                "retailer_code": r[2],
                "price": r[3],
                "date": r[4]
            }
            for r in results
        ]

    def get_cheapest_store(self, product_name: str) -> Dict:
        """Find the cheapest store for a specific product."""
        prices = self.get_current_prices(product_name)
        if not prices:
            return {"error": "Product not found"}

        cheapest = min(prices, key=lambda x: x["price"])
        most_expensive = max(prices, key=lambda x: x["price"])

        savings = most_expensive["price"] - cheapest["price"]
        savings_pct = (savings / most_expensive["price"]) * 100

        return {
            "product": cheapest["product"],
            "cheapest_store": cheapest["retailer"],
            "cheapest_price": cheapest["price"],
            "expensive_store": most_expensive["retailer"],
            "expensive_price": most_expensive["price"],
            "potential_savings": round(savings, 3),
            "savings_percentage": round(savings_pct, 1),
            "all_prices": prices
        }

    def compare_stores(self) -> Dict:
        """Compare overall pricing across all stores."""
        sql = """
            SELECT
                pr.retailer,
                COUNT(DISTINCT pr.product_id) as products,
                ROUND(AVG(pr.price), 3) as avg_price,
                ROUND(MIN(pr.price), 3) as min_price,
                ROUND(MAX(pr.price), 3) as max_price
            FROM prices pr
            WHERE pr.date = (SELECT MAX(date) FROM prices)
            GROUP BY pr.retailer
            ORDER BY avg_price
        """
        results = self._query(sql)

        stores = []
        for r in results:
            stores.append({
                "retailer": RETAILERS.get(r[0], {}).get("name", r[0]),
                "retailer_code": r[0],
                "products_tracked": r[1],
                "avg_price": r[2],
                "min_price": r[3],
                "max_price": r[4]
            })

        # Determine cheapest/expensive
        if stores:
            cheapest = stores[0]
            most_expensive = stores[-1]

            return {
                "stores": stores,
                "cheapest_overall": cheapest["retailer"],
                "most_expensive_overall": most_expensive["retailer"],
                "price_spread": round(most_expensive["avg_price"] - cheapest["avg_price"], 3)
            }

        return {"stores": [], "error": "No data available"}

    def get_price_history(self, product_name: str, days: int = 30) -> Dict:
        """Get price history for a product across all stores."""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        sql = """
            SELECT pr.date, pr.retailer, pr.price
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            WHERE p.name LIKE ?
            AND pr.date >= ?
            ORDER BY pr.date, pr.retailer
        """
        results = self._query(sql, (f"%{product_name}%", start_date))

        if not results:
            return {"error": "Product not found or no history"}

        # Organize by date and retailer
        history = {}
        for date, retailer, price in results:
            if date not in history:
                history[date] = {}
            history[date][retailer] = price

        return {
            "product": product_name,
            "days": days,
            "history": history,
            "dates": sorted(history.keys())
        }

    def detect_price_changes(self, days: int = 7) -> List[Dict]:
        """Detect significant price changes in the last N days."""
        sql = """
            WITH recent_prices AS (
                SELECT
                    p.id, p.name, p.category,
                    pr.retailer, pr.price, pr.date,
                    LAG(pr.price) OVER (PARTITION BY p.id, pr.retailer ORDER BY pr.date) as prev_price
                FROM prices pr
                JOIN products p ON pr.product_id = p.id
                WHERE pr.date >= date('now', ?)
            )
            SELECT
                name, category, retailer, prev_price, price, date,
                ROUND((price - prev_price) / prev_price * 100, 2) as change_pct
            FROM recent_prices
            WHERE prev_price IS NOT NULL
            AND ABS((price - prev_price) / prev_price) >= ?
            ORDER BY ABS(change_pct) DESC
            LIMIT 20
        """
        results = self._query(sql, (f"-{days} days", PRICE_CHANGE_THRESHOLD))

        changes = []
        for r in results:
            changes.append({
                "product": r[0],
                "category": r[1],
                "retailer": RETAILERS.get(r[2], {}).get("name", r[2]),
                "old_price": r[3],
                "new_price": r[4],
                "date": r[5],
                "change_pct": r[6],
                "direction": "increase" if r[6] > 0 else "decrease"
            })

        return changes

    def calculate_basket_cost(self, shopping_list: List[str]) -> Dict:
        """
        Calculate total basket cost at each store.
        This is the Consumer Savings Advisor feature.
        """
        store_totals = {code: {"total": 0, "items_found": 0, "items": []}
                       for code in RETAILERS.keys()}

        for item in shopping_list:
            prices = self.get_current_prices(item)

            for price_data in prices:
                code = price_data["retailer_code"]
                if code in store_totals:
                    store_totals[code]["total"] += price_data["price"]
                    store_totals[code]["items_found"] += 1
                    store_totals[code]["items"].append({
                        "product": price_data["product"],
                        "price": price_data["price"]
                    })

        # Convert to list and sort by total
        results = []
        for code, data in store_totals.items():
            if data["items_found"] > 0:
                results.append({
                    "retailer": RETAILERS.get(code, {}).get("name", code),
                    "retailer_code": code,
                    "total": round(data["total"], 3),
                    "items_found": data["items_found"],
                    "items_requested": len(shopping_list),
                    "items": data["items"]
                })

        results.sort(key=lambda x: x["total"])

        if len(results) >= 2:
            cheapest = results[0]
            expensive = results[-1]
            savings = expensive["total"] - cheapest["total"]

            return {
                "shopping_list": shopping_list,
                "recommendation": f"Shop at {cheapest['retailer']} to save OMR {savings:.3f}",
                "cheapest_store": cheapest["retailer"],
                "cheapest_total": cheapest["total"],
                "potential_savings": round(savings, 3),
                "store_comparison": results
            }

        return {
            "shopping_list": shopping_list,
            "error": "Not enough data for comparison",
            "store_comparison": results
        }

    def get_category_analysis(self) -> List[Dict]:
        """Analyze prices by category."""
        sql = """
            SELECT
                p.category,
                COUNT(DISTINCT p.id) as products,
                ROUND(AVG(pr.price), 3) as avg_price,
                ROUND(MIN(pr.price), 3) as min_price,
                ROUND(MAX(pr.price), 3) as max_price
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            WHERE pr.date = (SELECT MAX(date) FROM prices)
            GROUP BY p.category
            ORDER BY avg_price DESC
        """
        results = self._query(sql)

        return [
            {
                "category": r[0],
                "products": r[1],
                "avg_price": r[2],
                "min_price": r[3],
                "max_price": r[4]
            }
            for r in results
        ]

    def calculate_inflation(self, days: int = 30) -> Dict:
        """Calculate price inflation over time."""
        sql = """
            WITH price_periods AS (
                SELECT
                    pr.product_id,
                    MIN(CASE WHEN pr.date = (SELECT MIN(date) FROM prices WHERE date >= date('now', ?))
                        THEN pr.price END) as start_price,
                    MIN(CASE WHEN pr.date = (SELECT MAX(date) FROM prices)
                        THEN pr.price END) as end_price
                FROM prices pr
                WHERE pr.date >= date('now', ?)
                GROUP BY pr.product_id, pr.retailer
            )
            SELECT
                ROUND(AVG((end_price - start_price) / start_price * 100), 2) as avg_change,
                COUNT(*) as comparisons
            FROM price_periods
            WHERE start_price > 0 AND end_price > 0
        """
        result = self._query(sql, (f"-{days} days", f"-{days} days"))

        if result and result[0][0]:
            return {
                "period_days": days,
                "avg_price_change_pct": result[0][0],
                "data_points": result[0][1],
                "annualized_rate": round(result[0][0] * (365 / days), 2)
            }

        return {"error": "Insufficient data for inflation calculation"}

    def get_summary_stats(self) -> Dict:
        """Get overall summary statistics."""
        product_count = self._query("SELECT COUNT(*) FROM products")[0][0]
        price_count = self._query("SELECT COUNT(*) FROM prices")[0][0]
        date_range = self._query(
            "SELECT MIN(date), MAX(date) FROM prices"
        )[0]
        retailer_count = self._query(
            "SELECT COUNT(DISTINCT retailer) FROM prices"
        )[0][0]

        return {
            "total_products": product_count,
            "total_price_records": price_count,
            "retailers_tracked": retailer_count,
            "data_from": date_range[0],
            "data_to": date_range[1],
            "retailers": list(RETAILERS.keys())
        }


if __name__ == "__main__":
    analyzer = PriceAnalyzer()

    print("\n=== Summary Stats ===")
    print(analyzer.get_summary_stats())

    print("\n=== Store Comparison ===")
    print(analyzer.compare_stores())

    print("\n=== Cheapest Rice ===")
    print(analyzer.get_cheapest_store("Basmati Rice"))

    print("\n=== Shopping Basket ===")
    basket = ["Basmati Rice", "Sunflower Oil", "Fresh Milk", "Eggs"]
    print(analyzer.calculate_basket_cost(basket))
