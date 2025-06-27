#!/usr/bin/env python3
"""
Synchronous Manifest Helper for Vanguard Viz Desktop
Provides synchronous manifest data access for the desktop application.
"""

import os
import json
import time
import requests
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables for API key
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BUNGIE_API_KEY = os.getenv("BUNGIE_API_KEY")
MANIFEST_CACHE_DIR = Path("manifest_cache")
MANIFEST_CACHE_DIR.mkdir(exist_ok=True)

class DesktopManifestHelper:
    """Synchronous manifest helper for desktop application"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or BUNGIE_API_KEY
        self.cache_dir = MANIFEST_CACHE_DIR
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the API connection"""
        try:
            url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "Response" in data:
                    return {
                        "status": "connected",
                        "version": data.get("Response", {}).get("version", "unknown"),
                        "message": "Successfully connected to Bungie API"
                    }
            
            return {
                "status": "error",
                "message": f"API returned status code: {response.status_code}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }
    
    def get_manifest_info(self) -> Dict[str, Any]:
        """Get manifest information from Bungie API"""
        try:
            url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                return {"error": f"API returned status code: {response.status_code}"}
            
            data = response.json()
            if "Response" not in data:
                return {"error": "Invalid API response"}
            
            manifest_data = data["Response"]
            return {
                "version": manifest_data.get("version", "unknown"),
                "jsonWorldContentPaths": manifest_data.get("jsonWorldComponentContentPaths", {}).get("en", {})
            }
            
        except Exception as e:
            return {"error": f"Failed to get manifest info: {str(e)}"}
    
    def download_manifest_component(self, component_type: str, force_update: bool = False) -> Dict[str, Any]:
        """Download a specific manifest component"""
        try:
            # Get manifest info
            manifest_info = self.get_manifest_info()
            if "error" in manifest_info:
                return manifest_info
            
            # Get component path
            content_paths = manifest_info.get("jsonWorldContentPaths", {})
            if component_type not in content_paths:
                return {"error": f"Component type {component_type} not found"}
            
            component_path = content_paths[component_type]
            component_url = f"https://www.bungie.net{component_path}"
            
            # Check cache
            cache_file = self.cache_dir / f"{component_type}_{manifest_info['version']}.json"
            
            if cache_file.exists() and not force_update:
                # Check if cache is still valid (less than 7 days old)
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < 604800:  # 7 days
                    logger.info(f"Using cached {component_type}")
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            return {"status": "success", "data": json.load(f), "cached": True}
                    except Exception as e:
                        logger.warning(f"Failed to load cache: {e}, downloading fresh data")
            
            # Download component
            logger.info(f"Downloading {component_type}...")
            response = self.session.get(component_url, timeout=300)
            
            if response.status_code != 200:
                return {"error": f"Failed to download component: {response.status_code}"}
            
            try:
                component_data = response.json()
            except json.JSONDecodeError:
                return {"error": "Failed to parse component JSON"}
            
            # Save to cache
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(component_data, f)
                logger.info(f"Downloaded and cached {component_type}")
            except Exception as e:
                logger.warning(f"Failed to cache data: {e}")
            
            return {"status": "success", "data": component_data, "cached": False}
            
        except Exception as e:
            return {"error": f"Failed to download component: {str(e)}"}
    
    def get_inventory_items(self, filters: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get inventory items with optional filtering"""
        try:
            result = self.download_manifest_component("DestinyInventoryItemDefinition")
            if "error" in result:
                return []
            
            items_data = result["data"]
            items = []
            count = 0
            
            for item_hash, item_data in items_data.items():
                # Skip items without names
                display_props = item_data.get("displayProperties", {})
                if not display_props.get("name"):
                    continue
                
                # Apply filters if provided
                if filters:
                    # Filter by damage type (weapons only)
                    if "damage_type" in filters:
                        damage_types = filters["damage_type"]
                        item_damage = item_data.get("defaultDamageType", 0)
                        if item_damage not in damage_types:
                            continue
                    
                    # Filter by item type
                    if "item_type" in filters:
                        item_type = item_data.get("itemTypeDisplayName", "")
                        if filters["item_type"].lower() not in item_type.lower():
                            continue
                    
                    # Filter by tier type
                    if "tier_type" in filters:
                        tier_types = filters["tier_type"]
                        inventory = item_data.get("inventory", {})
                        item_tier = inventory.get("tierType", 0)
                        if item_tier not in tier_types:
                            continue
                
                # Transform item data
                inventory = item_data.get("inventory", {})
                
                transformed_item = {
                    "hash": item_hash,
                    "name": display_props.get("name", ""),
                    "description": display_props.get("description", ""),
                    "icon": f"https://www.bungie.net{display_props.get('icon', '')}" if display_props.get("hasIcon") else "",
                    "type": item_data.get("itemTypeDisplayName", ""),
                    "tier_type": inventory.get("tierTypeName", ""),
                    "rarity": inventory.get("tierType", 0),
                    "class_type": item_data.get("classType", 3),
                    "damage_type": item_data.get("defaultDamageType", 0),
                    "equippable": item_data.get("equippable", False),
                    "bucket_hash": inventory.get("bucketTypeHash", 0)
                }
                
                items.append(transformed_item)
                count += 1
                
                # Apply limit if specified
                if limit and count >= limit:
                    break
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting inventory items: {e}")
            return []
    
    def search_items(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for items by name"""
        try:
            # First try to get weapons only for faster search
            weapons_filter = {"damage_type": [1, 2, 3, 4, 6, 7]}  # Valid weapon damage types
            items = self.get_inventory_items(filters=weapons_filter, limit=2000)
            
            search_term = search_term.lower()
            results = []
            
            for item in items:
                if search_term in item["name"].lower():
                    results.append(item)
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching items: {e}")
            return []
    
    def get_user_profile(self, bungie_name: str, bungie_code: str) -> Dict[str, Any]:
        """Get user profile by Bungie name and code"""
        try:
            # Search for user
            search_url = "https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayerByBungieName/-1/"
            search_payload = {
                "displayName": bungie_name,
                "displayNameCode": bungie_code
            }
            
            response = self.session.post(search_url, json=search_payload, timeout=30)
            
            if response.status_code != 200:
                return {"error": f"Search failed: {response.status_code}"}
            
            search_data = response.json()
            if "Response" not in search_data or not search_data["Response"]:
                return {"error": "User not found"}
            
            # Get first result
            membership = search_data["Response"][0]
            
            # Get profile
            profile_url = f"https://www.bungie.net/Platform/Destiny2/{membership['membershipType']}/Profile/{membership['membershipId']}/"
            profile_params = {"components": "100,200"}  # Profiles and Characters
            
            response = self.session.get(profile_url, params=profile_params, timeout=30)
            
            if response.status_code != 200:
                return {"error": f"Profile fetch failed: {response.status_code}"}
            
            profile_data = response.json()
            if "Response" not in profile_data:
                return {"error": "Invalid profile response"}
            
            return {
                "status": "success",
                "membership": membership,
                "profile": profile_data["Response"]
            }
            
        except Exception as e:
            return {"error": f"Failed to get user profile: {str(e)}"}
    
    def get_weapon_stats(self, membership_type: int, membership_id: str, character_id: str = "0") -> Dict[str, Any]:
        """Get weapon statistics for a character"""
        try:
            # Get unique weapons stats
            stats_url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Account/{membership_id}/Character/{character_id}/Stats/UniqueWeapons/"
            
            response = self.session.get(stats_url, timeout=30)
            
            if response.status_code != 200:
                return {"error": f"Weapon stats fetch failed: {response.status_code}"}
            
            stats_data = response.json()
            if "Response" not in stats_data:
                return {"error": "Invalid weapon stats response"}
            
            # Transform weapon stats
            weapons = []
            for weapon in stats_data["Response"].get("weapons", []):
                values = weapon.get("values", {})
                weapon_data = {
                    "reference_id": weapon.get("referenceId", "0"),
                    "name": "Unknown Weapon",  # Would need manifest lookup
                    "type": "Unknown",
                    "kills": values.get("uniqueWeaponKills", {}).get("basic", {}).get("value", 0),
                    "precision_kills": values.get("uniqueWeaponPrecisionKills", {}).get("basic", {}).get("value", 0),
                    "usage_time": values.get("uniqueWeaponKillsPrecisionKills", {}).get("basic", {}).get("value", 0)
                }
                weapons.append(weapon_data)
            
            return {
                "status": "success",
                "weapons": weapons
            }
            
        except Exception as e:
            return {"error": f"Failed to get weapon stats: {str(e)}"}

# Global instance for easy access
_manifest_helper = None

def get_helper(api_key: str = None) -> DesktopManifestHelper:
    """Get or create manifest helper instance"""
    global _manifest_helper
    
    if _manifest_helper is None or (api_key and api_key != _manifest_helper.api_key):
        _manifest_helper = DesktopManifestHelper(api_key)
    
    return _manifest_helper

# Convenience functions for desktop app
def test_api_connection(api_key: str = None) -> Dict[str, Any]:
    """Test API connection"""
    return get_helper(api_key).test_connection()

def search_items_by_name(search_term: str, api_key: str = None) -> List[Dict[str, Any]]:
    """Search items by name"""
    return get_helper(api_key).search_items(search_term)

def get_user_profile(bungie_name: str, bungie_code: str, api_key: str = None) -> Dict[str, Any]:
    """Get user profile"""
    return get_helper(api_key).get_user_profile(bungie_name, bungie_code)

def get_weapon_usage_stats(membership_type: int, membership_id: str, character_id: str = "0", api_key: str = None) -> Dict[str, Any]:
    """Get weapon usage statistics"""
    return get_helper(api_key).get_weapon_stats(membership_type, membership_id, character_id)

def get_manifest_component(component_type: str, api_key: str = None) -> Dict[str, Any]:
    """Get manifest component"""
    result = get_helper(api_key).download_manifest_component(component_type)
    if "error" in result:
        return {"status": "error", "error": result["error"]}
    
    return {
        "status": "success",
        "componentType": component_type,
        "componentData": result["data"],
        "cached": result.get("cached", False)
    }

if __name__ == "__main__":
    # Test the manifest helper
    helper = DesktopManifestHelper()
    
    print("Testing API connection...")
    result = helper.test_connection()
    print(f"Connection test: {result}")
    
    if result["status"] == "connected":
        print("\nGetting manifest info...")
        manifest_info = helper.get_manifest_info()
        print(f"Manifest version: {manifest_info.get('version', 'unknown')}")
        
        print("\nSearching for 'Gjallarhorn'...")
        search_results = helper.search_items("Gjallarhorn")
        for item in search_results[:5]:  # Show first 5 results
            print(f"- {item['name']} ({item['type']})")
