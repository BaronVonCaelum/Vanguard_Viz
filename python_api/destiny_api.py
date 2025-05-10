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


# Run the main function if this script is executed directly
if __name__ == "__main__":
    asyncio.run(main())

