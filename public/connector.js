(function() {
    // Create the connector object
    var myConnector = tableau.makeConnector();
    
    // Log initialization for debugging
    console.log("Initializing Destiny 2 Data Connector...");
    console.log("Tableau version: " + tableau.versionNumber);
    console.log("Tableau phase: " + tableau.phase);
    
    // Define the schema
    myConnector.getSchema = function(schemaCallback) {
        console.log("Building Destiny 2 data schema...");
        
        var cols = [{
            id: "itemName",
            dataType: tableau.dataTypeEnum.string,
            alias: "Item Name",
            description: "Name of the Destiny 2 item or weapon"
        }, {
            id: "powerLevel",
            dataType: tableau.dataTypeEnum.float,
            alias: "Power Level",
            description: "Power/Light level of the item"
        }, {
            id: "startDate",
            dataType: tableau.dataTypeEnum.date,
            alias: "Start Date",
            description: "Start date of the data range (optional)"
        }, {
            id: "endDate",
            dataType: tableau.dataTypeEnum.date,
            alias: "End Date",
            description: "End date of the data range (optional)"
        }, {
            id: "popularity",
            dataType: tableau.dataTypeEnum.int,
            alias: "Usage Count",
            description: "Number of Guardians using this item"
        }];

        var tableSchema = {
            id: "destiny2Data",
            alias: "Destiny 2 Guardian Items",
            description: "Item data from the Destiny 2 API",
            columns: cols
        };

        console.log("Schema created successfully");
        schemaCallback([tableSchema]);
    };

    // Download the data
    myConnector.getData = function(table, doneCallback) {
        // Get the parameters from the connection data
        var connectionData = JSON.parse(tableau.connectionData || '{}');
        var apiKey = tableau.password || ""; // Use password for API key
        
        // Get date parameters if they exist
        var startDate = connectionData.startDate || "";
        var endDate = connectionData.endDate || "";
        
        console.log("Date parameters - startDate: " + (startDate || "not provided") + ", endDate: " + (endDate || "not provided"));
        
        // Ensure dates are in the correct format (YYYY-MM-DD) if provided
        try {
            // Validate date objects if they are provided
            if (startDate) {
                var startDateObj = new Date(startDate);
                if (isNaN(startDateObj.getTime())) {
                    throw new Error("Invalid start date format");
                }
                startDate = startDateObj.toISOString().split('T')[0];
            }
            
            if (endDate) {
                var endDateObj = new Date(endDate);
                if (isNaN(endDateObj.getTime())) {
                    throw new Error("Invalid end date format");
                }
                endDate = endDateObj.toISOString().split('T')[0];
            }
        } catch (e) {
            console.error("Error formatting dates:", e);
            tableau.abortWithError("Invalid Date Format: Dates must be in YYYY-MM-DD format");
            return;
        }
        
        console.log("Guardian, fetching Destiny 2 data" + (startDate ? " from " + startDate : "") + (endDate ? " to " + endDate : ""));
        console.log("Using Bungie API Key: " + (apiKey ? "******" : "None provided"));
        
        // Construct the API URL
        var apiUrl = "/api/data";
        
        // Make the AJAX request
        console.log("Sending request to: " + apiUrl);
        // Build request data with only provided parameters
        var requestData = {
            apiKey: apiKey
        };
        
        // Only add date parameters if they're provided
        if (startDate) {
            requestData.startDate = startDate;
        }
        if (endDate) {
            requestData.endDate = endDate;
        }
        
        $.ajax({
            url: apiUrl,
            data: requestData,
            dataType: 'json',
            success: function(resp) {
                console.log("Data received from server, processing...");
                var tableData = [];
                
                // Map the API response to our schema
                if (Array.isArray(resp)) {
                    console.log("Processing " + resp.length + " items from the Bungie API");
                    for (var i = 0; i < resp.length; i++) {
                        var row = {
                            "itemName": resp[i].symbol,
                            "powerLevel": resp[i].price,
                            "popularity": resp[i].volume
                        };
                        
                        // Add dates if provided
                        if (startDate) {
                            row.startDate = startDate;
                        }
                        if (endDate) {
                            row.endDate = endDate;
                        }
                        
                        tableData.push(row);
                    }
                } else {
                    console.warn("Unexpected data format received, using fallback data");
                    // Fallback Destiny-themed data
                    tableData = [
                        { 
                            "itemName": "Gjallarhorn", 
                            "powerLevel": 1350, 
                            "popularity": 1000000,
                            ...(startDate ? { "startDate": startDate } : {}),
                            ...(endDate ? { "endDate": endDate } : {})
                        },
                        { 
                            "itemName": "Thorn", 
                            "powerLevel": 1345, 
                            "popularity": 750000,
                            ...(startDate ? { "startDate": startDate } : {}),
                            ...(endDate ? { "endDate": endDate } : {})
                        },
                        { 
                            "itemName": "Ace of Spades", 
                            "powerLevel": 1340, 
                            "popularity": 500000,
                            ...(startDate ? { "startDate": startDate } : {}),
                            ...(endDate ? { "endDate": endDate } : {})
                        }
                    ];
                }
                
                console.log("Adding " + tableData.length + " rows to Tableau table");
                table.appendRows(tableData);
                console.log("Data load complete, calling doneCallback()");
                doneCallback();
            },
            error: function(xhr, status, error) {
                console.error("Guardian down! Error fetching Destiny 2 data: " + error);
                
                // Check for Bungie-specific error responses
                var errorMessage = "Error fetching data: " + error;
                
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
                
                console.error(errorMessage);
                tableau.abortWithError(errorMessage);
            }
        });
    };

    // Init function for when the page loads
    myConnector.init = function(initCallback) {
        tableau.authType = tableau.authTypeEnum.basic;
        
        console.log("Initializing connector in phase: " + tableau.phase);
        
        // Handle initialization based on the phase
        if (tableau.phase == tableau.phaseEnum.interactivePhase || tableau.phase == tableau.phaseEnum.authPhase) {
            console.log("In interactive/auth phase, setting up UI handlers");
            
            // Add event listeners for the submit button
            $(document).ready(function() {
                $("#submitButton").click(function() {
                    console.log("Connect button clicked");
                    
                    // Get the input values
                    var apiKey = $("#apiKey").val().trim();
                    var startDate = $("#startDate").val().trim();
                    var endDate = $("#endDate").val().trim();
                    
                    // Validate inputs - only API key is required
                    if (!apiKey) {
                        console.warn("Missing required API key");
                        alert("Guardian, please enter Bungie API Key");
                        return;
                    }
                    
                    // Dates are optional now
                    
                    // Enhanced date validation - only if dates are provided
                    try {
                        // Validate start date if provided
                        if (startDate) {
                            var start = new Date(startDate);
                            if (isNaN(start.getTime())) {
                                throw new Error("Invalid start date format");
                            }
                            startDate = start.toISOString().split('T')[0];
                        }
                        
                        // Validate end date if provided
                        if (endDate) {
                            var end = new Date(endDate);
                            if (isNaN(end.getTime())) {
                                throw new Error("Invalid end date format");
                            }
                            endDate = end.toISOString().split('T')[0];
                        }
                        
                        // Validate date range if both dates are provided
                        if (startDate && endDate) {
                            if (new Date(endDate) < new Date(startDate)) {
                                console.warn("Invalid date range");
                                alert("End date must be after start date");
                                return;
                            }
                        }
                    } catch (e) {
                        console.error("Date validation error:", e);
                        alert("Please enter valid dates in YYYY-MM-DD format");
                        return;
                    }
                    
                    console.log("Storing connection information");
                    
                    // Store the API key as the password for security
                    tableau.username = "destiny_guardian";
                    tableau.password = apiKey;
                    
                    // Store the dates in connectionData (if provided)
                    var connectionData = {};
                    if (startDate) {
                        connectionData.startDate = startDate;
                    }
                    if (endDate) {
                        connectionData.endDate = endDate;
                    }
                    tableau.connectionData = JSON.stringify(connectionData);
                    
                    console.log("Connection data set:", connectionData);
                    
                    // Show loading indicator
                    $("#loadingIndicator").show();
                    console.log("Submitting connection to Tableau");
                    
                    // Submit the connector
                    tableau.connectionName = "Destiny 2 Guardian Data";
                    tableau.submit();
                });
                
                console.log("UI handlers initialized");
            });
        } else {
            console.log("In data gathering phase or other non-interactive phase");
        }
        
        console.log("Calling initCallback()");
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
    console.log("Destiny 2 connector registered with Tableau");
})();

