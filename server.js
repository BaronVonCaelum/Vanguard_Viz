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
async function callBungieAPI(endpoint, params = {}, isFullUrl = false) {
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
        // Use the full URL if specified, otherwise construct it with BUNGIE_API_ROOT
        const url = isFullUrl ? endpoint : `${BUNGIE_API_ROOT}${endpoint}`;
        console.log(`Making Bungie ${isFullUrl ? 'CDN' : 'API'} request to: ${url}`);
        
        const requestConfig = {
            timeout: REQUEST_TIMEOUT,
            params: params
        };

        // Only add API key header for platform API requests, not CDN requests
        if (!isFullUrl) {
            requestConfig.headers = {
                'X-API-Key': BUNGIE_API_KEY
            };
        }
        
        const response = await axios.get(url, requestConfig);
        
        // For API requests, check for Bungie error responses
        if (!isFullUrl && response.data.ErrorCode && response.data.ErrorCode !== 1) {
            throw new Error(`Bungie API Error: ${response.data.ErrorStatus} - ${response.data.Message}`);
        }
        
        // Cache successful response
        apiCache.set(cacheKey, response.data);
        
        console.log(`${isFullUrl ? 'CDN' : 'API'} request successful, response status: ${response.status}`);
        return response.data;
    } catch (error) {
        console.error(`Bungie ${isFullUrl ? 'CDN' : 'API'} Error:`, error.message);
        if (error.response) {
            console.error("Response status:", error.response.status);
            console.error("Response data:", JSON.stringify(error.response.data).substring(0, 500) + "...");
        }
        throw error;
    }
}

// Define transformers for different manifest definition types
const definitionTransformers = {
    DestinyInventoryItemDefinition: (item, hash) => {
        // Safely get nested properties with proper type coercion
        const displayProps = item.displayProperties || {};
        const inventory = item.inventory || {};
        
        return {
            hash: hash.toString(),
            name: displayProps.name || "Unknown",
            description: displayProps.description || "",
            icon: displayProps.hasIcon ? `https://www.bungie.net${displayProps.icon}` : "",
            type: item.itemTypeDisplayName || "Unknown Type",
            tierType: inventory.tierTypeName || "Unknown",
            rarity: Number(inventory.tierType || 0),
            classType: getClassName(Number(item.classType)),
            damageType: Number(item.defaultDamageType || 0),
            damageTypeHash: item.defaultDamageTypeHash?.toString() || "0",
            equippable: Boolean(item.equippable),
            isExotic: Boolean(inventory.tierType === 6),
            isLegendary: Boolean(inventory.tierType === 5),
            bucketHash: inventory.bucketTypeHash?.toString() || "0",
            referenceId: hash.toString()
        };
    },
    
    DestinyActivityDefinition: (item, hash) => ({
        hash: hash.toString(),
        name: item.displayProperties?.name || "Unknown",
        description: item.displayProperties?.description || "",
        icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
        type: item.activityTypeHash ? "activityType" : "activity",
        activityTypeHash: item.activityTypeHash?.toString() || "0",
        destinationHash: item.destinationHash?.toString() || "0",
        placeHash: item.placeHash?.toString() || "0",
        activityModeHash: item.activityModeHash?.toString() || "0",
        isPlaylist: Boolean(item.isPlaylist),
        recommended_light: item.recommendedLight || 0,
        matchmaking: Boolean(item.matchmaking),
        referenceId: hash.toString()
    }),
    
    DestinyClassDefinition: (item, hash) => ({
        hash: hash.toString(),
        name: item.displayProperties?.name || "Unknown",
        description: item.displayProperties?.description || "",
        icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
        classType: getClassName(item.classType),
        classTypeValue: item.classType || 0,
        mentorVendorHash: item.mentorVendorHash?.toString() || "0",
        referenceId: hash.toString()
    }),
    
    DestinyDamageTypeDefinition: (item, hash) => ({
        hash: hash.toString(),
        name: item.displayProperties?.name || "Unknown",
        description: item.displayProperties?.description || "",
        icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
        enumValue: item.enumValue || 0,
        color: item.transparentIconPath ? item.transparentIconPath.split('/').pop().split('.')[0] : "none",
        showIcon: Boolean(item.showIcon),
        referenceId: hash.toString()
    }),
    
    DestinyStatDefinition: (item, hash) => ({
        hash: hash.toString(),
        name: item.displayProperties?.name || "Unknown",
        description: item.displayProperties?.description || "",
        icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
        aggregationType: item.aggregationType || 0,
        hasComputedBlock: Boolean(item.hasComputedBlock),
        statCategory: item.statCategory || 0,
        interpolate: Boolean(item.interpolate),
        referenceId: hash.toString()
    }),
    
    DestinyVendorDefinition: (item, hash) => ({
        hash: hash.toString(),
        name: item.displayProperties?.name || "Unknown",
        description: item.displayProperties?.description || "",
        icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
        vendorProgressionType: item.vendorProgressionType || 0,
        buyString: item.buyString || "",
        sellString: item.sellString || "",
        displayItemHash: item.displayItemHash?.toString() || "0",
        inhibitBuying: Boolean(item.inhibitBuying),
        inhibitSelling: Boolean(item.inhibitSelling),
        factionHash: item.factionHash?.toString() || "0",
        resetIntervalMinutes: item.resetIntervalMinutes || 0,
        resetOffsetMinutes: item.resetOffsetMinutes || 0,
        referenceId: hash.toString()
    }),
    
    DestinyEquipmentSlotDefinition: (item, hash) => ({
        hash: hash.toString(),
        name: item.displayProperties?.name || "Unknown",
        description: item.displayProperties?.description || "",
        icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
        equipmentCategoryHash: item.equipmentCategoryHash?.toString() || "0",
        bucketTypeHash: item.bucketTypeHash?.toString() || "0",
        applyCustomArtDyes: Boolean(item.applyCustomArtDyes),
        artDyeChannels: JSON.stringify(item.artDyeChannels || []),
        referenceId: hash.toString()
    })
};

