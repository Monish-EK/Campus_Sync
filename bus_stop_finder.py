import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

def show():
    st.title("🚍 Find Your Nearest Bus Stop")
    st.markdown("### Enter your location to discover the closest bus stop and route!")

    # Load the CSV with coordinates
    df = pd.read_csv('bus_routes_with_coordinates.csv')

    # User inputs a location
    user_location = st.text_input("Enter your location (e.g., Vanagaram):")

    def get_coordinates(location):
        geolocator = Nominatim(user_agent="bus_stop_locator")
        try:
            location_info = geolocator.geocode(location)
            if location_info:
                return (location_info.latitude, location_info.longitude)
            else:
                return None
        except Exception as e:
            st.error(f"Error finding location: {e}")
            return None

    def find_nearest_stop(user_lat, user_lon, df):
        # Add default coordinates if they don't exist
        if 'Latitude' not in df.columns:
            # This is a simple placeholder. In a real app, you'd have real coordinates
            df['Latitude'] = [13.0087 + (i * 0.001) for i in range(len(df))]
            df['Longitude'] = [80.0034 + (i * 0.001) for i in range(len(df))]
        
        df['Latitude'] = df['Latitude'].astype(float)
        df['Longitude'] = df['Longitude'].astype(float)

        min_distance = float('inf')
        nearest_stop = None

        for _, row in df.iterrows():
            stop_coords = (row['Latitude'], row['Longitude'])
            distance = geodesic((user_lat, user_lon), stop_coords).kilometers

            if distance < min_distance:
                min_distance = distance
                nearest_stop = row

        return nearest_stop, min_distance

    if st.button("🔎 Find Nearest Bus Stop"):
        if user_location:
            coords = get_coordinates(user_location)
            if coords:
                user_lat, user_lon = coords
                nearest_stop, distance = find_nearest_stop(user_lat, user_lon, df)
                if nearest_stop is not None:
                    st.success(
                        f"### 🚉 Nearest Bus Stop:\n{nearest_stop['Bus Stop']}\n on route  \n {nearest_stop['Bus Route']} \n📍 Distance:  {distance: .2f} km away")
                else:
                    st.warning("No bus stops found. Please try another location.")
            else:
                st.warning("Could not find the location. Please try another place.")
        else:
            st.info("Please enter a valid location.")

if __name__ == "__main__":
    # Setup for standalone run
    st.set_page_config(page_title="Bus Stop Finder", page_icon="🚍")
    show()
