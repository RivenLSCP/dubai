import osmnx as ox
import geopandas as gpd
import json

# Configure osmnx
ox.config(use_cache=True, log_console=True)

# Define Dubai's approximate bounding box
dubai_bbox = [25.0742, 25.3340, 55.1447, 55.4529]  # [south, north, west, east]

# Get administrative boundaries for Dubai
dubai = ox.geocode_to_gdf('Dubai, United Arab Emirates')
dubai_boundaries = ox.geometries_from_place('Dubai, United Arab Emirates', tags={'boundary': 'administrative'})

# Get neighborhoods
neighborhoods = ox.geometries_from_bbox(
    north=dubai_bbox[1],
    south=dubai_bbox[0],
    east=dubai_bbox[3],
    west=dubai_bbox[2],
    tags={'place': ['suburb', 'neighbourhood', 'quarter']}
)

# Clean and prepare the data
if not neighborhoods.empty:
    # Keep only relevant columns
    neighborhoods = neighborhoods[['name:en', 'geometry']]
    neighborhoods = neighborhoods.rename(columns={'name:en': 'neighborhood'})
    
    # Convert to GeoJSON
    neighborhoods_geojson = neighborhoods.to_crs('EPSG:4326').__geo_interface__
    
    # Save to file
    with open('dubai_neighborhoods.geojson', 'w') as f:
        json.dump(neighborhoods_geojson, f)

print("GeoJSON file created successfully!") 