// Helper function to fetch manifest definitions
async function fetchManifestDefinitions(definitionType) {
    try {
        console.log(`Fetching manifest definitions for ${definitionType}`);
        
        // Step 1: Get the manifest paths
        const manifestResponse = await callBungieAPI('/Destiny2/Manifest/');
        
        if (!manifestResponse.Response || !manifestResponse.Response.jsonWorldComponentContentPaths) {
            throw new Error("Invalid manifest response format");
        }
        
        // Get English (or specified language) paths
        const language = process.env.MANIFEST_LANGUAGE || 'en';
        const contentPaths = manifestResponse.Response.jsonWorldComponentContentPaths[language];
        
        if (!contentPaths || !contentPaths[definitionType]) {
            throw new Error(`Definition path not found for type: ${definitionType}`);
        }
        
        // Step 2: Get the full URL for the definition JSON
        const definitionPath = contentPaths[definitionType];
        const fullUrl = `https://www.bungie.net${definitionPath}`;
        
        // Step 3: Fetch the actual definitions
        const definitionsResponse = await callBungieAPI(fullUrl, {}, true);
        
        if (!definitionsResponse || typeof definitionsResponse !== 'object') {
            throw new Error("Invalid definition response format");
        }
        
        // Step 4: Transform the definitions using the appropriate transformer
        console.log("Processing definition response...");
        
        // Get the appropriate transformer for this definition type
        const transformer = definitionTransformers[definitionType];
        if (!transformer) {
            throw new Error(`No transformer found for definition type: ${definitionType}`);
        }
        
        // Apply the transformer to each item
        const transformedDefinitions = Object.entries(definitionsResponse).map(([hash, item]) => {
            try {
                // Debug log for the first few items
                if (parseInt(hash) < 3) {
                    console.log("Raw definition data:", {
                        hash,
                        type: definitionType,
                        name: item.displayProperties?.name,
                    });
                }

                // Apply the transformer
                const transformed = transformer(item, hash);
                
                // Add standard fields for Tableau compatibility
                transformed.kills = 0;
                transformed.precision = 0;
                transformed.usage = 0;
                transformed.vendor = "";
                transformed.date = "";  // Will be set by the endpoint if date is provided

                // Verify all fields have proper types
                Object.entries(transformed).forEach(([key, value]) => {
                    if (value === null || value === undefined) {
                        console.warn(`Null/undefined value for field ${key} in item ${hash}`);
                        // Set appropriate default based on field type
                        if (typeof transformed[key] === 'string' || key.endsWith('Hash') || 
                            ['hash', 'name', 'description', 'icon', 'type', 'tierType', 
                             'classType', 'source', 'referenceId', 'vendor', 'date'].includes(key)) {
                            transformed[key] = "";
                        } else if (typeof transformed[key] === 'number' || 
                                  ['rarity', 'damageType', 'bucket', 'kills', 'precision', 'usage'].includes(key)) {
                            transformed[key] = 0;
                        } else if (typeof transformed[key] === 'boolean' || 
                                  ['equippable', 'isExotic', 'isLegendary', 'isPlaylist', 'matchmaking'].includes(key)) {
                            transformed[key] = false;
                        }
                    }
                });
                
                return transformed;
            } catch (error) {
                console.error(`Error transforming item ${hash}:`, error);
                return null;
            }
        }).filter(item => item !== null);
        
        console.log(`Successfully transformed ${transformedDefinitions.length} ${definitionType} definitions`);
        // Log the first item to verify structure
        if (transformedDefinitions.length > 0) {
            console.log("First transformed item:", JSON.stringify(transformedDefinitions[0], null, 2));
        }
        
        return transformedDefinitions;
    } catch (error) {
        console.error(`Error fetching manifest definitions for ${definitionType}:`, error.message);
        throw error;
    }
}

// Helper function to get class name from class type
function getClassName(classType) {
    switch (classType) {
        case 0: return "Titan";
        case 1: return "Hunter";
        case 2: return "Warlock";
        default: return "Unknown";
    }
}

