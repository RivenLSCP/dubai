import json
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def get_neighborhood(lat, lon, geolocator, cache, retries=3):
    key = (round(lat, 5), round(lon, 5))
    if key in cache:
        return cache[key]
    
    try:
        # Request the result in English by specifying language="en"
        location = geolocator.reverse((lat, lon), exactly_one=True, language="en", addressdetails=True)
        if location is None:
            cache[key] = None
            return None
        
        address = location.raw.get("address", {})
        neighborhood = (address.get("neighbourhood") or 
                        address.get("suburb") or 
                        address.get("quarter") or 
                        address.get("city_district"))
        cache[key] = neighborhood
        return neighborhood
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        if retries > 0:
            time.sleep(1)
            return get_neighborhood(lat, lon, geolocator, cache, retries - 1)
        else:
            print(f"Error geocoding {lat}, {lon}: {e}")
            cache[key] = None
            return None

def update_json_file(input_file, output_file):
    # Load the JSON data from the input file.
    with open(input_file, "r") as f:
        data = json.load(f)
    
    # Initialize the geolocator. Make sure to use a unique user agent.
    geolocator = Nominatim(user_agent="dubai_real_estate_analysis")
    
    # Dictionary for caching geocoding results.
    cache = {}
    total = len(data)
    
    for idx, record in enumerate(data):
        # Retrieve the coordinates as they are in the file.
        original_lat = record.get("geolocation", {}).get("lat")
        original_lng = record.get("geolocation", {}).get("lng")
        if original_lat is not None and original_lng is not None:
            # Swap the coordinates because they are reversed in the JSON file.
            correct_lat = original_lng
            correct_lng = original_lat
            neighborhood = get_neighborhood(correct_lat, correct_lng, geolocator, cache)
            if neighborhood:
                record["neighborhoods"] = [neighborhood]
                print(f"[{idx+1}/{total}] {record.get('building')}: Updated with {neighborhood}")
            else:
                record["neighborhoods"] = []
                print(f"[{idx+1}/{total}] {record.get('building')}: No neighborhood found.")
            # Pause to respect the geocoder's rate limit.
            time.sleep(0.1)
        else:
            print(f"[{idx+1}/{total}] {record.get('building')}: Missing geolocation data.")
    
    # Write the updated JSON data to the output file.
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Finished updating. Output saved to {output_file}")

if __name__ == "__main__":
    # Specify your input and output file paths.
    input_json = "/Users/haron/dubai-real_estate/dubai/06-02-2025/property_analysis.json"
    output_json = "/Users/haron/dubai-real_estate/dubai/06-02-2025/property_analysis_updated.json"
    update_json_file(input_json, output_json)