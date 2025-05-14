(function() {
    // Create the connector object
    var myConnector = tableau.makeConnector();
    
    // Add debug helper
    function logTableauState() {
        console.log("=== Tableau State ===");
        console.log("Phase:", tableau.phase);
        console.log("Auth Type:", tableau.authType);
        console.log("Connection Name:", tableau.connectionName);
        console.log("Connection Data:", tableau.connectionData);
        console.log("==================");
    }
    
    // Log initialization for debugging
    console.log("Initializing Destiny 2 Data Connector...");
    console.log("Tableau version: " + tableau.versionNumber);
    console.log("Tableau phase: " + tableau.phase);
    
    // Define the schema
    myConnector.getSchema = function(schemaCallback) {
        console.log("Building Destiny 2 manifest schema...");
        
        var tableSchemas = [
            {
                id: "activities",
                alias: "Destiny 2 Activities",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "type", dataType: tableau.dataTypeEnum.string },
                    { id: "activityTypeHash", dataType: tableau.dataTypeEnum.string },
                    { id: "destinationHash", dataType: tableau.dataTypeEnum.string },
                    { id: "placeHash", dataType: tableau.dataTypeEnum.string },
                    { id: "activityModeHash", dataType: tableau.dataTypeEnum.string },
                    { id: "isPlaylist", dataType: tableau.dataTypeEnum.bool },
                    { id: "recommended_light", dataType: tableau.dataTypeEnum.int },
                    { id: "matchmaking", dataType: tableau.dataTypeEnum.bool },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            },
            {
                id: "classes",
                alias: "Destiny 2 Classes",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "classType", dataType: tableau.dataTypeEnum.string },
                    { id: "classTypeValue", dataType: tableau.dataTypeEnum.int },
                    { id: "mentorVendorHash", dataType: tableau.dataTypeEnum.string },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            },
            {
                id: "inventory_items",
                alias: "Destiny 2 Inventory Items",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "type", dataType: tableau.dataTypeEnum.string },
                    { id: "tierType", dataType: tableau.dataTypeEnum.string },
                    { id: "rarity", dataType: tableau.dataTypeEnum.int },
                    { id: "classType", dataType: tableau.dataTypeEnum.string },
                    { id: "damageType", dataType: tableau.dataTypeEnum.int },
                    { id: "damageTypeHash", dataType: tableau.dataTypeEnum.string },
                    { id: "equippable", dataType: tableau.dataTypeEnum.bool },
                    { id: "isExotic", dataType: tableau.dataTypeEnum.bool },
                    { id: "isLegendary", dataType: tableau.dataTypeEnum.bool },
                    { id: "bucketHash", dataType: tableau.dataTypeEnum.string },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            },
            {
                id: "damage_types",
                alias: "Destiny 2 Damage Types",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "enumValue", dataType: tableau.dataTypeEnum.int },
                    { id: "color", dataType: tableau.dataTypeEnum.string },
                    { id: "showIcon", dataType: tableau.dataTypeEnum.bool },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            }
        ];

        // Also add the remaining tables (stats, vendors, equipment_slots)
        var additionalTables = [
            {
                id: "stats",
                alias: "Destiny 2 Stats",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "aggregationType", dataType: tableau.dataTypeEnum.int },
                    { id: "hasComputedBlock", dataType: tableau.dataTypeEnum.bool },
                    { id: "statCategory", dataType: tableau.dataTypeEnum.int },
                    { id: "interpolate", dataType: tableau.dataTypeEnum.bool },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            },
            {
                id: "vendors",
                alias: "Destiny 2 Vendors",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "vendorProgressionType", dataType: tableau.dataTypeEnum.int },
                    { id: "buyString", dataType: tableau.dataTypeEnum.string },
                    { id: "sellString", dataType: tableau.dataTypeEnum.string },
                    { id: "displayItemHash", dataType: tableau.dataTypeEnum.string },
                    { id: "inhibitBuying", dataType: tableau.dataTypeEnum.bool },
                    { id: "inhibitSelling", dataType: tableau.dataTypeEnum.bool },
                    { id: "factionHash", dataType: tableau.dataTypeEnum.string },
                    { id: "resetIntervalMinutes", dataType: tableau.dataTypeEnum.int },
                    { id: "resetOffsetMinutes", dataType: tableau.dataTypeEnum.int },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            },
            {
                id: "equipment_slots",
                alias: "Destiny 2 Equipment Slots",
                columns: [
                    { id: "hash", dataType: tableau.dataTypeEnum.string },
                    { id: "name", dataType: tableau.dataTypeEnum.string },
                    { id: "description", dataType: tableau.dataTypeEnum.string },
                    { id: "icon", dataType: tableau.dataTypeEnum.string },
                    { id: "equipmentCategoryHash", dataType: tableau.dataTypeEnum.string },
                    { id: "bucketTypeHash", dataType: tableau.dataTypeEnum.string },
                    { id: "applyCustomArtDyes", dataType: tableau.dataTypeEnum.bool },
                    { id: "artDyeChannels", dataType: tableau.dataTypeEnum.string },
                    { id: "referenceId", dataType: tableau.dataTypeEnum.string }
                ]
            }
        ];

        // Combine all tables
        tableSchemas = tableSchemas.concat(additionalTables);

        console.log("Schema created successfully with " + tableSchemas.length + " tables");
        schemaCallback(tableSchemas);
    };

    // Download the data
    myConnector.getData = function(table, doneCallback) {
        console.log("getData called for table:", table.tableInfo.id);
        
        // Get connection data including selected tables
        var connectionData = JSON.parse(tableau.connectionData || '{}');
        var apiKey = tableau.password || connectionData.apiKey;  // Use password if available
        var dataDate = connectionData.dataDate;
        
        // Debug logging for API key
        console.log("API Key source:", {
            fromPassword: !!tableau.password,
            fromConnectionData: !!connectionData.apiKey,
            finalKeyExists: !!apiKey
        });
        
        // Validate API key exists
        if (!apiKey) {
            console.error("No API key found in either password or connectionData");
            tableau.abortWithError("API Key is required. Please enter your Bungie API key.");
            return;
        }
        
        // Map table IDs to API endpoints
        var endpointMap = {
            'inventory_items': '/api/manifest/inventory-items',
            'activities': '/api/manifest/activities',
            'classes': '/api/manifest/classes',
            'damage_types': '/api/manifest/damage-types',
            'stats': '/api/manifest/stats',
            'vendors': '/api/manifest/vendors',
            'equipment_slots': '/api/manifest/equipment-slots'
        };

        // Build the full URL using our local server
        var endpoint = 'http://localhost:3000' + endpointMap[table.tableInfo.id];
        
        if (!endpoint) {
            console.error("Unknown table:", table.tableInfo.id);
            tableau.abortWithError("Unknown table: " + table.tableInfo.id);
            return;
        }

        console.log("Fetching data from endpoint:", endpoint);
        // Build filter parameters based on table type
        // Build filter parameters based on table type
        var requestData = {
            apiKey: apiKey,  // Required by our local server
            date: dataDate,
            destiny2Only: true,  // Filter for Destiny 2 content only
            gameVersion: 2,      // Specifically Destiny 2 (not Destiny 1)
            locale: 'en'         // English language content only
        };
        
        // Add table-specific filters
        switch(table.tableInfo.id) {
            case 'inventory_items':
                requestData.itemCategoryType = 1;       // Primary/Special/Heavy weapons
                requestData.itemSubType = {
                    in: [
                        6,  // Auto Rifle
                        7,  // Hand Cannon
                        8,  // Pulse Rifle
                        9,  // Scout Rifle
                        10, // Fusion Rifle
                        11, // Sniper Rifle
                        12, // Shotgun
                        13, // Machine Gun
                        14, // Rocket Launcher
                        17, // Submachine Gun
                        18, // Trace Rifle
                        19, // Linear Fusion Rifle
                        20, // Grenade Launcher
                        21, // Sword
                        22, // Glaive
                        23, // Bow
                    ]
                };
                requestData.tierType = ['Legendary', 'Exotic'];  // Only legendary and exotic items
                requestData.hasDamageType = true;               // Must have a damage type
                requestData.damageType = {                      // Must have a valid damage type value
                    exists: true,
                    notEqual: 0                                 // 0 typically means no damage type
                };
                requestData.hasStats = true;                    // Must have stats (like RPM)
                break;
                
            case 'activities':
                requestData.isAvailable = true;    // Only currently available activities
                requestData.isVisible = true;      // Only visible activities
                break;
                
            case 'vendors':
                requestData.hasInventory = true;   // Only vendors with inventory
                requestData.isActive = true;       // Only active vendors
                break;
                
            case 'stats':
                requestData.statCategory = 1;        // Weapon stats only
                requestData.isDisplayable = true;    // Only stats that are meant to be displayed
                requestData.hasComputedBlock = false; // Only base stats
                requestData.isWeaponStat = true;     // Only weapon-related stats
                requestData.statHash = {             // Only specific weapon stats
                    in: [
                        4284893193,   // Rounds Per Minute
                        3614673599,   // Blast Radius
                        2523465841,   // Velocity
                        1240592695,   // Range
                        155624089,    // Stability
                        943549884,    // Handling
                        4188031367,   // Reload Speed
                        1345609583,   // Aim Assistance
                        2714457168,   // Airborne Effectiveness
                        3555269338,   // Zoom
                        2961396640    // Charge Time
                    ]
                };
                break;
                
            case 'damage_types':
                requestData.showIcon = true;         // Only damage types with icons
                requestData.exists = true;           // Must exist in current game
                requestData.enumValue = {            // Valid damage types only
                    notEqual: 0,                     // Not "None"
                    in: [1, 2, 3, 4, 6, 7]          // Kinetic, Arc, Solar, Void, Stasis, Strand
                };
                break;
        }

        $.ajax({
            url: endpoint,
            headers: {
                'X-API-Key': apiKey,  // Required by Bungie API
                'Accept': 'application/json',
                'User-Agent': 'Vanguard_Viz/1.0 AppId/54134 (https://public.tableau.com/app/profile/josh.caelum/vizzes;josh@housecaelum.com)'
            },
            data: requestData,
            success: function(resp) {
                console.log("Received data for table:", table.tableInfo.id);
                console.log("Number of records:", resp.length);
                
                var tableData = [];
                
                // Process the response data according to the table schema
                for (var i = 0; i < resp.length; i++) {
                    var row = {};
                    // Map each column from the schema to the response data
                    table.tableInfo.columns.forEach(function(column) {
                        var value;
                        
                        // Handle special fields
                        if (column.id === "name" || column.id === "description" || column.id === "icon") {
                            // Handle displayProperties fields
                            if (column.id === "icon" && resp[i].displayProperties?.hasIcon) {
                                value = `https://www.bungie.net${resp[i].displayProperties.icon}`;
                            } else {
                                value = resp[i].displayProperties?.[column.id] || "";
                            }
                        } else if (column.id === "type" && table.tableInfo.id === "inventory_items") {
                            // For inventory items, get the itemType
                            value = resp[i].itemTypeAndTierDisplayName || resp[i].itemTypeDisplayName || "";
                        } else if (column.id === "damageType") {
                            // Get actual damage type value
                            value = resp[i].defaultDamageType || 0;
                        } else if (column.id === "tierType") {
                            // Get tier type (Exotic, Legendary, etc.)
                            value = resp[i].inventory?.tierTypeName || "";
                        } else {
                            // Handle other fields normally
                            value = resp[i][column.id];
                        }
                        
                        // Handle data type conversions
                        switch(column.dataType) {
                            case tableau.dataTypeEnum.bool:
                                row[column.id] = Boolean(value);
                                break;
                            case tableau.dataTypeEnum.int:
                                row[column.id] = value === null || value === undefined ? 0 : parseInt(value);
                                break;
                            case tableau.dataTypeEnum.string:
                                row[column.id] = value === null || value === undefined ? "" : String(value);
                                break;
                            default:
                                row[column.id] = value;
                        }
                    });
                    tableData.push(row);
                }

                console.log("Processed records:", tableData.length);
                table.appendRows(tableData);
                doneCallback();
            },
            error: function(xhr, status, error) {
                console.error("Error fetching data:", error);
                var errorMessage = "Error fetching data from " + endpoint + ": " + error;
                
                try {
                    if (xhr.responseJSON) {
                        if (xhr.responseJSON.ErrorCode) {
                            errorMessage = "Bungie API Error " + xhr.responseJSON.ErrorCode + ": " + xhr.responseJSON.Message;
                        } else if (xhr.responseJSON.error) {
                            errorMessage = xhr.responseJSON.error + ": " + xhr.responseJSON.message;
                        }
                    }
                } catch (e) {
                    console.error("Error parsing error response:", e);
                }
                
                tableau.abortWithError(errorMessage);
            }
        });
    };

    // Init function for when the page loads
    myConnector.init = function(initCallback) {
        console.log("Initializing connector...");
        tableau.authType = tableau.authTypeEnum.custom;
        
        // If we have a stored API key, save it in the password field
        if (tableau.phase === tableau.phaseEnum.authPhase) {
            console.log("Auth phase - checking for API key");
            var connectionData = JSON.parse(tableau.connectionData || '{}');
            if (connectionData.apiKey) {
                tableau.password = connectionData.apiKey;
                console.log("Stored API key in tableau.password");
            }
        }
        
        // Set up basic button handlers
        if (tableau.phase === tableau.phaseEnum.interactivePhase || 
            tableau.phase === tableau.phaseEnum.authPhase) {
            
            // Select All
            document.getElementById('selectAllBtn').onclick = function() {
                document.querySelectorAll('input[name="tables"]')
                    .forEach(function(checkbox) { checkbox.checked = true; });
            };
            
            // Deselect All
            document.getElementById('deselectAllBtn').onclick = function() {
                document.querySelectorAll('input[name="tables"]')
                    .forEach(function(checkbox) { checkbox.checked = false; });
            };
            
            // Submit
            document.getElementById('submitButton').onclick = function() {
                var apiKey = document.getElementById('apiKey').value.trim();
                var dataDate = document.getElementById('dataDate').value.trim();
                var selectedTables = [];
                
                document.querySelectorAll('input[name="tables"]:checked')
                    .forEach(function(checkbox) {
                        selectedTables.push(checkbox.value);
                    });
                
                if (!apiKey) {
                    alert("Please enter your API Key");
                    return;
                }
                
                if (selectedTables.length === 0) {
                    alert("Please select at least one table");
                    return;
                }
                
                // Store API key in both connectionData and password
                tableau.connectionData = JSON.stringify({
                    apiKey: apiKey,
                    dataDate: dataDate,
                    tables: selectedTables
                });
                tableau.password = apiKey;
                
                tableau.connectionName = "Destiny 2 Manifest Data";
                tableau.submit();
            };
        }
        
        initCallback();
    };

    // Define the shutdown hook for the connector
    myConnector.shutdown = function(shutdownCallback) {
        console.log("Shutting down Destiny 2 connector...");
        // Clean up any resources
        shutdownCallback();
    };

    // Register the connector with Tableau
    tableau.registerConnector(myConnector);
    
    // Log connector registration
    console.log("Connector registered");
    
})();
