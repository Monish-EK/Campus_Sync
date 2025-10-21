import streamlit as st

# 🚨 This must be the first Streamlit command in the entire file
st.set_page_config(
    page_title="CampUS Sync",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Now you can safely import everything else
import os
import sys
import importlib
import pandas as pd
import sqlite3
from datetime import datetime
import json

import bus_stop_finder
import campus_navigation
import peer_resource_exchange
import timetable_scheduler

# Your remaining code below...
if not os.path.exists("uploads"):
    os.makedirs("uploads")


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

if "data" not in st.session_state:
    DATA_FILE = "schedule.json"
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            st.session_state["data"] = json.load(f)
    else:
        st.session_state["data"] = {"events": {}, "assignments": {}, "finalized_dates": []}

if "selected_date" not in st.session_state:
    st.session_state["selected_date"] = None


def create_tables():
    conn = sqlite3.connect("peer_resource_exchange.db")
    c = conn.cursor()
    
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Rental items table
    c.execute("""
        CREATE TABLE IF NOT EXISTS rental_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT,
            name TEXT,
            description TEXT,
            price REAL,
            image_path TEXT,
            contact TEXT,
            rented_by TEXT DEFAULT NULL,
            borrow_date TEXT DEFAULT NULL,
            return_date TEXT DEFAULT NULL,
            approved TEXT DEFAULT 'pending'
        )
    """)
    
    conn.commit()
    conn.close()

# Create database tables
create_tables()

# Function to save schedule data
def save_data(data):
    with open("schedule.json", "w") as f:
        json.dump(data, f, indent=4)

# Sidebar for main navigation
st.sidebar.title("CampUS Sync")
app_choice = st.sidebar.radio(
    "Choose Application",
    ["Home", "Bus Stop Finder", "Campus Navigation", "Peer Resource Exchange", "Timetable Scheduler"]
)

# Home Page
if app_choice == "Home":
    st.title("🎓 Welcome to CampUS Sync")
    st.markdown("""
    ### Your all-in-one campus companion\nThis application combines several useful tools to help you navigate campus life:\n\n\n\n• **Bus Stop Finder** - Find the nearest bus stop and route from your location
    \n•  **Campus Navigation** - Navigate between important campus locations
    \n•  **Peer Resource Exchange** - Borrow and lend items with fellow students
    \n•  **Timetable Scheduler** - Manage your class schedule and assignments
    \nChoose any option from the sidebar to get started!
    """)
    
    # Display some statistics or featured content
    st.subheader("📊 Campus Insights")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Available Bus Routes", value="20+")
    
    with col2:
        st.metric(label="Campus Locations", value="6")
    
    with col3:
        # Count items in the exchange
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM rental_items")
        item_count = c.fetchone()[0]
        conn.close()
        
        st.metric(label="Items for Exchange", value=str(item_count))
    
    # Display upcoming events from the scheduler
    st.subheader("📆 Upcoming Events")
    today = datetime.today().strftime("%Y-%m-%d")
    upcoming_events = []
    
    for date, events in st.session_state["data"]["events"].items():
        if date >= today:
            for event in events:
                upcoming_events.append({
                    "date": date,
                    "name": event["name"],
                    "time": f"{event['start_time']} - {event['end_time']}"
                })
    
    if upcoming_events:
        # Sort by date
        upcoming_events.sort(key=lambda x: x["date"])
        
        # Display the first 5 events
        for event in upcoming_events[:5]:
            st.write(f"**{event['date']}**: {event['name']} ({event['time']})")
    else:
        st.info("No upcoming events scheduled.")

# Call the appropriate module based on the app choice
elif app_choice == "Bus Stop Finder":
    bus_stop_finder.show()
elif app_choice == "Campus Navigation":
    campus_navigation.show()
elif app_choice == "Peer Resource Exchange":
    peer_resource_exchange.show()
elif app_choice == "Timetable Scheduler":
    timetable_scheduler.show()

if __name__ == "__main__":
    # This will run when the file is executed directly
    pass
