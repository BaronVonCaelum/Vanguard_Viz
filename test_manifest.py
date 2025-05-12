#!/usr/bin/env python3
"""
Test script for retrieving Destiny 2 Manifest components.
This script demonstrates how to fetch and use the Destiny 2 Manifest data
through the get_manifest_component function.
"""
import asyncio
import json
from python_api.destiny_api import get_manifest_component

async def test_inventory_items():
    """Test retrieving inventory item definitions from the manifest"""
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
            print(f"Tier: {sample_item.get('inventory', {}).get('tierTypeName', 'Unknown')}")
            print(f"Description: {sample_item.get('displayProperties', {}).get('description', 'No description')}")
            
            # Check if it has an icon
            icon = sample_item.get('displayProperties', {}).get('icon', '')
            if icon:
                print(f"Icon URL: https://www.bungie.net{icon}")
            
            return True
    else:
        print(f"Error retrieving inventory items: {result.get('error', 'Unknown error')}")
        return False

async def test_activity_definitions():
    """Test retrieving activity definitions from the manifest"""
    print("\nRetrieving Destiny Activity Definitions...")
    result = await get_manifest_component("DestinyActivityDefinition")
    
    if result.get("status") == "success":
        component_data = result.get("componentData", {})
        print(f"Successfully retrieved {len(component_data)} activity definitions")
        
        # Display a sample activity
        if component_data:
            sample_hash = next(iter(component_data))
            sample_activity = component_data[sample_hash]
            print("\nSample Activity Details:")
            print(f"Hash: {sample_hash}")
            print(f"Name: {sample_activity.get('displayProperties', {}).get('name', 'Unknown')}")
            print(f"Description: {sample_activity.get('displayProperties', {}).get('description', 'No description')}")
            print(f"Activity Type: {sample_activity.get('activityTypeHash', 'Unknown')}")
            
            return True
    else:
        print(f"Error retrieving activity definitions: {result.get('error', 'Unknown error')}")
        return False

async def main():
    """Main test function"""
    print("Testing Destiny 2 Manifest Component Retrieval")
    print("=============================================\n")
    
    # Test inventory items
    items_success = await test_inventory_items()
    
    # Test activity definitions
    activities_success = await test_activity_definitions()
    
    # Summary
    print("\nTest Summary:")
    print(f"Inventory Items Test: {'SUCCESS' if items_success else 'FAILED'}")
    print(f"Activity Definitions Test: {'SUCCESS' if activities_success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())

