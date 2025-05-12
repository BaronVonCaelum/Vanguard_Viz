"""
Bungie.net API Client for the Vanguard Viz Web Data Connector
This module provides functions to interact with the Bungie.net API using BungIO
"""
import os
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta

# For environment variables
from dotenv import load_dotenv

# BungIO imports
from bungio import Client
from bungio.models import (
    DestinyComponentType,
    BungieMembershipType,
    GroupsForMemberFilter,
    DestinyStatsGroupType,
    PeriodType
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


async def get_player_stats(
    membership_type: int, 
    destiny_membership_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get a player's Destiny 2 stats.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        start_date: Optional start date for filtering stats
        end_date: Optional end date for filtering stats
        
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
        
        # Add date parameters if specified
        date_params = ""
        if start_date:
            date_params += f"&daystart={start_date.strftime('%Y-%m-%d')}"
        if end_date:
            date_params += f"&dayend={end_date.strftime('%Y-%m-%d')}"
            
        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Stats/?groups={groups_str}{date_params}"
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


async def get_manifest_component(component_type: str = "DestinyInventoryItemDefinition") -> Dict[str, Any]:
    """
    Retrieves a specific component from the Destiny 2 Manifest.
    
    Args:
        component_type: The manifest component to retrieve. Default is "DestinyInventoryItemDefinition".
                       Other examples include "DestinyClassDefinition", "DestinySandboxPerkDefinition", etc.
        
    Returns:
        Dict containing the requested manifest component data
    """
    try:
        # Step 1: Get the manifest
        manifest_url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Make request to get the manifest paths
        async with aiohttp.ClientSession() as session:
            async with session.get(manifest_url, headers=headers) as response:
                manifest_response = await response.json()
                if response.status != 200 or "Response" not in manifest_response:
                    logger.error(f"Failed to get manifest: {manifest_response.get('Message', 'Unknown error')}")
                    return {"error": "Failed to retrieve Destiny 2 manifest"}
                
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
        logger.info(f"Fetching manifest component: {component_type}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(component_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get component data: {response.status}")
                        return {"error": f"Failed to retrieve component data: {response.status}"}
                    
                    # Parse the response - can be large so we handle with care
                    component_data = await response.json()
                    
                    logger.info(f"Successfully retrieved {component_type} with {len(component_data)} entries")
                    return {
                        "status": "success",
                        "componentType": component_type,
                        "componentData": component_data
                    }
        except Exception as e:
            logger.error(f"Error fetching component data: {e}")
            return {"error": f"Failed to retrieve or parse component data: {e}"}
    
    except BungieException as e:
        logger.error(f"Bungie API error: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving manifest component: {e}")
        return {"error": f"Unexpected error: {e}"}


async def get_weapon_usage_stats(
    membership_type: int, 
    destiny_membership_id: str, 
    character_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get detailed weapon usage statistics for a specific character, including metadata from the manifest.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        character_id: The character ID for which to retrieve weapon stats
        start_date: Optional start date for filtering stats
        end_date: Optional end date for filtering stats
        
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
        # Get item definitions using our new method
        item_definitions_response = await get_manifest_component("DestinyInventoryItemDefinition")
        
        # Extract the item definitions if successful
        item_definitions = {}
        if "status" in item_definitions_response and item_definitions_response["status"] == "success":
            item_definitions = item_definitions_response.get("componentData", {})
        else:
            logger.warning(f"Failed to retrieve item definitions: {item_definitions_response.get('error', 'Unknown error')}")
            # We'll proceed without item definitions if there's an issue
        
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


async def get_activity_history(
    membership_type: int,
    destiny_membership_id: str,
    character_id: str,
    mode: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 0,
    count: int = 25
) -> Dict[str, Any]:
    """
    Get a player's activity history with optional date filtering.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        character_id: The character ID for which to retrieve activity history
        mode: Optional activity mode filter (None returns all activities)
        start_date: Optional start date for filtering activities
        end_date: Optional end date for filtering activities
        page: Page number for pagination
        count: Number of activities to return per page
        
    Returns:
        Dict containing activity history data
    """
    try:
        # Build the URL for activity history request
        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/Activities/"
        
        # Add query parameters
        params = []
        if mode is not None:
            params.append(f"mode={mode}")
        if page is not None:
            params.append(f"page={page}")
        if count is not None:
            params.append(f"count={count}")
            
        # Add params to URL if any exist
        if params:
            url += "?" + "&".join(params)
            
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create a new session for the request
        activities_data = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                activities_response = await response.json()
                if response.status == 200 and "Response" in activities_response:
                    activities_data = activities_response.get("Response", {})
        
        # Filter by date if specified
        if start_date or end_date:
            filtered_activities = []
            
            if "activities" in activities_data:
                for activity in activities_data.get("activities", []):
                    # Get the activity date
                    period = activity.get("period", "")
                    if period:
                        # Parse the date from the period string
                        activity_date = datetime.strptime(period, "%Y-%m-%dT%H:%M:%SZ")
                        
                        # Check if within date range
                        if start_date and activity_date < start_date:
                            continue
                        if end_date and activity_date > end_date:
                            continue
                            
                        # If we reach here, the activity is within the date range
                        filtered_activities.append(activity)
                
                # Replace the activities with the filtered list
                activities_data["activities"] = filtered_activities
        
        # Transform the data for Tableau
        tableau_data = transform_activities_for_tableau(activities_data)
        
        return {
            "status": "success",
            "activities": activities_data,
            "tableauData": tableau_data,
            "totalActivities": len(activities_data.get("activities", []))
        }
    
    except BungieException as e:
        logger.error(f"Bungie API error getting activity history: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error getting activity history: {e}")
        return {"error": f"Unexpected error: {e}"}


async def get_aggregate_activity_stats(
    membership_type: int,
    destiny_membership_id: str,
    character_id: str
) -> Dict[str, Any]:
    """
    Get aggregate activity statistics for a character.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        character_id: The character ID for which to retrieve activity stats
        
    Returns:
        Dict containing aggregate activity statistics
    """
    try:
        # Build the URL for aggregate stats request
        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/AggregateActivityStats/"
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create a new session for the request
        aggregate_data = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                aggregate_response = await response.json()
                if response.status == 200 and "Response" in aggregate_response:
                    aggregate_data = aggregate_response.get("Response", {})
        
        # Transform the data for Tableau
        tableau_data = transform_aggregate_stats_for_tableau(aggregate_data)
        
        return {
            "status": "success",
            "aggregateStats": aggregate_data,
            "tableauData": tableau_data
        }
    
    except BungieException as e:
        logger.error(f"Bungie API error getting aggregate stats: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error getting aggregate stats: {e}")
        return {"error": f"Unexpected error: {e}"}


async def get_historical_stats_with_period(
    membership_type: int,
    destiny_membership_id: str,
    character_id: str,
    period_type: PeriodType = PeriodType.ALLTIME,
    modes: Optional[List[int]] = None,
    groups: Optional[List[int]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get historical stats for a character with period filtering.
    
    Args:
        membership_type: The player's membership type (e.g., BungieMembershipType.STEAM)
        destiny_membership_id: The player's Destiny membership ID
        character_id: The character ID for which to retrieve stats (0 for account-wide)
        period_type: The period type to retrieve (Daily, AllTime, Activity)
        modes: Optional list of activity modes to include
        groups: Optional list of stat groups to include
        start_date: Optional start date for filtering daily stats
        end_date: Optional end date for filtering daily stats
        
    Returns:
        Dict containing historical stats
    """
    try:
        # Build the URL for historical stats request
        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{destiny_membership_id}/Character/{character_id}/Stats/"
        
        # Add query parameters
        params = []
        
        # Add period type
        if period_type:
            params.append(f"periodType={period_type.value}")
            
        # Add modes if specified
        if modes:
            modes_str = ",".join(str(m) for m in modes)
            params.append(f"modes={modes_str}")
            
        # Add groups if specified
        if groups:
            groups_str = ",".join(str(g) for g in groups)
            params.append(f"groups={groups_str}")
            
        # Add date range if period type is daily
        if period_type == PeriodType.DAILY:
            if start_date:
                params.append(f"daystart={start_date.strftime('%Y-%m-%d')}")
            if end_date:
                params.append(f"dayend={end_date.strftime('%Y-%m-%d')}")
        
        # Add params to URL if any exist
        if params:
            url += "?" + "&".join(params)
            
        headers = {
            "X-API-Key": BUNGIE_API_KEY
        }
        
        # Create a new session for the request
        stats_data = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                stats_response = await response.json()
                if response.status == 200 and "Response" in stats_response:
                    stats_data = stats_response.get("Response", {})
        
        # Transform the data for Tableau
        tableau_data = transform_historical_stats_for_tableau(stats_data, period_type)
        
        return {
            "status": "success",
            "historicalStats": stats_data,
            "tableauData": tableau_data
        }
    
    except BungieException as e:
        logger.error(f"Bungie API error getting historical stats: {e}")
        return {"error": f"Bungie API error: {e}"}
    
    except Exception as e:
        logger.error(f"Unexpected error getting historical stats: {e}")
        return {"error": f"Unexpected error: {e}"}


# Data transformation functions for Tableau

def transform_activities_for_tableau(activities_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform activity history data into a format suitable for Tableau.
    
    Args:
        activities_data: Activity history data from the Bungie API
        
    Returns:
        List of dicts with flattened activity data for Tableau
    """
    tableau_data = []
    
    for activity in activities_data.get("activities", []):
        # Basic activity info
        activity_entry = {
            "instanceId": activity.get("activityDetails", {}).get("instanceId", ""),
            "activityDate": activity.get("period", ""),
            "activityHash": activity.get("activityDetails", {}).get("referenceId", 0),
            "activityName": activity.get("activityDetails", {}).get("displayProperties", {}).get("name", "Unknown Activity"),
            "activityMode": activity.get("activityDetails", {}).get("mode", 0),
            "activityModeType": activity.get("activityDetails", {}).get("modeType", 0),
            "isPrivate": activity.get("activityDetails", {}).get("isPrivate", False),
            "completed": activity.get("values", {}).get("completed", {}).get("basic", {}).get("value", 0),
            "timePlayedSeconds": activity.get("values", {}).get("timePlayedSeconds", {}).get("basic", {}).get("value", 0),
            "kills": activity.get("values", {}).get("kills", {}).get("basic", {}).get("value", 0),
            "deaths": activity.get("values", {}).get("deaths", {}).get("basic", {}).get("value", 0),
            "assists": activity.get("values", {}).get("assists", {}).get("basic", {}).get("value", 0),
            "score": activity.get("values", {}).get("score", {}).get("basic", {}).get("value", 0),
            "standing": activity.get("values", {}).get("standing", {}).get("basic", {}).get("value", 0)
        }
        tableau_data.append(activity_entry)
    
    return tableau_data


def transform_aggregate_stats_for_tableau(aggregate_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform aggregate stats data into a format suitable for Tableau.
    
    Args:
        aggregate_data: Aggregate stats data from the Bungie API
        
    Returns:
        List of dicts with flattened stats data for Tableau
    """
    tableau_data = []
    
    for activity in aggregate_data.get("activities", []):
        stats_entry = {
            "activityHash": activity.get("activityHash", 0),
            "activityName": activity.get("activityName", "Unknown"),
        }
        
        # Add all values from the activity's values dictionary
        values = activity.get("values", {})
        for stat_name, stat_data in values.items():
            if "basic" in stat_data:
                stats_entry[stat_name] = stat_data["basic"].get("value", 0)
        
        tableau_data.append(stats_entry)
    
    return tableau_data


def transform_historical_stats_for_tableau(stats_data: Dict[str, Any], period_type: PeriodType) -> List[Dict[str, Any]]:
    """
    Transform historical stats data into a format suitable for Tableau.
    
    Args:
        stats_data: Historical stats data from the Bungie API
        period_type: The period type of the stats (daily, all time, etc.)
        
    Returns:
        List of dicts with flattened stats data for Tableau
    """
    tableau_data = []
    
    # Handle different period types differently
    if period_type == PeriodType.DAILY:
        # For daily stats, create an entry for each day
        for mode_key, mode_data in stats_data.items():
            for day, day_stats in mode_data.get("daily", {}).items():
                entry = {
                    "date": day,
                    "mode": mode_key
                }
                
                # Add all stat values for this day
                for stat_name, stat_data in day_stats.get("values", {}).items():
                    if "basic" in stat_data:
                        entry[stat_name] = stat_data["basic"].get("value", 0)
                
                tableau_data.append(entry)
    else:
        # For all time or other period types, create a single entry per mode
        for mode_key, mode_data in stats_data.items():
            if "allTime" in mode_data:
                entry = {
                    "mode": mode_key
                }
                
                # Add all stat values for this mode
                for stat_name, stat_data in mode_data["allTime"].items():
                    if "basic" in stat_data:
                        entry[stat_name] = stat_data["basic"].get("value", 0)
                
                tableau_data.append(entry)
    
    return tableau_data


async def main():
    """
    Main function to test the API client
    """
    print("Testing Bungie API connection...")
    # Test the API connection
    connection_test = await test_api_connection()
    print(f"Connection test result: {connection_test}")

    # Test the manifest component retrieval
    print("\nTesting manifest component retrieval...")
    inventory_items = await get_manifest_component("DestinyInventoryItemDefinition")
    if "status" in inventory_items and inventory_items["status"] == "success":
        component_data = inventory_items.get("componentData", {})
        print(f"Successfully retrieved inventory item definitions with {len(component_data)} entries")
        
        # Print a sample item to demonstrate the data structure
        if component_data:
            sample_hash = next(iter(component_data))
            sample_item = component_data[sample_hash]
            print("\nSample Item:")
            print(f"Hash: {sample_hash}")
            print(f"Name: {sample_item.get('displayProperties', {}).get('name', 'Unknown')}")
            print(f"Type: {sample_item.get('itemTypeDisplayName', 'Unknown')}")
            print(f"Tier: {sample_item.get('inventory', {}).get('tierTypeName', 'Unknown')}")
    else:
        print(f"Error retrieving inventory items: {inventory_items.get('error', 'Unknown error')}")
    
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

