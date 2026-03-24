"""
Visualization Module
Creates charts and visual reports for price intelligence.
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys
sys.path.append(str(__file__).rsplit('\\', 2)[0])

from config import ASSETS_DIR, RETAILERS
from src.analyzer import PriceAnalyzer


class PriceVisualizer:
    """Creates visualizations for retail price data."""

    def __init__(self):
        self.analyzer = PriceAnalyzer()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.colors = {
            "lulu": "#E31837",       # Lulu red
            "carrefour": "#004E9A",  # Carrefour blue
            "sultan_center": "#006B3F",  # Green
            "nesto": "#FF6B00"       # Orange
        }
        plt.style.use('seaborn-v0_8-whitegrid')

    def _save_figure(self, name: str) -> Path:
        """Save current figure to assets folder."""
        path = ASSETS_DIR / f"{name}.png"
        plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        return path

    def plot_store_comparison(self) -> Path:
        """Bar chart comparing average prices across stores."""
        data = self.analyzer.compare_stores()
        stores = data["stores"]

        if not stores:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        names = [s["retailer"] for s in stores]
        prices = [s["avg_price"] for s in stores]
        colors = [self.colors.get(s["retailer_code"], "#888888") for s in stores]

        bars = ax.bar(names, prices, color=colors, edgecolor='white', linewidth=1.5)

        # Add value labels
        for bar, price in zip(bars, prices):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                   f'OMR {price:.3f}', ha='center', va='bottom', fontweight='bold')

        ax.set_title('Average Product Price by Retailer', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Retailer', fontsize=11)
        ax.set_ylabel('Average Price (OMR)', fontsize=11)
        ax.set_ylim(0, max(prices) * 1.15)

        # Add cheapest indicator
        cheapest_idx = prices.index(min(prices))
        bars[cheapest_idx].set_edgecolor('#2ecc71')
        bars[cheapest_idx].set_linewidth(3)

        plt.tight_layout()
        return self._save_figure("store_comparison")

    def plot_category_prices(self) -> Path:
        """Horizontal bar chart of average prices by category."""
        categories = self.analyzer.get_category_analysis()

        if not categories:
            return None

        fig, ax = plt.subplots(figsize=(10, 7))

        names = [c["category"] for c in categories]
        prices = [c["avg_price"] for c in categories]
        colors = plt.cm.Blues([0.3 + (i * 0.1) for i in range(len(categories))])

        bars = ax.barh(names, prices, color=colors, edgecolor='white')

        # Add value labels
        for bar, price in zip(bars, prices):
            ax.text(price + 0.05, bar.get_y() + bar.get_height()/2,
                   f'OMR {price:.3f}', va='center', fontweight='bold')

        ax.set_title('Average Price by Product Category', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Average Price (OMR)', fontsize=11)
        ax.set_xlim(0, max(prices) * 1.2)

        plt.tight_layout()
        return self._save_figure("category_prices")

    def plot_price_history(self, product_name: str) -> Path:
        """Line chart showing price history for a product."""
        history = self.analyzer.get_price_history(product_name)

        if "error" in history:
            return None

        fig, ax = plt.subplots(figsize=(12, 6))

        dates = history["dates"]
        retailers_data = {}

        # Organize data by retailer
        for date in dates:
            for retailer, price in history["history"].get(date, {}).items():
                if retailer not in retailers_data:
                    retailers_data[retailer] = {"dates": [], "prices": []}
                retailers_data[retailer]["dates"].append(date)
                retailers_data[retailer]["prices"].append(price)

        # Plot each retailer
        for retailer, data in retailers_data.items():
            color = self.colors.get(retailer, "#888888")
            label = RETAILERS.get(retailer, {}).get("name", retailer)
            ax.plot(data["dates"], data["prices"], marker='o', markersize=3,
                   color=color, label=label, linewidth=2)

        ax.set_title(f'Price History: {product_name}', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Price (OMR)', fontsize=11)
        ax.legend(loc='upper left')

        # Format x-axis
        ax.tick_params(axis='x', rotation=45)
        step = max(1, len(dates) // 10)
        ax.set_xticks(dates[::step])

        plt.tight_layout()
        return self._save_figure(f"price_history_{product_name.replace(' ', '_')[:20]}")

    def plot_basket_comparison(self, shopping_list: List[str]) -> Path:
        """Bar chart comparing basket costs across stores."""
        result = self.analyzer.calculate_basket_cost(shopping_list)

        if "error" in result:
            return None

        stores = result["store_comparison"]

        if not stores:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))

        names = [s["retailer"] for s in stores]
        totals = [s["total"] for s in stores]
        colors = [self.colors.get(s["retailer_code"], "#888888") for s in stores]

        bars = ax.bar(names, totals, color=colors, edgecolor='white', linewidth=1.5)

        # Add value labels
        for bar, total in zip(bars, totals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                   f'OMR {total:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

        # Highlight cheapest
        cheapest_idx = totals.index(min(totals))
        bars[cheapest_idx].set_edgecolor('#2ecc71')
        bars[cheapest_idx].set_linewidth(3)

        ax.set_title(f'Shopping Basket Cost Comparison\n({len(shopping_list)} items)',
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Retailer', fontsize=11)
        ax.set_ylabel('Total Cost (OMR)', fontsize=11)
        ax.set_ylim(0, max(totals) * 1.15)

        # Add savings annotation
        if len(totals) >= 2:
            savings = max(totals) - min(totals)
            ax.annotate(f'Potential Savings: OMR {savings:.3f}',
                       xy=(0.5, 0.95), xycoords='axes fraction',
                       ha='center', fontsize=12, fontweight='bold',
                       color='#27ae60',
                       bbox=dict(boxstyle='round', facecolor='#e8f8f5', edgecolor='#27ae60'))

        plt.tight_layout()
        return self._save_figure("basket_comparison")

    def plot_price_changes(self) -> Path:
        """Show recent significant price changes."""
        changes = self.analyzer.detect_price_changes(days=7)

        if not changes:
            return None

        # Take top 10 changes
        changes = changes[:10]

        fig, ax = plt.subplots(figsize=(12, 7))

        products = [f"{c['product'][:25]}..." if len(c['product']) > 25
                   else c['product'] for c in changes]
        pct_changes = [c['change_pct'] for c in changes]
        colors = ['#e74c3c' if p > 0 else '#27ae60' for p in pct_changes]

        bars = ax.barh(products, pct_changes, color=colors)

        # Add value labels
        for bar, pct in zip(bars, pct_changes):
            x_pos = pct + (0.5 if pct > 0 else -0.5)
            ax.text(x_pos, bar.get_y() + bar.get_height()/2,
                   f'{pct:+.1f}%', va='center', fontweight='bold',
                   color='#333333')

        ax.axvline(x=0, color='black', linewidth=0.8)
        ax.set_title('Significant Price Changes (Last 7 Days)', fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Price Change (%)', fontsize=11)

        # Legend
        ax.plot([], [], color='#e74c3c', label='Price Increase', linewidth=10)
        ax.plot([], [], color='#27ae60', label='Price Decrease', linewidth=10)
        ax.legend(loc='lower right')

        plt.tight_layout()
        return self._save_figure("price_changes")

    def generate_all_charts(self, shopping_list: List[str] = None) -> Dict[str, Path]:
        """Generate all visualization charts."""
        if shopping_list is None:
            shopping_list = ["Basmati Rice", "Sunflower Oil", "Fresh Milk", "Eggs"]

        charts = {}

        print("Generating visualizations...")

        chart = self.plot_store_comparison()
        if chart:
            charts["store_comparison"] = chart
            print(f"  [+] {chart.name}")

        chart = self.plot_category_prices()
        if chart:
            charts["category_prices"] = chart
            print(f"  [+] {chart.name}")

        chart = self.plot_price_history("Basmati Rice")
        if chart:
            charts["price_history"] = chart
            print(f"  [+] {chart.name}")

        chart = self.plot_basket_comparison(shopping_list)
        if chart:
            charts["basket_comparison"] = chart
            print(f"  [+] {chart.name}")

        chart = self.plot_price_changes()
        if chart:
            charts["price_changes"] = chart
            print(f"  [+] {chart.name}")

        print(f"Generated {len(charts)} charts in {ASSETS_DIR}")
        return charts


if __name__ == "__main__":
    viz = PriceVisualizer()
    viz.generate_all_charts()
