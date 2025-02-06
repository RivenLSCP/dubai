#!/usr/bin/env python3
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---

# Replace with your Google service account JSON key file path
SERVICE_ACCOUNT_FILE = '/Users/haron/dubai-real_estate/dubai/Gemini API Client Secret.json'

# The scope required for managing your business location data.
SCOPES = ['https://www.googleapis.com/auth/business.manage']

# Your Google My Business (Business Profile) account ID (as a string)
ACCOUNT_ID = '104966700893-tsfsee8ltbgaeondck2ih1sgot8j91hr.apps.googleusercontent.com'  # e.g., '1234567890'

# A dictionary mapping your building names to their corresponding location IDs.
# You must supply the correct location IDs from your Business Profile.
locations = {
    "Opera Grand": "location_id_1",
    "The Residence 8": "location_id_2",
    "South Ridge 2": "location_id_3",
    "Mada Residences": "location_id_4",
    "Executive Tower E": "location_id_5",
    "Grande": "location_id_6",
    "The Address Downtown Hotel (Lake Hotel)": "location_id_7",
    "29 Boulevard 1": "location_id_8",
    "Act Two": "location_id_9",
    "Dunya Tower": "location_id_10",
    "Bay Square 12": "location_id_11",
    "Burj Views C": "location_id_12",
    "Burj Khalifa": "location_id_13",
    "Boulevard Central 2": "location_id_14",
    "Zaafaran 3": "location_id_15",
    "Boulevard Crescent Tower 1": "location_id_16",
    "Forte 2": "location_id_17",
    "Burj Royale": "location_id_18",
    "Kempinski Central Avenue Dubai": "location_id_19",
    "The Residence 1": "location_id_20",
    "Kempinski The Boulevard": "location_id_21",
    "Burj Vista 1": "location_id_22",
    "The Pad": "location_id_23",
    "Standpoint Tower 2": "location_id_24",
    "15 Northside Tower 1": "location_id_25",
    "DAMAC Paramount Tower (Midtown) Hotel And Residences": "location_id_26",
    "RP Heights": "location_id_27",
    "Nobles Tower": "location_id_28",
    "DAMAC Maison The Distinction": "location_id_29",
    "Boulevard Central 1": "location_id_30",
    "South Ridge 5": "location_id_31",
    "South Ridge 6": "location_id_32",
    "The Residence 7": "location_id_33",
    "Boulevard Point": "location_id_34",
    "Miska 4": "location_id_35",
    "The Address The Blvd": "location_id_36",
    "Boulevard Central Podium": "location_id_37",
    "Amna": "location_id_38",
    "Standpoint Tower 1": "location_id_39",
    "Bay Square 9": "location_id_40",
    "Burj Views A": "location_id_41",
    "South Ridge 4": "location_id_42",
    "The Lofts West": "location_id_43",
    "The Lofts Central Tower": "location_id_44",
    "Act One": "location_id_45",
    "Executive Tower M (West Heights 1)": "location_id_46",
    "Executive Tower K": "location_id_47",
    "Zanzebeel 1": "location_id_48",
    "Claren Tower 1": "location_id_49",
    "The Lofts East": "location_id_50",
    "DAMAC Maison Mall Street (The Signature)": "location_id_51",
    "Noora": "location_id_52",
    "Burj Al Nujoom": "location_id_53",
    "Bellevue Tower 2": "location_id_54",
    "MAG 318": "location_id_55",
    "The Residence 5": "location_id_56",
    "Reehan 7": "location_id_57",
    "Peninsula Five": "location_id_58",
    "Ahad Residences": "location_id_59",
    "The Bay": "location_id_60",
    "15 Northside Tower 2": "location_id_61",
    "Urban Oasis by Missoni": "location_id_62",
    "Millennium Atria": "location_id_63",
    "Vezul Tower": "location_id_64",
    "The Sterling West": "location_id_65",
    "UPSIDE": "location_id_66",
    "Tower D": "location_id_67",
    "J One Tower A": "location_id_68",
    "Binghatti Canal Building": "location_id_69",
    "U-Bora Tower 1": "location_id_70",
    "Burj Views Podium": "location_id_71",
    "Burj Views B": "location_id_72",
    "SLS Dubai Hotel & Residences": "location_id_73",
    "Executive Tower B (East Heights 4)": "location_id_74",
    "29 Boulevard 2": "location_id_75",
    "Aykon City Tower C": "location_id_76",
    "Capital Bay Tower B": "location_id_77",
    "Bellevue Tower 1": "location_id_78",
    "Yansoon 4": "location_id_79",
    "Windsor Manor": "location_id_80",
    "Bayz by Danube": "location_id_81",
    "DAMAC Maison Bay's Edge": "location_id_82",
    "Merano Tower": "location_id_83",
    "Elite 1 Downtown Residence": "location_id_84",
    "8 Boulevard Walk": "location_id_85",
    "DAMAC Maison Aykon City": "location_id_86",
    "Churchill Residence": "location_id_87",
    "Marquise Square": "location_id_88",
    "DAMAC Maison Majestine": "location_id_89",
    "Executive Tower J": "location_id_90",
    "Claren Tower 2": "location_id_91",
    "SOL Bay": "location_id_92",
    "Executive Tower F": "location_id_93",
    "Damac Maison Prive Tower A": "location_id_94",
    "The Atria Residences": "location_id_95",
    "Millennium Binghatti Residences": "location_id_96",
    "DAMAC Maison Canal Views": "location_id_97",
    "The Residences at Business Central": "location_id_98",
    "Reva Residences": "location_id_99",
    "Damac Maison Prive Tower B": "location_id_100",
    "Scala Tower": "location_id_101",
    "Vera Residences": "location_id_102",
    "West Wharf": "location_id_103",
    "Clayton Residency": "location_id_104",
    "The Lofts Podium": "location_id_105",
    "Claren Podium": "location_id_106",
    "Upper Crest (Burjside Terrace)": "location_id_107",
    "The Cosmopolitan (Damac Maison)": "location_id_108",
    "Safeer Tower 1": "location_id_109",
    "Executive Bay Tower A": "location_id_110",
    "Fairview Residency": "location_id_111",
    "Ontario Tower": "location_id_112",
    "Avanti Tower": "location_id_113",
    "The Court Tower": "location_id_114",
    "Zada Tower": "location_id_115",
    "Capital Bay Tower A": "location_id_116",
    "29 Boulevard Podium": "location_id_117",
    "AG Tower": "location_id_118",
    "Bay Square 10": "location_id_119",
    "Park Central": "location_id_120",
    "Mayfair Residency": "location_id_121",
    "Safeer Tower 2": "location_id_122",
    "Elite Business Bay Residence": "location_id_123",
    "Mayfair Tower": "location_id_124",
    "The Voleo": "location_id_125",
    "Executive Bay Tower B": "location_id_126",
    "Waves Tower": "location_id_127"
}

