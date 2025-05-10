require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");
const axios = require("axios");
const NodeCache = require("node-cache");

const app = express();
const port = process.env.PORT || 3000;

// Create a cache with TTL (time to live)
const apiCache = new NodeCache({ stdTTL: parseInt(process.env.CACHE_DURATION) || 3600 });

// Bungie API configuration
const BUNGIE_API_ROOT = process.env.BUNGIE_API_ROOT || "https://www.bungie.net/Platform";
const BUNGIE_API_KEY = process.env.BUNGIE_API_KEY;
const USE_SAMPLE_DATA = process.env.USE_SAMPLE_DATA === "true";
const REQUEST_TIMEOUT = parseInt(process.env.REQUEST_TIMEOUT) || 10000;

// Enable CORS for Tableau Desktop
app.use(cors());

// Request logging middleware
app.use((req, res, next) => {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    next();
});

// Serve static files from the public directory
app.use(express.static("public"));
app.use("/src", express.static("src"));

// Rate limiting configuration
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = 100; // Milliseconds between API requests

// Helper function to make Bungie API calls with rate limiting
async function callBungieAPI(endpoint, params = {}) {
    // Check if result is in cache
    const cacheKey = `${endpoint}:${JSON.stringify(params)}`;
    const cachedResult = apiCache.get(cacheKey);
    
    if (cachedResult) {
        console.log(`Cache hit for ${endpoint}`);
        return cachedResult;
    }

    // Apply rate limiting
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    
    if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
        const waitTime = MIN_REQUEST_INTERVAL - timeSinceLastRequest;
        console.log(`Rate limiting: waiting ${waitTime}ms before making API request`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    lastRequestTime = Date.now();
    
    // Make the API request
    try {
        const url = `${BUNGIE_API_ROOT}${endpoint}`;
        console.log(`Making Bungie API request to: ${url}`);
        
        const response = await axios.get(url, {
            headers: {
                'X-API-Key': BUNGIE_API_KEY
            },
            params: params,
            timeout: REQUEST_TIMEOUT
        });
        
        // Check for Bungie API error responses
        if (response.data.ErrorCode && response.data.ErrorCode !== 1) {
            throw new Error(`Bungie API Error: ${response.data.ErrorStatus} - ${response.data.Message}`);
        }
        
        // Cache successful response
        apiCache.set(cacheKey, response.data);
        
        console.log(`API request successful, response status: ${response.status}`);
        return response.data;
    } catch (error) {
        console.error("Bungie API Error:", error.message);
        if (error.response) {
            console.error("Response status:", error.response.status);
            console.error("Response data:", JSON.stringify(error.response.data).substring(0, 500) + "...");
        }
        throw error;
    }
}

// Transform Bungie API response to Tableau-friendly format
function transformBungieDataForTableau(bungieData, date) {
    // Use empty string for date if not provided
    const formattedDate = date || "";
    // Transformation for Destiny 2 weapon usage data
    try {
        // Handle weapon usage stats data
        if (bungieData.status === "success" && Array.isArray(bungieData.weaponStats)) {
            console.log(`Processing ${bungieData.weaponStats.length} weapon stats entries`);
            return bungieData.weaponStats.map(weapon => ({
                // Map the weapon fields to Tableau-friendly format
                symbol: weapon.weaponName || "Unknown Weapon",
                weaponType: weapon.weaponType || "Unknown",
                date: formattedDate,
                kills: weapon.killCount || 0,
                precision: weapon.precisionKillCount || 0,
                usage: weapon.usageTime || 0,
                activityType: weapon.activityType || "All",
                referenceId: weapon.referenceId || "0",
                // Add price and volume fields for backward compatibility
                price: weapon.killCount || 0,
                volume: weapon.usageTime || 0
            }));
        }
        
        // If we're using the manifest endpoint (legacy support)
        if (bungieData.Response && bungieData.Response.jsonWorldComponentContentPaths) {
            const items = [];
            const components = bungieData.Response.jsonWorldComponentContentPaths.en;
            
            // Example processing, would need to make additional API calls
            // to fetch actual item details based on manifest paths
            for (const category in components) {
                items.push({
                    symbol: category,
                    weaponType: "Manifest Item",
                    date: formattedDate,
                    kills: 0,
                    precision: 0,
                    usage: 0,
                    activityType: "Unknown",
                    price: Math.random() * 1000, // Placeholder for backward compatibility
                    volume: Math.floor(Math.random() * 10000) // Placeholder for backward compatibility
                });
            }
            
            return items.slice(0, 50); // Limit number of items
        }
        
        // If we're using a character or item endpoint (legacy support)
        if (bungieData.Response && Array.isArray(bungieData.Response.items)) {
            return bungieData.Response.items.map(item => ({
                symbol: item.itemHash || "Unknown",
                weaponType: "Character Item",
                date: formattedDate,
                kills: 0,
                precision: 0,
                usage: 0,
                activityType: "Unknown",
                price: item.primaryStat ? item.primaryStat.value : 0, // Backward compatibility
                volume: item.quantity || 1 // Backward compatibility
            }));
        }
        
        // Generic fallback transformation
        console.warn("Using generic data transformation - unsupported data structure");
        return [{
            symbol: "UNKNOWN",
            weaponType: "Unknown",
            date: formattedDate,
            kills: 0,
            precision: 0,
            usage: 0,
            activityType: "Unknown",
            price: 0, // Backward compatibility
            volume: 0 // Backward compatibility
        }];
    } catch (error) {
        console.error("Error transforming Bungie data:", error);
        return [];
    }
}

// Generate sample weapon data based on the date provided (now optional)
function generateSampleData(date) {
    let formattedDate = "";
    let randomFactor = Math.random(); // Default random factor
    
    if (date) {
        // Parse the date if provided
        const parsedDate = new Date(date);
        formattedDate = parsedDate.toISOString().split('T')[0]; // YYYY-MM-DD format
        
        // Generate some randomness based on the date
        const seed = parsedDate.getTime();
        randomFactor = (seed % 100) / 100; // Between 0 and 1
    }
    
    // List of sample weapons with usage statistics
    const weapons = [
        { 
            symbol: "Gjallarhorn", 
            weaponType: "Rocket Launcher",
            baseKills: 15025, 
            basePrecision: 2505, 
            baseUsage: 1000000,
            activityType: "PvE",
            referenceId: "1274330687"
        },
        { 
            symbol: "Thorn", 
            weaponType: "Hand Cannon",
            baseKills: 29045, 
            basePrecision: 18926, 
            baseUsage: 750000,
            activityType: "PvP",
            referenceId: "3973202132"
        },
        { 
            symbol: "Ace of Spades", 
            weaponType: "Hand Cannon",
            baseKills: 28010, 
            basePrecision: 19607, 
            baseUsage: 500000,
            activityType: "PvP",
            referenceId: "347366834"
        },
        { 
            symbol: "Last Word", 
            weaponType: "Hand Cannon",
            baseKills: 32075, 
            basePrecision: 22452, 
            baseUsage: 600000,
            activityType: "PvP",
            referenceId: "1364093401"
        },
        { 
            symbol: "Hawkmoon", 
            weaponType: "Hand Cannon",
            baseKills: 27535, 
            basePrecision: 19274, 
            baseUsage: 850000,
            activityType: "PvP",
            referenceId: "3856705927"
        },
        { 
            symbol: "Vex Mythoclast", 
            weaponType: "Fusion Rifle",
            baseKills: 80040, 
            basePrecision: 48024, 
            baseUsage: 900000,
            activityType: "PvE",
            referenceId: "4289226715"
        },
        { 
            symbol: "Fatebringer", 
            weaponType: "Hand Cannon",
            baseKills: 34520, 
            basePrecision: 24164, 
            baseUsage: 720000,
            activityType: "PvE",
            referenceId: "2171478765"
        },
        { 
            symbol: "Eyasluna", 
            weaponType: "Hand Cannon",
            baseKills: 53060, 
            basePrecision: 37142, 
            baseUsage: 450000,
            activityType: "PvP",
            referenceId: "1321792747"
        }
    ];
    
    // Generate data with some randomness
    return weapons.map(weapon => {
        const killsVariation = weapon.baseKills * 0.05 * (Math.random() - 0.5 + randomFactor);
        const precisionVariation = weapon.basePrecision * 0.08 * (Math.random() - 0.5 + randomFactor);
        const usageVariation = weapon.baseUsage * 0.2 * (Math.random() - 0.5 + randomFactor);
        
        return {
            symbol: weapon.symbol,
            weaponType: weapon.weaponType,
            date: formattedDate,
            kills: Math.floor(weapon.baseKills + killsVariation),
            precision: Math.floor(weapon.basePrecision + precisionVariation),
            usage: Math.floor(weapon.baseUsage + usageVariation),
            activityType: weapon.activityType,
            referenceId: weapon.referenceId,
            // Include price and volume for backward compatibility
            price: Math.floor(weapon.baseKills + killsVariation),
            volume: Math.floor(weapon.baseUsage + usageVariation)
        };
    });
}

// API endpoint to fetch data
app.get("/api/data", async (req, res) => {
    try {
        const { apiKey, date } = req.query;
        
        console.log(`Request received for data with apiKey: ${apiKey ? '******' : 'missing'}, date: ${date || 'not provided (optional)'}`);
        
        // Validate parameters
        if (!apiKey) {
            console.warn("API Key is missing");
            return res.status(400).json({ 
                error: "Missing API Key",
                message: "API Key is required" 
            });
        }
        
        // Date parameter is now optional
        if (!date) {
            console.log("Date parameter is not provided (optional)");
        }
        
        // Check if we should use sample data
        if (USE_SAMPLE_DATA === true) {
            console.log("Using sample data (configured in .env)");
            const sampleData = generateSampleData(date);
            console.log(`Returning ${sampleData.length} sample records${date ? ` for date: ${date}` : ' with no date specified'}`);
            return res.json(sampleData);
        }
        
        // Use the Bungie API if not using sample data
        try {
            const bungieResponse = await callBungieAPI(process.env.BUNGIE_DESTINY2_MANIFEST_ENDPOINT);
            
            // Transform the data for Tableau
            const transformedData = transformBungieDataForTableau(bungieResponse, date);
            console.log(`Returning ${transformedData.length} records from Bungie API${date ? ` for date: ${date}` : ' with no date specified'}`);
            
            return res.json(transformedData);
        } catch (bungieError) {
            console.error("Error calling Bungie API, falling back to sample data:", bungieError.message);
            
            // Fallback to sample data if Bungie API fails
            const sampleData = generateSampleData(date);
            console.log(`Returning ${sampleData.length} FALLBACK sample records${date ? ` for date: ${date}` : ' with no date specified'}`);
            
            return res.json(sampleData);
        }
    } catch (error) {
        console.error("Error processing request:", error);
        res.status(500).json({ 
            error: "Failed to process request",
            message: error.message 
        });
    }
});

// Status endpoint to check API configuration
app.get("/api/status", (req, res) => {
    res.json({
        server: "OK",
        bungie_api: BUNGIE_API_KEY ? "Configured" : "Not Configured",
        using_sample_data: USE_SAMPLE_DATA,
        cache_ttl: process.env.CACHE_DURATION || 3600,
        api_root: BUNGIE_API_ROOT
    });
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
    console.log(`Access your WDC at http://localhost:${port}`);
    console.log(`Status endpoint: http://localhost:${port}/api/status`);
    console.log(`Data endpoint: http://localhost:${port}/api/data?apiKey=test&date=${new Date().toISOString().split('T')[0]}`);
    
    if (USE_SAMPLE_DATA) {
        console.log("NOTICE: Using SAMPLE DATA mode (configured in .env)");
    } else {
        console.log("NOTICE: Using REAL Bungie API data mode");
    }
});
