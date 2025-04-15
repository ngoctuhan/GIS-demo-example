// Initialize the map
let map = L.map('map').setView([20.9818, 105.7172], 11);

// Define basemap layers
let osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
});

let satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 19
});

// Add satellite layer as default
satelliteLayer.addTo(map);

// Create a layer control
let baseLayers = {
    "Bản đồ vệ tinh": satelliteLayer,
    "OpenStreetMap": osmLayer
};

L.control.layers(baseLayers, null, {position: 'topright'}).addTo(map);

// Store the industrial zones data
let industrialZones = [];
let dailyData = [];
let gridLayerGroup = L.layerGroup().addTo(map);
let zoneLayerGroup = L.layerGroup().addTo(map);

// Get AQI description based on value
function getAqiDescription(aqi) {
    if (aqi <= 50) {
        return "Tốt";
    } else if (aqi <= 100) {
        return "Trung bình";
    } else if (aqi <= 150) {
        return "Không lành mạnh cho nhóm nhạy cảm";
    } else if (aqi <= 200) {
        return "Không lành mạnh";
    } else if (aqi <= 300) {
        return "Rất không lành mạnh";
    } else {
        return "Nguy hại";
    }
}

// Function to get color based on AQI value
function getColorForAqi(aqi) {
    // AQI color coding
    if (aqi <= 50) {
        return "#00e400";  // Good - Green
    } else if (aqi <= 100) {
        return "#ffff00";  // Moderate - Yellow
    } else if (aqi <= 150) {
        return "#ff7e00";  // Unhealthy for Sensitive Groups - Orange
    } else if (aqi <= 200) {
        return "#ff0000";  // Unhealthy - Red
    } else if (aqi <= 300) {
        return "#99004c";  // Very Unhealthy - Purple
    } else {
        return "#7e0023";  // Hazardous - Maroon
    }
}

// Fetch air quality data from the server
function fetchAirQualityData() {
    fetch('/api/air_quality_data')
        .then(response => response.json())
        .then(data => {
            industrialZones = data;
            renderMap('all');
        })
        .catch(error => console.error('Error fetching air quality data:', error));
}

// Fetch daily data from the server
function fetchDailyData() {
    fetch('/api/daily_data')
        .then(response => response.json())
        .then(data => {
            dailyData = data;
            updateCharts();
            updateDataTable();
        })
        .catch(error => console.error('Error fetching daily data:', error));
}