# --- SET UP GOOGLE MY BUSINESS API CLIENT ---

# Create credentials using the service account file and scope
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the API client for version v4 of the My Business API
service = build('mybusiness', 'v4', credentials=credentials)

# --- FUNCTION TO FETCH REVIEWS FOR A GIVEN LOCATION ---

def fetch_reviews(building_name, location_id):
    """
    Fetch and print review data for a building given its location_id.
    """
    # Construct the parent string as required by the API:
    parent = f"accounts/{ACCOUNT_ID}/locations/{location_id}"
    try:
        # Call the reviews.list endpoint
        response = service.accounts().locations().reviews().list(parent=parent).execute()
        reviews = response.get("reviews", [])
        if reviews:
            print(f"\nReviews for {building_name} (Location ID: {location_id}):")
            for review in reviews:
                star_rating = review.get("starRating")
                comment = review.get("comment", "").strip()
                review_id = review.get("reviewId")
                print(f" - Review ID: {review_id} | Rating: {star_rating} | Comment: {comment}")
        else:
            print(f"\nNo reviews found for {building_name} (Location ID: {location_id}).")
    except Exception as e:
        print(f"\nError fetching reviews for {building_name} (Location ID: {location_id}): {e}")

# --- MAIN SCRIPT ---
if __name__ == "__main__":
    # Loop over each building in our dictionary
    for building, loc_id in locations.items():
        fetch_reviews(building, loc_id)
        # Pause briefly between requests to avoid rate limits
        time.sleep(1)