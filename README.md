# Vanguard Viz Desktop

A standalone desktop application for Destiny 2 data analytics and visualization.

## Overview

Vanguard Viz Desktop is a Python-based GUI application that provides Destiny 2 players with powerful analytics tools for their gameplay data. No web server or browser required!

## Features

- **Weapon Usage Statistics** - Track kills, precision kills, and usage time for all your weapons
- **Activity History** - Analyze your PvE and PvP activity performance
- **Manifest Data Browsing** - Search and explore Destiny 2's weapon and activity database
- **Data Export** - Export your data to JSON for further analysis
- **Offline Caching** - Manifest data is cached locally for faster access
- **User-Friendly Interface** - Clean, tabbed interface built with tkinter

## Installation

### Option 1: Download Executable (Recommended)
1. Download the latest release from the Releases page
2. Extract `VanguardViz.exe` from the zip file
3. Run the executable - no installation required!

### Option 2: Run from Source
1. Install Python 3.8 or newer
2. Clone this repository
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python vanguard_viz_desktop.py`

## Setup

### Getting Your Bungie API Key
1. Go to https://www.bungie.net/en/Application
2. Sign in with your Bungie account
3. Click "Create New App"
4. Fill out the form:
   - Application Name: "Vanguard Viz Desktop"
   - Website: (can be left blank)
   - Application Status: "Private"
   - OAuth Client Type: "Not Applicable"
5. Copy the API Key from your application page

### First Run
1. Launch Vanguard Viz Desktop
2. Go to the Configuration tab
3. Enter your Bungie API key
4. Enter your Bungie name and code (e.g., "Guardian#1234")
5. Click "Test Connection" to verify your setup
6. Start collecting your data!

## Usage

### Data Collection
1. Configure your API key and user information
2. Select which data types to collect (weapons, activities, stats)
3. Click "Collect All Data" to gather your information
4. View results in the Data Collection tab

### Analysis
1. Use the Analysis tab to generate reports
2. View top weapons by kills
3. Analyze damage type preferences
4. Export data for external analysis

### Manifest Browsing
1. Use the Manifest tab to search Destiny 2's item database
2. Search for specific weapons or items
3. Browse weapon types and rarities

## Building from Source

To create your own executable:

```bash
# Install build dependencies
pip install -r requirements.txt

# Build the executable
python build_executable.py
```

The executable will be created in the `release/` directory.

## Technical Details

- **Framework**: Python 3.8+ with tkinter GUI
- **API**: Bungie.net Platform API
- **Caching**: Local JSON file caching for manifest data
- **Data Format**: JSON export format for compatibility

## Privacy

- All data processing happens locally on your computer
- Your API key is stored locally and never shared
- Only official Bungie API endpoints are contacted
- No telemetry or usage tracking

## Support

If you encounter issues:

1. Check your internet connection
2. Verify your Bungie API key is valid
3. Ensure your Bungie name/code are correct
4. Check the console output for error details

## Contributing

This is an open-source project. Contributions welcome!

## License

MIT License - see LICENSE file for details.

## Changelog

### v1.0.0 (Initial Release)
- Standalone desktop application
- Weapon usage statistics
- Activity history tracking
- Manifest data browsing
- Data export functionality
- Offline manifest caching
