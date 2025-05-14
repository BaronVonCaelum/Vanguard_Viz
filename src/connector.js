(function () {
    // Create the connector object
    var myConnector = tableau.makeConnector();

    // Define the schema for all manifest tables
    myConnector.getSchema = function (schemaCallback) {
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
            },
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

        schemaCallback(tableSchemas);
    };

    // Download the data
    myConnector.getData = function(table, doneCallback) {
        console.log("getData called for table:", table.tableInfo.id);
        
        // Get connection data including selected tables
        var connectionData = JSON.parse(tableau.connectionData);
        var apiKey = connectionData.apiKey;
        var dataDate = connectionData.dataDate;
        var selectedTables = connectionData.tables || [];

        console.log("Selected tables:", selectedTables);
        console.log("Processing table:", table.tableInfo.id);

        // Verify this table was selected
        if (selectedTables.length > 0 && !selectedTables.includes(table.tableInfo.id)) {
            console.log("Table was not selected:", table.tableInfo.id);
            doneCallback();
            return;
        }

        // Map table IDs to API endpoints
        var endpointMap = {
            'activities': '/api/manifest/activities',
            'classes': '/api/manifest/classes',
            'inventory_items': '/api/manifest/inventory-items',
            'damage_types': '/api/manifest/damage-types',
            'stats': '/api/manifest/stats',
            'vendors': '/api/manifest/vendors',
            'equipment_slots': '/api/manifest/equipment-slots'
        };

        var endpoint = endpointMap[table.tableInfo.id];
        
        if (!endpoint) {
            console.error("Unknown table:", table.tableInfo.id);
            tableau.abortWithError("Unknown table: " + table.tableInfo.id);
            return;
        }

        console.log("Fetching data from endpoint:", endpoint);

        $.ajax({
            url: endpoint,
            data: {
                apiKey: apiKey,
                date: dataDate
            },
            success: function(resp) {
                console.log("Received data for table:", table.tableInfo.id);
                console.log("Number of records:", resp.length);
                
                var tableData = [];
                
                // Process the response data according to the table schema
                for (var i = 0; i < resp.length; i++) {
                    var row = {};
                    // Map each column from the schema to the response data
                    table.tableInfo.columns.forEach(function(column) {
                        row[column.id] = resp[i][column.id];
                    });
                    tableData.push(row);
                }

                console.log("Processed records:", tableData.length);
                table.appendRows(tableData);
                doneCallback();
            },
            error: function(xhr, status, error) {
                console.error("Error fetching data:", error);
                tableau.abortWithError("Error fetching data from " + endpoint + ": " + error);
            }
        });
    };

    // Init function for when the page loads
    // Init function 
    myConnector.init = function(initCallback) {
        tableau.authType = tableau.authTypeEnum.custom;
        
        if (tableau.phase == tableau.phaseEnum.authPhase) {
            // Add checkboxes for each available table
            const tableContainer = document.createElement('div');
            tableContainer.id = 'tableSelection';
            tableContainer.innerHTML = `
                <h3>Select tables to import:</h3>
                <div class="checkbox-list">
                    <label><input type="checkbox" name="tables" value="activities" checked> Activities</label>
                    <label><input type="checkbox" name="tables" value="classes" checked> Classes</label>
                    <label><input type="checkbox" name="tables" value="inventory_items" checked> Inventory Items</label>
                    <label><input type="checkbox" name="tables" value="damage_types" checked> Damage Types</label>
                    <label><input type="checkbox" name="tables" value="stats" checked> Stats</label>
                    <label><input type="checkbox" name="tables" value="vendors" checked> Vendors</label>
                    <label><input type="checkbox" name="tables" value="equipment_slots" checked> Equipment Slots</label>
                </div>
            `;
            
            // Insert the table selection before the submit button
            const submitButton = document.getElementById('submitButton');
            submitButton.parentNode.insertBefore(tableContainer, submitButton);
        }
        
        // Initialize the click event handler for the submit button
        $(document).ready(function() {
            $("#submitButton").click(function() {
                console.log("Submit button clicked");
                var apiKey = $("#apiKey").val().trim();
                var dataDate = $("#dataDate").val().trim();
                
                // Get selected tables
                var selectedTables = [];
                $('input[name="tables"]:checked').each(function() {
                    selectedTables.push($(this).val());
                });
                
                console.log("Selected tables:", selectedTables);
                
                if (apiKey) {
                    if (selectedTables.length === 0) {
                        alert("Please select at least one table");
                        return;
                    }
                    
                    tableau.connectionData = JSON.stringify({
                        apiKey: apiKey,
                        dataDate: dataDate,
                        tables: selectedTables
                    });
                    
                    console.log("Submitting connection data");
                    tableau.connectionName = "Destiny 2 Manifest Data";
                    tableau.submit();
                } else {
                    alert("Please enter your API Key");
                }
            });
        });
        

        initCallback();
    };

    tableau.registerConnector(myConnector);
})();
