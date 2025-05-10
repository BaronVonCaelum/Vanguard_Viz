"""
Bungie.net API Client for the Vanguard Viz Web Data Connector
This module provides functions to interact with the Bungie.net API using BungIO
"""
import os
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, List, Union

# For environment variables
from dotenv import load_dotenv

# BungIO imports
from bungio import Client
from bungio.models import (
    DestinyComponentType,
    BungieMembershipType,
    GroupsForMemberFilter,
    DestinyStatsGroupType
)
from bungio.error import BungieException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# API credentials from environment variables
BUNGIE_API_KEY = os.getenv("BUNGIE_API_KEY")
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_AUTH_URL = os.getenv("OAUTH_AUTH_URL")
OAUTH_TOKEN_URL = os.getenv("OAUTH_TOKEN_URL")
OAUTH_CALLBACK_URL = os.getenv("OAUTH_CALLBACK_URL")

# Initialize BungIO client
# Include all required parameters for the BungIO client
client = Client(
    bungie_token=BUNGIE_API_KEY,
    bungie_client_id=OAUTH_CLIENT_ID if OAUTH_CLIENT_ID else "0",  # Must be a string
    bungie_client_secret=""  # Bungie.net doesn't use client secrets, but the library requires a string
)

# Token storage (in a real application, this should be persisted securely)
access_token = None
refresh_token = None


async def get_user_profile(bungie_name: str, bungie_code: str) -> Dict[str, Any]:
    """
    Get a user's Destiny 2 profile information by Bungie name and code.
    
    Args:
        bungie_name: The user's Bungie name
        bungie_code: The user's Bungie code (numbers after the #)
        
    Returns:
        Dict containing user profile data
    """
    try:
        # Search for the user by their Bungie name and code
        search_payload = {
            "displayName": bungie_name,
            "displayNameCode": bungie_code
        }
        
        # Access the Bungie API directly
        url = "https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/-1/"
        headers = {
            "X-API-Key": BUNGIE_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Create a new session for the request
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=search_payload, headers=headers) as response:
                user_search_response = await response.json()
        
        if not user_search_response or not user_search_response.get("Response"):
            logger.error(f"No user found with Bungie name: {bungie_name}#{bungie_code}")
            return {"error": "User not found"}
        
        # Get the first membership from the search results
        search_results = user_search_response.get("Response", [])
        if not search_results:
            logger.error(f"Empty search results for Bungie name: {bungie_name}#{bungie_code}")
            return {"error": "User not found"}
            
        # Get the first result
        membership = search_results[0]
        
        # Get the user's profile
        components = [
            DestinyComponentType.PROFILES.value, 
            DestinyComponentType.CHARACTERS.value, 
            DestinyComponentType.CHARACTER_EQUIPMENT.value
        ]
        
        # Build the URL for profile request
        components_str = ",".join(str(c) for c in components)
        url = f"https://www.bungie.net/Platform/Destiny2/{membership['membershipType']}/Profile/{membership['membershipId']}/?components={components_str}"
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create a new session for the request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                profile_response = await response.json()
        
        return {
            "profile": profile_response.get("Response", {}),
            "membership": membership
        }
    
    except BungieException as e:
        logger.error(f"Bungie API error: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {e}"}


async def get_player_stats(membership_type: int, destiny_membership_id: str) -> Dict[str, Any]:
    """
    Get a player's Destiny 2 stats.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        
    Returns:
        Dict containing player stats
    """
    try:
        # Define the groups we want to retrieve
        groups = [
            DestinyStatsGroupType.GENERAL.value,
            DestinyStatsGroupType.WEAPONS.value,
            DestinyStatsGroupType.MEDALS.value
        ]
        
        # Build the URL for stats request
        groups_str = ",".join(str(g) for g in groups)
        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Stats/?groups={groups_str}"
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create a new session for the request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                stats_response = await response.json()
        
        return stats_response.get("Response", {})
    
    except BungieException as e:
        logger.error(f"Bungie API error: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {e}"}


async def test_api_connection() -> Dict[str, Any]:
    """
    Test the API connection by fetching the Destiny 2 manifest.
    
    Returns:
        Dict indicating connection status and version information
    """
    try:
        # Attempt to get the Destiny 2 manifest using direct HTTP request
        url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create a new session for the request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                manifest_response = await response.json()
        
        if manifest_response and "Response" in manifest_response:
            return {
                "status": "connected",
                "version": manifest_response.get("Response", {}).get("version", "unknown"),
                "message": "Successfully connected to Bungie API"
            }
        else:
            return {
                "status": "error",
                "message": "Connected but received empty response"
            }
    
    except BungieException as e:
        logger.error(f"Bungie API error during connection test: {e}")
        return {
            "status": "error",
            "message": f"API connection failed: {e}"
        }
    
    except Exception as e:
        logger.error(f"Unexpected error during connection test: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}"
        }


