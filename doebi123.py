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
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.colors import LinearSegmentedColormap

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

# Instead, just use the original dataframe
filtered_df = df

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
    # Calculate ROI statistics and remove outliers
    q1 = filtered_df['roi_num'].quantile(0.05)
    q3 = filtered_df['roi_num'].quantile(0.95)
    roi_filtered = filtered_df[filtered_df['roi_num'].between(q1, q3)]
    
    fig_roi = px.histogram(
        roi_filtered, 
        x='roi_num',
        nbins=20,
        labels={'roi_num': 'ROI (%)'},
        title="ROI Distribution (excluding outliers)",
    )
    
    # Update traces with larger, centered text
    fig_roi.update_traces(
        texttemplate="ROI(%)=%{x:.1f}<br>n=%{y}",
        textposition='inside',
        textfont=dict(size=14),  # Increased font size
        textangle=0,  # Ensure text is horizontal
        insidetextanchor='middle',  # Center text vertically
        hovertemplate='ROI: %{x:.1f}%<br>Count: %{y}<extra></extra>'
    )
    
    fig_roi.update_layout(
        bargap=0.1,
        showlegend=False,
        xaxis_title="ROI (%)",
        yaxis_title="Number of Properties"
    )
    
    st.plotly_chart(fig_roi, use_container_width=True)

