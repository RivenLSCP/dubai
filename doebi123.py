import streamlit as st
import pandas as pd
import json
import plotly.express as px
import pydeck as pdk
import re

# -------------------------------
# Helper Functions
# -------------------------------
def parse_size_range(size_range_str):
    """
    Parse a string like "600-799 sqft" and return the average as a float.
    """
    pattern = r"(\d+)-(\d+)"
    match = re.search(pattern, size_range_str)
    if match:
        min_val = int(match.group(1))
        max_val = int(match.group(2))
        return (min_val + max_val) / 2
    return None

# -------------------------------
# Page Config and Title
# -------------------------------
st.set_page_config(page_title="Dubai Real Estate Investment Dashboard", layout="wide")
st.title("Dubai Real Estate Investment Dashboard")
st.markdown("This dashboard provides insights into which neighborhoods and buildings in Dubai offer the best investment potential based on ROI, sale prices, rental yields, and more.")

# -------------------------------
# Load and Process Data
# -------------------------------
@st.cache_data
def load_data():
    with open('06-02-2025/property_analysis_usd.json', 'r') as file:
        data = json.load(file)
    rows = []
    # Flatten the data so that each variant becomes its own row
    for entry in data:
        building = entry.get("building")
        neighborhood = entry.get("neighborhood")
        # If neighborhood is a list, extract its first element
        if isinstance(neighborhood, list):
            neighborhood = neighborhood[0] if neighborhood else None
        # Loop over each variant and add building/neighborhood info
        for variant in entry.get("variants", []):
            row = variant.copy()  # Copy variant data
            row["building"] = building
            row["neighborhood"] = neighborhood
            rows.append(row)
    return pd.DataFrame(rows)

df = load_data()

# Process ROI: ensure it is numeric.
df['roi_num'] = pd.to_numeric(df['roi'], errors='coerce')

# Convert average sale and rent from AED to USD (using 1 AED = 0.27 USD).
CONVERSION_RATE = 0.27
df['avg_sale_usd'] = df['avg_sale'] * CONVERSION_RATE
df['avg_rent_usd'] = df['avg_rent'] * CONVERSION_RATE

# Create a new column for monthly rent (in USD) once.
df['avg_rent_monthly_usd'] = df['avg_rent_usd'] / 12

# Derive an average sqft (for additional analysis) from the size_range string.
df['avg_sqft'] = df['size_range'].apply(parse_size_range)

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.header("Filters")
# Filter out None values before sorting the unique neighborhoods.
neighborhood_options = sorted(df['neighborhood'].dropna().unique())
selected_neighborhoods = st.sidebar.multiselect("Select Neighborhood(s)", options=neighborhood_options, default=neighborhood_options)

bedroom_options = sorted(df['bedrooms'].unique())
selected_bedrooms = st.sidebar.multiselect("Select Number of Bedrooms", options=bedroom_options, default=bedroom_options)

# Filter the dataframe based on the sidebar selections.
filtered_df = df[(df['neighborhood'].isin(selected_neighborhoods)) & (df['bedrooms'].isin(selected_bedrooms))]

# -------------------------------
# Create Dashboard Tabs
# -------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview", 
    "Neighborhood Analysis", 
    "Building Analysis", 
    "Map View", 
    "Recommendations",
    "Living Yourself"
])

# ----- Tab 1: Overview -----
with tab1:
    st.header("Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Properties", len(filtered_df))
    with col2:
        st.metric("Average ROI (%)", f"{filtered_df['roi_num'].mean():.2f}%")
    with col3:
        st.metric("Average Sale ($)", f"${filtered_df['avg_sale_usd'].mean():,.0f}")
    with col4:
        st.metric("Average Rent ($/month)", f"${filtered_df['avg_rent_monthly_usd'].mean():,.0f}")
    
    st.markdown("### ROI Distribution")
    fig_roi = px.histogram(filtered_df, x='roi_num', nbins=20, labels={'roi_num': 'ROI (%)'}, title="ROI Distribution")
    st.plotly_chart(fig_roi, use_container_width=True)
    
    if filtered_df['avg_sqft'].notnull().any():
        st.markdown("### Property Size Distribution (sqft)")
        fig_sqft = px.histogram(filtered_df, x='avg_sqft', nbins=20, labels={'avg_sqft': 'Avg Sqft'}, title="Average Size (sqft) Distribution")
        st.plotly_chart(fig_sqft, use_container_width=True)

# ----- Tab 2: Neighborhood Analysis -----
with tab2:
    st.header("Neighborhood Analysis")
    neigh_group = filtered_df.groupby('neighborhood').agg(
        total_properties=('building', 'count'),
        avg_roi=('roi_num', 'mean'),
        avg_sale=('avg_sale_usd', 'mean'),
        avg_rent=('avg_rent_monthly_usd', 'mean')
    ).reset_index().sort_values('avg_roi', ascending=False, na_position='last')
    
    neigh_group['avg_sale'] = neigh_group['avg_sale'].apply(lambda x: f"${x:,.0f}")
    neigh_group['avg_rent'] = neigh_group['avg_rent'].apply(lambda x: f"${x:,.0f}")
    
    st.subheader("Neighborhood Performance Metrics")
    st.dataframe(neigh_group[['neighborhood', 'total_properties', 'avg_roi', 'avg_sale', 'avg_rent']])
    
    st.markdown("#### Average ROI by Neighborhood")
    fig_neigh = px.bar(neigh_group, x='neighborhood', y='avg_roi',
                        labels={'avg_roi': 'Average ROI (%)'},
                        title="Neighborhood Average ROI")
    st.plotly_chart(fig_neigh, use_container_width=True)