// Render the map based on the selected zone
function renderMap(selectedZone) {
    // Clear previous layers
    gridLayerGroup.clearLayers();
    zoneLayerGroup.clearLayers();
    
    let totalAqi = 0;
    let cellCount = 0;
    
    // Filter zones based on selection
    const zonesToRender = selectedZone === 'all' 
        ? industrialZones 
        : industrialZones.filter(zone => zone.name === selectedZone);
    
    // Zoom to selected zone if not showing all
    if (selectedZone !== 'all' && zonesToRender.length > 0) {
        map.setView(zonesToRender[0].center, 15);
    } else if (selectedZone === 'all') {
        // Center map to show both zones
        map.setView([20.9818, 105.7172], 11);
    }
    
    // Render each zone
    zonesToRender.forEach(zone => {
        // Check if the zone has a boundary property
        if (!zone.boundary && zone.original_squares && zone.original_squares.length > 0) {
            // Create boundary from original_squares
            const boundaryPoints = [];
            zone.original_squares.forEach(square => {
                square.coordinates.forEach(coord => {
                    boundaryPoints.push([coord[0], coord[1]]);
                });
            });
            
            // Remove duplicate points
            const uniqueBoundary = [];
            for (const point of boundaryPoints) {
                if (!uniqueBoundary.some(p => p[0] === point[0] && p[1] === point[1])) {
                    uniqueBoundary.push(point);
                }
            }
            
            zone.boundary = uniqueBoundary;
        } else if (!zone.boundary) {
            // Fallback boundary if neither boundary nor original_squares exist
            console.warn(`Zone ${zone.name} has no boundary defined.`);
            return; // Skip this zone
        }
        
        // Create a polygon for the zone boundary - OPTIONAL - Set opacity to 0 to hide
        // const boundaryCoords = zone.boundary.map(coord => [coord[0], coord[1]]);
        // const zoneBoundary = L.polygon(boundaryCoords, {
        //     color: '#3388ff',
        //     weight: 2,
        //     fillOpacity: 0.05,
        //     fillColor: '#3388ff',
        //     opacity: 0.5
        // }).addTo(zoneLayerGroup);
        
        // Add zone label
        L.marker(zone.center, {
            icon: L.divIcon({
                className: 'zone-label',
                html: `<div style="background: rgba(255,255,255,0.9); padding: 5px; border-radius: 3px; box-shadow: 0 0 5px rgba(0,0,0,0.2);">${zone.name}</div>`,
                iconSize: [100, 40],
                iconAnchor: [50, 20]
            })
        }).addTo(zoneLayerGroup);
        
        // Render grid cells
        zone.cells.forEach(cell => {
            const cellCoords = [
                [cell.lat, cell.lng],
                [cell.lat, cell.lng_end],
                [cell.lat_end, cell.lng_end],
                [cell.lat_end, cell.lng]
            ];
            
            // Create a polygon for each cell
            const cellPolygon = L.polygon(cellCoords, {
                color: '#ffffff',
                weight: 1,
                fillColor: cell.color,
                fillOpacity: 0.8,
                className: 'grid-cell'
            }).addTo(gridLayerGroup);
            
            // Add a popup with AQI information
            cellPolygon.bindPopup(`
                <div style="min-width: 200px;">
                    <strong>Khu vực:</strong> ${zone.name}<br>
                    <strong>AQI:</strong> ${cell.aqi}<br>
                    <strong>Đánh giá:</strong> ${getAqiDescription(cell.aqi)}
                </div>
            `);
            
            totalAqi += cell.aqi;
            cellCount++;
        });
    });
    
    // Update zone info in sidebar
    document.getElementById('selected-zone').textContent = selectedZone === 'all' ? 'Tất cả' : selectedZone;
    
    // Calculate average AQI
    if (cellCount > 0) {
        const avgAqi = Math.round(totalAqi / cellCount);
        document.getElementById('avg-aqi').textContent = avgAqi;
        document.getElementById('aqi-status').textContent = getAqiDescription(avgAqi);
    } else {
        document.getElementById('avg-aqi').textContent = '-';
        document.getElementById('aqi-status').textContent = '-';
    }
}

// Update data table with filtered data
function updateDataTable() {
    const selectedZone = document.getElementById('detail-zone-selector').value;
    const dateRange = parseInt(document.getElementById('date-range').value);
    
    // Get all data for the selected zone
    const filteredData = dailyData.filter(item => item.zone === selectedZone);
    
    // Group by date and cell_id to show only the latest data for each cell
    const groupedByDate = {};
    
    // Sort by date (newest first)
    filteredData.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    // Only take the most recent dates up to dateRange
    const dates = [...new Set(filteredData.map(item => item.date))].slice(0, dateRange);
    
    // Filter data for selected dates
    const recentData = filteredData.filter(item => dates.includes(item.date));
    
    // Clear the table
    const tableBody = document.getElementById('data-table').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = '';
    
    // Group data by date
    for (const date of dates) {
        const dateData = recentData.filter(item => item.date === date);
        
        // Calculate average AQI for all cells on this date
        const avgAqi = Math.round(dateData.reduce((sum, item) => sum + item.overall_aqi, 0) / dateData.length);
        
        // Average pollutant values
        const avgPollutants = {};
        for (const pollutant of ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]) {
            avgPollutants[pollutant] = Math.round(
                dateData.reduce((sum, item) => sum + item.pollutants[pollutant], 0) / dateData.length
            );
        }
        
        // Add row to table
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = date;
        row.insertCell(1).textContent = avgAqi;
        row.insertCell(2).textContent = avgPollutants["PM2.5"];
        row.insertCell(3).textContent = avgPollutants["PM10"];
        row.insertCell(4).textContent = avgPollutants["O3"];
        row.insertCell(5).textContent = avgPollutants["NO2"];
        row.insertCell(6).textContent = avgPollutants["SO2"];
        row.insertCell(7).textContent = avgPollutants["CO"];
        
        // Add color coding to AQI cell
        const aqiCell = row.cells[1];
        aqiCell.style.backgroundColor = getColorForAqi(avgAqi);
        aqiCell.style.color = avgAqi > 150 ? '#fff' : '#000';
        aqiCell.style.fontWeight = 'bold';
    }
}

