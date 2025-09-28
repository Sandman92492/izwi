// Dashboard Map and Alert Management
console.log('Dashboard JavaScript loading...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready, initializing map...');
    
    // Check if map container exists and has dimensions
    var mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('Map container not found!');
        return;
    }
    
    console.log('Map container dimensions:', mapContainer.offsetWidth, 'x', mapContainer.offsetHeight);
    
    // Get alerts data from data attribute
    var alertsData = document.getElementById('alerts-data');
    var alerts = alertsData ? JSON.parse(alertsData.textContent) : [];
    
    console.log('Alerts data:', alerts);

    // Get boundary data from data attribute  
    var boundaryDataElement = document.getElementById('boundary-data');
    var boundaryData = boundaryDataElement ? JSON.parse(boundaryDataElement.textContent) : null;
    
    console.log('Boundary data:', boundaryData);

    // Calculate map center based on alerts
    var mapCenter = [-26.2041, 28.0473]; // Default to Johannesburg
    var mapZoom = 13;

    if (alerts.length > 0) {
        // Filter alerts with valid coordinates
        var validAlerts = alerts.filter(function(alert) {
            return alert.lat !== -26.2041 || alert.lng !== 28.0473;
        });
        
        if (validAlerts.length > 0) {
            // Calculate average coordinates
            var sumLat = validAlerts.reduce(function(sum, alert) { return sum + alert.lat; }, 0);
            var sumLng = validAlerts.reduce(function(sum, alert) { return sum + alert.lng; }, 0);
            
            mapCenter = [sumLat / validAlerts.length, sumLng / validAlerts.length];
            mapZoom = validAlerts.length === 1 ? 15 : 13; // Zoom closer for single alert
        }
    }

    console.log('Map center:', mapCenter, 'zoom:', mapZoom);

    // Initialize the map with calculated center
    var map;
    try {
        map = L.map('map').setView(mapCenter, mapZoom);
        console.log('Map initialized successfully');
    } catch (e) {
        console.error('Error initializing map:', e);
        return;
    }

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Community boundary variable
    var communityBoundary = null;

    // Load and display community boundary if available
    if (boundaryData) {
        try {
            var geoJsonData = JSON.parse(boundaryData);
            
            // Add boundary to map with styling
            communityBoundary = L.geoJSON(geoJsonData, {
                style: {
                    color: '#264653',
                    weight: 3,
                    opacity: 0.8,
                    fillColor: '#264653',
                    fillOpacity: 0.1,
                    dashArray: '5, 5'
                }
            }).addTo(map);
            
            // Fit map to boundary if no alerts or if alerts don't provide good bounds
            if (alerts.length === 0) {
                map.fitBounds(communityBoundary.getBounds(), {
                    padding: [20, 20]
                });
            }
        } catch (e) {
            console.log('Error loading community boundary:', e);
        }
    }

    // Add markers for each alert
    alerts.forEach(function(alert) {
        var categoryColor = getCategoryColor(alert.category);
        var categoryIcon = getCategoryIcon(alert.category);
        
        var icon = L.divIcon({
            className: 'custom-alert-marker',
            html: '<div class="relative">' +
                  '<div class="w-12 h-12 rounded-full flex items-center justify-center text-white text-xl font-bold shadow-lg border-4 border-white" style="background-color: ' + categoryColor + ';">' + 
                  categoryIcon + 
                  '</div>' +
                  '<div class="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-8 border-transparent" style="border-top-color: ' + categoryColor + ';"></div>' +
                  '</div>',
            iconSize: [48, 56],
            iconAnchor: [24, 48]
        });
        
        var marker = L.marker([alert.lat, alert.lng], {icon: icon}).addTo(map);
        marker.bindPopup('<div class="p-3"><div class="flex items-center gap-2 mb-2"><span class="text-lg">' + categoryIcon + '</span><strong class="text-lg">' + alert.category + '</strong></div>' + 
                         '<p class="text-gray-700">' + alert.description + '</p><small class="text-gray-500">' + alert.timestamp + '</small></div>');
    });

    // If no valid alerts, try to get user's location
    if (alerts.length === 0 || alerts.every(function(alert) { 
        return alert.lat === -26.2041 && alert.lng === 28.0473; 
    })) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var userLat = position.coords.latitude;
                var userLng = position.coords.longitude;
                map.setView([userLat, userLng], 15);
            });
        }
    }

    // Make map available globally for debugging
    window.dashboardMap = map;
    
    console.log('Map setup complete');
});

// Utility functions for alert categories
function getCategoryIcon(category) {
    switch(category.toLowerCase()) {
        case 'emergency': return '🚨';
        case 'fire': return '🔥';
        case 'traffic': return '🚗';
        case 'weather': return '⛈️';
        case 'community': return '🏘️';
        default: return '❗';
    }
}

function getCategoryColor(category) {
    switch(category.toLowerCase()) {
        case 'emergency': return '#DC2626'; // Red
        case 'fire': return '#EA580C'; // Orange-red
        case 'traffic': return '#2563EB'; // Blue
        case 'weather': return '#7C3AED'; // Purple
        case 'community': return '#059669'; // Green
        default: return '#6B7280'; // Gray
    }
}

// Navigation functions
function showPostAlert() {
    window.location.href = '/post-alert';
}

function reportAlert(alertId) {
    if (confirm('Are you sure you want to report this alert for inappropriate content?')) {
        fetch('/report-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]') ? 
                    document.querySelector('input[name="csrf_token"]').value : ''
            },
            body: JSON.stringify({
                alert_id: alertId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Thank you for your report. We will review this content.');
            } else {
                alert('There was an error submitting your report. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error reporting alert:', error);
            alert('There was an error submitting your report. Please try again.');
        });
    }
}

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alertMessages = document.querySelectorAll('.alert-message');
    alertMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
                // Refresh map size after layout change
                if (window.dashboardMap) {
                    window.dashboardMap.invalidateSize();
                }
            }, 500);
        }, 5000);
    });
});