async def get_weapon_usage_stats(membership_type: int, destiny_membership_id: str, character_id: str) -> Dict[str, Any]:
    """
    Get detailed weapon usage statistics for a specific character, including metadata from the manifest.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        character_id: The character ID for which to retrieve weapon stats
        
    Returns:
        Dict containing detailed weapon usage statistics with metadata
    """
    try:
        # Step 1: Get unique weapons data for the character
        unique_weapons_url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/UniqueWeapons/"
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create session for unique weapons request
        unique_weapons_data = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(unique_weapons_url, headers=headers) as response:
                unique_weapons_response = await response.json()
                if response.status == 200 and "Response" in unique_weapons_response:
                    unique_weapons_data = unique_weapons_response.get("Response", {})
        
        # Step 2: Get historical stats for the account to supplement weapon data
        historical_stats_url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Stats/"
        historical_stats_data = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(historical_stats_url, headers=headers) as response:
                historical_stats_response = await response.json()
                if response.status == 200 and "Response" in historical_stats_response:
                    historical_stats_data = historical_stats_response.get("Response", {})
        
        # Step 3: Get weapon definitions from the manifest
        # First, get the manifest path
        manifest_url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
        manifest_data = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(manifest_url, headers=headers) as response:
                manifest_response = await response.json()
                if response.status == 200 and "Response" in manifest_response:
                    manifest_data = manifest_response.get("Response", {})
        
        # Extract the path to the inventory item definitions
        item_definitions = {}
        if manifest_data and "jsonWorldComponentContentPaths" in manifest_data:
            content_paths = manifest_data["jsonWorldComponentContentPaths"]["en"]
            if "DestinyInventoryItemDefinition" in content_paths:
                item_def_path = content_paths["DestinyInventoryItemDefinition"]
                
                # Get the item definitions
                item_def_url = f"https://www.bungie.net{item_def_path}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(item_def_url, headers=headers) as response:
                        if response.status == 200:
                            try:
                                item_definitions = await response.json()
                            except Exception as e:
                                logger.warning(f"Failed to parse item definitions: {e}")
                                # Definitions can be large, so we'll proceed without them if there's an issue
        
        # Step 4: Process the data and merge weapon stats with metadata
        weapon_stats = []
        
        # Process unique weapons data
        if "weapons" in unique_weapons_data:
            for weapon in unique_weapons_data["weapons"]:
                weapon_hash = str(weapon.get("referenceId", "0"))
                weapon_data = {
                    "referenceId": weapon_hash,
                    "weaponName": "Unknown Weapon",
                    "weaponType": "Unknown",
                    "weaponIcon": "",
                    "killCount": 0,
                    "precisionKillCount": 0,
                    "usageTime": 0,
                    "activityType": "All",
                }
                
                # Add basic stats from unique weapons
                values = weapon.get("values", {})
                weapon_data["killCount"] = values.get("uniqueWeaponKills", {}).get("basic", {}).get("value", 0)
                weapon_data["precisionKillCount"] = values.get("uniqueWeaponPrecisionKills", {}).get("basic", {}).get("value", 0)
                weapon_data["usageTime"] = values.get("uniqueWeaponTimeUsed", {}).get("basic", {}).get("value", 0)
                
                # Add metadata from manifest if available
                if weapon_hash in item_definitions:
                    item_def = item_definitions[weapon_hash]
                    weapon_data["weaponName"] = item_def.get("displayProperties", {}).get("name", "Unknown Weapon")
                    weapon_data["weaponType"] = item_def.get("itemTypeDisplayName", "Unknown")
                    weapon_data["weaponIcon"] = item_def.get("displayProperties", {}).get("icon", "")
                    weapon_data["tierType"] = item_def.get("inventory", {}).get("tierType", 0)
                    weapon_data["damageType"] = item_def.get("defaultDamageType", 0)
                
                weapon_stats.append(weapon_data)
        
        # Add PvE/PvP split if available from historical stats
        if historical_stats_data:
            # Process PvE weapon stats
            if "allPvE" in historical_stats_data and "allTime" in historical_stats_data["allPvE"]:
                pve_stats = historical_stats_data["allPvE"]["allTime"]
                if "weaponKillsPrecisionKills" in pve_stats:
                    pve_weapon_stats = pve_stats["weaponKillsPrecisionKills"].get("statId", {})
                    # Could add more detailed PvE weapon stats here
            
            # Process PvP weapon stats
            if "allPvP" in historical_stats_data and "allTime" in historical_stats_data["allPvP"]:
                pvp_stats = historical_stats_data["allPvP"]["allTime"]
                if "weaponKillsPrecisionKills" in pvp_stats:
                    pvp_weapon_stats = pvp_stats["weaponKillsPrecisionKills"].get("statId", {})
                    # Could add more detailed PvP weapon stats here
        
        # Return combined data
        return {
            "status": "success",
            "weaponStats": weapon_stats,
            "totalWeapons": len(weapon_stats)
        }
    
    except BungieException as e:
        logger.error(f"Bungie API error getting weapon stats: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error getting weapon stats: {e}")
        return {"error": f"Unexpected error: {e}"}


