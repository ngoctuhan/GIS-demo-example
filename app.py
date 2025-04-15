from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import json
import random
import datetime
import os
import uuid

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static'))

# Set secret key for session
app.secret_key = 'air_quality_dashboard_secret_key'

# Mock data storage path
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

ZONES_FILE = os.path.join(DATA_DIR, 'zones.json')
DAILY_DATA_FILE = os.path.join(DATA_DIR, 'daily_data.json')
PHU_NGHIA_FILE = os.path.join(DATA_DIR, 'phunghia.json')
QUANG_MINH_FILE = os.path.join(DATA_DIR, 'quangminh.json')

# Admin credentials (in a real app, use a proper auth system)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Default industrial zones (used only if no external JSON files are found)
DEFAULT_ZONES = [
    {
        "name": "Khu Công nghiệp Phú Nghĩa",
        "center": [20.8494, 105.6700],
        "boundary": [
            [20.8550, 105.6650],
            [20.8550, 105.6750],
            [20.8440, 105.6750],
            [20.8440, 105.6650]
        ],
        "grid_size": 10,  # Number of cells in each direction
        "cells": []
    },
    {
        "name": "Khu Công nghiệp Quang Minh",
        "center": [21.1142, 105.7640],
        "boundary": [
            [21.1200, 105.7590],
            [21.1200, 105.7690],
            [21.1090, 105.7690],
            [21.1090, 105.7590]
        ],
        "grid_size": 10,  # Number of cells in each direction
        "cells": []
    }
]

