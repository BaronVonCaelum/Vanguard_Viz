#!/usr/bin/env python3
"""
Destiny 2 Manifest Database Manager

This script fetches Destiny 2 Manifest data and stores it in a SQLite database
for faster access, reduced API calls, and offline capabilities.
"""
import os
import asyncio
import sqlite3
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
import argparse

# Import our manifest component retrieval function
from manifest_helper import get_manifest_component

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DB_FILENAME = "destiny_manifest.db"
COMPONENTS_TO_FETCH = [
    "DestinyInventoryItemDefinition",
    "DestinyActivityDefinition",
    "DestinyClassDefinition",
    "DestinyDamageTypeDefinition"
]

def create_database() -> sqlite3.Connection:
    """
    Create and initialize the SQLite database for storing manifest data.
    Returns a connection to the database.
    """
    logger.info(f"Creating/connecting to database: {DB_FILENAME}")
    conn = sqlite3.connect(DB_FILENAME)
    
    # Create component manifest version tracking table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS manifest_versions (
        component_type TEXT PRIMARY KEY,
        version TEXT NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create inventory items table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS inventory_items (
        hash INTEGER PRIMARY KEY,
        json_data TEXT NOT NULL,
        name TEXT,
        description TEXT,
        icon TEXT,
        item_type TEXT,
        tier_type TEXT,
        class_type INTEGER,
        damage_type INTEGER,
        equippable BOOLEAN,
        bucket_hash INTEGER
    )
    ''')
    
    # Create activities table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS activities (
        hash INTEGER PRIMARY KEY,
        json_data TEXT NOT NULL,
        name TEXT,
        description TEXT,
        activity_type_hash INTEGER,
        destination_hash INTEGER,
        place_hash INTEGER,
        activity_mode_hash INTEGER,
        is_playlist BOOLEAN
    )
    ''')
    
    # Create classes table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        hash INTEGER PRIMARY KEY,
        json_data TEXT NOT NULL,
        name TEXT,
        class_type INTEGER
    )
    ''')
    
    # Create damage types table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS damage_types (
        hash INTEGER PRIMARY KEY,
        json_data TEXT NOT NULL,
        name TEXT,
        description TEXT,
        icon TEXT,
        enum_value INTEGER
    )
    ''')
    
    conn.commit()
    return conn

async def fetch_and_store_component(
    conn: sqlite3.Connection,
    component_type: str,
    force_update: bool = False
) -> bool:
    """
    Fetch a specific manifest component and store it in the database.
    
    Args:
        conn: SQLite database connection
        component_type: The manifest component to fetch
        force_update: If True, update even if version hasn't changed
        
    Returns:
        True if the database was updated, False otherwise
    """
    logger.info(f"Processing component: {component_type}")
    
    # Step 1: Fetch the manifest component
    result = await get_manifest_component(component_type)
    
    if result.get("status") != "success":
        logger.error(f"Failed to retrieve {component_type}: {result.get('error')}")
        return False
    
    component_data = result.get("componentData", {})
    if not component_data:
        logger.warning(f"No data found for {component_type}")
        return False
    
    # Step 2: Store in database based on component type
    cursor = conn.cursor()
    
    # Check if we need to update based on manifest version
    # In a real implementation, we'd compare versions here
    # For now, we'll use the item count as a proxy for the version
    cursor.execute("SELECT * FROM manifest_versions WHERE component_type = ?", (component_type,))
    version_record = cursor.fetchone()
    
    # Generate a simple version identifier based on data size
    current_version = f"{len(component_data)}-{int(time.time())}"
    
    if version_record and not force_update:
        stored_version = version_record[1]
        # In a real implementation, compare actual version strings
        if stored_version.split('-')[0] == current_version.split('-')[0]:
            logger.info(f"{component_type} is already up to date (version: {stored_version})")
            return False
    
    # Step 3: Process and store the data
    if component_type == "DestinyInventoryItemDefinition":
        store_inventory_items(conn, component_data)
    elif component_type == "DestinyActivityDefinition":
        store_activities(conn, component_data)
    elif component_type == "DestinyClassDefinition":
        store_classes(conn, component_data)
    elif component_type == "DestinyDamageTypeDefinition":
        store_damage_types(conn, component_data)
    else:
        logger.warning(f"No specific storage handler for {component_type}, skipping")
        return False
    
    # Update the version record
    if version_record:
        cursor.execute(
            "UPDATE manifest_versions SET version = ?, last_updated = CURRENT_TIMESTAMP WHERE component_type = ?",
            (current_version, component_type)
        )
    else:
        cursor.execute(
            "INSERT INTO manifest_versions (component_type, version) VALUES (?, ?)",
            (component_type, current_version)
        )
    
    conn.commit()
    logger.info(f"Updated {component_type} in database (version: {current_version})")
    return True

