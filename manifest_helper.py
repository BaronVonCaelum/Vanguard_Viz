#!/usr/bin/env python3
"""
Standalone helper module for retrieving Destiny 2 Manifest components.
This module provides functions to interact with the Bungie.net API for manifest data
without dependencies on the rest of the API client.
"""
import os
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API key from environment variables (loaded from .env file)
BUNGIE_API_KEY = os.getenv("BUNGIE_API_KEY")

# Log whether API key was found
if BUNGIE_API_KEY:
    logger.info("Bungie API key loaded successfully")
else:
    logger.warning("No Bungie API key found in environment variables")

async def get_manifest_component(
    component_type: str = "DestinyInventoryItemDefinition",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieves a specific component from the Destiny 2 Manifest.
    
    Args:
        component_type: The manifest component to retrieve. Default is "DestinyInventoryItemDefinition".
                        Other examples include "DestinyClassDefinition", "DestinySandboxPerkDefinition", etc.
        api_key: Optional Bungie API key. If not provided, will use BUNGIE_API_KEY from environment variables.
        
    Returns:
        Dict containing the requested manifest component data
    """
    # Use provided API key or environment variable
    used_api_key = api_key or BUNGIE_API_KEY
    
    if not used_api_key:
        return {
            "error": "No Bungie API key provided. Please set BUNGIE_API_KEY environment variable or pass api_key parameter."
        }
    
    try:
        # Step 1: Get the manifest
        manifest_url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
        headers = {
            "X-API-Key": used_api_key
        }
        
        # Make request to get the manifest paths
        logger.info(f"Fetching Destiny 2 manifest from {manifest_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(manifest_url, headers=headers) as response:
                manifest_response = await response.json()
                if response.status != 200 or "Response" not in manifest_response:
                    error_msg = manifest_response.get('Message', 'Unknown error')
                    logger.error(f"Failed to get manifest: {error_msg}")
                    return {"error": f"Failed to retrieve Destiny 2 manifest: {error_msg}"}
                
                manifest_data = manifest_response.get("Response", {})
        
        # Step 2: Extract the path for the requested component
        if "jsonWorldComponentContentPaths" not in manifest_data or "en" not in manifest_data["jsonWorldComponentContentPaths"]:
            logger.error("Manifest data does not contain jsonWorldComponentContentPaths or language data")
            return {"error": "Invalid manifest data structure"}
            
        content_paths = manifest_data["jsonWorldComponentContentPaths"]["en"]
        if component_type not in content_paths:
            logger.error(f"Component type {component_type} not found in manifest")
            return {"error": f"Component type {component_type} not found in manifest"}
            
        component_path = content_paths[component_type]
        
        # Step 3: Construct the full URL
        component_url = f"https://www.bungie.net{component_path}"
        
        # Step 4: Make second call to get the actual definitions
        logger.info(f"Fetching manifest component: {component_type} from {component_url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(component_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get component data: {response.status}")
                        return {"error": f"Failed to retrieve component data: {response.status}"}
                    
                    # Parse the response - can be large so we handle with care
                    component_data = await response.json()
                    
                    # Check if we got valid data
                    if not isinstance(component_data, dict):
                        logger.error(f"Received invalid data format for {component_type}")
                        return {"error": f"Invalid data format received for {component_type}"}
                    
                    logger.info(f"Successfully retrieved {component_type} with {len(component_data)} entries")
                    return {
                        "status": "success",
                        "componentType": component_type,
                        "componentData": component_data
                    }
        except Exception as e:
            logger.error(f"Error fetching component data: {e}")
            return {"error": f"Failed to retrieve or parse component data: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving manifest component: {e}")
        return {"error": f"Unexpected error: {e}"}

async def main():
    """
    Main function to test the manifest component retrieval functionality.
    """
    print("Testing Destiny 2 Manifest Component Retrieval")
    print("=============================================\n")
    
    # Test retrieving inventory item definitions
    print("Retrieving Destiny Inventory Item Definitions...")
    result = await get_manifest_component("DestinyInventoryItemDefinition")
    
    if result.get("status") == "success":
        component_data = result.get("componentData", {})
        print(f"Successfully retrieved {len(component_data)} inventory item definitions")
        
        # Display a sample item
        if component_data:
            sample_hash = next(iter(component_data))
            sample_item = component_data[sample_hash]
            print("\nSample Item Details:")
            print(f"Hash: {sample_hash}")
            print(f"Name: {sample_item.get('displayProperties', {}).get('name', 'Unknown')}")
            print(f"Type: {sample_item.get('itemTypeDisplayName', 'Unknown')}")
            print(f"Description: {sample_item.get('displayProperties', {}).get('description', 'No description')}")
            
            # Check if it has an icon
            icon = sample_item.get('displayProperties', {}).get('icon', '')
            if icon:
                print(f"Icon URL: https://www.bungie.net{icon}")
    else:
        print(f"Error retrieving inventory items: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())