# Check if data files exist, create them if not
def initialize_data_files():
    # Always regenerate zones.json from source files
    zones = generate_air_quality_data()
    with open(ZONES_FILE, 'w', encoding='utf-8') as f:
        json.dump(zones, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(DAILY_DATA_FILE):
        daily_data = generate_daily_data()
        with open(DAILY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(daily_data, f, ensure_ascii=False, indent=2)

# Load zone coordinates from external JSON files
def load_zone_coordinates():
    zones = []
    
    # Try to load Phu Nghia data
    phu_nghia = None
    if os.path.exists(PHU_NGHIA_FILE):
        try:
            with open(PHU_NGHIA_FILE, 'r', encoding='utf-8') as f:
                phu_nghia_data = json.load(f)
                
                # Create zone with direct data from file
                phu_nghia = {
                    "name": "Khu Công nghiệp Phú Nghĩa",
                    "cells": [],
                    "original_squares": [],  # Store the original square data
                }
                
                # Use center directly from the file
                if "center" in phu_nghia_data:
                    center_lat = float(phu_nghia_data["center"][1])
                    center_lng = float(phu_nghia_data["center"][0])
                    phu_nghia["center"] = [center_lat, center_lng]
                else:
                    phu_nghia["center"] = DEFAULT_ZONES[0]["center"]
                
                # Extract cells from squares
                if "square" in phu_nghia_data:
                    phu_nghia["grid_size"] = phu_nghia_data.get("size", 10)
                    
                    # Store original squares for reference
                    boundary_points = []
                    for square in phu_nghia_data["square"]:
                        square_id = square["id"]
                        square_coords = square["coordinates"]
                        square_center = square["center"]
                        
                        # Convert coordinates to float and swap lat/lng
                        converted_coords = []
                        for coord in square_coords:
                            lat = float(coord[1])
                            lng = float(coord[0])
                            converted_coords.append([lat, lng])
                            boundary_points.append([lat, lng])
                        
                        center_lat = float(square_center[1])
                        center_lng = float(square_center[0])
                        
                        phu_nghia["original_squares"].append({
                            "id": square_id,
                            "coordinates": converted_coords,
                            "center": [center_lat, center_lng]
                        })
                    
                    # Create boundary from all points
                    unique_boundary = []
                    for point in boundary_points:
                        if point not in unique_boundary:
                            unique_boundary.append(point)
                    
                    phu_nghia["boundary"] = unique_boundary
                else:
                    phu_nghia["grid_size"] = 10
                    phu_nghia["boundary"] = DEFAULT_ZONES[0]["boundary"]
        except Exception as e:
            print(f"Error loading Phu Nghia data: {str(e)}")
    
    # Try to load Quang Minh data
    quang_minh = None
    if os.path.exists(QUANG_MINH_FILE):
        try:
            with open(QUANG_MINH_FILE, 'r', encoding='utf-8') as f:
                quang_minh_data = json.load(f)
                
                # Create zone with direct data from file
                quang_minh = {
                    "name": "Khu Công nghiệp Quang Minh",
                    "cells": [],
                    "original_squares": [],  # Store the original square data
                }
                
                # Use center directly from the file
                if "center" in quang_minh_data:
                    center_lat = float(quang_minh_data["center"][1])
                    center_lng = float(quang_minh_data["center"][0])
                    quang_minh["center"] = [center_lat, center_lng]
                else:
                    quang_minh["center"] = DEFAULT_ZONES[1]["center"]
                
                # Extract cells from squares
                if "square" in quang_minh_data:
                    quang_minh["grid_size"] = quang_minh_data.get("size", 10)
                    
                    # Store original squares for reference
                    boundary_points = []
                    for square in quang_minh_data["square"]:
                        square_id = square["id"]
                        square_coords = square["coordinates"]
                        square_center = square["center"]
                        
                        # Convert coordinates to float and swap lat/lng
                        converted_coords = []
                        for coord in square_coords:
                            lat = float(coord[1])
                            lng = float(coord[0])
                            converted_coords.append([lat, lng])
                            boundary_points.append([lat, lng])
                        
                        center_lat = float(square_center[1])
                        center_lng = float(square_center[0])
                        
                        quang_minh["original_squares"].append({
                            "id": square_id,
                            "coordinates": converted_coords,
                            "center": [center_lat, center_lng]
                        })
                    
                    # Create boundary from all points
                    unique_boundary = []
                    for point in boundary_points:
                        if point not in unique_boundary:
                            unique_boundary.append(point)
                    
                    quang_minh["boundary"] = unique_boundary
                else:
                    quang_minh["grid_size"] = 10
                    quang_minh["boundary"] = DEFAULT_ZONES[1]["boundary"]
        except Exception as e:
            print(f"Error loading Quang Minh data: {str(e)}")
    
    # Add zones if data was loaded successfully
    if phu_nghia:
        zones.append(phu_nghia)
    if quang_minh:
        zones.append(quang_minh)
    
    # If no external data was loaded, use default zones
    if not zones:
        zones = DEFAULT_ZONES.copy()
    
    return zones

# Fake data for air quality
def generate_air_quality_data():
    # Load zones from external files or use defaults
    zones = load_zone_coordinates()
    
    # Generate grid cells for each zone
    for zone in zones:
        # If we have original squares, use them for cells
        if "original_squares" in zone and zone["original_squares"]:
            for square in zone["original_squares"]:
                # Generate random AQI (Air Quality Index) between 0 and 300
                aqi = random.randint(0, 300)
                
                # Get color based on AQI
                color = get_color_for_aqi(aqi)
                
                # Create a cell from the square
                zone["cells"].append({
                    "id": str(square["id"]),  # Keep original ID for reference
                    "square_id": square["id"],  # Add the original square ID for reference
                    "lat": square["coordinates"][0][0],  # First coordinate lat
                    "lng": square["coordinates"][0][1],  # First coordinate lng
                    "lat_end": square["coordinates"][2][0],  # Third coordinate lat (diagonal)
                    "lng_end": square["coordinates"][2][1],  # Third coordinate lng (diagonal) 
                    "aqi": aqi,
                    "color": color,
                    "center": square["center"]
                })
        else:
            # Fall back to the original method for default zones
            min_lat = min(point[0] for point in zone.get("boundary", DEFAULT_ZONES[0]["boundary"]))
            max_lat = max(point[0] for point in zone.get("boundary", DEFAULT_ZONES[0]["boundary"]))
            min_lng = min(point[1] for point in zone.get("boundary", DEFAULT_ZONES[0]["boundary"]))
            max_lng = max(point[1] for point in zone.get("boundary", DEFAULT_ZONES[0]["boundary"]))
            
            lat_step = (max_lat - min_lat) / zone["grid_size"]
            lng_step = (max_lng - min_lng) / zone["grid_size"]
            
            for i in range(zone["grid_size"]):
                for j in range(zone["grid_size"]):
                    cell_lat = min_lat + i * lat_step
                    cell_lng = min_lng + j * lng_step
                    
                    # Generate random AQI (Air Quality Index) between 0 and 300
                    aqi = random.randint(0, 300)
                    
                    # Get color based on AQI
                    color = get_color_for_aqi(aqi)
                    
                    zone["cells"].append({
                        "id": str(uuid.uuid4()),
                        "lat": cell_lat,
                        "lng": cell_lng,
                        "lat_end": cell_lat + lat_step,
                        "lng_end": cell_lng + lng_step,
                        "aqi": aqi,
                        "color": color
                    })
    
    return zones

def get_color_for_aqi(aqi):
    # AQI color coding
    if aqi <= 50:
        return "#00e400"  # Good - Green
    elif aqi <= 100:
        return "#ffff00"  # Moderate - Yellow
    elif aqi <= 150:
        return "#ff7e00"  # Unhealthy for Sensitive Groups - Orange
    elif aqi <= 200:
        return "#ff0000"  # Unhealthy - Red
    elif aqi <= 300:
        return "#99004c"  # Very Unhealthy - Purple
    else:
        return "#7e0023"  # Hazardous - Maroon

# Register enumerate function for jinja2 templates
app.jinja_env.globals.update(enumerate=enumerate, get_color_for_aqi=get_color_for_aqi)

def generate_daily_data(days=7):
    today = datetime.datetime.now()
    data = []
    
    # Get zones data to access the cell IDs
    try:
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            zones = json.load(f)
    except FileNotFoundError:
        # If zones.json doesn't exist, generate it
        zones = generate_air_quality_data()
        with open(ZONES_FILE, 'w', encoding='utf-8') as f:
            json.dump(zones, f, ensure_ascii=False, indent=2)
    
    # Get all cells from all zones
    all_cells = []
    for zone in zones:
        zone_name = zone["name"]
        for cell in zone["cells"]:
            all_cells.append({
                "id": cell.get("square_id", cell["id"]),  # Use square_id if available, otherwise use id
                "zone": zone_name
            })
    
    # Pollutants to generate
    pollutants = ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]
    
    # Generate data for each day and each cell
    for i in range(days):
        date = today - datetime.timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        for cell in all_cells:
            # Generate random data for the cell
            overall_aqi = random.randint(0, 300)
            pollutant_values = {}
            
            for pollutant in pollutants:
                pollutant_values[pollutant] = random.randint(0, 300)
            
            data.append({
                "id": str(uuid.uuid4()),
                "date": date_str,
                "zone": cell["zone"],
                "cell_id": cell["id"],
                "overall_aqi": overall_aqi,
                "pollutants": pollutant_values
            })
    
    return data

# Main routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/air_quality_data')
def air_quality_data():
    try:
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            zones = json.load(f)
        return jsonify(zones)
    except FileNotFoundError:
        zones = generate_air_quality_data()
        with open(ZONES_FILE, 'w', encoding='utf-8') as f:
            json.dump(zones, f, ensure_ascii=False, indent=2)
        return jsonify(zones)

@app.route('/api/daily_data')
def daily_data():
    try:
        with open(DAILY_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        data = generate_daily_data()
        with open(DAILY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify(data)

# Admin routes
@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Simple session management
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Sai tên đăng nhập hoặc mật khẩu', 'danger')
        return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            zones = json.load(f)
        
        with open(DAILY_DATA_FILE, 'r', encoding='utf-8') as f:
            daily_data = json.load(f)
        
        zone_names = [zone["name"] for zone in zones]
        return render_template('admin_dashboard.html', zones=zones, daily_data=daily_data, zone_names=zone_names)
    except FileNotFoundError:
        initialize_data_files()
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/generate_data', methods=['POST'])
def admin_generate_data():
    data_type = request.form.get('data_type')
    
    if data_type == 'zones':
        zones = generate_air_quality_data()
        with open(ZONES_FILE, 'w', encoding='utf-8') as f:
            json.dump(zones, f, ensure_ascii=False, indent=2)
        flash('Dữ liệu chất lượng không khí đã được cập nhật', 'success')
    
    elif data_type == 'daily':
        days = int(request.form.get('days', 7))
        data = generate_daily_data(days)
        with open(DAILY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        flash(f'Dữ liệu hàng ngày cho {days} ngày đã được cập nhật', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_cell', methods=['POST'])
def admin_edit_cell():
    zone_index = int(request.form.get('zone_index'))
    cell_id = request.form.get('cell_id')
    new_aqi = int(request.form.get('aqi'))
    
    try:
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            zones = json.load(f)
        
        # Find and update the cell
        for i, cell in enumerate(zones[zone_index]["cells"]):
            if cell["id"] == cell_id:
                zones[zone_index]["cells"][i]["aqi"] = new_aqi
                zones[zone_index]["cells"][i]["color"] = get_color_for_aqi(new_aqi)
                break
        
        with open(ZONES_FILE, 'w', encoding='utf-8') as f:
            json.dump(zones, f, ensure_ascii=False, indent=2)
        
        flash('Đã cập nhật ô lưới thành công', 'success')
    except Exception as e:
        flash(f'Lỗi khi cập nhật ô lưới: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_daily_data', methods=['POST'])
def admin_add_daily_data():
    zone = request.form.get('zone')
    date_str = request.form.get('date')
    overall_aqi = int(request.form.get('overall_aqi'))
    
    pollutants = {}
    for p in ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]:
        pollutants[p] = int(request.form.get(p, 0))
    
    try:
        with open(DAILY_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add new data point
        new_data = {
            "id": str(uuid.uuid4()),
            "date": date_str,
            "zone": zone,
            "overall_aqi": overall_aqi,
            "pollutants": pollutants
        }
        
        data.append(new_data)
        
        with open(DAILY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        flash('Đã thêm dữ liệu hàng ngày mới', 'success')
    except Exception as e:
        flash(f'Lỗi khi thêm dữ liệu: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_daily_data', methods=['POST'])
def admin_delete_daily_data():
    data_id = request.form.get('data_id')
    
    try:
        with open(DAILY_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Filter out the deleted item
        data = [item for item in data if item.get('id') != data_id]
        
        with open(DAILY_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        flash('Đã xóa dữ liệu thành công', 'success')
    except Exception as e:
        flash(f'Lỗi khi xóa dữ liệu: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    initialize_data_files()
    app.run(debug=True) 