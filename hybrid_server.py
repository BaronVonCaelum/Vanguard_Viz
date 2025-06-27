#!/usr/bin/env python3
"""
Hybrid Vanguard Viz Server
Provides both Tableau Web Data Connector and desktop API functionality
"""

import os
import json
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

from desktop_manifest_helper import (
    test_api_connection, get_user_profile, get_weapon_usage_stats,
    get_manifest_component, search_items_by_name, get_helper
)

app = Flask(__name__)
CORS(app)

# HTML template for the Tableau WDC
WDC_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vanguard Viz - Tableau Web Data Connector</title>
    <meta charset="utf-8">
    <meta http-equiv="Cache-Control" content="no-store" />
    
    <!-- Latest version of jQuery -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    
    <!-- Tableau WDC SDK -->
    <script src="https://connectors.tableau.com/libs/tableauwdc-2.3.latest.js"></script>
    
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
        }
        input[type="text"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        #submitButton {
            display: block;
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
        }
        #submitButton:hover {
            background-color: #45a049;
        }
        .info-text {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>Vanguard Viz - Destiny 2 Data Connector</h1>
        
        <div class="form-group">
            <label for="apiKey">Bungie API Key:</label>
            <input type="text" id="apiKey" placeholder="Enter your Bungie API key">
            <div class="info-text">Get your API key from the <a href="https://www.bungie.net/en/Application" target="_blank">Bungie Developer Portal</a></div>
        </div>

        <div class="form-group">
            <label for="dataDate">Date (Optional):</label>
            <input type="date" id="dataDate">
            <div class="info-text">Optional: Select a specific date for the data</div>
        </div>

        <button type="button" id="submitButton">Connect to Destiny 2 Data</button>
        
        <div id="status" class="status"></div>
    </div>

    <script>
        (function() {
            var myConnector = tableau.makeConnector();
            
            myConnector.getSchema = function(schemaCallback) {
                var weaponSchema = {
                    id: "destiny_weapons",
                    alias: "Destiny 2 Weapons",
                    columns: [
                        { id: "hash", dataType: tableau.dataTypeEnum.string },
                        { id: "name", dataType: tableau.dataTypeEnum.string },
                        { id: "type", dataType: tableau.dataTypeEnum.string },
                        { id: "tier_type", dataType: tableau.dataTypeEnum.string },
                        { id: "damage_type", dataType: tableau.dataTypeEnum.int },
                        { id: "class_type", dataType: tableau.dataTypeEnum.int },
                        { id: "date", dataType: tableau.dataTypeEnum.string }
                    ]
                };
                
                schemaCallback([weaponSchema]);
            };
            
            myConnector.getData = function(table, doneCallback) {
                var connectionData = JSON.parse(tableau.connectionData || '{}');
                var apiKey = tableau.password;
                var dataDate = connectionData.dataDate || '';
                
                if (!apiKey) {
                    tableau.abortWithError("API Key is required");
                    return;
                }
                
                $.ajax({
                    url: '/api/weapons',
                    data: {
                        apiKey: apiKey,
                        date: dataDate
                    },
                    success: function(resp) {
                        table.appendRows(resp);
                        doneCallback();
                    },
                    error: function(xhr, status, error) {
                        tableau.abortWithError("Error fetching data: " + error);
                    }
                });
            };
            
            myConnector.init = function(initCallback) {
                tableau.authType = tableau.authTypeEnum.custom;
                
                if (tableau.phase === tableau.phaseEnum.interactivePhase || 
                    tableau.phase === tableau.phaseEnum.authPhase) {
                    
                    document.getElementById('submitButton').onclick = function() {
                        var apiKey = document.getElementById('apiKey').value.trim();
                        var dataDate = document.getElementById('dataDate').value.trim();
                        
                        if (!apiKey) {
                            showStatus('Please enter your API Key', 'error');
                            return;
                        }
                        
                        // Test connection first
                        showStatus('Testing connection...', 'success');
                        
                        $.ajax({
                            url: '/api/test-connection',
                            data: { apiKey: apiKey },
                            success: function(result) {
                                if (result.status === 'connected') {
                                    showStatus('Connected successfully!', 'success');
                                    
                                    tableau.connectionData = JSON.stringify({
                                        dataDate: dataDate
                                    });
                                    tableau.password = apiKey;
                                    tableau.connectionName = "Destiny 2 Data";
                                    tableau.submit();
                                } else {
                                    showStatus('Connection failed: ' + result.message, 'error');
                                }
                            },
                            error: function() {
                                showStatus('Connection test failed', 'error');
                            }
                        });
                    };
                }
                
                initCallback();
            };
            
            function showStatus(message, type) {
                var statusDiv = document.getElementById('status');
                statusDiv.textContent = message;
                statusDiv.className = 'status ' + type;
                statusDiv.style.display = 'block';
            }
            
            tableau.registerConnector(myConnector);
        })();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the Tableau WDC interface"""
    return render_template_string(WDC_HTML_TEMPLATE)

@app.route('/api/test-connection')
def api_test_connection():
    """Test API connection endpoint"""
    api_key = request.args.get('apiKey')
    
    if not api_key:
        return jsonify({"status": "error", "message": "API key is required"}), 400
    
    try:
        result = test_api_connection(api_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/weapons')
def api_weapons():
    """Get weapons data for Tableau"""
    api_key = request.args.get('apiKey')
    date = request.args.get('date', '')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    try:
        # Get weapon data from manifest
        helper = get_helper(api_key)
        weapons_filter = {"damage_type": [1, 2, 3, 4, 6, 7]}  # Valid weapon damage types
        weapons = helper.get_inventory_items(filters=weapons_filter, limit=1000)
        
        # Transform for Tableau
        tableau_data = []
        for weapon in weapons:
            tableau_data.append({
                "hash": weapon["hash"],
                "name": weapon["name"],
                "type": weapon["type"],
                "tier_type": weapon["tier_type"],
                "damage_type": weapon["damage_type"],
                "class_type": weapon["class_type"],
                "date": date
            })
        
        return jsonify(tableau_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
def api_search():
    """Search weapons endpoint"""
    api_key = request.args.get('apiKey')
    search_term = request.args.get('q', '')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    if not search_term:
        return jsonify({"error": "Search term is required"}), 400
    
    try:
        results = search_items_by_name(search_term, api_key)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def api_status():
    """Server status endpoint"""
    return jsonify({
        "server": "Vanguard Viz Hybrid Server",
        "version": "1.0",
        "status": "running",
        "features": ["tableau_wdc", "desktop_api"]
    })

def start_server(port=3000, open_browser=True):
    """Start the hybrid server"""
    print(f"🚀 Starting Vanguard Viz Hybrid Server on port {port}")
    print(f"📊 Tableau WDC available at: http://localhost:{port}")
    print(f"🔧 Desktop API available at: http://localhost:{port}/api/*")
    
    if open_browser:
        # Open browser after a short delay
        def open_browser_delayed():
            import time
            time.sleep(1)
            webbrowser.open(f"http://localhost:{port}")
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Vanguard Viz Hybrid Server')
    parser.add_argument('--port', type=int, default=3000, help='Port to run server on')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t open browser automatically')
    
    args = parser.parse_args()
    
    start_server(port=args.port, open_browser=not args.no_browser)
