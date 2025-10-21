import streamlit as st
import folium
from streamlit_folium import st_folium
import math
from geopy.distance import geodesic
import streamlit.components.v1 as components
import requests

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        font-weight: 600;
    }
    .location-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    h1, h2, h3 {
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Campus locations with coordinates
CAMPUS_LOCATIONS = {
    "REC Ground": (13.008583, 80.004445),
    "REC Basketball Court": (13.009092, 80.004046),
    "Xerox": (13.008434, 80.003711),
    "B Block": (13.009143, 80.003212),
    "Aircraft": (13.009475, 80.003025),
    "REC Main Gate": (13.010573, 80.002384),
    "Architecture Block": (13.008279, 80.001577),
    "Heka": (13.007728, 80.002058),
    "D Block": (13.007839, 80.002421),
    "Indoor Auditorium": (13.008360, 80.005498),
    "Cafe Coffee Day": (13.008654, 80.005464),
    "Library Block": (13.008949, 80.005462),
    "Transport Office": (13.009275, 80.005503),
    "Tech Lounge": (13.009452, 80.005065),
    "A Block": (13.009449, 80.004216),
    "Ladies Hostel": (13.007242, 80.005592),
    "Boys Mess": (13.007440, 80.004371),
    "Hut Cafe": (13.008207, 80.003396),
    "REC Cafe": (13.008335, 80.002526),
    "Mechanical Block": (13.007880, 80.002729),
    "Solid Mechanics Lab": (13.008224, 80.002942),
    "Fluid Mechanics Lab": (13.008253, 80.003116),
    "Students Parking": (13.012133, 80.000642),
}

# Initialize session state
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'location_acquired' not in st.session_state:
    st.session_state.location_acquired = False
if 'use_live_location' not in st.session_state:
    st.session_state.use_live_location = False

def get_location_component():
    """Component to get user's live location"""
    location_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                text-align: center;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            }
            .icon {
                font-size: 64px;
                margin-bottom: 20px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            .spinner {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top: 4px solid white;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .status {
                font-size: 18px;
                margin: 20px 0;
                line-height: 1.6;
            }
            .coords {
                background: rgba(0, 0, 0, 0.3);
                padding: 15px;
                border-radius: 10px;
                font-family: monospace;
                margin-top: 20px;
                font-size: 14px;
            }
            .button {
                background: white;
                color: #667eea;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 20px;
                transition: all 0.3s;
            }
            .button:hover {
                transform: scale(1.05);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            .error {
                background: rgba(255, 107, 107, 0.3);
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
            }
            .success {
                color: #00ff88;
                font-size: 72px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon" id="icon">📍</div>
            <div class="status" id="status">Requesting your location...</div>
            <div class="spinner" id="spinner"></div>
            <div id="result"></div>
        </div>

        <script>
            const statusEl = document.getElementById('status');
            const spinnerEl = document.getElementById('spinner');
            const resultEl = document.getElementById('result');
            const iconEl = document.getElementById('icon');

            function getLocation() {
                if (!navigator.geolocation) {
                    showError('Geolocation not supported by your browser');
                    return;
                }

                statusEl.textContent = '🔔 Please allow location access';

                navigator.geolocation.getCurrentPosition(
                    position => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        const acc = Math.round(position.coords.accuracy);

                        spinnerEl.style.display = 'none';
                        iconEl.innerHTML = '✅';
                        iconEl.className = 'icon success';
                        statusEl.textContent = 'Location Acquired Successfully!';

                        resultEl.innerHTML = `
                            <div class="coords">
                                <div><strong>Latitude:</strong> ${lat.toFixed(6)}</div>
                                <div><strong>Longitude:</strong> ${lng.toFixed(6)}</div>
                                <div><strong>Accuracy:</strong> ±${acc}m</div>
                            </div>
                        `;

                        // Send to Streamlit
                        const data = {
                            latitude: lat,
                            longitude: lng,
                            accuracy: acc
                        };

                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: data
                        }, '*');

                        localStorage.setItem('campus_location', JSON.stringify(data));

                        setTimeout(() => {
                            statusEl.textContent = 'Redirecting to navigation...';
                            window.parent.postMessage({
                                type: 'streamlit:rerun'
                            }, '*');
                        }, 2000);
                    },
                    error => {
                        spinnerEl.style.display = 'none';
                        iconEl.innerHTML = '❌';
                        
                        let msg = '';
                        let help = '';
                        
                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                msg = 'Location Permission Denied';
                                help = `
                                    <strong>Enable Location Access:</strong><br><br>
                                    <strong>📱 Android Chrome:</strong><br>
                                    Settings → Site settings → Location → Allow<br><br>
                                    <strong>🍎 iOS Safari:</strong><br>
                                    Settings → Privacy → Location Services → Safari → While Using<br><br>
                                    <strong>💻 Desktop:</strong><br>
                                    Click lock icon in address bar → Location → Allow
                                `;
                                break;
                            case error.POSITION_UNAVAILABLE:
                                msg = 'Location Unavailable';
                                help = 'Please enable GPS on your device';
                                break;
                            case error.TIMEOUT:
                                msg = 'Request Timeout';
                                help = 'Please try again';
                                break;
                        }
                        
                        statusEl.textContent = msg;
                        resultEl.innerHTML = `<div class="error">${help}</div>`;
                        
                        const btn = document.createElement('button');
                        btn.className = 'button';
                        btn.textContent = '🔄 Try Again';
                        btn.onclick = () => location.reload();
                        resultEl.appendChild(btn);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 15000,
                        maximumAge: 0
                    }
                );
            }

            function showError(msg) {
                spinnerEl.style.display = 'none';
                iconEl.innerHTML = '❌';
                statusEl.textContent = msg;
            }

            getLocation();
        </script>
    </body>
    </html>
    """
    return components.html(location_html, height=600)

def calculate_distance(point1, point2):
    """Calculate distance between two coordinates in meters"""
    return geodesic(point1, point2).meters

def calculate_bearing(point1, point2):
    """Calculate bearing between two points"""
    lat1, lng1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lng2 = math.radians(point2[0]), math.radians(point2[1])
    
    dLng = lng2 - lng1
    x = math.sin(dLng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLng)
    
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

def get_direction(bearing):
    """Convert bearing to direction"""
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    idx = round(bearing / 45) % 8
    return directions[idx]

def get_route(start_coords, end_coords):
    """Get walking route from OSRM (OpenStreetMap routing)"""
    try:
        url = f"http://router.project-osrm.org/route/v1/foot/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('routes') and len(data['routes']) > 0:
                route = data['routes'][0]
                coordinates = route['geometry']['coordinates']
                route_points = [(coord[1], coord[0]) for coord in coordinates]
                
                distance = route['distance']
                duration = route['duration']
                
                steps = []
                if 'legs' in route and len(route['legs']) > 0:
                    for step in route['legs'][0].get('steps', []):
                        maneuver = step.get('maneuver', {})
                        instruction = maneuver.get('type', 'continue')
                        modifier = maneuver.get('modifier', '')
                        step_distance = step.get('distance', 0)
                        
                        if instruction != 'arrive':
                            steps.append({
                                'instruction': f"{instruction} {modifier}".strip(),
                                'distance': step_distance
                            })
                
                return {
                    'route_points': route_points,
                    'distance': distance,
                    'duration': duration,
                    'steps': steps
                }
        
        return {
            'route_points': [start_coords, end_coords],
            'distance': geodesic(start_coords, end_coords).meters,
            'duration': geodesic(start_coords, end_coords).meters / 1.4,
            'steps': []
        }
        
    except Exception as e:
        return {
            'route_points': [start_coords, end_coords],
            'distance': geodesic(start_coords, end_coords).meters,
            'duration': geodesic(start_coords, end_coords).meters / 1.4,
            'steps': []
        }

def create_map(source_coords, destination_coords, source_name, dest_name):
    """Create folium map with real road route"""
    
    route_data = get_route(source_coords, destination_coords)
    route_points = route_data['route_points']
    
    center_lat = (source_coords[0] + destination_coords[0]) / 2
    center_lng = (source_coords[1] + destination_coords[1]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=16,
        tiles=None
    )
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Satellite + Labels',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    folium.PolyLine(
        route_points,
        color='#FFD700',
        weight=8,
        opacity=0.9,
        popup=f'Walking Route: {route_data["distance"]:.0f}m'
    ).add_to(m)
    
    num_arrows = min(len(route_points) // 5, 10)
    for i in range(1, num_arrows):
        idx = i * (len(route_points) // num_arrows)
        if idx < len(route_points) - 1:
            folium.CircleMarker(
                route_points[idx],
                radius=4,
                color='yellow',
                fill=True,
                fillColor='#FFD700',
                fillOpacity=0.9,
                popup=f'Waypoint {i}'
            ).add_to(m)
    
    if source_name == "📱 Your Location":
        folium.Marker(
            source_coords,
            popup=f"<b>{source_name}</b><br>{source_coords[0]:.6f}, {source_coords[1]:.6f}",
            tooltip="You are here!",
            icon=folium.Icon(color='blue', icon='user', prefix='fa')
        ).add_to(m)
        
        for radius, opacity in [(10, 0.7), (20, 0.4), (30, 0.2)]:
            folium.Circle(
                source_coords,
                radius=radius,
                color='#0066FF',
                fill=True,
                fillColor='#0066FF',
                fillOpacity=opacity
            ).add_to(m)
    else:
        folium.Marker(
            source_coords,
            popup=f"<b>Start: {source_name}</b>",
            tooltip=source_name,
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(m)
        
        folium.Circle(
            source_coords,
            radius=8,
            color='green',
            fill=True,
            fillColor='green',
            fillOpacity=0.6
        ).add_to(m)
    
    folium.Marker(
        destination_coords,
        popup=f"<b>Destination: {dest_name}</b>",
        tooltip=dest_name,
        icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
    ).add_to(m)
    
    folium.Circle(
        destination_coords,
        radius=10,
        color='red',
        fill=True,
        fillColor='red',
        fillOpacity=0.7
    ).add_to(m)
    
    return m, route_data

def show():
    """Main function called from home.py"""
    st.markdown("<h1 style='text-align: center;'>🎯 Campus Navigation System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Live Location Tracking & Turn-by-Turn Navigation</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_toggle, col_btn = st.columns([3, 1])
    
    with col_toggle:
        use_live = st.checkbox(
            "🔴 Use My Current Location",
            value=st.session_state.use_live_location,
            help="Enable to navigate from your current GPS location"
        )
        st.session_state.use_live_location = use_live
    
    with col_btn:
        if use_live and not st.session_state.location_acquired:
            if st.button("📍 Get Location", type="primary"):
                st.markdown("---")
                get_location_component()
                st.stop()
    
    if use_live and not st.session_state.user_location:
        st.info("👆 Click 'Get Location' to start live navigation")
        st.markdown("---")
    
    if use_live and st.session_state.user_location:
        lat, lng = st.session_state.user_location
        st.markdown(f"""
        <div class="location-card">
            <h3>✅ Live Location Active</h3>
            <p><strong>Coordinates:</strong> {lat:.6f}, {lng:.6f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Update Location"):
            st.session_state.location_acquired = False
            st.rerun()
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📍 From")
        if use_live and st.session_state.user_location:
            source_name = "📱 Your Location"
            source_coords = st.session_state.user_location
            st.info(f"Using live GPS location\n\n{source_coords[0]:.6f}, {source_coords[1]:.6f}")
        else:
            source_name = st.selectbox(
                "Select starting point",
                options=list(CAMPUS_LOCATIONS.keys()),
                index=list(CAMPUS_LOCATIONS.keys()).index("Hut Cafe")
            )
            source_coords = CAMPUS_LOCATIONS[source_name]
    
    with col2:
        st.markdown("### 🎯 To")
        dest_name = st.selectbox(
            "Select destination",
            options=list(CAMPUS_LOCATIONS.keys()),
            index=list(CAMPUS_LOCATIONS.keys()).index("Library Block")
        )
        dest_coords = CAMPUS_LOCATIONS[dest_name]
    
    with st.spinner("🗺️ Calculating best route..."):
        campus_map, route_data = create_map(source_coords, dest_coords, source_name, dest_name)
    
    distance = route_data['distance']
    walking_time = int(route_data['duration'] / 60)
    bearing = calculate_bearing(source_coords, dest_coords)
    direction = get_direction(bearing)
    
    st.markdown("---")
    st.markdown("### 📊 Route Information")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #667eea; margin: 0;">📏</h2>
            <h3 style="margin: 5px 0;">{distance:.0f}m</h3>
            <p style="color: #666; margin: 0;">Distance</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_m2:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #667eea; margin: 0;">⏱️</h2>
            <h3 style="margin: 5px 0;">{walking_time} min</h3>
            <p style="color: #666; margin: 0;">Walking Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_m3:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #667eea; margin: 0;">🧭</h2>
            <h3 style="margin: 5px 0;">{direction}</h3>
            <p style="color: #666; margin: 0;">Direction</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_m4:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="color: #667eea; margin: 0;">📐</h2>
            <h3 style="margin: 5px 0;">{bearing:.0f}°</h3>
            <p style="color: #666; margin: 0;">Bearing</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🚶 Walking Directions")
    
    if route_data.get('steps') and len(route_data['steps']) > 0:
        st.success("📍 Turn-by-turn navigation:")
        for idx, step in enumerate(route_data['steps'][:5], 1):
            instruction = step['instruction'].replace('_', ' ').title()
            step_distance = step['distance']
            st.info(f"**Step {idx}:** {instruction} - Continue for {step_distance:.0f}m")
    else:
        instruction = f"Walk {direction} ({bearing:.0f}°) for approximately {distance:.0f} meters"
        st.info(f"📍 {instruction}")
    
    if distance < 50:
        st.success("🎯 You're very close to your destination!")
    elif distance < 100:
        st.success("✅ You're nearby! Just a short walk away.")
    
    st.markdown("---")
    st.markdown("### 🗺️ Live Navigation Map")
    st.caption("The yellow line shows the walking route following actual roads and pathways")
    
    st_folium(campus_map, width=700, height=500, returned_objects=[])
    
    st.markdown("---")
    st.markdown("### ⚡ Quick Access")
    
    popular_locations = ["Library Block", "Hut Cafe", "REC Cafe", "Indoor Auditorium", "A Block", "Tech Lounge"]
    cols = st.columns(3)
    
    for idx, loc in enumerate(popular_locations):
        with cols[idx % 3]:
            if st.button(f"📍 {loc}", use_container_width=True):
                st.session_state.quick_dest = loc
                st.rerun()
    
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        ### 📱 Getting Started
        
        **For Live Navigation:**
        1. ✅ Check "Use My Current Location"
        2. 📍 Click "Get Location" button
        3. 🔔 Allow location access when prompted
        4. 🎯 Select your destination
        5. 🗺️ Follow the yellow route on the map
        
        **Understanding the Map:**
        - 🔵 **Blue pulsing marker** = Your live location
        - 🟢 **Green marker** = Selected start point
        - 🔴 **Red flag** = Destination
        - 💛 **Yellow line** = Walking route
        
        **Navigation Info:**
        - **Distance**: Total walking distance
        - **Walking Time**: Estimated at 1.4 m/s (normal pace)
        - **Direction**: Cardinal direction (N, NE, E, etc.)
        - **Bearing**: Precise compass direction in degrees
        
        **Tips for Best Results:**
        - 📡 Move to an open area for better GPS accuracy
        - 🔋 Enable high accuracy mode in location settings
        - 🏢 Indoor GPS may be less accurate
        - 🔄 Click "Update Location" to refresh your position
        
        **Troubleshooting:**
        - **Permission denied**: Enable location in browser settings
        - **Inaccurate location**: Move outside or near windows
        - **Timeout**: Check if GPS is enabled on your device
        """)