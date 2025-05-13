import pandas as pd
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
import streamlit as st
import os

# Initialize geolocator with a user-agent
geolocator = Nominatim(user_agent="geo_locator_app")

# File path for storing node data
DATA_FILE = "data/el_achour_nodes.csv"

# Function to check if data exists
def is_data_exists():
    return os.path.exists(DATA_FILE)

# Load existing data or create a DataFrame
def load_data():
    if is_data_exists():
        return pd.read_csv(DATA_FILE, index_col=0)
    else:
        return pd.DataFrame(columns=["id", "lat", "lon", "name"])

df = load_data()

# Function to get place name using geopy
def get_place_name(lat, lon):
    try:
        location = geolocator.reverse((lat, lon))
        return location.address.split(',')[0] if location else "Unknown"
    except:
        return "Unknown"

# Function to construct the DataFrame from map nodes
def build_df(graph):
    global df
    last_node_id = df['id'].max() if not df.empty else 0
    new_entries = []

    for node, data in graph.nodes(data=True):
        if node <= last_node_id:
            continue

        lat, lon = data['y'], data['x']
        place_name = get_place_name(lat, lon)
        
        # Filter out road names, numerical names, and duplicates
        if not place_name.isdigit() and not place_name.startswith(('CW', 'RN', 'RU')) and place_name not in df['name'].values:
            new_entries.append([node, lat, lon, place_name])

    if new_entries:
        df = pd.concat([df, pd.DataFrame(new_entries, columns=df.columns)], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)

# Function to retrieve map data for a given area
def get_map_data(place_name="El Achour, Draria District, Algiers, Algeria"):
    try:
        return ox.graph_from_place(place_name, network_type="drive")
    except:
        st.error("Error fetching map data. Please check location settings.")
        return None

# A* search function for shortest path calculation
def a_star_search(graph, source, target):
    try:
        return nx.astar_path(graph, source, target, weight="length")
    except:
        st.error("Shortest path calculation failed.")
        return []

# Main Streamlit app
def main():
    st.title("🚗 Easy Path Finder")

    # Load and update graph data
    graph = get_map_data()
    if graph:
        build_df(graph)

    col1, col2 = st.columns(2, gap='large')

    with col1:
        # Dropdown selections for source and destination
        source = st.selectbox("Source", options=df["name"].values)
        destination = st.selectbox("Destination", options=df["name"].values)

        if st.button("Get Shortest Path") and source != destination:
            src_id = df[df["name"] == source]["id"].values[0]
            dest_id = df[df["name"] == destination]["id"].values[0]
            shortest_path = a_star_search(graph, src_id, dest_id)

            # Display the route map if found
            if shortest_path:
                fig, ax = ox.plot_graph_route(graph, shortest_path, route_color="r", route_linewidth=3, node_size=0, figsize=(12, 12), show=False, close=False)
                with col2:
                    st.pyplot(fig)
            else:
                st.warning("No valid path found.")
        else:
            st.warning("Please select different source and destination.")

    # Display location map
    map_data = pd.DataFrame(df, columns=["lat", "lon"])
    st.map(map_data)

if __name__ == "__main__":
    main()