# ----- Tab 3: Building Analysis -----
with tab3:
    st.header("Building Analysis")
    building_group = filtered_df.groupby(['neighborhood', 'building']).agg(
        total_variants=('size_range', 'nunique'),
        avg_roi=('roi_num', 'mean'),
        avg_sale=('avg_sale_usd', 'mean'),
        avg_rent=('avg_rent_monthly_usd', 'mean'),
        total_records=('building', 'count')
    ).reset_index().sort_values('avg_roi', ascending=False, na_position='last')
    
    building_group['avg_sale'] = building_group['avg_sale'].apply(lambda x: f"${x:,.0f}")
    building_group['avg_rent'] = building_group['avg_rent'].apply(lambda x: f"${x:,.0f}")
    
    st.dataframe(building_group[['neighborhood', 'building', 'total_variants', 'avg_roi', 'avg_sale', 'avg_rent', 'total_records']])
    
    st.markdown("#### Buildings: Sale Price vs ROI")
    fig_build = px.scatter(building_group, x='avg_sale', y='avg_roi',
                           color='neighborhood', size='total_records',
                           hover_data=['building'],
                           labels={'avg_sale': 'Average Sale ($)', 'avg_roi': 'Average ROI (%)'},
                           title="Buildings: Sale Price vs ROI")
    st.plotly_chart(fig_build, use_container_width=True)

# ----- Tab 4: Map View -----
with tab4:
    st.header("Map View")
    st.info("Neighborhood markers show average ROI. Click a marker for details.")
    def extract_coord(series, key):
        return pd.Series(series).apply(lambda g: g.get(key) if isinstance(g, dict) else None).mean()
    
    # Swap geolocation keys: use 'lng' as latitude and 'lat' as longitude.
    map_group = filtered_df.groupby('neighborhood').agg(
        avg_roi=('roi_num', 'mean'),
        latitude=('geolocation', lambda x: extract_coord(x, 'lng')),
        longitude=('geolocation', lambda x: extract_coord(x, 'lat'))
    ).reset_index()
    
    view_state = pdk.ViewState(
        latitude=map_group['latitude'].mean(),
        longitude=map_group['longitude'].mean(),
        zoom=12,
        pitch=0,
    )
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_group,
        get_position=["longitude", "latitude"],
        get_fill_color="[255, 140, 0, 160]",
        get_radius=300,
        pickable=True,
    )
    
    tooltip = {
        "html": "<b>Neighborhood:</b> {neighborhood}<br/><b>Avg ROI:</b> {avg_roi:.2f}%",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }
    
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    )
    st.pydeck_chart(r)

# ----- Tab 5: Investment Recommendations -----
with tab5:
    st.header("Investment Recommendations")
    top_neigh = neigh_group.sort_values('avg_roi', ascending=False, na_position='last').head(5)
    st.dataframe(top_neigh[['neighborhood', 'total_properties', 'avg_roi', 'avg_sale', 'avg_rent']])
    
    st.markdown("### Top Properties by ROI")
    top_properties = filtered_df.sort_values('roi_num', ascending=False, na_position='last').head(10)
    top_properties_display = top_properties.copy()
    top_properties_display['avg_sale'] = top_properties_display['avg_sale_usd'].round(0).astype(int)
    top_properties_display['avg_rent'] = (top_properties_display['avg_rent_usd'] / 12).round(0).astype(int)
    top_properties_display['avg_sale'] = top_properties_display['avg_sale'].apply(lambda x: f"${x:,}")
    top_properties_display['avg_rent'] = top_properties_display['avg_rent'].apply(lambda x: f"${x:,}")
    
    st.dataframe(top_properties_display[['building', 'neighborhood', 'bedrooms', 'size_range', 'roi_num', 'avg_sale', 'avg_rent']])
    
    st.markdown("""
    **Investment Insights:**
    - **High ROI:** Properties with higher ROI indicate strong rental yields.
    - **Market Volume:** Neighborhoods with more properties suggest better liquidity.
    - **Price Consideration:** Compare average sale prices with ROI to balance capital growth and rental income.
    - **Configuration Variants:** Evaluate distinct size ranges as they might indicate diverse investment opportunities within the same building.
    """)

# ----- Tab 6: Living Yourself -----
with tab6:
    st.header("Living Yourself: Downtown Dubai & Business Bay Buildings (Monthly Rent ≤ $3,500)")
    # Filter the data for buildings in either "Downtown Dubai" or "Business Bay" and rent <= $3500
    living_df = df[
        (df['neighborhood'].isin(["Downtown Dubai", "Business Bay"])) & 
        (df['avg_rent_monthly_usd'] <= 3500)
    ]
    if living_df.empty:
        st.info("No properties found for Downtown Dubai or Business Bay within the rent range.")
    else:
        # Group by building and neighborhood and calculate numeric average ROI, numeric average monthly rent, and number of variants
        living_buildings = living_df.groupby(['neighborhood', 'building']).agg(
            avg_roi=('roi_num', 'mean'),
            avg_rent=('avg_rent_monthly_usd', 'mean'),
            total_variants=('size_range', 'nunique')
        ).reset_index()
        # Sort by the numeric average monthly rent descending
        living_buildings = living_buildings.sort_values('avg_rent', ascending=False, na_position='last')
        # Create a new display column for average rent
        living_buildings['avg_rent_display'] = living_buildings['avg_rent'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(living_buildings[['neighborhood', 'building', 'avg_roi', 'avg_rent_display', 'total_variants']])

st.write("Dashboard provided by your custom Dubai Real Estate Investment Dashboard")