def store_inventory_items(conn: sqlite3.Connection, items_data: Dict[str, Any]) -> None:
    """Store inventory item definitions in the database."""
    cursor = conn.cursor()
    
    # Delete existing data - in a more sophisticated implementation, you might do an incremental update
    cursor.execute("DELETE FROM inventory_items")
    
    # Process and insert items
    items = []
    for hash_str, item in items_data.items():
        # Convert string hash to integer
        item_hash = int(hash_str)
        
        # Extract fields we want to query directly
        display_props = item.get("displayProperties", {})
        name = display_props.get("name", "")
        description = display_props.get("description", "")
        icon = display_props.get("icon", "")
        
        # Other useful fields
        item_type = item.get("itemTypeDisplayName", "")
        tier_type = item.get("inventory", {}).get("tierTypeName", "")
        class_type = item.get("classType", -1)
        damage_type = item.get("defaultDamageType", 0)
        equippable = item.get("equippable", False)
        bucket_hash = item.get("inventory", {}).get("bucketTypeHash", 0)
        
        # Store the full JSON for complete data access
        json_data = json.dumps(item)
        
        items.append((
            item_hash, json_data, name, description, icon, 
            item_type, tier_type, class_type, damage_type, 
            equippable, bucket_hash
        ))
    
    # Batch insert for improved performance
    cursor.executemany(
        '''INSERT INTO inventory_items 
           (hash, json_data, name, description, icon, item_type, tier_type, 
            class_type, damage_type, equippable, bucket_hash) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        items
    )
    
    conn.commit()
    logger.info(f"Stored {len(items)} inventory items in database")

def store_activities(conn: sqlite3.Connection, activities_data: Dict[str, Any]) -> None:
    """Store activity definitions in the database."""
    cursor = conn.cursor()
    
    # Delete existing data
    cursor.execute("DELETE FROM activities")
    
    # Process and insert activities
    activities = []
    for hash_str, activity in activities_data.items():
        # Convert string hash to integer
        activity_hash = int(hash_str)
        
        # Extract fields
        display_props = activity.get("displayProperties", {})
        name = display_props.get("name", "")
        description = display_props.get("description", "")
        
        # Other useful fields
        activity_type_hash = activity.get("activityTypeHash", 0)
        destination_hash = activity.get("destinationHash", 0)
        place_hash = activity.get("placeHash", 0)
        activity_mode_hash = activity.get("activityModeHash", 0)
        is_playlist = activity.get("isPlaylist", False)
        
        # Store the full JSON
        json_data = json.dumps(activity)
        
        activities.append((
            activity_hash, json_data, name, description,
            activity_type_hash, destination_hash, place_hash,
            activity_mode_hash, is_playlist
        ))
    
    # Batch insert
    cursor.executemany(
        '''INSERT INTO activities 
           (hash, json_data, name, description, 
            activity_type_hash, destination_hash, place_hash,
            activity_mode_hash, is_playlist) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        activities
    )
    
    conn.commit()
    logger.info(f"Stored {len(activities)} activities in database")

