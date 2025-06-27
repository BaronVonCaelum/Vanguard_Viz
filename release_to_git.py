#!/usr/bin/env python3
"""
Git Release Automation Script for Vanguard Viz Desktop
Automates the process of committing changes and creating a v1.0 release
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result"""
    print(f"🔄 Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"❌ Stderr: {e.stderr.strip()}")
        return None

def check_git_status():
    """Check if we're in a git repository and get status"""
    if not Path(".git").exists():
        print("❌ Not in a git repository!")
        return False
    
    # Check git status
    result = run_command("git status --porcelain", check=False)
    if result is None:
        return False
    
    if result.stdout.strip():
        print("📋 Git status:")
        print(result.stdout)
        return True
    else:
        print("✅ Working directory is clean")
        return True

def main():
    """Main release function"""
    
    print("🚀 Vanguard Viz Desktop - Git Release Automation")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("vanguard_viz_desktop.py").exists():
        print("❌ Error: vanguard_viz_desktop.py not found!")
        print("Please run this script from the Vanguard Viz directory.")
        return 1
    
    # Check git status
    if not check_git_status():
        print("❌ Git repository check failed")
        return 1
    
    # Check if we have changes to commit
    result = run_command("git status --porcelain", check=False)
    if result and result.stdout.strip():
        print("\n📋 Files to be committed:")
        print(result.stdout)
        
        response = input("\n❓ Proceed with commit? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Commit cancelled")
            return 1
        
        # Stage all changes
        print("\n📦 Staging changes...")
        if run_command("git add .") is None:
            return 1
        
        # Create commit message
        commit_message = """v1.0.0: Convert to standalone desktop application

- Replace Node.js web server with Python desktop GUI
- Add tkinter-based user interface with tabbed layout
- Implement synchronous manifest helper for desktop use
- Add data collection, analysis, and export features
- Include PyInstaller build system for executable creation
- Clean up repository to remove web-specific files
- Add comprehensive documentation for desktop version

This release transforms Vanguard Viz from a web-based Tableau connector
into a standalone desktop application that users can run without any
server setup or browser requirements."""
        
        # Commit changes
        print("\n💾 Committing changes...")
        if run_command(f'git commit -m "{commit_message}"') is None:
            return 1
        
        print("✅ Changes committed successfully!")
    else:
        print("ℹ️ No changes to commit")
    
    # Ask about pushing to remote
    response = input("\n❓ Push to remote repository? (y/N): ").strip().lower()
    if response == 'y':
        print("\n📤 Pushing to remote...")
        if run_command("git push origin main") is None:
            print("⚠️ Push failed, but continuing with tag creation...")
    
    # Create and push v1.0.0 tag
    print("\n🏷️ Creating v1.0.0 tag...")
    
    # Check if tag already exists
    result = run_command("git tag -l v1.0.0", check=False)
    if result and result.stdout.strip():
        print("⚠️ Tag v1.0.0 already exists")
        response = input("❓ Delete existing tag and recreate? (y/N): ").strip().lower()
        if response == 'y':
            run_command("git tag -d v1.0.0")
            run_command("git push origin --delete v1.0.0", check=False)
        else:
            print("❌ Tag creation cancelled")
            return 1
    
    # Create annotated tag
    tag_message = """Vanguard Viz Desktop v1.0.0

First release of the standalone desktop application.

Features:
- Standalone Python GUI application (no web server required)
- Weapon usage statistics and analysis
- Activity history tracking
- Manifest data browsing with search
- Data export to JSON format
- Offline manifest caching
- Cross-platform executable support

Installation:
- Download VanguardViz.exe from releases
- Or run from source with Python 3.8+

Setup:
- Get Bungie API key from bungie.net/en/Application
- Enter API key and Bungie name in the app
- Start analyzing your Destiny 2 data!"""
    
    if run_command(f'git tag -a v1.0.0 -m "{tag_message}"') is None:
        return 1
    
    # Push tag to remote
    response = input("\n❓ Push tag to remote repository? (y/N): ").strip().lower()
    if response == 'y':
        print("\n📤 Pushing tag to remote...")
        if run_command("git push origin v1.0.0") is None:
            print("❌ Failed to push tag")
            return 1
        
        print("✅ Tag pushed successfully!")
        
        # Show GitHub release URL
        result = run_command("git remote get-url origin", check=False)
        if result and result.stdout.strip():
            remote_url = result.stdout.strip()
            if "github.com" in remote_url:
                # Convert SSH/HTTPS URL to web URL
                if remote_url.startswith("git@github.com:"):
                    repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
                elif remote_url.startswith("https://github.com/"):
                    repo_path = remote_url.replace("https://github.com/", "").replace(".git", "")
                else:
                    repo_path = None
                
                if repo_path:
                    release_url = f"https://github.com/{repo_path}/releases/new?tag=v1.0.0"
                    print(f"\n🌐 Create GitHub release at:")
                    print(f"   {release_url}")
    
    print("\n🎉 Release process completed successfully!")
    print("\n📋 Next steps:")
    print("1. Build the executable: python build_executable.py")
    print("2. Test the executable thoroughly")
    print("3. Create GitHub release with the executable zip file")
    print("4. Update any documentation as needed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