// Transform Bungie API response to Tableau-friendly format
function transformBungieDataForTableau(bungieData, date) {
    // Use empty string for date if not provided
    const formattedDate = date || "";
    
    try {
        // If we're receiving pre-transformed manifest data (from fetchManifestDefinitions)
        if (Array.isArray(bungieData)) {
            console.log("Processing pre-transformed manifest data");
            return bungieData.map(item => ({
                ...item,
                date: formattedDate
            }));
        }
        
        // If we're receiving raw manifest data
        if (bungieData && typeof bungieData === 'object' && Object.keys(bungieData).length > 0 && 
            bungieData[Object.keys(bungieData)[0]]?.displayProperties) {
            console.log("Processing raw manifest data");
            return Object.entries(bungieData).map(([hash, item]) => ({
                hash,
                name: item.displayProperties?.name || "Unknown",
                description: item.displayProperties?.description || "",
                icon: item.displayProperties?.hasIcon ? `https://www.bungie.net${item.displayProperties.icon}` : "",
                type: item.itemTypeDisplayName || "Unknown Type",
                tierType: item.inventory?.tierTypeName || "Unknown",
                rarity: item.inventory?.tierType || 0,
                classType: item.classType !== undefined ? getClassName(item.classType) : "All Classes",
                damageType: item.defaultDamageType || 0,
                equippable: item.equippable || false,
                isExotic: item.inventory?.tierType === 6,
                isLegendary: item.inventory?.tierType === 5,
                bucket: item.inventory?.bucketTypeHash || 0,
                source: item.collectibleHash ? "Collections" : (item.sources || []).map(s => s.sourceName).join(", ") || "Unknown",
                referenceId: hash,
                date: formattedDate
            }));
        }
        
        // Handle weapon usage stats data (legacy support)
        if (bungieData.status === "success" && Array.isArray(bungieData.weaponStats)) {
            console.log(`Processing ${bungieData.weaponStats.length} weapon stats entries`);
            return bungieData.weaponStats.map(weapon => ({
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

        // If we're using the manifest endpoint but haven't processed it yet
        if (bungieData.Response && bungieData.Response.jsonWorldComponentContentPaths) {
            console.log("Processing manifest paths response");
            const items = [];
            const components = bungieData.Response.jsonWorldComponentContentPaths.en;
            
            for (const category in components) {
                items.push({
                    symbol: category,
                    weaponType: "Manifest Category", 
                    date: formattedDate,
                    name: category,
                    path: components[category],
                    // Include these fields for backward compatibility
                    kills: 0,
                    precision: 0,
                    usage: 0,
                    activityType: "Unknown",
                    price: 0,
                    volume: 0
                });
            }
            
            return items;
        }
        
        // If we're using a character or item endpoint (legacy support)
        if (bungieData.Response && Array.isArray(bungieData.Response.items)) {
            console.log("Processing character items response");
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
        console.warn("Unhandled data format - returning empty array");
        console.warn("Data type:", typeof bungieData);
        console.warn("Is array:", Array.isArray(bungieData));
        if (bungieData) {
            console.warn("Keys:", Object.keys(bungieData).slice(0, 5));
        }
        return [];
    } catch (error) {
        console.error("Error transforming Bungie data:", error);
        return [];
    }
}
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

// Helper function to fetch weapon stats
async function fetchWeaponStats(date) {
    // In a real implementation, this would call the Bungie API
    // For now, we'll return sample data
    return {
        status: "success",
        weaponStats: generateSampleData(date)
    };
}

// Helper function to fetch vendor inventory
async function fetchVendorInventory(date) {
    // In a real implementation, this would call the Bungie API
    // For now, we'll use our existing sample data generator
    return generateVendorInventoryData(date);
}

// Helper function to transform weapon stats
function transformWeaponStatsForTableau(weaponStats, date) {
    const formattedDate = date || "";
    
    if (weaponStats.status === "success" && Array.isArray(weaponStats.weaponStats)) {
        return weaponStats.weaponStats.map(weapon => ({
            id: weapon.referenceId || "0",
            name: weapon.symbol || "Unknown Weapon",
            type: weapon.weaponType || "Unknown",
            date: formattedDate,
            kills: weapon.kills || 0,
            precision: weapon.precision || 0,
            usage: weapon.usage || 0,
            activityType: weapon.activityType || "All"
        }));
    }
    
    return [];
}

// Helper function to transform vendor data
function transformVendorDataForTableau(vendorData, date) {
    const formattedDate = date || "";
    
    if (Array.isArray(vendorData)) {
        return vendorData.map(item => ({
            id: item.referenceId || "0",
            name: item.itemName || "Unknown Item",
            type: item.itemType || "Unknown",
            date: formattedDate,
            vendor: item.vendor || "Unknown Vendor",
            price: item.price || 0,
            rarity: item.rarity || "Common",
            lightLevel: item.lightLevel || 0
        }));
    }
    
    return [];
}

// API endpoint to fetch data
app.get("/api/data", async (req, res) => {
    try {
        const { apiKey, date, type = 'items' } = req.query;
        
        console.log(`Request received for data with:
            - apiKey: ${apiKey ? '******' : 'missing'}
            - date: ${date || 'not provided (optional)'}
            - type: ${type || 'items (default)'}`);
        
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
        
        try {
            // Handle different data types
            switch (type) {
                case 'items':
                    if (USE_SAMPLE_DATA === true) {
                        console.log("Using sample item data (configured in .env)");
                        const sampleData = generateSampleData(date);
                        console.log(`Returning ${sampleData.length} sample item records`);
                        return res.json(sampleData);
                    }
                    
                    try {
                        // Get available manifest tables first
                        const manifestResponse = await callBungieAPI('/Destiny2/Manifest/');
                        const language = process.env.MANIFEST_LANGUAGE || 'en';
                        const contentPaths = manifestResponse.Response.jsonWorldComponentContentPaths[language];
                        
                        // Create an array of available tables
                        const availableTables = Object.entries(contentPaths).map(([key, path]) => ({
                            tableName: key,
                            path: path
                        }));
                        
                        console.log("Available manifest tables:", availableTables.map(t => t.tableName).join(", "));
                        
                        // For now, we'll focus on InventoryItems, but this structure allows for more tables
                        const itemDefinitions = await fetchManifestDefinitions('DestinyInventoryItemDefinition');
                        
                        // Transform into a more detailed format
                        const transformedItems = itemDefinitions.map(item => ({
                            ...item,
                            table: 'DestinyInventoryItemDefinition',  // Mark which table this came from
                            date: date || "",
                            // Additional weapon-specific fields if it's a weapon
                            isWeapon: item.type.includes("Weapon"),
                            weaponType: item.type.includes("Weapon") ? item.type : null,
                            damageType: item.damageType,
                            // Fields for joining
                            hash: item.hash,
                            referenceId: item.hash  // Include both for compatibility
                        }));
                        
                        console.log(`Returning ${transformedItems.length} item definition records`);
                        return res.json(transformedItems);
                    } catch (error) {
                        console.error("Error fetching manifest data:", error);
                        // Fall back to sample data
                        const sampleData = generateSampleData(date);
                        console.log(`Falling back to ${sampleData.length} sample records due to error`);
                        return res.json(sampleData);
                    }
                
                case 'weapons':
                    if (USE_SAMPLE_DATA === true) {
                        console.log("Using sample weapon data (configured in .env)");
                        const sampleData = generateSampleData(date);
                        console.log(`Returning ${sampleData.length} sample weapon records`);
                        return res.json(sampleData);
                    }
                    
                    // Fetch weapon stats
                    const weaponStats = await fetchWeaponStats(date);
                    const transformedWeapons = transformWeaponStatsForTableau(weaponStats, date);
                    console.log(`Returning ${transformedWeapons.length} weapon stat records`);
                    return res.json(transformedWeapons);
                
                case 'vendors':
                    if (USE_SAMPLE_DATA === true) {
                        console.log("Using sample vendor data (configured in .env)");
                        const sampleData = generateVendorInventoryData(date);
                        console.log(`Returning ${sampleData.length} sample vendor records`);
                        return res.json(sampleData);
                    }
                    
                    // Fetch vendor inventory
                    const vendorData = await fetchVendorInventory(date);
                    const transformedVendors = transformVendorDataForTableau(vendorData, date);
                    console.log(`Returning ${transformedVendors.length} vendor inventory records`);
                    return res.json(transformedVendors);
                
                default:
                    return res.status(400).json({
                        error: "Invalid Type",
                        message: "Type must be one of: items, weapons, vendors"
                    });
            }
        } catch (bungieError) {
            console.error("Error calling Bungie API, falling back to sample data:", bungieError.message);
            
            // Fallback to sample data based on requested type
            switch (type) {
                case 'items':
                case 'weapons':
                    const sampleData = generateSampleData(date);
                    console.log(`Returning ${sampleData.length} FALLBACK sample ${type} records`);
                    return res.json(sampleData);
                    
                case 'vendors':
                    const vendorData = generateVendorInventoryData(date);
                    console.log(`Returning ${vendorData.length} FALLBACK sample vendor records`);
                    return res.json(vendorData);
                    
                default:
                    return res.status(400).json({
                        error: "Invalid Type",
                        message: "Type must be one of: items, weapons, vendors"
                    });
            }
        }
    } catch (error) {
        console.error("Error processing request:", error);
        res.status(500).json({ 
            error: "Failed to process request",
            message: error.message 
        });
    }
});

// Historical weapon stats endpoint with date-based querying
app.get("/api/historical-weapon-stats", async (req, res) => {
    try {
        const { 
            apiKey,
            startDate, 
            endDate, 
            membershipType, 
            destinyMembershipId, 
            characterId = 0 // Default to 0 for account-wide stats
        } = req.query;
        
        console.log(`Request received for historical weapon stats with:
            - apiKey: ${apiKey ? '******' : 'missing'}
            - date range: ${startDate || 'not provided'} to ${endDate || 'not provided'}
            - membershipType: ${membershipType || 'not provided'}
            - destinyMembershipId: ${destinyMembershipId || 'not provided'}
            - characterId: ${characterId || '0 (account-wide)'}`);
        
        // Validate parameters
        if (!apiKey) {
            console.warn("API Key is missing");
            return res.status(400).json({ 
                error: "Missing API Key",
                message: "API Key is required" 
            });
        }
        
        if (!membershipType || !destinyMembershipId) {
            console.warn("Required parameters missing");
            return res.status(400).json({ 
                error: "Missing Parameters",
                message: "membershipType and destinyMembershipId are required" 
            });
        }
        
        if (!startDate || !endDate) {
            console.warn("Date range parameters missing");
            return res.status(400).json({ 
                error: "Missing Date Range",
                message: "startDate and endDate are required" 
            });
        }
        
        // Check date format and validate range
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            return res.status(400).json({ 
                error: "Invalid Date Format",
                message: "Dates must be in YYYY-MM-DD format" 
            });
        }
        
        if (end - start > 30 * 24 * 60 * 60 * 1000) {
            return res.status(400).json({ 
                error: "Date Range Too Large",
                message: "Date range cannot exceed 31 days (Bungie API limitation)" 
            });
        }
        
        // Check if we should use sample data
        if (USE_SAMPLE_DATA === true) {
            console.log("Using sample data (configured in .env)");
            
            // Generate sample data for each day in the date range
            const sampleData = [];
            const currentDate = new Date(start);
            
            while (currentDate <= end) {
                const dateString = currentDate.toISOString().split('T')[0];
                const dailySample = generateSampleData(dateString);
                sampleData.push(...dailySample);
                
                // Move to next day
                currentDate.setDate(currentDate.getDate() + 1);
            }
            
            console.log(`Returning ${sampleData.length} sample records for date range: ${startDate} to ${endDate}`);
            return res.json(sampleData);
        }
        
        // Use the Bungie API if not using sample data
        try {
            // Build the endpoint for historical stats with weapons group
            const endpoint = `/Destiny2/${membershipType}/Account/${destinyMembershipId}/Character/${characterId}/Stats/`;
            
            // Build the parameters for the API call
            const params = {
                daystart: startDate,
                dayend: endDate,
                groups: "Weapons", // Request weapon stats
                periodType: 1 // Daily (from the API enum: PeriodType.Daily = 1)
            };
            
            const bungieResponse = await callBungieAPI(endpoint, params);
            
            // Transform the data for Tableau
            const transformedData = transformHistoricalWeaponStats(bungieResponse, startDate, endDate);
            console.log(`Returning ${transformedData.length} historical weapon stats records from Bungie API for date range: ${startDate} to ${endDate}`);
            
            return res.json(transformedData);
        } catch (bungieError) {
            console.error("Error calling Bungie API, falling back to sample data:", bungieError.message);
            
            // Fallback to sample data if Bungie API fails
            const sampleData = [];
            const currentDate = new Date(start);
            
            while (currentDate <= end) {
                const dateString = currentDate.toISOString().split('T')[0];
                const dailySample = generateSampleData(dateString);
                sampleData.push(...dailySample);
                
                // Move to next day
                currentDate.setDate(currentDate.getDate() + 1);
            }
            
            console.log(`Returning ${sampleData.length} FALLBACK sample records for date range: ${startDate} to ${endDate}`);
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

// Helper function to transform historical weapon stats from Bungie API
function transformHistoricalWeaponStats(bungieData, startDate, endDate) {
    try {
        if (!bungieData.Response || !bungieData.Response.weapons) {
            console.warn("Invalid or empty historical weapon stats response");
            return [];
        }

        const weapons = bungieData.Response.weapons;
        const results = [];

        // Iterate through each weapon
        weapons.forEach(weapon => {
            const weaponName = weapon.name || "Unknown Weapon";
            const weaponType = weapon.weaponType || "Unknown";
            const referenceId = weapon.referenceId || "0";
            
            // Get daily stats for this weapon
            if (weapon.values && weapon.values.daily && weapon.values.daily.dailyStats) {
                const dailyStats = weapon.values.daily.dailyStats;
                
                // For each day, add an entry
                dailyStats.forEach(dayStat => {
                    const date = new Date(dayStat.period);
                    const dateString = date.toISOString().split('T')[0]; // YYYY-MM-DD format
                    
                    // Check if the date is within our requested range
                    if (dateString >= startDate && dateString <= endDate) {
                        results.push({
                            symbol: weaponName,
                            weaponType: weaponType,
                            date: dateString,
                            kills: dayStat.values.uniqueWeaponKills?.basic?.value || 0,
                            precision: dayStat.values.uniqueWeaponPrecisionKills?.basic?.value || 0,
                            usage: dayStat.values.uniqueWeaponKillsPrecisionKills?.basic?.value || 0, // Placeholder, may need adjustment
                            activityType: "All", // Can be expanded if mode filtering is added
                            referenceId: referenceId,
                            // Include price and volume for backward compatibility
                            price: dayStat.values.uniqueWeaponKills?.basic?.value || 0,
                            volume: dayStat.values.uniqueWeaponKillsPrecisionKills?.basic?.value || 0
                        });
                    }
                });
            }
        });
        
        return results;
    } catch (error) {
        console.error("Error transforming historical weapon stats:", error);
        return [];
    }
}

// Helper function to generate sample vendor inventory data
function generateVendorInventoryData(date) {
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
    
    // List of sample weapons that could appear in vendor inventory
    const inventoryItems = [
        { 
            itemName: "Gjallarhorn", 
            itemType: "Rocket Launcher",
            vendor: "Xûr",
            basePrice: 29, 
            baseLightLevel: 1350,
            rarity: "Exotic",
            referenceId: "1274330687"
        },
        { 
            itemName: "Thorn", 
            itemType: "Hand Cannon",
            vendor: "Monument to Lost Lights",
            basePrice: 25, 
            baseLightLevel: 1350,
            rarity: "Exotic",
            referenceId: "3973202132"
        },
        { 
            itemName: "Ace of Spades", 
            itemType: "Hand Cannon",
            vendor: "Monument to Lost Lights",
            basePrice: 25, 
            baseLightLevel: 1350,
            rarity: "Exotic",
            referenceId: "347366834"
        },
        { 
            itemName: "Last Word", 
            itemType: "Hand Cannon",
            vendor: "Monument to Lost Lights",
            basePrice: 25, 
            baseLightLevel: 1350,
            rarity: "Exotic",
            referenceId: "1364093401"
        },
        { 
            itemName: "Hawkmoon", 
            itemType: "Hand Cannon",
            vendor: "Xûr",
            basePrice: 23, 
            baseLightLevel: 1350,
            rarity: "Exotic",
            referenceId: "3856705927"
        },
        { 
            itemName: "Fatebringer", 
            itemType: "Hand Cannon",
            vendor: "Banshee-44",
            basePrice: 15, 
            baseLightLevel: 1350,
            rarity: "Legendary",
            referenceId: "2171478765"
        },
        { 
            itemName: "Eyasluna", 
            itemType: "Hand Cannon",
            vendor: "Banshee-44",
            basePrice: 15, 
            baseLightLevel: 1350,
            rarity: "Legendary",
            referenceId: "1321792747"
        },
        { 
            itemName: "Falling Guillotine", 
            itemType: "Sword",
            vendor: "Banshee-44",
            basePrice: 17, 
            baseLightLevel: 1350,
            rarity: "Legendary",
            referenceId: "614426548"
        },
        { 
            itemName: "Ikelos SMG", 
            itemType: "Submachine Gun",
            vendor: "Banshee-44",
            basePrice: 12, 
            baseLightLevel: 1350,
            rarity: "Legendary",
            referenceId: "2222560548"
        },
        { 
            itemName: "Gnawing Hunger", 
            itemType: "Auto Rifle",
            vendor: "Banshee-44",
            basePrice: 13, 
            baseLightLevel: 1350,
            rarity: "Legendary",
            referenceId: "821154603"
        },
        { 
            itemName: "Dead Man's Tale", 
            itemType: "Scout Rifle",
            vendor: "Xûr",
            basePrice: 29, 
            baseLightLevel: 1350,
            rarity: "Exotic",
            referenceId: "3654674561"
        }
    ];
    
    // Determine which items are available based on the date
    // For sample purposes, we'll use a rotating inventory where different items
    // are available on different days, with some overlap
    const dayOfWeek = date ? new Date(date).getDay() : new Date().getDay();
    
    // Xûr only appears on weekends (Friday-Sunday)
    const isXurPresent = dayOfWeek >= 5 || dayOfWeek === 0;
    
    // Filter items based on vendor availability
    const availableItems = inventoryItems.filter(item => {
        if (item.vendor === "Xûr" && !isXurPresent) {
            return false;
        }
        
        // Monument items are always available
        if (item.vendor === "Monument to Lost Lights") {
            return true;
        }
        
        // Banshee rotates stock based on day of week
        if (item.vendor === "Banshee-44") {
            // Simple rotation algorithm - certain items available on certain days
            return (dayOfWeek + inventoryItems.indexOf(item)) % 5 < 3;
        }
        
        return true;
    });
    
    // Generate data with some price and light level variations
    return availableItems.map(item => {
        const priceVariation = item.basePrice * 0.1 * (Math.random() - 0.5 + randomFactor);
        const lightLevelVariation = item.baseLightLevel * 0.02 * (Math.random() - 0.5 + randomFactor);
        
        return {
            itemName: item.itemName,
            itemType: item.itemType,
            date: formattedDate,
            vendor: item.vendor,
            price: Math.round((item.basePrice + priceVariation) * 10) / 10, // Round to 1 decimal
            lightLevel: Math.floor(item.baseLightLevel + lightLevelVariation),
            rarity: item.rarity,
            referenceId: item.referenceId,
            // Additional fields that can be used for analysis
            inStock: true,
            quantity: Math.floor(Math.random() * 5) + 1
        };
    });
}

// Vendor inventory endpoint for joining with weapon stats
app.get("/api/vendor-inventory", async (req, res) => {
    try {
        const { 
            apiKey,
            startDate, 
            endDate 
        } = req.query;
        
        console.log(`Request received for vendor inventory with:
            - apiKey: ${apiKey ? '******' : 'missing'}
            - date range: ${startDate || 'not provided'} to ${endDate || 'not provided'}`);
        
        // Validate parameters
        if (!apiKey) {
            console.warn("API Key is missing");
            return res.status(400).json({ 
                error: "Missing API Key",
                message: "API Key is required" 
            });
        }
        
        if (!startDate || !endDate) {
            console.warn("Date range parameters missing");
            return res.status(400).json({ 
                error: "Missing Date Range",
                message: "startDate and endDate are required" 
            });
        }
        
        // Check date format and validate range
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            return res.status(400).json({ 
                error: "Invalid Date Format",
                message: "Dates must be in YYYY-MM-DD format" 
            });
        }
        
        if (end - start > 30 * 24 * 60 * 60 * 1000) {
            return res.status(400).json({ 
                error: "Date Range Too Large",
                message: "Date range cannot exceed 31 days" 
            });
        }
        
        // Always use sample data for vendor inventory in this version
        // In a real implementation, we would call the Bungie API for vendor info
        const inventoryData = [];
        const currentDate = new Date(start);
        
        // Generate inventory data for each day in the range
        while (currentDate <= end) {
            const dateString = currentDate.toISOString().split('T')[0];
            const dailyInventory = generateVendorInventoryData(dateString);
            inventoryData.push(...dailyInventory);
            
            // Move to next day
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        console.log(`Returning ${inventoryData.length} vendor inventory records for date range: ${startDate} to ${endDate}`);
        return res.json(inventoryData);
        
    } catch (error) {
        console.error("Error processing vendor inventory request:", error);
        res.status(500).json({ 
            error: "Failed to process request",
            message: error.message 
        });
    }
});

// Utility function to filter inventory items before transformation
function filterInventoryItems(rawItems, filters) {
    // Clone the object to avoid modifying the original
    let filtered = {...rawItems};
    const MAX_ITEMS = parseInt(process.env.MAX_ITEMS) || 5000;
    let itemCount = Object.keys(filtered).length;
    let appliedFilters = [];
    
    // Filter by itemCategoryHash if provided
    if (filters.itemCategoryHash) {
        const categoryHash = filters.itemCategoryHash;
        console.log(`Filtering by itemCategoryHash: ${categoryHash}`);
        appliedFilters.push(`itemCategoryHash=${categoryHash}`);
        
        filtered = Object.fromEntries(
            Object.entries(filtered).filter(([_, item]) => {
                return item.itemCategoryHashes && 
                       Array.isArray(item.itemCategoryHashes) && 
                       item.itemCategoryHashes.includes(parseInt(categoryHash));
            })
        );
    }
    
    // Filter by classType if provided (0=Titan, 1=Hunter, 2=Warlock, 3=Any)
    if (filters.classType !== undefined && filters.classType !== null) {
        const classType = parseInt(filters.classType);
        if (!isNaN(classType) && classType >= 0 && classType <= 3) {
            console.log(`Filtering by classType: ${classType}`);
            appliedFilters.push(`classType=${classType}`);
            
            filtered = Object.fromEntries(
                Object.entries(filtered).filter(([_, item]) => {
                    // If classType is 3 (Any), include items with classType 3 or undefined
                    if (classType === 3) {
                        return item.classType === 3 || item.classType === undefined;
                    }
                    // Otherwise match the specific class or include items for all classes (classType=3)
                    return item.classType === classType || item.classType === 3;
                })
            );
        }
    }
    
    // Filter by rarity/tierType if provided
    if (filters.rarity !== undefined && filters.rarity !== null) {
        const rarity = parseInt(filters.rarity);
        if (!isNaN(rarity) && rarity >= 0) {
            console.log(`Filtering by rarity/tierType: ${rarity}`);
            appliedFilters.push(`rarity=${rarity}`);
            
            filtered = Object.fromEntries(
                Object.entries(filtered).filter(([_, item]) => {
                    return item.inventory && item.inventory.tierType === rarity;
                })
            );
        }
    }
    
    // Filter by searchTerm if provided
    if (filters.searchTerm) {
        const searchTerm = filters.searchTerm.toLowerCase();
        console.log(`Filtering by searchTerm: ${searchTerm}`);
        appliedFilters.push(`searchTerm=${searchTerm}`);
        
        filtered = Object.fromEntries(
            Object.entries(filtered).filter(([_, item]) => {
                return (
                    (item.displayProperties && 
                     item.displayProperties.name && 
                     item.displayProperties.name.toLowerCase().includes(searchTerm)) ||
                    (item.itemTypeDisplayName && 
                     item.itemTypeDisplayName.toLowerCase().includes(searchTerm))
                );
            })
        );
    }
    
    // Filter by itemType if provided
    if (filters.itemType) {
        console.log(`Filtering by itemType: ${filters.itemType}`);
        appliedFilters.push(`itemType=${filters.itemType}`);
        
        filtered = Object.fromEntries(
            Object.entries(filtered).filter(([_, item]) => {
                return item.itemTypeDisplayName && 
                       item.itemTypeDisplayName.toLowerCase().includes(filters.itemType.toLowerCase());
            })
        );
    }
    
    // Check if the filtered dataset is still too large
    const filteredCount = Object.keys(filtered).length;
    const isTooBig = filteredCount > MAX_ITEMS;
    const warning = isTooBig 
        ? `Filtered result set (${filteredCount} items) exceeds maximum limit (${MAX_ITEMS}). Please apply more specific filters.`
        : null;
    
    // If filtered result is too large and we can provide a sample
    if (isTooBig) {
        // Take a sample of MAX_ITEMS
        const allKeys = Object.keys(filtered);
        const sampleKeys = allKeys.slice(0, MAX_ITEMS);
        filtered = Object.fromEntries(
            sampleKeys.map(key => [key, filtered[key]])
        );
    }
    
    console.log(`Filtering reduced item count from ${itemCount} to ${Object.keys(filtered).length}`);
    if (appliedFilters.length > 0) {
        console.log(`Applied filters: ${appliedFilters.join(", ")}`);
    }
    
    return {
        filteredItems: filtered,
        originalCount: itemCount,
        filteredCount: Object.keys(filtered).length,
        warning: warning,
        appliedFilters: appliedFilters
    };
}

// New endpoint to fetch specific manifest table data
app.get("/api/manifest/:type", async (req, res) => {
    try {
        const { apiKey } = req.query;
        const { type } = req.params;
        
        if (!apiKey) {
            return res.status(400).json({ 
                error: "Missing API Key",
                message: "API Key is required" 
            });
        }

        // Map endpoint type to definition type
        const definitionTypeMap = {
            'activities': 'DestinyActivityDefinition',
            'classes': 'DestinyClassDefinition',
            'inventory-items': 'DestinyInventoryItemDefinition',
            'damage-types': 'DestinyDamageTypeDefinition',
            'stats': 'DestinyStatDefinition',
            'vendors': 'DestinyVendorDefinition',
            'equipment-slots': 'DestinyEquipmentSlotDefinition'
        };
        
        const definitionType = definitionTypeMap[type];
        if (!definitionType) {
            return res.status(400).json({
                error: "Invalid Type",
                message: `Type must be one of: ${Object.keys(definitionTypeMap).join(', ')}`
            });
        }
        
        // Check if this is the inventory-items endpoint with filter parameters
        if (type === 'inventory-items') {
            // Extract filter parameters
            const filterParams = {
                itemCategoryHash: req.query.itemCategoryHash,
                classType: req.query.classType,
                rarity: req.query.rarity,
                searchTerm: req.query.searchTerm,
                itemType: req.query.itemType
            };
            
            const hasFilters = Object.values(filterParams).some(val => val !== undefined);
            
            if (hasFilters) {
                // We'll handle filtering differently for inventory items
                console.log("Processing inventory items with filtering");
                
                // Step 1: Get the manifest paths - same as in fetchManifestDefinitions
                const manifestResponse = await callBungieAPI('/Destiny2/Manifest/');
                
                if (!manifestResponse.Response || !manifestResponse.Response.jsonWorldComponentContentPaths) {
                    throw new Error("Invalid manifest response format");
                }
                
                // Get English (or specified language) paths
                const language = process.env.MANIFEST_LANGUAGE || 'en';
                const contentPaths = manifestResponse.Response.jsonWorldComponentContentPaths[language];
                
                if (!contentPaths || !contentPaths[definitionType]) {
                    throw new Error(`Definition path not found for type: ${definitionType}`);
                }
                
                // Step 2: Get the full URL for the definition JSON
                const definitionPath = contentPaths[definitionType];
                const fullUrl = `https://www.bungie.net${definitionPath}`;
                
                // Step 3: Fetch the actual definitions
                const definitionsResponse = await callBungieAPI(fullUrl, {}, true);
                
                if (!definitionsResponse || typeof definitionsResponse !== 'object') {
                    throw new Error("Invalid definition response format");
                }
                
                // Step 4: Apply filtering BEFORE transformation
                const { 
                    filteredItems, 
                    originalCount, 
                    filteredCount, 
                    warning,
                    appliedFilters 
                } = filterInventoryItems(definitionsResponse, filterParams);
                
                // Step 5: Transform the filtered definitions
                console.log("Transforming filtered inventory items");
                
                // Get the transformer for this definition type
                const transformer = definitionTransformers[definitionType];
                if (!transformer) {
                    throw new Error(`No transformer found for definition type: ${definitionType}`);
                }
                
                // Apply the transformer to each filtered item
                const transformedDefinitions = Object.entries(filteredItems).map(([hash, item]) => {
                    try {
                        // Apply the transformer
                        const transformed = transformer(item, hash);
                        
                        // Add standard fields for Tableau compatibility
                        transformed.kills = 0;
                        transformed.precision = 0;
                        transformed.usage = 0;
                        transformed.vendor = "";
                        transformed.date = "";
                        
                        // Verify all fields have proper types
                        Object.entries(transformed).forEach(([key, value]) => {
                            if (value === null || value === undefined) {
                                console.warn(`Null/undefined value for field ${key} in item ${hash}`);
                                // Set appropriate default based on field type
                                if (typeof transformed[key] === 'string' || 
                                    key.endsWith('Hash') || 
                                    ['hash', 'name', 'description', 'icon', 'type', 'tierType', 
                                     'classType', 'source', 'referenceId', 'vendor', 'date'].includes(key)) {
                                    transformed[key] = "";
                                } else if (typeof transformed[key] === 'number' || 
                                          ['rarity', 'damageType', 'bucket', 'kills', 'precision', 'usage'].includes(key)) {
                                    transformed[key] = 0;
                                } else if (typeof transformed[key] === 'boolean' || 
                                          ['equippable', 'isExotic', 'isLegendary', 'isPlaylist', 'matchmaking'].includes(key)) {
                                    transformed[key] = false;
                                }
                            }
                        });
                        
                        return transformed;
                    } catch (error) {
                        console.error(`Error transforming item ${hash}:`, error);
                        return null;
                    }
                }).filter(item => item !== null);
                
                // Include warning about large dataset if needed
                let response = {
                    data: transformedDefinitions
                };
                
                if (warning) {
                    response.warning = warning;
                    response.originalCount = originalCount;
                    response.filteredCount = filteredCount;
                    response.appliedFilters = appliedFilters;
                }
                
                console.log(`Returning ${transformedDefinitions.length} filtered ${type} records`);
                return res.json(response.data);
            }
        }
        
        // Fetch and transform the data
        const transformedData = await fetchManifestDefinitions(definitionType);
        
        console.log(`Returning ${transformedData.length} ${type} records`);
        return res.json(transformedData);
        
    } catch (error) {
        console.error("Error in manifest endpoint:", error);
        res.status(500).json({ 
            error: "Failed to fetch manifest data",
            message: error.message 
        });
    }
});

// Manifest tables endpoint
app.get("/api/manifest-tables", async (req, res) => {
    try {
        const { apiKey, tables, date } = req.query;
        
        if (!apiKey) {
            return res.status(400).json({ 
                error: "Missing API Key",
                message: "API Key is required" 
            });
        }

        // If no specific tables requested, default to InventoryItems
        const requestedTables = tables ? tables.split(',') : ['DestinyInventoryItemDefinition'];
        
        // Validate requested tables
        const validTables = Object.keys(definitionTransformers);
        const invalidTables = requestedTables.filter(table => !validTables.includes(table));
        
        if (invalidTables.length > 0) {
            return res.status(400).json({
                error: "Invalid Tables",
                message: `Invalid tables requested: ${invalidTables.join(', ')}. Valid tables are: ${validTables.join(', ')}`
            });
        }

        // Fetch all requested tables
        const results = {};
        await Promise.all(requestedTables.map(async (table) => {
            try {
                results[table] = await fetchManifestDefinitions(table);
                
                // Add date if provided
                if (date) {
                    results[table].forEach(item => {
                        item.date = date;
                    });
                }
            } catch (error) {
                console.error(`Error fetching ${table}:`, error);
                results[table] = [];
            }
        }));

        console.log(`Returning data for ${Object.keys(results).length} manifest tables`);
        return res.json(results);

    } catch (error) {
        console.error("Error in manifest-tables endpoint:", error);
        res.status(500).json({ 
            error: "Failed to fetch manifest tables",
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

// Cache management endpoint
app.get("/api/clear-cache", (req, res) => {
    apiCache.flushAll();
    console.log("Cache cleared");
    res.json({
        status: "success",
        message: "Cache cleared successfully"
    });
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
    console.log(`Access your WDC at http://localhost:${port}`);
    console.log(`Status endpoint: http://localhost:${port}/api/status`);
    
    // Example URLs for all endpoints
    const today = new Date().toISOString().split('T')[0];
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    // Main data endpoint with different types
    console.log(`Items data: http://localhost:${port}/api/data?apiKey=test&type=items&date=${today}`);
    console.log(`Weapons data: http://localhost:${port}/api/data?apiKey=test&type=weapons&date=${today}`);
    console.log(`Vendors data: http://localhost:${port}/api/data?apiKey=test&type=vendors&date=${today}`);
    
    // Historical and range-based endpoints
    console.log(`Historical weapon stats: http://localhost:${port}/api/historical-weapon-stats?apiKey=test&startDate=${weekAgo}&endDate=${today}&membershipType=3&destinyMembershipId=12345678`);
    console.log(`Vendor inventory: http://localhost:${port}/api/vendor-inventory?apiKey=test&startDate=${weekAgo}&endDate=${today}`);
    
    // Manifest tables endpoints
    console.log(`Manifest tables (multiple): http://localhost:${port}/api/manifest-tables?apiKey=test&tables=DestinyInventoryItemDefinition,DestinyClassDefinition`);
    console.log(`Manifest activities: http://localhost:${port}/api/manifest/activities?apiKey=test`);
    console.log(`Manifest classes: http://localhost:${port}/api/manifest/classes?apiKey=test`);
    console.log(`Manifest items: http://localhost:${port}/api/manifest/inventory-items?apiKey=test`);
    
    if (USE_SAMPLE_DATA) {
        console.log("NOTICE: Using SAMPLE DATA mode (configured in .env)");
    } else {
        console.log("NOTICE: Using REAL Bungie API data mode");
    }
});