def store_classes(conn: sqlite3.Connection, classes_data: Dict[str, Any]) -> None:
    """Store class definitions in the database."""
    cursor = conn.cursor()
    
    # Delete existing data
    cursor.execute("DELETE FROM classes")
    
    # Process and insert classes
    classes = []
    for hash_str, class_def in classes_data.items():
        # Convert string hash to integer
        class_hash = int(hash_str)
        
        # Extract fields
        display_props = class_def.get("displayProperties", {})
        name = display_props.get("name", "")
        class_type = class_def.get("classType", -1)
        
        # Store the full JSON
        json_data = json.dumps(class_def)
        
        classes.append((class_hash, json_data, name, class_type))
    
    # Batch insert
    cursor.executemany(
        "INSERT INTO classes (hash, json_data, name, class_type) VALUES (?, ?, ?, ?)", 
        classes
    )
    
    conn.commit()
    logger.info(f"Stored {len(classes)} classes in database")

def store_damage_types(conn: sqlite3.Connection, damage_types_data: Dict[str, Any]) -> None:
    """Store damage type definitions in the database."""
    cursor = conn.cursor()
    
    # Delete existing data
    cursor.execute("DELETE FROM damage_types")
    
    # Process and insert damage types
    damage_types = []
    for hash_str, damage_type in damage_types_data.items():
        # Convert string hash to integer
        damage_hash = int(hash_str)
        
        # Extract fields
        display_props = damage_type.get("displayProperties", {})
        name = display_props.get("name", "")
        description = display_props.get("description", "")
        icon = display_props.get("icon", "")
        enum_value = damage_type.get("enumValue", 0)
        
        # Store the full JSON
        json_data = json.dumps(damage_type)
        
        damage_types.append((damage_hash, json_data, name, description, icon, enum_value))
    
    # Batch insert
    cursor.executemany(
        '''INSERT INTO damage_types 
           (hash, json_data, name, description, icon, enum_value) 
           VALUES (?, ?, ?, ?, ?, ?)''', 
        damage_types
    )
    
    conn.commit()
    logger.info(f"Stored {len(damage_types)} damage types in database")

# Query functions for accessing stored data
def get_item_by_hash(conn: sqlite3.Connection, item_hash: int) -> Optional[Dict[str, Any]]:
    """Retrieve an item by its hash ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT json_data FROM inventory_items WHERE hash = ?", (item_hash,))
    result = cursor.fetchone()
    
    if result:
        return json.loads(result[0])
    return None

def search_items_by_name(conn: sqlite3.Connection, name_pattern: str) -> List[Dict[str, Any]]:
    """Search for items by name pattern."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT hash, name, item_type, tier_type FROM inventory_items WHERE name LIKE ?", 
        (f"%{name_pattern}%",)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "hash": row[0],
            "name": row[1],
            "itemType": row[2],
            "tierType": row[3]
        })
    
    return results

