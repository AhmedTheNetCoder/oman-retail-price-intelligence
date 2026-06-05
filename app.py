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

DATABASE_PATH = Path(__file__).parent / "data" / "prices.db"

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
        st.warning("No products found in database. Run data generation first.")

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
