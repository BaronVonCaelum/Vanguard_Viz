#!/usr/bin/env python3
"""
Simple test script for retrieving Destiny 2 Manifest components.
This avoids dependencies on other parts of the module that might have issues.
"""
import asyncio
import sys
import os

# Import the get_manifest_component function from our standalone helper
from manifest_helper import get_manifest_component

async def test_manifest_component():
    """Test basic manifest component retrieval"""
    print("Testing Destiny 2 Manifest Component Retrieval")
    print("=============================================\n")
    
    print("Retrieving Destiny Inventory Item Definitions...")
    result = await get_manifest_component("DestinyInventoryItemDefinition")
    
    if result.get("status") == "success":
        component_data = result.get("componentData", {})
        count = len(component_data)
        print(f"Success! Retrieved {count} inventory item definitions")
        
        # Display a sample item if we have data
        if count > 0:
            sample_hash = next(iter(component_data))
            sample_item = component_data[sample_hash]
            print("\nSample Item:")
            print(f"Hash: {sample_hash}")
            name = sample_item.get('displayProperties', {}).get('name', 'Unknown')
            print(f"Name: {name}")
            item_type = sample_item.get('itemTypeDisplayName', 'Unknown')
            print(f"Type: {item_type}")
            
            return True
    else:
        error_msg = result.get('error', 'Unknown error')
        print(f"Error retrieving inventory items: {error_msg}")
        return False
        
    return False

if __name__ == "__main__":
    success = asyncio.run(test_manifest_component())
    if success:
        print("\nTest completed successfully!")
        sys.exit(0)
    else:
        print("\nTest failed!")
        sys.exit(1)

