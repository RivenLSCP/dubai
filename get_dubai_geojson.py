import osmnx as ox
import geopandas as gpd
import json

try:
    # Get neighborhoods using the newer API
    print("Fetching neighborhood data...")
    tags = {'place': ['suburb', 'neighbourhood', 'quarter', 'district']}
    
    neighborhoods = ox.features.features_from_place(
        'Dubai, United Arab Emirates',
        tags=tags
    )

    if not neighborhoods.empty:
        print("Processing neighborhood data...")
        # Keep only relevant columns and handle potential missing English names
        neighborhoods = neighborhoods.reset_index()
        
        # Try different name columns in order of preference
        name_columns = ['name:en', 'name', 'alt_name']
        for col in name_columns:
            if col in neighborhoods.columns:
                neighborhoods['neighborhood'] = neighborhoods[col]
                break
        
        # Keep only necessary columns
        neighborhoods = neighborhoods[['neighborhood', 'geometry']]
        
        # Convert to GeoJSON
        print("Converting to GeoJSON...")
        neighborhoods_geojson = neighborhoods.to_crs('EPSG:4326').__geo_interface__
        
        # Save to file
        print("Saving to file...")
        with open('dubai_neighborhoods.geojson', 'w', encoding='utf-8') as f:
            json.dump(neighborhoods_geojson, f, ensure_ascii=False)

        print("GeoJSON file created successfully!")
    else:
        print("No neighborhood data found!")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    print("Please make sure you have the latest version of osmnx installed.") 