#!/usr/bin/env python3
"""
Test script to debug manifest search functionality
"""

from desktop_manifest_helper import search_items_by_name, test_api_connection
import os

def main():
    # Test with environment API key first
    api_key = os.getenv("BUNGIE_API_KEY")
    
    if not api_key:
        api_key = input('Enter your API key: ')
    
    print('Testing connection...')
    result = test_api_connection(api_key)
    print('Connection result:', result)

    if result['status'] == 'connected':
        print('\nSearching for Gjallarhorn...')
        results = search_items_by_name('Gjallarhorn', api_key)
        print(f'Found {len(results)} results:')
        
        for i, item in enumerate(results[:3]):
            print(f'{i+1}. {item["name"]} - {item["type"]} ({item["tier_type"]})')
            print(f'   Hash: {item["hash"]}')
            print(f'   Damage Type: {item["damage_type"]}')
            print()
        
        # Test search for a more common weapon
        print('\nSearching for "Hand Cannon"...')
        results2 = search_items_by_name('Hand Cannon', api_key)
        print(f'Found {len(results2)} results containing "Hand Cannon"')
        
        for i, item in enumerate(results2[:5]):
            print(f'{i+1}. {item["name"]} - {item["type"]}')
    else:
        print('Connection failed, cannot test search')

if __name__ == "__main__":
    main()
