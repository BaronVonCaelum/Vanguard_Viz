#!/usr/bin/env python3
"""
Prepare Vanguard Viz directory for executable release
This script cleans up the directory to contain only files needed for the desktop executable
"""

import os
import shutil
import json
from pathlib import Path
from typing import List

def main():
    """Main cleanup function"""
    
    print("🧹 Preparing Vanguard Viz for Desktop Release")
    print("=" * 50)
    
    # Files to keep for desktop version
    keep_files = [
        "vanguard_viz_desktop.py",
        "desktop_manifest_helper.py", 
        "requirements.txt",
        "build_executable.py",
        "prepare_for_release.py",
        "README.md",
        ".env",
        ".gitignore"
    ]
    
    # Directories to remove (web server related)
    remove_dirs = [
        "public",
        "src", 
        "bungie-api",
        "python_api",
        "node_modules",
        "build",
        "dist",
        "__pycache__",
        "manifest_cache"
    ]
    
    # Files to remove (web server related)
    remove_files = [
        "server.js",
        "package.json",
        "package-lock.json",
        "corrected_code.js",
        "checkItems.js",
        "manifest_db.py",
        "manifest_helper.py",
        "test_manifest.py",
        "test_simple.py",
        "integration-checklist.md",
        "optimization-notes.md"
    ]
    
    print("📋 Files and directories to be removed:")
    
    # Show what will be removed
    for dir_name in remove_dirs:
        if Path(dir_name).exists():
            print(f"  📁 {dir_name}/")
    
    for file_name in remove_files:
        if Path(file_name).exists():
            print(f"  📄 {file_name}")
    
    print(f"\n📋 Files to keep:")
    for file_name in keep_files:
        if Path(file_name).exists():
            print(f"  ✅ {file_name}")
        else:
            print(f"  ❌ {file_name} (missing)")
    
    # Ask for confirmation
    response = input("\n❓ Proceed with cleanup? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Cleanup cancelled")
        return 1
    
    print("\n🧹 Starting cleanup...")
    
    # Remove directories
    for dir_name in remove_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✅ Removed directory: {dir_name}/")
            except Exception as e:
                print(f"  ❌ Failed to remove {dir_name}/: {e}")
    
    # Remove files
    for file_name in remove_files:
        file_path = Path(file_name)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"  ✅ Removed file: {file_name}")
            except Exception as e:
                print(f"  ❌ Failed to remove {file_name}: {e}")
    
    # Create a new README for the desktop version
    create_desktop_readme()
    
    # Update .gitignore for desktop version
    update_gitignore()
    
    # Create desktop-specific requirements
    create_minimal_requirements()
    
    print("\n✅ Cleanup completed!")
    print("\n📋 Next steps:")
    print("1. Review the updated README.md")
    print("2. Test the desktop application: python vanguard_viz_desktop.py")
    print("3. Build the executable: python build_executable.py")
    print("4. Commit changes to git")
    print("5. Create v1.0 release")
    
    return 0

def create_desktop_readme():
    """Create a new README for the desktop version"""
    readme_content = """# Vanguard Viz Desktop

A standalone desktop application for Destiny 2 data analytics and visualization.

## Overview

Vanguard Viz Desktop is a Python-based GUI application that provides Destiny 2 players with powerful analytics tools for their gameplay data. No web server or browser required!

## Features

- 🔫 **Weapon Usage Statistics** - Track kills, precision kills, and usage time for all your weapons
- 🎯 **Activity History** - Analyze your PvE and PvP activity performance
- 📊 **Manifest Data Browsing** - Search and explore Destiny 2's weapon and activity database
- 💾 **Data Export** - Export your data to JSON for further analysis
- 🗂️ **Offline Caching** - Manifest data is cached locally for faster access
- ⚙️ **User-Friendly Interface** - Clean, tabbed interface built with tkinter

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
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("  ✅ Created desktop README.md")

def update_gitignore():
    """Update .gitignore for desktop version"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Environment variables
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Manifest cache
manifest_cache/

# Application data
vanguard_viz_settings.json

# Release builds
release/
*.zip

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Backup files
*.bak
*.orig
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("  ✅ Updated .gitignore")

def create_minimal_requirements():
    """Create minimal requirements for desktop version"""
    minimal_requirements = """# Core dependencies for Vanguard Viz Desktop
requests>=2.31.0
python-dotenv>=1.0.0

# For building executable
pyinstaller>=6.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(minimal_requirements)
    
    print("  ✅ Created minimal requirements.txt")

if __name__ == "__main__":
    exit(main())
