import json
import re

def parse_size_range(size_range_str):
    """
    Extracts the minimum and maximum square footage from a size_range string.
    Assumes the format is like "600-799 sqft".
    Returns a tuple (min_sqft, max_sqft) as integers.
    """
    pattern = r"(\d+)-(\d+)"
    match = re.search(pattern, size_range_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def group_variants(data):
    """
    Groups records by building. Each building becomes a single object
    with a common 'building' and 'neighborhood' field and a list of variants.
    Each variant holds attributes that differ (bedrooms, bathrooms, size_range, etc.).
    """
    grouped = {}
    for record in data:
        building = record.get("building")
        if not building:
            continue  # Skip records without a building name

        # Use the first neighborhood as the common neighborhood
        neighborhood = None
        nbh = record.get("neighborhoods")
        if isinstance(nbh, list) and nbh:
            neighborhood = nbh[0]
        else:
            neighborhood = nbh

        if building not in grouped:
            # Create a new group with common fields
            grouped[building] = {
                "building": building,
                "neighborhood": neighborhood,
                "variants": []
            }

        # Create a variant entry with the desired fields
        variant = {
            "bedrooms": record.get("bedrooms"),
            "bathrooms": record.get("bathrooms"),
            "size_range": record.get("size_range"),
            "avg_rent": record.get("avg_rent"),
            "avg_sale": record.get("avg_sale"),
            "roi": record.get("roi"),
            "rent_samples": record.get("rent_samples"),
            "sale_samples": record.get("sale_samples"),
            "weight": record.get("weight"),
            "weighted_roi": record.get("weighted_roi"),
            "geolocation": record.get("geolocation")
        }
        # Extract min and max sqft from size_range.
        min_sqft, max_sqft = parse_size_range(variant["size_range"])
        variant["min_sqft"] = min_sqft
        variant["max_sqft"] = max_sqft

        # Append the variant to the building's list.
        grouped[building]["variants"].append(variant)
    return list(grouped.values())

if __name__ == "__main__":
    # Read the flat JSON data.
    with open("/Users/haron/dubai-real_estate/dubai/06-02-2025/property_analysis_updated.json", "r") as infile:
        data = json.load(infile)

    # Group the data by building.
    grouped_data = group_variants(data)

    # Write the grouped data to a new JSON file.
    with open("property_analysis_grouped.json", "w") as outfile:
        json.dump(grouped_data, outfile, indent=2)

    print("Grouped JSON file 'property_analysis_grouped.json' has been created.")