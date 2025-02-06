import streamlit as st
import pandas as pd
import json
import plotly.express as px
import pydeck as pdk
import re
import folium
from folium import plugins
import geopandas as gpd
from branca.colormap import LinearColormap
import numpy as np
from scipy.spatial import Voronoi

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
    st.info("Areas show average ROI by neighborhood. Colors indicate ROI levels: Red (low) to Green (high)")
    
    def extract_coord(series, key):
        return pd.Series(series).apply(lambda g: g.get(key) if isinstance(g, dict) else None).mean()
    
    # Prepare map data
    map_group = filtered_df.groupby('neighborhood').agg(
        avg_roi=('roi_num', 'mean'),
        latitude=('geolocation', lambda x: extract_coord(x, 'lng')),
        longitude=('geolocation', lambda x: extract_coord(x, 'lat'))
    ).reset_index()
    
    map_group['avg_roi'] = map_group['avg_roi'].round(2)
    
    # Create Voronoi polygons
    points = map_group[['longitude', 'latitude']].values
    # Add boundary points to create a bounded Voronoi diagram
    boundary_points = np.array([
        [55.1447, 25.0742], [55.1466, 25.1210], [55.1639, 25.1486],
        [55.2068, 25.1695], [55.2631, 25.1835], [55.3073, 25.1889],
        [55.3641, 25.1878], [55.4071, 25.1722], [55.4347, 25.1537],
        [55.4529, 25.1210], [55.4511, 25.0882], [55.4401, 25.0591],
        [55.3989, 25.0300], [55.3577, 25.0155], [55.2885, 25.0119],
        [55.2178, 25.0209], [55.1447, 25.0742]
    ])
    
    # Combine actual points with boundary points
    all_points = np.vstack([points, boundary_points])
    vor = Voronoi(all_points)
    
    # Create the base map
    m = folium.Map(
        location=[25.2048, 55.2708],
        zoom_start=11,
        tiles='cartodbpositron'
    )
    
    # Create color map for ROI values
    min_roi = map_group['avg_roi'].min()
    max_roi = map_group['avg_roi'].max()
    colormap = LinearColormap(
        colors=['red', 'yellow', 'green'],
        vmin=min_roi,
        vmax=max_roi
    )
    
    # Function to create a polygon from Voronoi region
    def create_polygon(region, vertices):
        return [[vertices[i][1], vertices[i][0]] for i in region]
    
    # Add Voronoi polygons to map
    for i, point in enumerate(points):
        if i < len(map_group):  # Only process actual neighborhood points
            region = vor.regions[vor.point_region[i]]
            if -1 not in region and len(region) > 0:  # Valid region
                polygon = create_polygon(region, vor.vertices)
                roi_value = map_group.iloc[i]['avg_roi']
                color = colormap(roi_value)
                
                # Create GeoJSON for the polygon
                geo_json = {
                    "type": "Feature",
                    "properties": {
                        "neighborhood": map_group.iloc[i]['neighborhood'],
                        "roi": roi_value
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon]
                    }
                }
                
                # Add polygon to map
                folium.GeoJson(
                    geo_json,
                    style_function=lambda x, color=color: {
                        'fillColor': color,
                        'fillOpacity': 0.7,
                        'color': 'white',
                        'weight': 1
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['neighborhood', 'roi'],
                        aliases=['Neighborhood', 'ROI (%)'],
                        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
                    )
                ).add_to(m)
    
    # Add the Dubai boundary
    dubai_boundary = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [boundary_points.tolist()]
        }
    }
    
    folium.GeoJson(
        dubai_boundary,
        style_function=lambda x: {
            'fillColor': 'none',
            'color': '#333333',
            'weight': 2
        }
    ).add_to(m)
    
    # Add the colormap to the map
    colormap.add_to(m)
    colormap.caption = 'ROI %'
    
    # Display the map
    st_folium = st.components.v1.html(m._repr_html_(), height=600)
    
    # Add a color scale legend
    st.markdown("### ROI Color Scale")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"🔴 Low ROI: {min_roi:.1f}%")
    with col2:
        st.markdown(f"🟡 Medium ROI: {((max_roi + min_roi)/2):.1f}%")
    with col3:
        st.markdown(f"🟢 High ROI: {max_roi:.1f}%")

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
        # Group by building and neighborhood and calculate average monthly rent
        living_buildings = living_df.groupby(['neighborhood', 'building']).agg(
            avg_rent=('avg_rent_monthly_usd', 'mean')
        ).reset_index()
        # Sort by the numeric average monthly rent descending
        living_buildings = living_buildings.sort_values('avg_rent', ascending=False, na_position='last')
        # Create a new display column for average rent
        living_buildings['avg_rent_display'] = living_buildings['avg_rent'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(living_buildings[['neighborhood', 'building', 'avg_rent_display']])

st.write("Dashboard provided by your custom Dubai Real Estate Investment Dashboard")