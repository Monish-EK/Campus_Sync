import streamlit as st
import os
import sqlite3
import hashlib
from datetime import datetime

def show():
    st.title("📌 Peer Exchange Platform")
    
    # Initialize session state if not already done
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
    
    # Sub-navigation for Peer Exchange
    peer_menu = ["Home", "Login", "Register", "Add Listing", "Skill Tutoring", "Student Services", "Users & Rentals"]
    peer_choice = st.sidebar.radio("Peer Exchange Navigation", peer_menu)
    
    # Hash passwords for security
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    # Register a new user
    def register_user(username, password):
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        hashed_password = hash_password(password)
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    # Authenticate user login
    def authenticate_user(username, password):
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        hashed_password = hash_password(password)
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = c.fetchone()
        conn.close()
        return user

    # Add a listing (can be item, skill, or service)
    def add_listing(owner, name, description, price, image_path, contact, listing_type):
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO rental_items (owner, name, description, price, image_path, contact, listing_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (owner, name, description, price, image_path, contact, listing_type))
        conn.commit()
        conn.close()

    # Fetch all listings of a specific type
    def get_items_by_type(listing_type=None):
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        
        if listing_type:
            c.execute("SELECT * FROM rental_items WHERE listing_type = ?", (listing_type,))
        else:
            c.execute("SELECT * FROM rental_items")
            
        items = c.fetchall()
        conn.close()
        return items

    # Request rental/service approval
    def request_rental(item_id, rented_by, borrow_date, return_date):
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        c.execute("""
            UPDATE rental_items 
            SET rented_by = ?, borrow_date = ?, return_date = ?, approved = 'pending'
            WHERE id = ?
        """, (rented_by, borrow_date, return_date, item_id))
        conn.commit()
        conn.close()

    # Approve rental/service requests
    def approve_rental(item_id):
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        c.execute("UPDATE rental_items SET approved = 'approved' WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    # Fetch user rentals
    def get_users_and_rented_items():
        conn = sqlite3.connect("peer_resource_exchange.db")
        c = conn.cursor()
        c.execute("SELECT id, owner, name, price, rented_by, borrow_date, return_date, approved, listing_type FROM rental_items")
        data = c.fetchall()
        conn.close()
        return data
    
    # Implement Peer Exchange based on chosen submenu
    if peer_choice == "Home":
        st.subheader("🏠 Available Listings")
        
        # Add filter options
        filter_options = ["All", "Items", "Skills", "Services"]
        filter_choice = st.selectbox("Filter by type:", filter_options)
        
        # Get listings based on filter
        if filter_choice == "All":
            items = get_items_by_type()
        elif filter_choice == "Items":
            items = get_items_by_type("item")
        elif filter_choice == "Skills":
            items = get_items_by_type("skill")
        else:
            items = get_items_by_type("service")
        
        if not items:
            st.info("No listings available yet.")
        else:
            cols = st.columns(2)  # Display in a 2-column format

            for index, item in enumerate(items):
                with cols[index % 2]:  # Distribute items across columns
                    # Get listing type (default to "item" for backward compatibility)
                    listing_type = item[11] if len(item) > 11 and item[11] else "item"
                    
                    # Icons based on listing type
                    icons = {
                        "item": "📦",
                        "skill": "📚",
                        "service": "🛠️"
                    }
                    icon = icons.get(listing_type, "📦")
                    
                    st.subheader(f"{icon} {item[2]} (by {item[1]})")
                    
                    # Show price with appropriate label
                    if listing_type == "item":
                        st.write(f"💰 ₹{item[4]} per day")
                    elif listing_type == "skill":
                        st.write(f"💰 ₹{item[4]} per hour")
                    else:
                        st.write(f"💰 ₹{item[4]}")
                        
                    st.write(f"📞 Contact: {item[6]}")
                    st.write(f"📝 {item[3]}")

                    if item[5] and os.path.exists(item[5]):
                        st.image(item[5], width=150)
                    else:
                        st.warning("No image available.")

                    if item[7]:  # If rented/booked
                        if item[10] == "pending":
                            st.info(f"⏳ {item[7]} requested. Waiting for approval.")
                        else:
                            st.success(f"✅ Booked by {item[7]} from {item[8]} to {item[9]}")
                    else:
                        if st.session_state["logged_in"]:
                            if listing_type == "item":
                                borrow_label = "Borrow Date"
                                return_label = "Return Date"
                                button_label = f"Request to Rent {item[2]}"
                            elif listing_type == "skill":
                                borrow_label = "Start Date"
                                return_label = "End Date"
                                button_label = f"Schedule Tutoring with {item[1]}"
                            else:
                                borrow_label = "Service Date"
                                return_label = "Completion Date"
                                button_label = f"Book Service from {item[1]}"
                                
                            borrow_date = st.date_input(f"{borrow_label} for {item[2]}", datetime.today())
                            return_date = st.date_input(f"{return_label} for {item[2]}", datetime.today())

                            if st.button(button_label, key=f"rent_{item[0]}"):
                                request_rental(item[0], st.session_state["username"], borrow_date, return_date)
                                st.success(f"Request for {item[2]} sent.")
                                st.rerun()

    elif peer_choice == "Register":
        st.subheader("📝 Create an Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if register_user(new_user, new_pass):
                st.success("🎉 Account created! You can now log in.")
            else:
                st.error("Username already exists.")

    elif peer_choice == "Login":
        st.subheader("🔑 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"✅ Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    elif peer_choice == "Add Listing":
        if st.session_state["logged_in"]:
            st.subheader("➕ Create a New Listing")
            
            # Toggle button for listing type
            listing_type = st.radio(
                "What would you like to offer?",
                options=["Item for Rent", "Skill Tutoring", "Student Service"],
                horizontal=True
            )
            
            # Map radio button choices to database values
            listing_type_map = {
                "Item for Rent": "item",
                "Skill Tutoring": "skill",
                "Student Service": "service"
            }
            
            # Form fields based on listing type
            if listing_type == "Item for Rent":
                item_name = st.text_input("Item Name")
                description = st.text_area("Description")
                price = st.number_input("Daily Rental Price (in ₹)", min_value=0.0, format="%.2f")
                placeholder = "Example: Calculator, Electronics Lab equipment, Books"
            elif listing_type == "Skill Tutoring":
                item_name = st.text_input("Subject/Skill")
                description = st.text_area("Description (include your expertise level, teaching style, etc.)")
                price = st.number_input("Hourly Rate (in ₹)", min_value=0.0, format="%.2f")
                placeholder = "Example: Python Programming, Physics, Guitar lessons"
            else:  # Student Service
                item_name = st.text_input("Service Name")
                description = st.text_area("Description (include details, turnaround time, etc.)")
                price = st.number_input("Service Price (in ₹)", min_value=0.0, format="%.2f")
                placeholder = "Example: Poster Design, Website Development, Engineering Drawing"
            
            st.caption(placeholder)
            contact = st.text_input("Your Contact Number")
            image = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

            image_path = None
            if image:
                if not os.path.exists("uploads"):
                    os.makedirs("uploads")
                image_path = os.path.join("uploads", image.name)
                with open(image_path, "wb") as f:
                    f.write(image.read())

            if st.button("Add Listing"):
                add_listing(
                    st.session_state["username"], 
                    item_name, 
                    description, 
                    price, 
                    image_path, 
                    contact, 
                    listing_type_map[listing_type]
                )
                st.success(f"'{item_name}' added successfully!")
                st.rerun()
        else:
            st.warning("You must log in first.")

    elif peer_choice == "Skill Tutoring":
        st.subheader("📚 Available Tutoring")
        skills = get_items_by_type("skill")
        
        if not skills:
            st.info("No tutoring services available yet.")
        else:
            for skill in skills:
                st.write("---")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"📚 {skill[2]}")
                    st.write(f"**Tutor:** {skill[1]}")
                    st.write(f"**Rate:** ₹{skill[4]} per hour")
                    st.write(f"**Contact:** {skill[6]}")
                    st.write(f"**Description:** {skill[3]}")
                
                with col2:
                    if skill[5] and os.path.exists(skill[5]):
                        st.image(skill[5], width=150)
                
                if skill[7]:  # If booked
                    if skill[10] == "pending":
                        st.info(f"⏳ {skill[7]} requested tutoring. Waiting for tutor approval.")
                    else:
                        st.success(f"✅ Booked by {skill[7]} from {skill[8]} to {skill[9]}")
                else:
                    if st.session_state["logged_in"]:
                        col3, col4 = st.columns(2)
                        with col3:
                            start_date = st.date_input(f"Start Date for {skill[2]}", datetime.today())
                        with col4:
                            end_date = st.date_input(f"End Date for {skill[2]}", datetime.today())

                        if st.button(f"Schedule Tutoring with {skill[1]}", key=f"skill_{skill[0]}"):
                            request_rental(skill[0], st.session_state["username"], start_date, end_date)
                            st.success(f"Tutoring request for {skill[2]} sent.")
                            st.rerun()

    elif peer_choice == "Student Services":
        st.subheader("🛠️ Student Services")
        services = get_items_by_type("service")
        
        if not services:
            st.info("No student services available yet.")
        else:
            for service in services:
                st.write("---")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"🛠️ {service[2]}")
                    st.write(f"**Provider:** {service[1]}")
                    st.write(f"**Price:** ₹{service[4]}")
                    st.write(f"**Contact:** {service[6]}")
                    st.write(f"**Description:** {service[3]}")
                
                with col2:
                    if service[5] and os.path.exists(service[5]):
                        st.image(service[5], width=150)
                
                if service[7]:  # If booked
                    if service[10] == "pending":
                        st.info(f"⏳ {service[7]} requested this service. Waiting for approval.")
                    else:
                        st.success(f"✅ Booked by {service[7]} from {service[8]} to {service[9]}")
                else:
                    if st.session_state["logged_in"]:
                        col3, col4 = st.columns(2)
                        with col3:
                            service_date = st.date_input(f"Service Date for {service[2]}", datetime.today())
                        with col4:
                            completion_date = st.date_input(f"Expected Completion for {service[2]}", datetime.today())

                        if st.button(f"Book Service from {service[1]}", key=f"service_{service[0]}"):
                            request_rental(service[0], st.session_state["username"], service_date, completion_date)
                            st.success(f"Service request for {service[2]} sent.")
                            st.rerun()

    elif peer_choice == "Users & Rentals":
        st.subheader("📋 Pending Requests")
        rentals = get_users_and_rented_items()
        
        # Group by listing type
        pending_items = []
        pending_skills = []
        pending_services = []
        approved_items = []
        
        for rental in rentals:
            listing_type = rental[8] if len(rental) > 8 and rental[8] else "item"  # Default to "item" for backward compatibility
            
            if rental[4] and rental[7] == "pending" and rental[1] == st.session_state["username"]:
                if listing_type == "item":
                    pending_items.append(rental)
                elif listing_type == "skill":
                    pending_skills.append(rental)
                else:
                    pending_services.append(rental)
            else:
                approved_items.append(rental)
        
        # Display pending item rentals
        if pending_items:
            st.write("### 📦 Pending Item Rental Requests")
            for item in pending_items:
                if st.button(f"Approve {item[4]}'s request for {item[2]}", key=f"approve_item_{item[0]}"):
                    approve_rental(item[0])
                    st.success(f"Rental approved for {item[4]}.")
                    st.rerun()
        
        # Display pending skill tutoring
        if pending_skills:
            st.write("### 📚 Pending Tutoring Requests")
            for skill in pending_skills:
                if st.button(f"Approve {skill[4]}'s request for {skill[2]} tutoring", key=f"approve_skill_{skill[0]}"):
                    approve_rental(skill[0])
                    st.success(f"Tutoring session approved for {skill[4]}.")
                    st.rerun()
        
        # Display pending services
        if pending_services:
            st.write("### 🛠️ Pending Service Requests")
            for service in pending_services:
                if st.button(f"Approve {service[4]}'s request for {service[2]}", key=f"approve_service_{service[0]}"):
                    approve_rental(service[0])
                    st.success(f"Service approved for {service[4]}.")
                    st.rerun()
        
        # If no pending requests
        if not pending_items and not pending_skills and not pending_services:
            st.info("No pending requests.")
        
        # Show all approved listings
        st.write("### 📋 All Listings")
        for rental in approved_items:
            listing_type = rental[8] if len(rental) > 8 and rental[8] else "item"
            
            icons = {
                "item": "📦",
                "skill": "📚",
                "service": "🛠️"
            }
            icon = icons.get(listing_type, "📦")
            
            st.write(f"{icon} **{rental[1]}** listed **{rental[2]}** (₹{rental[3]}) - {rental[4] or 'Available'}")

if __name__ == "__main__":
    # Create necessary database tables when run standalone
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

        # Rental items table - Add listing_type column if it doesn't exist
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
                approved TEXT DEFAULT 'pending',
                listing_type TEXT DEFAULT 'item'
            )
        """)
        
        # Check if listing_type column exists, add it if not
        try:
            c.execute("SELECT listing_type FROM rental_items LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            c.execute("ALTER TABLE rental_items ADD COLUMN listing_type TEXT DEFAULT 'item'")
        
        conn.commit()
        conn.close()

    # Setup for standalone run
    create_tables()
    st.set_page_config(page_title="Peer Exchange Platform", page_icon="📌")
    show()