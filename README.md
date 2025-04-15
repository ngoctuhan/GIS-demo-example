# Air Quality Monitoring System

A Flask web application to display air quality data in industrial zones using GIS (Geographic Information System) on a satellite map.

## Features

- Display air quality map with grid cells
- Color classification based on AQI (Air Quality Index)
- Display on satellite map or street map (switchable)
- Show detailed information for each cell on click
- Time-series data charts
- Detailed pollutant data tables
- Filter data by area and time period
- Admin Dashboard for management and mock data generation

## Installation

### Local Development

1. Clone this repository:
```
git clone <repository-url>
cd gis_air_quality
```

2. Create and activate a virtual environment:
```
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate
```

3. Install required libraries:
```
pip install -r requirements.txt
```

### Docker Deployment

For production deployment, you can use Docker and docker-compose:

1. Build and start the containers:
```
docker-compose up -d
```

2. Check the container status:
```
docker-compose ps
```

3. View the logs:
```
docker-compose logs -f
```

4. Stop the application:
```
docker-compose down
```

## Running the Application

### Local Development

1. Start the server:
```
python app.py
```

2. Open your browser and access:
```
http://127.0.0.1:5000/
```

### Production Deployment

When deployed with Docker, the application uses Gunicorn with 2 workers for better performance. Access the application at:
```
http://your-server-ip:5000/
```

## Accessing the Admin Dashboard

1. Access the admin login page at:
```
http://127.0.0.1:5000/admin
```

2. Login with:
```
Username: admin
Password: admin123
```

3. Admin Dashboard features:
   - Edit air quality data for each grid cell
   - Add/delete daily data
   - Generate new random data

## Data Structure

Sample data is randomly generated with the following parameters:

- PM2.5 (fine particulate matter)
- PM10 (coarse particulate matter)
- O3 (ozone)
- NO2 (nitrogen dioxide)
- SO2 (sulfur dioxide)
- CO (carbon monoxide)

AQI is classified into levels:
- 0-50: Good (green)
- 51-100: Moderate (yellow)
- 101-150: Unhealthy for Sensitive Groups (orange)
- 151-200: Unhealthy (red)
- 201-300: Very Unhealthy (purple)
- >300: Hazardous (maroon)

## Technologies Used

- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Map: Leaflet.js with satellite layer from Esri
- Charts: Chart.js
- UI: Bootstrap 5
- Data Storage: JSON (for simplicity, in real applications a database should be used)
- Deployment: Docker, Gunicorn 