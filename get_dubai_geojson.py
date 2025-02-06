import osmnx as ox
import geopandas as gpd
import json

try:
    print("Fetching Dubai administrative boundary...")
    # Get Dubai's administrative boundary
    dubai_boundary = ox.features.features_from_place(
        'Dubai, United Arab Emirates',
        tags={'boundary': 'administrative', 'admin_level': '4'}
    )
    
    print("Fetching neighborhood data...")
    tags = {'place': ['suburb', 'neighbourhood', 'quarter', 'district']}
    neighborhoods = ox.features.features_from_place(
        'Dubai, United Arab Emirates',
        tags=tags
    )

    if not neighborhoods.empty and not dubai_boundary.empty:
        print("Processing data...")
        # Process neighborhoods
        neighborhoods = neighborhoods.reset_index()
        
        # Try different name columns in order of preference
        name_columns = ['name:en', 'name', 'alt_name']
        for col in name_columns:
            if col in neighborhoods.columns:
                neighborhoods['neighborhood'] = neighborhoods[col]
                break
        
        neighborhoods = neighborhoods[['neighborhood', 'geometry']]
        
        # Save neighborhoods GeoJSON
        print("Saving neighborhoods GeoJSON...")
        neighborhoods_geojson = neighborhoods.to_crs('EPSG:4326').__geo_interface__
        with open('dubai_neighborhoods.geojson', 'w', encoding='utf-8') as f:
            json.dump(neighborhoods_geojson, f, ensure_ascii=False)
            
        # Save Dubai boundary GeoJSON
        print("Saving Dubai boundary GeoJSON...")
        dubai_boundary = dubai_boundary.to_crs('EPSG:4326')
        dubai_boundary_geojson = dubai_boundary.geometry.unary_union.__geo_interface__
        with open('dubai_boundary.geojson', 'w', encoding='utf-8') as f:
            json.dump(dubai_boundary_geojson, f, ensure_ascii=False)

        print("GeoJSON files created successfully!")
    else:
        print("No data found!")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    print("Please make sure you have the latest version of osmnx installed.") 