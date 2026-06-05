"""
Oman Retail Price Intelligence - Streamlit Dashboard
Interactive price comparison across major Omani retailers
"""

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import random

# Page config
st.set_page_config(
    page_title="Oman Retail Price Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
RETAILERS = {
    "lulu": {"name": "Lulu Hypermarket", "color": "#E31837"},
    "carrefour": {"name": "Carrefour Oman", "color": "#004E9A"},
    "sultan_center": {"name": "Sultan Center", "color": "#8B4513"},
    "nesto": {"name": "Nesto Hypermarket", "color": "#FF6B00"}
}

# Product data for generation
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

# Database path
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIR / "prices.db"

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    conn.commit()
    conn.close()

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
            cursor.execute(
                "INSERT INTO products (id, name, category, unit) VALUES (?, ?, ?, ?)",
                (product_id, product["name"], category, product["unit"])
            )

            base_price = product["base_price"]

            for retailer in retailers:
                retailer_base = base_price * random.uniform(0.95, 1.08)

                for day_offset in range(days, -1, -1):
                    date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    daily_variation = random.uniform(-0.02, 0.02)

                    if random.random() < 0.10:
                        promotion = random.uniform(-0.15, -0.05)
                    else:
                        promotion = 0

                    inflation = (days - day_offset) * 0.0003
                    final_price = retailer_base * (1 + daily_variation + promotion + inflation)
                    final_price = round(max(final_price, 0.100), 3)

                    cursor.execute(
                        "INSERT INTO prices (product_id, retailer, price, date) VALUES (?, ?, ?, ?)",
                        (product_id, retailer, final_price, date)
                    )

            product_id += 1

    conn.commit()
    conn.close()

def check_and_init_db():
    """Check if database exists and has data, if not generate it."""
    if not DATABASE_PATH.exists():
        with st.spinner("Initializing database with sample data..."):
            generate_sample_data(30)
        return True

    # Check if tables have data
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            with st.spinner("Generating sample data..."):
                generate_sample_data(30)
            return True
    except:
        with st.spinner("Initializing database..."):
            generate_sample_data(30)
        return True

    return False

# Initialize database on app start
check_and_init_db()

# Database helper
def query_db(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute query and return DataFrame."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            return pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Analysis functions
def get_summary_stats():
    """Get overall summary statistics."""
    products = query_db("SELECT COUNT(*) as count FROM products")
    prices = query_db("SELECT COUNT(*) as count FROM prices")
    dates = query_db("SELECT MIN(date) as min_date, MAX(date) as max_date FROM prices")

    return {
        "products": products['count'].iloc[0] if not products.empty else 0,
        "price_records": prices['count'].iloc[0] if not prices.empty else 0,
        "date_from": dates['min_date'].iloc[0] if not dates.empty else "N/A",
        "date_to": dates['max_date'].iloc[0] if not dates.empty else "N/A"
    }

def get_store_comparison():
    """Compare pricing across stores."""
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
    return query_db(sql)

def get_category_analysis():
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
    return query_db(sql)

def get_current_prices(product_name: str = None):
    """Get current prices, optionally filtered by product."""
    if product_name:
        sql = """
            SELECT p.name, p.category, pr.retailer, pr.price, pr.date
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            WHERE p.name LIKE ?
            AND pr.date = (SELECT MAX(date) FROM prices)
            ORDER BY pr.price
        """
        return query_db(sql, (f"%{product_name}%",))
    else:
        sql = """
            SELECT p.name, p.category, pr.retailer, pr.price, pr.date
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            WHERE pr.date = (SELECT MAX(date) FROM prices)
            ORDER BY p.category, p.name, pr.price
        """
        return query_db(sql)

def get_all_products():
    """Get list of all products."""
    sql = "SELECT DISTINCT name FROM products ORDER BY name"
    df = query_db(sql)
    return df['name'].tolist() if not df.empty else []

def calculate_basket_cost(shopping_list: list):
    """Calculate basket cost at each store."""
    store_totals = {code: {"total": 0, "items_found": 0, "items": []} for code in RETAILERS.keys()}

    for item in shopping_list:
        prices_df = get_current_prices(item)
        if not prices_df.empty:
            for _, row in prices_df.iterrows():
                code = row['retailer']
                if code in store_totals:
                    store_totals[code]["total"] += row['price']
                    store_totals[code]["items_found"] += 1
                    store_totals[code]["items"].append({"product": row['name'], "price": row['price']})

    results = []
    for code, data in store_totals.items():
        if data["items_found"] > 0:
            results.append({
                "retailer": RETAILERS.get(code, {}).get("name", code),
                "retailer_code": code,
                "total": round(data["total"], 3),
                "items_found": data["items_found"],
                "items_requested": len(shopping_list)
            })

    results.sort(key=lambda x: x["total"])
    return results

def get_price_changes(days: int = 7):
    """Detect recent price changes."""
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
        AND ABS((price - prev_price) / prev_price) >= 0.05
        ORDER BY ABS(change_pct) DESC
        LIMIT 20
    """
    return query_db(sql, (f"-{days} days",))

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #E31837, #004E9A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .store-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=80)
    st.title("Navigation")
    page = st.radio(
        "Select Page",
        ["Overview", "Store Comparison", "Shopping Advisor", "Price Tracker", "Category Analysis"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Oman Retail Price Intelligence")
    st.caption("Tracking prices across 4 major retailers")

    # Regenerate data button
    if st.button("Refresh Data"):
        with st.spinner("Regenerating data..."):
            generate_sample_data(30)
        st.success("Data refreshed!")
        st.rerun()

# Main content
if page == "Overview":
    st.markdown('<h1 class="main-header">Oman Retail Price Intelligence</h1>', unsafe_allow_html=True)
    st.caption("Real-time price tracking across major Omani supermarkets")

    # Stats
    stats = get_summary_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Products Tracked", stats["products"])
    col2.metric("Price Records", f"{stats['price_records']:,}")
    col3.metric("Retailers", len(RETAILERS))
    col4.metric("Data Range", f"{stats['date_from']} to {stats['date_to']}")

    st.divider()

    # Store comparison chart
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Price by Store")
        store_df = get_store_comparison()
        if not store_df.empty:
            store_df['store_name'] = store_df['retailer'].map(lambda x: RETAILERS.get(x, {}).get("name", x))
            colors = [RETAILERS.get(r, {}).get("color", "#666") for r in store_df['retailer']]

            fig = px.bar(
                store_df,
                x='store_name',
                y='avg_price',
                color='store_name',
                color_discrete_sequence=colors,
                labels={'avg_price': 'Average Price (OMR)', 'store_name': 'Retailer'}
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Price by Category")
        cat_df = get_category_analysis()
        if not cat_df.empty:
            fig = px.pie(
                cat_df,
                values='avg_price',
                names='category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    # Recent price changes
    st.subheader("Recent Price Changes (Last 7 Days)")
    changes_df = get_price_changes(7)
    if not changes_df.empty:
        changes_df['direction'] = changes_df['change_pct'].apply(lambda x: '📈 Up' if x > 0 else '📉 Down')
        changes_df['store_name'] = changes_df['retailer'].map(lambda x: RETAILERS.get(x, {}).get("name", x))
        st.dataframe(
            changes_df[['name', 'store_name', 'prev_price', 'price', 'change_pct', 'direction']].rename(columns={
                'name': 'Product',
                'store_name': 'Store',
                'prev_price': 'Old Price (OMR)',
                'price': 'New Price (OMR)',
                'change_pct': 'Change %',
                'direction': 'Trend'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No significant price changes detected in the last 7 days.")

elif page == "Store Comparison":
    st.header("Store Comparison")
    st.caption("Compare prices across all retailers")

    store_df = get_store_comparison()
    if not store_df.empty:
        store_df['store_name'] = store_df['retailer'].map(lambda x: RETAILERS.get(x, {}).get("name", x))

        # Metrics
        cheapest = store_df.iloc[0]
        expensive = store_df.iloc[-1]

        col1, col2, col3 = st.columns(3)
        col1.metric("Cheapest Overall", cheapest['store_name'], f"OMR {cheapest['avg_price']:.3f} avg")
        col2.metric("Most Expensive", expensive['store_name'], f"OMR {expensive['avg_price']:.3f} avg")
        col3.metric("Price Spread", f"OMR {expensive['avg_price'] - cheapest['avg_price']:.3f}")

        st.divider()

        # Detailed comparison
        fig = go.Figure()
        for _, row in store_df.iterrows():
            color = RETAILERS.get(row['retailer'], {}).get("color", "#666")
            fig.add_trace(go.Bar(
                name=row['store_name'],
                x=['Min Price', 'Avg Price', 'Max Price'],
                y=[row['min_price'], row['avg_price'], row['max_price']],
                marker_color=color
            ))

        fig.update_layout(
            barmode='group',
            title="Price Range by Store",
            yaxis_title="Price (OMR)",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "Shopping Advisor":
    st.header("Consumer Savings Advisor")
    st.caption("Find the cheapest store for your shopping list")

    # Product selection
    all_products = get_all_products()

    if all_products:
        selected_products = st.multiselect(
            "Select products for your shopping list:",
            options=all_products,
            default=all_products[:5] if len(all_products) >= 5 else all_products
        )

        if selected_products:
            if st.button("Calculate Best Store", type="primary"):
                results = calculate_basket_cost(selected_products)

                if results:
                    cheapest = results[0]
                    expensive = results[-1] if len(results) > 1 else results[0]
                    savings = expensive['total'] - cheapest['total']

                    st.success(f"**Recommendation:** Shop at **{cheapest['retailer']}** to save **OMR {savings:.3f}**")

                    st.divider()

                    # Store comparison
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        fig = px.bar(
                            pd.DataFrame(results),
                            x='retailer',
                            y='total',
                            color='retailer',
                            color_discrete_map={r['retailer']: RETAILERS.get(r['retailer_code'], {}).get("color", "#666") for r in results},
                            labels={'total': 'Total Cost (OMR)', 'retailer': 'Store'}
                        )
                        fig.update_layout(showlegend=False, title="Basket Cost Comparison")
                        st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        st.subheader("Breakdown")
                        for r in results:
                            emoji = "🏆" if r == cheapest else ""
                            st.write(f"{emoji} **{r['retailer']}**")
                            st.write(f"   Total: OMR {r['total']:.3f}")
                            st.write(f"   Items: {r['items_found']}/{r['items_requested']}")
                            st.divider()
                else:
                    st.warning("No price data found for selected products.")
        else:
            st.info("Select products to compare prices across stores.")
    else:
        st.warning("No products found in database. Click 'Refresh Data' in sidebar.")

elif page == "Price Tracker":
    st.header("Price Tracker")
    st.caption("Search and track product prices")

    search = st.text_input("Search for a product:", placeholder="e.g., Rice, Milk, Oil...")

    if search:
        prices_df = get_current_prices(search)

        if not prices_df.empty:
            prices_df['store_name'] = prices_df['retailer'].map(lambda x: RETAILERS.get(x, {}).get("name", x))

            # Find cheapest
            cheapest = prices_df.loc[prices_df['price'].idxmin()]
            expensive = prices_df.loc[prices_df['price'].idxmax()]
            savings = expensive['price'] - cheapest['price']

            st.success(f"**Cheapest:** {cheapest['store_name']} at **OMR {cheapest['price']:.3f}** | Save **OMR {savings:.3f}** vs {expensive['store_name']}")

            # Price comparison chart
            fig = px.bar(
                prices_df,
                x='store_name',
                y='price',
                color='store_name',
                text='price',
                labels={'price': 'Price (OMR)', 'store_name': 'Store'}
            )
            fig.update_traces(texttemplate='OMR %{text:.3f}', textposition='outside')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Table
            st.dataframe(
                prices_df[['name', 'category', 'store_name', 'price']].rename(columns={
                    'name': 'Product',
                    'category': 'Category',
                    'store_name': 'Store',
                    'price': 'Price (OMR)'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"No products found matching '{search}'")

elif page == "Category Analysis":
    st.header("Category Analysis")
    st.caption("Price breakdown by product category")

    cat_df = get_category_analysis()

    if not cat_df.empty:
        # Category overview
        fig = px.bar(
            cat_df,
            x='category',
            y='avg_price',
            color='category',
            text='avg_price',
            labels={'avg_price': 'Average Price (OMR)', 'category': 'Category'}
        )
        fig.update_traces(texttemplate='OMR %{text:.3f}', textposition='outside')
        fig.update_layout(showlegend=False, height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Detailed table
        st.subheader("Category Details")
        cat_df_display = cat_df.copy()
        cat_df_display.columns = ['Category', 'Products', 'Avg Price (OMR)', 'Min Price (OMR)', 'Max Price (OMR)']
        st.dataframe(cat_df_display, use_container_width=True, hide_index=True)
    else:
        st.warning("No category data available.")

# Footer
st.divider()
st.caption("Built by Ahmed Al-Khaldi | Data Analyst Portfolio Project")