def get_items_by_type(conn: sqlite3.Connection, item_type: str) -> List[Dict[str, Any]]:
    """Get all items of a specific type."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT hash, name, tier_type FROM inventory_items WHERE item_type = ?", 
        (item_type,)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "hash": row[0],
            "name": row[1],
            "tierType": row[2]
        })
    
    return results

def get_weapons_by_damage_type(conn: sqlite3.Connection, damage_type: int) -> List[Dict[str, Any]]:
    """Get weapons of a specific damage type."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT i.hash, i.name, i.item_type, i.tier_type, d.name as damage_name
        FROM inventory_items i
        JOIN damage_types d ON i.damage_type = d.enum_value
        WHERE i.damage_type = ? AND i.item_type LIKE '%Weapon%'
        """, 
        (damage_type,)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "hash": row[0],
            "name": row[1],
            "itemType": row[2],
            "tierType": row[3],
            "damageName": row[4]
        })
    
    return results

def get_weapons_by_tier(conn: sqlite3.Connection, tier_type: str) -> List[Dict[str, Any]]:
    """Get weapons of a specific rarity tier (Common, Rare, Legendary, etc)."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT hash, name, item_type, tier_type
        FROM inventory_items
        WHERE tier_type = ? AND item_type LIKE '%Weapon%'
        ORDER BY name
        """, 
        (tier_type,)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "hash": row[0],
            "name": row[1],
            "itemType": row[2],
            "tierType": row[3]
        })
    
    return results

def get_class_items(conn: sqlite3.Connection, class_type: int) -> List[Dict[str, Any]]:
    """Get items for a specific class."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT hash, name, item_type, tier_type
        FROM inventory_items
        WHERE class_type = ? AND equippable = 1
        ORDER BY item_type, tier_type DESC
        """, 
        (class_type,)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "hash": row[0],
            "name": row[1],
            "itemType": row[2],
            "tierType": row[3]
        })
    
    return results

async def update_database(force_update: bool = False) -> None:
    """
    Update the database with the latest manifest data.
    
    Args:
        force_update: If True, update regardless of version
    """
    # Create the database if it doesn't exist
    conn = create_database()
    
    # Fetch and store each component
    for component_type in COMPONENTS_TO_FETCH:
        try:
            updated = await fetch_and_store_component(conn, component_type, force_update)
            if updated:
                logger.info(f"Updated {component_type}")
            else:
                logger.info(f"No update needed for {component_type}")
        except Exception as e:
            logger.error(f"Error updating {component_type}: {e}")
    
    # Close the connection when done
    conn.close()

def print_table(results: List[Dict[str, Any]], fields: List[str], title: str = None) -> None:
    """
    Print query results in a nice table format.
    """
    if not results:
        print("No results found")
        return
    
    if title:
        print(f"\n{title}")
        print("-" * len(title))
    
    # Calculate column widths
    widths = {}
    for field in fields:
        widths[field] = max(len(field), max(len(str(item.get(field, ""))) for item in results))
    
    # Print headers
    header = "  ".join(f"{field:{widths[field]}}" for field in fields)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for item in results:
        row = "  ".join(f"{str(item.get(field, '')):{widths[field]}}" for field in fields)
        print(row)

async def main():
    """
    Main function to demonstrate database creation and usage.
    """
    # Create a command-line argument parser
    parser = argparse.ArgumentParser(description="Destiny 2 Manifest Database Manager")
    
    # Add arguments
    parser.add_argument(
        "--update", 
        action="store_true", 
        help="Update the database with the latest manifest data"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force update even if versions match"
    )
    parser.add_argument(
        "--query", 
        choices=["examples", "search", "item", "type", "class", "damage", "tier"],
        help="Run specific queries on the database"
    )
    parser.add_argument(
        "--param", 
        help="Parameter for the query (e.g., item hash, search term, etc.)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to update if no arguments are provided
    if not any([args.update, args.query]):
        print("No action specified. Try --update or --query.")
        parser.print_help()
        return
    
    # Update the database if requested
    if args.update:
        print("Updating database with latest manifest data...")
        await update_database(args.force)
        print("Database update complete.")
    
    # Run queries if requested
    if args.query:
        # Check if the database exists
        if not Path(DB_FILENAME).exists():
            print(f"Database {DB_FILENAME} not found. Please run with --update first.")
            return
        
        # Connect to the database
        conn = sqlite3.connect(DB_FILENAME)
        
        try:
            # Run the requested query
            if args.query == "examples":
                run_example_queries(conn)
            elif args.query == "search" and args.param:
                results = search_items_by_name(conn, args.param)
                print_table(
                    results,
                    ["hash", "name", "itemType", "tierType"],
                    f"Search results for '{args.param}'"
                )
            elif args.query == "item" and args.param:
                item = get_item_by_hash(conn, int(args.param))
                if item:
                    print(f"\nDetails for item with hash {args.param}:")
                    print(f"Name: {item.get('displayProperties', {}).get('name', 'Unknown')}")
                    print(f"Type: {item.get('itemTypeDisplayName', 'Unknown')}")
                    print(f"Tier: {item.get('inventory', {}).get('tierTypeName', 'Unknown')}")
                    print(f"Description: {item.get('displayProperties', {}).get('description', '')}")
                else:
                    print(f"No item found with hash {args.param}")
            elif args.query == "type" and args.param:
                results = get_items_by_type(conn, args.param)
                print_table(
                    results,
                    ["hash", "name", "tierType"],
                    f"Items of type '{args.param}'"
                )
            elif args.query == "class" and args.param:
                results = get_class_items(conn, int(args.param))
                print_table(
                    results,
                    ["hash", "name", "itemType", "tierType"],
                    f"Items for class type {args.param}"
                )
            elif args.query == "damage" and args.param:
                results = get_weapons_by_damage_type(conn, int(args.param))
                print_table(
                    results,
                    ["hash", "name", "itemType", "tierType", "damageName"],
                    f"Weapons with damage type {args.param}"
                )
            elif args.query == "tier" and args.param:
                results = get_weapons_by_tier(conn, args.param)
                print_table(
                    results,
                    ["hash", "name", "itemType", "tierType"],
                    f"Weapons of tier '{args.param}'"
                )
            else:
                print("Invalid query or missing parameter. Use --help for more information.")
        finally:
            # Close the connection
            conn.close()

def run_example_queries(conn: sqlite3.Connection) -> None:
    """Run example queries to demonstrate database usage."""
    print("\nRunning example queries to demonstrate database usage...\n")
    
    # Example 1: Search for items containing "Gjallarhorn"
    print("Example 1: Searching for items containing 'Gjallarhorn'")
    gjallarhorn_results = search_items_by_name(conn, "Gjallarhorn")
    print_table(gjallarhorn_results, ["hash", "name", "itemType", "tierType"])
    
    # Example 2: Get all Hand Cannons
    print("\nExample 2: Getting all items of type 'Hand Cannon'")
    hand_cannons = get_items_by_type(conn, "Hand Cannon")
    print_table(hand_cannons[:10], ["hash", "name", "tierType"])
    print(f"...and {len(hand_cannons) - 10} more Hand Cannons" if len(hand_cannons) > 10 else "")
    
    # Example 3: Get Solar damage weapons
    print("\nExample 3: Getting Solar damage weapons")
    solar_weapons = get_weapons_by_damage_type(conn, 1)  # 1 is typically Solar
    print_table(solar_weapons[:10], ["hash", "name", "itemType", "damageName"])
    print(f"...and {len(solar_weapons) - 10} more Solar weapons" if len(solar_weapons) > 10 else "")
    
    # Example 4: Get Exotic tier weapons
    print("\nExample 4: Getting Exotic tier weapons")
    exotic_weapons = get_weapons_by_tier(conn, "Exotic")
    print_table(exotic_weapons[:10], ["hash", "name", "itemType"])
    print(f"...and {len(exotic_weapons) - 10} more Exotic weapons" if len(exotic_weapons) > 10 else "")
    
    # Get database stats
    cursor = conn.cursor()
    
    # Get component counts
    print("\nDatabase Statistics:")
    cursor.execute("SELECT COUNT(*) FROM inventory_items")
    item_count = cursor.fetchone()[0]
    print(f"- Inventory Items: {item_count}")
    
    cursor.execute("SELECT COUNT(*) FROM activities")
    activity_count = cursor.fetchone()[0]
    print(f"- Activities: {activity_count}")
    
    cursor.execute("SELECT COUNT(*) FROM classes")
    class_count = cursor.fetchone()[0]
    print(f"- Classes: {class_count}")
    
    cursor.execute("SELECT COUNT(*) FROM damage_types")
    damage_count = cursor.fetchone()[0]
    print(f"- Damage Types: {damage_count}")
    
    # Get database versions
    cursor.execute("SELECT component_type, version, last_updated FROM manifest_versions")
    versions = cursor.fetchall()
    
    print("\nComponent Versions:")
    for component, version, last_updated in versions:
        print(f"- {component}: {version} (updated: {last_updated})")

if __name__ == "__main__":
    asyncio.run(main())
