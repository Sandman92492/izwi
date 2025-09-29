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

    // Location detection and map centering
    var mapCenter = [-26.2041, 28.0473]; // Default to Johannesburg
    var mapZoom = 13;
    var locationDetected = false;

    // Check if we have meaningful alerts with real coordinates
    if (alerts.length > 0) {
        // Filter alerts with valid coordinates (not default Johannesburg)
        var validAlerts = alerts.filter(function(alert) {
            return alert.lat !== -26.2041 || alert.lng !== 28.0473;
        });
        
        if (validAlerts.length > 0) {
            // Calculate average coordinates from real alerts
            var sumLat = validAlerts.reduce(function(sum, alert) { return sum + alert.lat; }, 0);
            var sumLng = validAlerts.reduce(function(sum, alert) { return sum + alert.lng; }, 0);
            
            mapCenter = [sumLat / validAlerts.length, sumLng / validAlerts.length];
            mapZoom = validAlerts.length === 1 ? 15 : 13; // Zoom closer for single alert
            locationDetected = true;
        }
    }

    console.log('Map center:', mapCenter, 'zoom:', mapZoom, 'Location detected:', locationDetected);

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

    // Request user location if no meaningful location data exists
    if (!locationDetected) {
        requestUserLocation(map);
    }

    // Make map available globally for debugging
    window.dashboardMap = map;
    
    console.log('Map setup complete');
});

// Location request function with user-friendly prompts
function requestUserLocation(map) {
    // Check if geolocation is supported
    if (!navigator.geolocation) {
        showLocationMessage('Location services are not supported by your browser. The map will show the default area.', 'info');
        return;
    }

    // Show initial prompt asking for location permission
    showLocationPrompt(function(userAgreed) {
        if (!userAgreed) {
            showLocationMessage('Location access was declined. You can manually search for your area or view community alerts from the default location.', 'info');
            return;
        }

        // Show loading message
        showLocationMessage('Getting your location...', 'loading');

        // Request location with timeout
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Success - update map to user's location
                var userLat = position.coords.latitude;
                var userLng = position.coords.longitude;
                
                hideLocationMessage();
                map.setView([userLat, userLng], 15);
                
                // Add a marker for user's location
                var userIcon = L.divIcon({
                    className: 'user-location-marker',
                    html: '<div class="w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow-lg"></div>',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                });
                
                L.marker([userLat, userLng], {icon: userIcon})
                    .addTo(map)
                    .bindPopup('<div class="text-center p-2"><strong>Your Location</strong></div>');
                
                console.log('User location set:', userLat, userLng);
            },
            function(error) {
                // Error handling
                var message = '';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        message = 'Location access was denied. You can manually search for your area or browse alerts from the default view.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message = 'Your location could not be determined. Please check your device settings and try again.';
                        break;
                    case error.TIMEOUT:
                        message = 'Location request timed out. Please check your connection and try refreshing the page.';
                        break;
                    default:
                        message = 'An error occurred while getting your location. The map will show the default area.';
                        break;
                }
                showLocationMessage(message, 'warning');
                console.log('Geolocation error:', error);
            },
            {
                timeout: 10000, // 10 second timeout
                enableHighAccuracy: true,
                maximumAge: 300000 // 5 minutes cache
            }
        );
    });
}

// Show location permission prompt
function showLocationPrompt(callback) {
    var promptDiv = document.createElement('div');
    promptDiv.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    promptDiv.innerHTML = `
        <div class="bg-white rounded-lg p-6 m-4 max-w-md">
            <div class="flex items-center gap-3 mb-4">
                <span class="text-2xl">📍</span>
                <h3 class="text-lg font-semibold">Share Your Location</h3>
            </div>
            <p class="text-gray-600 mb-4">
                This app works best when we can show you alerts and information relevant to your area. 
                Would you like to share your location to see nearby community alerts?
            </p>
            <div class="flex gap-3 justify-end">
                <button onclick="closeLocationPrompt(false)" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">
                    No, thanks
                </button>
                <button onclick="closeLocationPrompt(true)" class="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded">
                    Share Location
                </button>
            </div>
        </div>
    `;
    
    // Store callback for access by button handlers
    window.locationPromptCallback = callback;
    document.body.appendChild(promptDiv);
    window.locationPromptElement = promptDiv;
}

// Close location prompt
function closeLocationPrompt(agreed) {
    if (window.locationPromptElement) {
        document.body.removeChild(window.locationPromptElement);
        window.locationPromptElement = null;
    }
    
    if (window.locationPromptCallback) {
        window.locationPromptCallback(agreed);
        window.locationPromptCallback = null;
    }
}

// Show location status messages
function showLocationMessage(message, type) {
    // Remove existing message if any
    hideLocationMessage();
    
    var messageDiv = document.createElement('div');
    var bgColor = type === 'loading' ? 'bg-blue-100 text-blue-800' : 
                  type === 'warning' ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-gray-100 text-gray-800';
    
    messageDiv.className = 'fixed top-4 right-4 p-3 rounded-lg shadow-lg z-40 max-w-sm ' + bgColor;
    messageDiv.innerHTML = `
        <div class="flex items-center gap-2">
            ${type === 'loading' ? '<div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>' : ''}
            <span>${message}</span>
            ${type !== 'loading' ? '<button onclick="hideLocationMessage()" class="ml-2 text-xl leading-none">&times;</button>' : ''}
        </div>
    `;
    
    document.body.appendChild(messageDiv);
    window.locationMessageElement = messageDiv;
    
    // Auto-hide after 8 seconds if not loading
    if (type !== 'loading') {
        setTimeout(hideLocationMessage, 8000);
    }
}

// Hide location message
function hideLocationMessage() {
    if (window.locationMessageElement) {
        document.body.removeChild(window.locationMessageElement);
        window.locationMessageElement = null;
    }
}

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