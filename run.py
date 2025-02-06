import asyncio
import aiohttp
import json
from collections import defaultdict
import os
from datetime import datetime

base_url = "https://wd0ptz13zs-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key=cef139620248f1bc328a00fddc7107a6&x-algolia-application-id=WD0PTZ13ZS"

# City ID: 2 = Dubai
# City ID: 4 = UAE
def residential_rent_request_body(page: int, hits: int) -> bytes:
    request_body_template = '''{{
    "requests": [
        {{
            "indexName": "by_verification_feature_asc_property-for-rent-residential.com",
            "query": "",
            "params": "page={0}&attributesToHighlight=%5B%5D&hitsPerPage={1}&attributesToRetrieve=%5B%22id%22%2C%22category_id%22%2C%22objectID%22%2C%22name%22%2C%22property_reference%22%2C%22price%22%2C%22featured_listing%22%2C%22has_tour_url%22%2C%22has_video_url%22%2C%22is_verified%22%2C%22listed_by%22%2C%22categories%22%2C%22agent%22%2C%22bedrooms%22%2C%22bathrooms%22%2C%22size%22%2C%22neighborhoods%22%2C%22city%22%2C%22building%22%2C%22photos%22%2C%22promoted%22%2C%22tour_360%22%2C%22photos_count%22%2C%22added%22%2C%22video_url%22%2C%22has_dld_history%22%2C%22tour_url%22%2C%22highlighted_ad%22%2C%22has_whatsapp_number%22%2C%22has_agents_whatsapp%22%2C%22has_sms_number%22%2C%22short_url%22%2C%22absolute_url%22%2C%22id%22%2C%22category_id%22%2C%22badges%22%2C%22room_type%22%2C%22uuid%22%2C%22can_chat%22%2C%22is_premium_ad%22%2C%22description_short%22%2C%22_geoloc%22%2C%22completion_status%22%2C%22is_verified_user%22%2C%22agent_profile%22%2C%22payment_frequency%22%2C%22furnished%22%2C%22is_developer_listing%22%2C%22sale_type%22%2C%22handover_date%22%2C%22payment_plan%22%2C%22original_price%22%2C%22amount_paid%22%2C%22property_info%22%2C%22is_emirati_agent%22%5D&facets=%5B%22language%22%5D&filters=(%22categories_v2.slug_paths%22%3A%22property-for-rent%22)%20AND%20(%22categories_v2.slug_paths%22%3A%22property-for-rent%2Fresidential%22)%20AND%20(%22city.id%22%3D2)"
        }}
    ]
}}'''
    return request_body_template.format(page, hits).encode('utf-8')


def residential_sale_request_body(page: int, hits: int) -> bytes:
    request_body_template = '''{{
    "requests": [
        {{
            "indexName": "by_verification_feature_asc_property-for-sale-residential.com",
            "query": "",
            "params": "page={0}&attributesToHighlight=%5B%5D&hitsPerPage={1}&attributesToRetrieve=%5B%22id%22%2C%22category_id%22%2C%22objectID%22%2C%22name%22%2C%22property_reference%22%2C%22price%22%2C%22featured_listing%22%2C%22has_tour_url%22%2C%22has_video_url%22%2C%22is_verified%22%2C%22listed_by%22%2C%22categories%22%2C%22agent%22%2C%22bedrooms%22%2C%22bathrooms%22%2C%22size%22%2C%22neighborhoods%22%2C%22city%22%2C%22building%22%2C%22photos%22%2C%22promoted%22%2C%22tour_360%22%2C%22photos_count%22%2C%22added%22%2C%22video_url%22%2C%22has_dld_history%22%2C%22tour_url%22%2C%22highlighted_ad%22%2C%22has_whatsapp_number%22%2C%22has_agents_whatsapp%22%2C%22has_sms_number%22%2C%22short_url%22%2C%22absolute_url%22%2C%22id%22%2C%22category_id%22%2C%22badges%22%2C%22room_type%22%2C%22uuid%22%2C%22can_chat%22%2C%22is_premium_ad%22%2C%22description_short%22%2C%22_geoloc%22%2C%22completion_status%22%2C%22is_verified_user%22%2C%22agent_profile%22%2C%22payment_frequency%22%2C%22furnished%22%2C%22is_developer_listing%22%2C%22sale_type%22%2C%22handover_date%22%2C%22payment_plan%22%2C%22original_price%22%2C%22amount_paid%22%2C%22property_info%22%2C%22is_emirati_agent%22%5D&facets=%5B%22language%22%5D&filters=(%22categories_v2.slug_paths%22%3A%22property-for-sale%22)%20AND%20(%22categories_v2.slug_paths%22%3A%22property-for-sale%2Fresidential%22)%20AND%20(%22city.id%22%3D2)"
        }}
    ]
}}'''
    return request_body_template.format(page, hits).encode('utf-8')