// Update charts with daily data
function updateCharts() {
    const selectedZone = document.getElementById('detail-zone-selector').value;
    const dateRange = parseInt(document.getElementById('date-range').value);
    
    // Get all data for the selected zone
    const filteredData = dailyData.filter(item => item.zone === selectedZone);
    
    // Get unique dates, sorted chronologically
    const dates = [...new Set(filteredData.map(item => item.date))];
    dates.sort();  // Sort chronologically
    
    // Take only the most recent dates up to dateRange
    const recentDates = dates.slice(-dateRange);
    
    // Prepare data for each date
    const chartData = [];
    for (const date of recentDates) {
        const dateData = filteredData.filter(item => item.date === date);
        
        // Calculate average AQI for all cells on this date
        const avgAqi = Math.round(dateData.reduce((sum, item) => sum + item.overall_aqi, 0) / dateData.length);
        
        // Average pollutant values
        const avgPollutants = {};
        for (const pollutant of ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]) {
            avgPollutants[pollutant] = Math.round(
                dateData.reduce((sum, item) => sum + item.pollutants[pollutant], 0) / dateData.length
            );
        }
        
        chartData.push({
            date: date,
            overall_aqi: avgAqi,
            pollutants: avgPollutants
        });
    }
    
    // Extract dates and AQI values for the line chart
    const chartDates = chartData.map(item => item.date);
    const aqiValues = chartData.map(item => item.overall_aqi);
    
    // AQI Chart
    const aqiCtx = document.getElementById('aqi-chart').getContext('2d');
    if (window.aqiChart) {
        window.aqiChart.destroy();
    }
    
    window.aqiChart = new Chart(aqiCtx, {
        type: 'line',
        data: {
            labels: chartDates,
            datasets: [{
                label: 'AQI',
                data: aqiValues,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 350,
                    title: {
                        display: true,
                        text: 'Chỉ số AQI'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Ngày'
                    }
                }
            }
        }
    });
    
    // Pollutants Chart - use the most recent date's data
    if (chartData.length > 0) {
        const latestData = chartData[chartData.length - 1];
        const pollutants = Object.keys(latestData.pollutants);
        const pollutantValues = pollutants.map(p => latestData.pollutants[p]);
        
        const pollutantsCtx = document.getElementById('pollutants-chart').getContext('2d');
        if (window.pollutantsChart) {
            window.pollutantsChart.destroy();
        }
        
        window.pollutantsChart = new Chart(pollutantsCtx, {
            type: 'bar',
            data: {
                labels: pollutants,
                datasets: [{
                    label: 'Chỉ số ô nhiễm',
                    data: pollutantValues,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)',
                        'rgba(255, 159, 64, 0.6)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 350,
                        title: {
                            display: true,
                            text: 'Chỉ số'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Chất ô nhiễm'
                        }
                    }
                }
            }
        });
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Fetch initial data
    fetchAirQualityData();
    fetchDailyData();
    
    // Zone selector change event (Map view)
    document.getElementById('zone-selector').addEventListener('change', (e) => {
        renderMap(e.target.value);
    });
    
    // Update button click event (Data view)
    document.getElementById('update-chart').addEventListener('click', () => {
        updateCharts();
        updateDataTable();
    });
}); 