# ----- Tab 2: Neighborhood Analysis -----
with tab2:
    st.header("Neighborhood Analysis")
    
    # Create neighborhood grouping first
    neigh_group = filtered_df.groupby('neighborhood').agg(
        total_properties=('building', 'count'),
        avg_roi=('roi_num', 'mean'),
        avg_sale=('avg_sale_usd', 'mean'),
        avg_rent=('avg_rent_monthly_usd', 'mean')
    ).reset_index()
    
    # Format the columns
    neigh_group['avg_roi'] = neigh_group['avg_roi'].round(1)
    neigh_group['avg_sale'] = neigh_group['avg_sale'].apply(lambda x: f"${x:,.0f}")
    neigh_group['avg_rent'] = neigh_group['avg_rent'].apply(lambda x: f"${x:,.0f}")
    
    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Average ROI by Neighborhood")
        fig_neigh = px.bar(neigh_group, 
                          x='neighborhood', 
                          y='avg_roi',
                          labels={'avg_roi': 'Average ROI (%)', 
                                 'neighborhood': 'Neighborhood'},
                          text=neigh_group['avg_roi'].round(1),
                          title="")
        
        # Improve bar chart formatting
        fig_neigh.update_traces(
            textposition='inside',
            textfont=dict(size=12),
            marker_color='#1f77b4'
        )
        fig_neigh.update_layout(
            xaxis_tickangle=-45,
            height=400,
            margin=dict(t=0, b=0)
        )
        st.plotly_chart(fig_neigh, use_container_width=True)
    
    with col2:
        st.subheader("Key Metrics")
        st.dataframe(
            neigh_group,
            column_order=["neighborhood", "total_properties", "avg_roi", "avg_sale", "avg_rent"],
            hide_index=True,
            column_config={
                "neighborhood": "Neighborhood",
                "total_properties": st.column_config.NumberColumn(
                    "Properties",
                    help="Total number of properties",
                ),
                "avg_roi": st.column_config.NumberColumn(
                    "ROI",
                    help="Average Return on Investment",
                    format="%.1f%%"
                ),
                "avg_sale": st.column_config.TextColumn(
                    "Avg. Sale Price",
                    help="Average sale price in USD"
                ),
                "avg_rent": st.column_config.TextColumn(
                    "Avg. Monthly Rent",
                    help="Average monthly rent in USD"
                )
            }
        )

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
    
    
    # Load GeoJSON data
    try:
        with open('dubai_neighborhoods.geojson', 'r') as f:
            neighborhoods_geojson = json.load(f)
    except FileNotFoundError:
        st.error("Neighborhood boundary data not found. Please run the data collection script first.")
        st.stop()
    
    # Prepare map data
    map_group = filtered_df.groupby('neighborhood').agg(
        avg_roi=('roi_num', 'mean')
    ).reset_index()
    
    map_group['avg_roi'] = map_group['avg_roi'].round(2)
    
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
    
    # Create choropleth layer
    for feature in neighborhoods_geojson['features']:
        neighborhood_name = feature['properties']['neighborhood']
        roi_data = map_group[map_group['neighborhood'] == neighborhood_name]
        
        if not roi_data.empty:
            roi_value = roi_data.iloc[0]['avg_roi']
            color = colormap(roi_value)
            
            folium.GeoJson(
                feature,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'fillOpacity': 0.7,
                    'color': 'white',
                    'weight': 1
                },
                tooltip=f"{neighborhood_name}<br>ROI: {roi_value:.2f}%"
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
    
    # Create three columns for KPIs
    col1, col2, col3 = st.columns(3)
    
    # Get top ROI neighborhood
    top_roi_neigh = neigh_group.nlargest(1, 'avg_roi')
    with col1:
        st.metric(
            "Highest ROI Neighborhood",
            f"{top_roi_neigh['neighborhood'].iloc[0]}",
            f"{top_roi_neigh['avg_roi'].iloc[0]}%"
        )
    
    # Get lowest entry price neighborhood
    lowest_price_neigh = neigh_group.copy()
    lowest_price_neigh['avg_sale_num'] = pd.to_numeric(lowest_price_neigh['avg_sale'].str.replace('$', '').str.replace(',', ''))
    lowest_price = lowest_price_neigh.nsmallest(1, 'avg_sale_num')
    with col2:
        st.metric(
            "Most Affordable Neighborhood",
            f"{lowest_price['neighborhood'].iloc[0]}",
            lowest_price['avg_sale'].iloc[0]
        )
    
    # Get neighborhood with most properties
    most_properties = neigh_group.nlargest(1, 'total_properties')
    with col3:
        st.metric(
            "Most Active Market",
            f"{most_properties['neighborhood'].iloc[0]}",
            f"{most_properties['total_properties'].iloc[0]} properties"
        )
    
    # Top Properties Section
    st.subheader("Top 10 Properties by ROI")
    
    # Get top properties
    top_properties = filtered_df.nlargest(10, 'roi_num')
    
    # Create a more visually appealing property cards layout
    for i in range(0, len(top_properties), 2):
        col1, col2 = st.columns(2)
        
        # First property in the row
        with col1:
            if i < len(top_properties):
                prop = top_properties.iloc[i]
                with st.container(border=True):
                    st.markdown(f"### {prop['building']}")
                    st.markdown(f"**Neighborhood:** {prop['neighborhood']}")
                    st.markdown(f"**ROI:** {prop['roi_num']:.1f}%")
                    st.markdown(f"**Configuration:** {prop['bedrooms']} BR | {prop['size_range']}")
                    st.markdown(f"**Sale Price:** ${prop['avg_sale_usd']:,.0f}")
                    st.markdown(f"**Monthly Rent:** ${prop['avg_rent_monthly_usd']:,.0f}")
        
        # Second property in the row
        with col2:
            if i + 1 < len(top_properties):
                prop = top_properties.iloc[i + 1]
                with st.container(border=True):
                    st.markdown(f"### {prop['building']}")
                    st.markdown(f"**Neighborhood:** {prop['neighborhood']}")
                    st.markdown(f"**ROI:** {prop['roi_num']:.1f}%")
                    st.markdown(f"**Configuration:** {prop['bedrooms']} BR | {prop['size_range']}")
                    st.markdown(f"**Sale Price:** ${prop['avg_sale_usd']:,.0f}")
                    st.markdown(f"**Monthly Rent:** ${prop['avg_rent_monthly_usd']:,.0f}")

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