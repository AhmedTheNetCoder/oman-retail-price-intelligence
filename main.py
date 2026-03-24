"""
Oman Retail Price Intelligence System
Main entry point for the application.
"""

import argparse
import sys
from src.data_generator import generate_sample_data, init_database
from src.analyzer import PriceAnalyzer
from src.visualizer import PriceVisualizer


def run_data_generation(days: int = 30):
    """Generate sample price data."""
    print("\n" + "="*50)
    print("GENERATING SAMPLE DATA")
    print("="*50)
    result = generate_sample_data(days)
    print(f"\nData generation complete!")
    return result


def run_analysis():
    """Run price analysis and display results."""
    print("\n" + "="*50)
    print("PRICE ANALYSIS REPORT")
    print("="*50)

    analyzer = PriceAnalyzer()

    # Summary Statistics
    print("\n--- Summary Statistics ---")
    stats = analyzer.get_summary_stats()
    print(f"Products Tracked: {stats['total_products']}")
    print(f"Price Records: {stats['total_price_records']}")
    print(f"Retailers: {stats['retailers_tracked']}")
    print(f"Data Range: {stats['data_from']} to {stats['data_to']}")

    # Store Comparison
    print("\n--- Store Comparison ---")
    comparison = analyzer.compare_stores()
    if "stores" in comparison and comparison["stores"]:
        print(f"{'Retailer':<25} {'Avg Price':>12} {'Products':>10}")
        print("-" * 50)
        for store in comparison["stores"]:
            print(f"{store['retailer']:<25} OMR {store['avg_price']:>7.3f} {store['products_tracked']:>10}")
        print(f"\nCheapest Overall: {comparison['cheapest_overall']}")
        print(f"Most Expensive: {comparison['most_expensive_overall']}")
        print(f"Price Spread: OMR {comparison['price_spread']:.3f}")

    # Category Analysis
    print("\n--- Category Analysis ---")
    categories = analyzer.get_category_analysis()
    if categories:
        print(f"{'Category':<20} {'Avg Price':>12} {'Products':>10}")
        print("-" * 45)
        for cat in categories:
            print(f"{cat['category']:<20} OMR {cat['avg_price']:>7.3f} {cat['products']:>10}")

    # Price Changes
    print("\n--- Recent Price Changes (Last 7 Days) ---")
    changes = analyzer.detect_price_changes(days=7)
    if changes:
        for change in changes[:5]:
            direction = "UP" if change['change_pct'] > 0 else "DOWN"
            print(f"  {change['product'][:30]:<30} {direction} {abs(change['change_pct']):.1f}%")
    else:
        print("  No significant price changes detected")

    # Inflation
    print("\n--- Inflation Analysis (30 Days) ---")
    inflation = analyzer.calculate_inflation(days=30)
    if "error" not in inflation:
        print(f"Average Price Change: {inflation['avg_price_change_pct']:.2f}%")
        print(f"Annualized Rate: {inflation['annualized_rate']:.2f}%")
    else:
        print(f"  {inflation['error']}")

    return analyzer


def run_consumer_advisor():
    """Run the Consumer Savings Advisor feature."""
    print("\n" + "="*50)
    print("CONSUMER SAVINGS ADVISOR")
    print("="*50)

    analyzer = PriceAnalyzer()

    # Sample shopping list
    shopping_list = [
        "Basmati Rice",
        "Sunflower Oil",
        "Fresh Milk",
        "Eggs",
        "Cheddar Cheese"
    ]

    print(f"\nYour Shopping List ({len(shopping_list)} items):")
    for item in shopping_list:
        print(f"  - {item}")

    result = analyzer.calculate_basket_cost(shopping_list)

    if "error" not in result:
        print(f"\n--- Store Comparison ---")
        print(f"{'Store':<25} {'Total':>12} {'Items Found':>12}")
        print("-" * 52)

        for store in result["store_comparison"]:
            print(f"{store['retailer']:<25} OMR {store['total']:>7.3f} {store['items_found']:>10}/{store['items_requested']}")

        print(f"\n>>> RECOMMENDATION: {result['recommendation']}")
        print(f">>> Potential Savings: OMR {result['potential_savings']:.3f}")
    else:
        print(f"Error: {result['error']}")

    return result


def run_visualizations():
    """Generate all visualization charts."""
    print("\n" + "="*50)
    print("GENERATING VISUALIZATIONS")
    print("="*50)

    viz = PriceVisualizer()

    shopping_list = ["Basmati Rice", "Sunflower Oil", "Fresh Milk", "Eggs", "Cheddar Cheese"]
    charts = viz.generate_all_charts(shopping_list)

    print(f"\nGenerated {len(charts)} charts:")
    for name, path in charts.items():
        print(f"  - {path}")

    return charts


def find_cheapest(product_name: str):
    """Find the cheapest store for a specific product."""
    print(f"\n--- Finding Cheapest: {product_name} ---")

    analyzer = PriceAnalyzer()
    result = analyzer.get_cheapest_store(product_name)

    if "error" not in result:
        print(f"\nProduct: {result['product']}")
        print(f"Cheapest: {result['cheapest_store']} at OMR {result['cheapest_price']:.3f}")
        print(f"Most Expensive: {result['expensive_store']} at OMR {result['expensive_price']:.3f}")
        print(f"Savings: OMR {result['potential_savings']:.3f} ({result['savings_percentage']:.1f}%)")

        print(f"\nAll Prices:")
        for p in result['all_prices']:
            print(f"  {p['retailer']:<25} OMR {p['price']:.3f}")
    else:
        print(f"Error: {result['error']}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Oman Retail Price Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --generate          Generate sample price data
  python main.py --analyze           Run price analysis
  python main.py --advisor           Run Consumer Savings Advisor
  python main.py --visualize         Generate charts
  python main.py --find "Rice"       Find cheapest store for a product
  python main.py --all               Run everything
        """
    )

    parser.add_argument('--generate', '-g', action='store_true',
                       help='Generate sample price data')
    parser.add_argument('--analyze', '-a', action='store_true',
                       help='Run price analysis')
    parser.add_argument('--advisor', '-c', action='store_true',
                       help='Run Consumer Savings Advisor')
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='Generate visualization charts')
    parser.add_argument('--find', '-f', type=str,
                       help='Find cheapest store for a product')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='Number of days for data generation (default: 30)')
    parser.add_argument('--all', action='store_true',
                       help='Run all features')

    args = parser.parse_args()

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    print("\n" + "="*50)
    print("OMAN RETAIL PRICE INTELLIGENCE SYSTEM")
    print("="*50)

    if args.all:
        run_data_generation(args.days)
        run_analysis()
        run_consumer_advisor()
        run_visualizations()
    else:
        if args.generate:
            run_data_generation(args.days)

        if args.analyze:
            run_analysis()

        if args.advisor:
            run_consumer_advisor()

        if args.visualize:
            run_visualizations()

        if args.find:
            find_cheapest(args.find)

    print("\n" + "="*50)
    print("Complete!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