async def fetch_data(session, body):
    async with session.post(base_url, data=body, headers={'Content-Type': 'application/json'}) as response:
        return await response.json()

async def fetch_property_data(is_rent):
    page = 0
    hits_per_page = 1000
    all_results = []
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                if is_rent:
                    body = residential_rent_request_body(page, hits_per_page)
                else:
                    body = residential_sale_request_body(page, hits_per_page)
                
                data = await fetch_data(session, body)
                results = data['results'][0]['hits']

                if not results:
                    break

                all_results.extend(results)
                page += 1
                print(f"Completed page [{page} / {data['results'][0]['nbPages']}]")

            except Exception as e:
                print(f"An error occurred on page {page}: {e}")
                break

    return all_results

def get_data_directory():
    """Create and return the path for today's data directory"""
    today = datetime.now().strftime('%d-%m-%Y')
    directory = os.path.join(os.getcwd(), today)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

async def fetch_residential_rent():
    print("Fetching residential rent data...")
    all_results = await fetch_property_data(True)
    building_counts = {}
    
    for result in all_results:
        building = result.get('building')
        if building and isinstance(building, dict):
            building_name = building.get('name', {}).get('en')
            if building_name:
                building_counts[building_name] = building_counts.get(building_name, 0) + 1

    data_dir = get_data_directory()
    print(f'Saving {len(all_results)} results to {data_dir}/residential_rent_data.json')
    with open(os.path.join(data_dir, 'residential_rent_data.json'), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    sorted_building_counts = dict(sorted(building_counts.items(), key=lambda item: item[1], reverse=True))
    with open(os.path.join(data_dir, 'residential_rent_building_frequencies.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted_building_counts, f, ensure_ascii=False, indent=2)

async def fetch_residential_sale():
    print("Fetching residential sale data...")
    all_results = await fetch_property_data(False)
    building_counts = {}
    
    for result in all_results:
        building = result.get('building')
        if building and isinstance(building, dict):
            building_name = building.get('name', {}).get('en')
            if building_name:
                building_counts[building_name] = building_counts.get(building_name, 0) + 1

    data_dir = get_data_directory()
    print(f'Saving {len(all_results)} results to {data_dir}/residential_sale_data.json')
    with open(os.path.join(data_dir, 'residential_sale_data.json'), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    sorted_building_counts = dict(sorted(building_counts.items(), key=lambda item: item[1], reverse=True))
    with open(os.path.join(data_dir, 'residential_sale_building_frequencies.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted_building_counts, f, ensure_ascii=False, indent=2)

def load_json_file(filename):
    data_dir = get_data_directory()
    filepath = os.path.join(data_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File {filepath} not found. Please make sure it exists.")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding {filepath}. Please make sure it's a valid JSON file.")
        return []

def analyze_property_data():
    rent_data = load_json_file('residential_rent_data.json')
    sale_data = load_json_file('residential_sale_data.json')

    building_data = defaultdict(lambda: defaultdict(lambda: {
        'rent': [], 
        'sale': [], 
        'geoloc_points': [],
        'neighborhoods': set()
    }))

    print(f'Processing {len(rent_data + sale_data)} properties')
    for item in rent_data + sale_data:
        building = item.get('building')
        if not building or not isinstance(building, dict):
            continue
        
        building_name = building.get('name', {}).get('en')
        if not building_name:
            continue

        bedrooms = item.get('bedrooms')
        bathrooms = item.get('bathrooms')
        size = item.get('size')
        price = item.get('price')

        if all(v is not None for v in [bedrooms, bathrooms, size, price]):
            size_range = (size // 200) * 200  # Round size to nearest 200 sqft
            key = (bedrooms, bathrooms, size_range)
            
            # Add geolocation if available
            geoloc = item.get('_geoloc')
            if geoloc and isinstance(geoloc, dict):
                lat = geoloc.get('lat')
                lng = geoloc.get('lng')
                if lat is not None and lng is not None:
                    building_data[building_name][key]['geoloc_points'].append((lat, lng))

            # Add neighborhoods if available
            neighborhoods = item.get('neighborhoods', {})
            if isinstance(neighborhoods, dict):
                # Get English names from the nested structure
                neighborhood_names = neighborhoods.get('name', {}).get('en', [])
                if isinstance(neighborhood_names, list):
                    building_data[building_name][key]['neighborhoods'].update(neighborhood_names)
            
            if item in rent_data:
                building_data[building_name][key]['rent'].append(price)
            else:
                building_data[building_name][key]['sale'].append(price)

    results = []

    print(f'Analyzing {len(building_data)} buildings')
    for building, property_types in building_data.items():
        for prop_type, data in property_types.items():
            if data['rent'] and data['sale']:
                avg_rent = sum(data['rent']) / len(data['rent'])
                avg_sale = sum(data['sale']) / len(data['sale'])
                roi = (avg_rent / avg_sale) * 100  # Annual ROI as a percentage
                
                # Calculate weight based on the number of samples
                rent_samples = len(data['rent'])
                sale_samples = len(data['sale'])
                weight = min(rent_samples, sale_samples)  # Use the smaller of the two sample sizes
                
                # Calculate average geolocation
                geoloc_points = data['geoloc_points']
                avg_geoloc = None
                if geoloc_points:
                    avg_lat = sum(point[0] for point in geoloc_points) / len(geoloc_points)
                    avg_lng = sum(point[1] for point in geoloc_points) / len(geoloc_points)
                    avg_geoloc = {"lat": avg_lat, "lng": avg_lng}

                # Convert neighborhoods set to sorted list
                neighborhoods = sorted(list(data['neighborhoods']))

                results.append({
                    'building': building,
                    'bedrooms': prop_type[0],
                    'bathrooms': prop_type[1],
                    'size_range': f"{prop_type[2]}-{prop_type[2]+199} sqft",
                    'avg_rent': avg_rent,
                    'avg_sale': avg_sale,
                    'roi': roi,
                    'rent_samples': rent_samples,
                    'sale_samples': sale_samples,
                    'weight': weight,
                    'weighted_roi': roi * weight,
                    'geolocation': avg_geoloc,
                    'neighborhoods': neighborhoods
                })

    # Sort by weighted ROI instead of just the ROI
    results.sort(key=lambda x: x['weighted_roi'], reverse=True)

    data_dir = get_data_directory()
    print(f'Saving {len(results)} results to {data_dir}/property_analysis.json')
    with open(os.path.join(data_dir, 'property_analysis.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Analysis complete. Results saved to property_analysis.json")
    
    # Print top 10 results
    print("\nTop 10 buildings with highest weighted ROI:")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['building']} - {result['bedrooms']} bed, {result['bathrooms']} bath, {result['size_range']}")
        print(f"   Avg Rent: {result['avg_rent']:.2f}, Avg Sale: {result['avg_sale']:.2f}, ROI: {result['roi']:.2f}%")
        print(f"   Rent Samples: {result['rent_samples']}, Sale Samples: {result['sale_samples']}, Weight: {result['weight']}")
        print(f"   Weighted ROI: {result['weighted_roi']:.4f}")

async def main():
    # Run both fetch operations concurrently
    await asyncio.gather(
        fetch_residential_rent(),
        fetch_residential_sale()
    )
    
    # Run the analysis after both fetches are complete
    analyze_property_data()

if __name__ == "__main__":
    asyncio.run(main())
