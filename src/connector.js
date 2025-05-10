(function () {
    // Create the connector object
    var myConnector = tableau.makeConnector();

    // Define the schema
    myConnector.getSchema = function (schemaCallback) {
        var cols = [{
            id: "symbol",
            dataType: tableau.dataTypeEnum.string,
            alias: "Symbol"
        }, {
            id: "price",
            dataType: tableau.dataTypeEnum.float,
            alias: "Price"
        }, {
            id: "date",
            dataType: tableau.dataTypeEnum.date,
            alias: "Date"
        }, {
            id: "volume",
            dataType: tableau.dataTypeEnum.int,
            alias: "Volume"
        }];

        var tableSchema = {
            id: "vanguardData",
            alias: "Vanguard Financial Data",
            columns: cols
        };

        schemaCallback([tableSchema]);
    };

    // Download the data
    myConnector.getData = function(table, doneCallback) {
        // Get the parameters from the UI
        let apiKey = tableau.connectionData ? JSON.parse(tableau.connectionData).apiKey : "";
        let dataDate = tableau.connectionData ? JSON.parse(tableau.connectionData).dataDate : "";

        // You will need to replace this URL with your actual API endpoint
        $.ajax({
            url: "/api/data",
            data: {
                apiKey: apiKey,
                date: dataDate
            },
            success: function(resp) {
                var tableData = [];
                
                // Assuming resp is an array of data objects
                for (var i = 0; i < resp.length; i++) {
                    tableData.push({
                        "symbol": resp[i].symbol,
                        "price": resp[i].price,
                        "date": resp[i].date,
                        "volume": resp[i].volume
                    });
                }

                table.appendRows(tableData);
                doneCallback();
            },
            error: function(xhr, status, error) {
                tableau.abortWithError("Error fetching data: " + error);
            }
        });
    };

    // Init function for when the page loads
    myConnector.init = function(initCallback) {
        tableau.authType = tableau.authTypeEnum.custom;
        
        // If we are in the auth phase, we only want to show the UI needed for auth
        if (tableau.phase == tableau.phaseEnum.authPhase) {
            $("#submitButton").click(function() {
                var apiKey = $("#apiKey").val().trim();
                var dataDate = $("#dataDate").val().trim();
                
                if (apiKey && dataDate) {
                    tableau.connectionData = JSON.stringify({
                        apiKey: apiKey,
                        dataDate: dataDate
                    });
                    tableau.submit();
                } else {
                    alert("Please enter both API Key and Date");
                }
            });
        }

        initCallback();
    };

    tableau.registerConnector(myConnector);
})();