# Example usage
async def main():
    """
    Main function to test the API client
    """
    print("Testing Bungie API connection...")
    # Test the API connection
    connection_test = await test_api_connection()
    print(f"Connection test result: {connection_test}")
    
    # If connected successfully, try to fetch a user profile
    if connection_test["status"] == "connected":
        # Use real Bungie name and code
        bungie_name = "Caelum(Adept)"
        bungie_code = "1507"
        
        print(f"\nAttempting to fetch profile for {bungie_name}#{bungie_code}...")
        
        profile = await get_user_profile(bungie_name, bungie_code)
        if "error" in profile:
            print(f"Error: {profile['error']}")
        else:
            print(f"Successfully retrieved profile!")
            # Print some basic information
            if "profile" in profile:
                response_data = profile["profile"]
                if "characters" in response_data and "data" in response_data["characters"]:
                    characters = response_data["characters"]["data"]
                    print(f"Found {len(characters)} characters")
                    
                    # Get character details
                    for char_id, char_data in characters.items():
                        char_class = char_data.get("classType", "Unknown")
                        char_light = char_data.get("light", 0)
                        char_race = char_data.get("raceType", "Unknown")
                        print(f"Character: {char_id} - Class: {char_class}, Light: {char_light}, Race: {char_race}")
                
                # If we have membership data, attempt to get stats as well
                if "membership" in profile:
                    membership_type = profile["membership"].get("membershipType")
                    membership_id = profile["membership"].get("membershipId")
                    
                    if membership_type and membership_id:
                        print(f"\nFetching stats for membership ID: {membership_id}...")
                        stats = await get_player_stats(membership_type, membership_id)
                        
                        if "error" not in stats:
                            print("Successfully retrieved stats!")
                            
                            # Print some basic PvE stats if available
                            if "allPvE" in stats and "allTime" in stats["allPvE"]:
                                pve_stats = stats["allPvE"]["allTime"]
                                if "activitiesCleared" in pve_stats:
                                    activities = pve_stats["activitiesCleared"]["basic"]["value"]
                                    print(f"PvE Activities Cleared: {activities}")
                                if "kills" in pve_stats:
                                    kills = pve_stats["kills"]["basic"]["value"]
                                    print(f"PvE Kills: {kills}")
                        else:
                            print(f"Error fetching stats: {stats.get('error')}")

                    # Now let's get weapon usage for the first character if any characters are found
                    if "characters" in response_data and "data" in response_data["characters"]:
                        characters = response_data["characters"]["data"]
                        if characters:
                            first_char_id = next(iter(characters))
                            print(f"\nFetching weapon usage stats for character: {first_char_id}...")
                            
                            weapon_stats = await get_weapon_usage_stats(
                                membership_type, 
                                membership_id, 
                                first_char_id
                            )
                            
                            if "error" not in weapon_stats:
                                print("Successfully retrieved weapon stats!")
                                print(f"Total weapons: {weapon_stats.get('totalWeapons', 0)}")
                                
                                # Print top 5 weapons by kill count
                                weapons = sorted(
                                    weapon_stats.get("weaponStats", []), 
                                    key=lambda w: w.get("killCount", 0), 
                                    reverse=True
                                )[:5]
                                
                                print("\nTop 5 weapons by kill count:")
                                for idx, weapon in enumerate(weapons, 1):
                                    print(f"{idx}. {weapon.get('weaponName', 'Unknown')} - Kills: {weapon.get('killCount', 0)}, Precision: {weapon.get('precisionKillCount', 0)}")
                            else:
                                print(f"Error fetching weapon stats: {weapon_stats.get('error')}")


# Run the main function if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main())

