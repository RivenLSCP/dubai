import json

# Define the conversion rate from AED to USD.
# (Adjust the rate as needed; here we use 1 AED = 0.27 USD.)
CONVERSION_RATE = 0.27

def convert_values(record):
    """
    Converts avg_sale and avg_rent from AED to USD for a single record.
    Adds new keys 'avg_sale_usd' and 'avg_rent_usd'.
    """
    # Multiply original AED values by the conversion rate.
    record['avg_sale_usd'] = record.get('avg_sale', 0) * CONVERSION_RATE
    record['avg_rent_usd'] = record.get('avg_rent', 0) * CONVERSION_RATE
    return record

def main():
    # Load the original JSON data.
    input_file = '/Users/haron/dubai-real_estate/dubai/property_analysis_grouped.json'
    output_file = 'property_analysis_usd.json'
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Convert the values for each record.
    converted_data = [convert_values(record) for record in data]
    
    # Write the updated data to a new JSON file.
    with open(output_file, 'w') as f:
        json.dump(converted_data, f, indent=2)
    
    print(f"Conversion completed. New file '{output_file}' has been created.")

if __name__ == "__main__":
    main()