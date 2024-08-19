import streamlit as st
import pandas as pd
import json

# Set page config at the very beginning
st.set_page_config(layout="wide")

# Load and process data
@st.cache_data
def load_data():
    with open('final_dubai_neighborhoods_v36.json', 'r') as file:
        data = json.load(file)
    df = pd.json_normalize(data['Dubai Neighborhoods'])
    
    # Extract nested fields
    df['Proximity to Key Areas'] = df['Location & Accessibility.Proximity to Key Areas']
    df['Traffic Conditions'] = df['Location & Accessibility.Traffic Conditions']
    df['Available Housing Types'] = df['Housing Options & Costs.Available Housing Types']
    df['Average Rent (EUR/month)'] = df['Housing Options & Costs.Average Rent (EUR/month)']
    df['Cost of Living Index'] = df['Housing Options & Costs.Cost of Living Index']
    df['Parks and Recreation'] = df['Amenities & Facilities.Parks and Recreation']
    df['Healthcare Facilities'] = df['Amenities & Facilities.Healthcare Facilities']
    df['Demographics'] = df['Community & Lifestyle.Demographics']
    df['Family-Friendliness'] = df['Community & Lifestyle.Family-Friendliness']
    df['Safety Rating'] = df['Community & Lifestyle.Safety Rating']
    df['Green Spaces'] = df['Environment & Weather.Green Spaces']
    df['Noise Levels'] = df['Environment & Weather.Noise Levels']
    df['Air Quality Index'] = df['Environment & Weather.Air Quality Index']
    df['Risk of Sandstorm'] = df['Risk Factors.Risk of Sandstorm']
    df['Risk of Apartment Flooding'] = df['Risk Factors.Risk of Apartment Flooding']
    df['Sports Facilities'] = df['Leisure & Entertainment.Sports Facilities']
    df['Beach Access'] = df['Leisure & Entertainment.Beach Access']

    # Sort by Total Score and add Rank
    df = df.sort_values('Total Score', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1
    return df

# Load data
df = load_data()

# Streamlit app title
st.title('Dubai Neighborhoods Dashboard')

# Sidebar filters
st.sidebar.header('Filters')
min_rent = int(df['Average Rent (EUR/month)'].min())
max_rent = int(df['Average Rent (EUR/month)'].max())
rent_range = st.sidebar.slider('Average Rent (EUR/month)', min_value=min_rent, max_value=max_rent, value=(min_rent, max_rent))

min_coli = int(df['Cost of Living Index'].min())
max_coli = int(df['Cost of Living Index'].max())
coli_range = st.sidebar.slider('Cost of Living Index', min_value=min_coli, max_value=max_coli, value=(min_coli, max_coli))

min_safety = int(df['Safety Rating'].min())
max_safety = int(df['Safety Rating'].max())
safety_range = st.sidebar.slider('Safety Rating', min_value=min_safety, max_value=max_safety, value=(min_safety, max_safety))

# Filter data
filtered_df = df[
    (df['Average Rent (EUR/month)'] >= rent_range[0]) & 
    (df['Average Rent (EUR/month)'] <= rent_range[1]) &
    (df['Cost of Living Index'] >= coli_range[0]) & 
    (df['Cost of Living Index'] <= coli_range[1]) &
    (df['Safety Rating'] >= safety_range[0]) & 
    (df['Safety Rating'] <= safety_range[1])
]

df = df.rename(columns={'Average Rent (EUR/month)': 'Rent (EUR)'})
# Normalize Scores and Rent
df['Normalized Score'] = (df['Total Score'] - df['Total Score'].min()) / (df['Total Score'].max() - df['Total Score'].min())
df['Normalized Rent'] = (df['Rent (EUR)'].max() - df['Rent (EUR)']) / (df['Rent (EUR)'].max() - df['Rent (EUR)'].min())

# Calculate Value Index
weight_score = 0.5
weight_rent = 0.5
df['Value Index'] = weight_score * df['Normalized Score'] + weight_rent * df['Normalized Rent']

# Calculate Score to Rent Ratio
df['Score to Rent Ratio'] = df['Total Score'] / df['Rent (EUR)']

# Display Neighborhood Rankings
st.subheader('Neighborhood Rankings')
columns_to_display = [
    'Area', 'Total Score', 'Rent (EUR)', 'Risk of Sandstorm', 
    'Risk of Apartment Flooding', 'Sports Facilities', 'Beach Access', 
    'Noise Levels', 'Proximity to Key Areas', 'Traffic Conditions',
    'Available Housing Types', 'Cost of Living Index', 'Parks and Recreation', 
    'Healthcare Facilities', 'Demographics', 'Family-Friendliness', 
    'Safety Rating', 'Green Spaces', 'Air Quality Index'
]
st.dataframe(df.set_index('Rank')[columns_to_display])

# Display Top 10 Most Expensive and Least Expensive Areas side by side
st.subheader('Top 10 Most Expensive and Least Expensive Areas')
col1, col2 = st.columns(2)

with col1:
    st.write("Most Expensive Areas")
    top_10_expensive = df.nlargest(10, 'Rent (EUR)').reset_index(drop=True)
    top_10_expensive['Rank'] = top_10_expensive.index + 1
    st.table(top_10_expensive.set_index('Rank')[['Area', 'Rent (EUR)']])

with col2:
    st.write("Least Expensive Areas")
    top_10_cheapest = df.nsmallest(10, 'Rent (EUR)').reset_index(drop=True)
    top_10_cheapest['Rank'] = top_10_cheapest.index + 1
    st.table(top_10_cheapest.set_index('Rank')[['Area', 'Rent (EUR)']])

# Display Top 10 Areas with Highest Score to Rent Ratio
st.subheader('Top 10 Areas with Highest Scores but Lowest Rent (Good Value)')
top_10_ratio = df.nlargest(10, 'Score to Rent Ratio').reset_index(drop=True)
top_10_ratio['Rank'] = top_10_ratio.index + 1
st.table(top_10_ratio.set_index('Rank')[['Area', 'Total Score', 'Rent (EUR)', 'Score to Rent Ratio']])


# Add CSS to make the tables more readable
st.markdown("""
<style>
    .dataframe {
        font-size: 12px;
    }
    .dataframe th {
        text-align: left;
    }
    .dataframe td {
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)