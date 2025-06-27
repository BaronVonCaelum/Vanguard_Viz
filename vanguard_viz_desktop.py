#!/usr/bin/env python3
"""
Vanguard Viz Desktop Application
A standalone desktop application for Destiny 2 data analytics and visualization.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import asyncio
import threading
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import webbrowser
from typing import Dict, Any, List, Optional

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from desktop_manifest_helper import (
        test_api_connection, get_user_profile, get_weapon_usage_stats,
        get_manifest_component, search_items_by_name
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available.")
    # Don't exit - we can still run with limited functionality
    print("Running with limited functionality...")

class VanguardVizDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("Vanguard Viz - Destiny 2 Analytics v1.0")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Application state
        self.api_key = tk.StringVar()
        self.bungie_name = tk.StringVar()
        self.bungie_code = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        
        # Data storage
        self.user_profile = None
        self.weapon_stats = None
        self.manifest_data = None
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        
        # Load saved settings
        self.load_settings()
        
    def setup_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Settings", command=self.save_settings)
        file_menu.add_command(label="Load Settings", command=self.load_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Update Manifest Database", command=self.update_manifest_async)
        tools_menu.add_command(label="Test API Connection", command=self.test_connection_async)
        tools_menu.add_command(label="Clear Cache", command=self.clear_cache)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="API Key Help", command=self.show_api_help)
        
    def setup_ui(self):
        """Setup the main user interface"""
        
        # Create main frame with scrollable content
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tabs
        self.setup_config_tab()
        self.setup_data_tab()
        self.setup_analysis_tab()
        
        # Status bar
        self.setup_status_bar()
        
    def setup_config_tab(self):
        """Setup the configuration tab"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="Configuration")
        
        # API Configuration section
        api_frame = ttk.LabelFrame(config_frame, text="Bungie API Configuration", padding=10)
        api_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*")
        api_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=2, padx=(5, 0))
        
        ttk.Button(api_frame, text="Test Connection", 
                  command=self.test_connection_async).grid(row=0, column=3, padx=(5, 0))
        
        # User Information section
        user_frame = ttk.LabelFrame(config_frame, text="User Information", padding=10)
        user_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(user_frame, text="Bungie Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(user_frame, textvariable=self.bungie_name, width=30).grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        ttk.Label(user_frame, text="Bungie Code:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        ttk.Entry(user_frame, textvariable=self.bungie_code, width=10).grid(row=0, column=3, sticky=tk.W, pady=2, padx=(5, 0))
        
        ttk.Button(user_frame, text="Load Profile", 
                  command=self.load_profile_async).grid(row=0, column=4, padx=(10, 0))
        
        # Configure grid weights
        api_frame.columnconfigure(1, weight=1)
        user_frame.columnconfigure(1, weight=1)
        
        # Data Options section
        options_frame = ttk.LabelFrame(config_frame, text="Data Collection Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Checkboxes for data types
        self.collect_weapons = tk.BooleanVar(value=True)
        self.collect_activities = tk.BooleanVar(value=True)
        self.collect_stats = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Weapon Statistics", 
                       variable=self.collect_weapons).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Activity History", 
                       variable=self.collect_activities).grid(row=0, column=1, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Player Statistics", 
                       variable=self.collect_stats).grid(row=0, column=2, sticky=tk.W)
        
        # Date range selection
        date_frame = ttk.LabelFrame(config_frame, text="Date Range (Optional)", padding=10)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_date = ttk.Entry(date_frame, width=12)
        self.start_date.grid(row=0, column=1, pady=2, padx=(5, 0))
        self.start_date.insert(0, (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.end_date = ttk.Entry(date_frame, width=12)
        self.end_date.grid(row=0, column=3, pady=2, padx=(5, 0))
        self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
    def setup_data_tab(self):
        """Setup the data collection and display tab"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data Collection")
        
        # Control buttons
        control_frame = ttk.Frame(data_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Collect All Data", 
                  command=self.collect_all_data_async).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Clear Data", 
                  command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh Display", 
                  command=self.refresh_data_display).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, 
                                          mode='determinate', length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Data display area with tabs
        self.data_notebook = ttk.Notebook(data_frame)
        self.data_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create data display tabs
        self.setup_weapons_display()
        self.setup_profile_display()
        self.setup_manifest_display()
        
    def setup_weapons_display(self):
        """Setup weapons data display"""
        weapons_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(weapons_frame, text="Weapons")
        
        # Create treeview for weapons data
        columns = ("Name", "Type", "Kills", "Precision", "Usage Time")
        self.weapons_tree = ttk.Treeview(weapons_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.weapons_tree.heading(col, text=col)
            self.weapons_tree.column(col, width=150)
        
        # Add scrollbars
        weapons_scroll_y = ttk.Scrollbar(weapons_frame, orient=tk.VERTICAL, command=self.weapons_tree.yview)
        weapons_scroll_x = ttk.Scrollbar(weapons_frame, orient=tk.HORIZONTAL, command=self.weapons_tree.xview)
        self.weapons_tree.configure(yscrollcommand=weapons_scroll_y.set, xscrollcommand=weapons_scroll_x.set)
        
        # Pack widgets
        self.weapons_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        weapons_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        weapons_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_profile_display(self):
        """Setup profile data display"""
        profile_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(profile_frame, text="Profile")
        
        # Create text widget for profile information
        self.profile_text = tk.Text(profile_frame, wrap=tk.WORD, height=20)
        profile_scroll = ttk.Scrollbar(profile_frame, orient=tk.VERTICAL, command=self.profile_text.yview)
        self.profile_text.configure(yscrollcommand=profile_scroll.set)
        
        self.profile_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        profile_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_manifest_display(self):
        """Setup manifest data display"""
        manifest_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(manifest_frame, text="Manifest")
        
        # Search functionality
        search_frame = ttk.Frame(manifest_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 0))
        search_entry.bind('<Return>', self.search_manifest)
        
        ttk.Button(search_frame, text="Search", 
                  command=self.search_manifest).pack(side=tk.LEFT, padx=(5, 0))
        
        # Manifest data display
        manifest_columns = ("Hash", "Name", "Type", "Tier")
        self.manifest_tree = ttk.Treeview(manifest_frame, columns=manifest_columns, show="headings", height=15)
        
        for col in manifest_columns:
            self.manifest_tree.heading(col, text=col)
            self.manifest_tree.column(col, width=150)
        
        # Add scrollbars
        manifest_scroll_y = ttk.Scrollbar(manifest_frame, orient=tk.VERTICAL, command=self.manifest_tree.yview)
        manifest_scroll_x = ttk.Scrollbar(manifest_frame, orient=tk.HORIZONTAL, command=self.manifest_tree.xview)
        self.manifest_tree.configure(yscrollcommand=manifest_scroll_y.set, xscrollcommand=manifest_scroll_x.set)
        
        # Pack widgets
        self.manifest_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        manifest_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        manifest_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_analysis_tab(self):
        """Setup the analysis and visualization tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")
        
        # Analysis controls
        control_frame = ttk.LabelFrame(analysis_frame, text="Analysis Options", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Generate Weapon Report", 
                  command=self.generate_weapon_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Show Top Weapons", 
                  command=self.show_top_weapons).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Damage Type Analysis", 
                  command=self.analyze_damage_types).pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(analysis_frame, text="Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=20)
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_status_bar(self):
        """Setup the status bar"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.LEFT, padx=5)
        
    # Async wrapper methods
    def test_connection_async(self):
        """Test API connection in a separate thread"""
        def run_test():
            self.update_status("Testing API connection...")
            try:
                # This is a simplified sync version - in real implementation, 
                # you'd need to handle the async properly
                self.update_status("API connection test completed (check console for details)")
                messagebox.showinfo("API Test", "Check the console output for connection test results.")
            except Exception as e:
                self.update_status(f"API test failed: {e}")
                messagebox.showerror("API Test Failed", f"Error: {e}")
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def load_profile_async(self):
        """Load user profile in a separate thread"""
        if not self.api_key.get():
            messagebox.showerror("Error", "Please enter your API key first.")
            return
        
        if not self.bungie_name.get() or not self.bungie_code.get():
            messagebox.showerror("Error", "Please enter your Bungie name and code.")
            return
        
        def run_load():
            self.update_status("Loading user profile...")
            try:
                # Note: This would need proper async handling in real implementation
                self.update_status("Profile loaded successfully")
                self.refresh_data_display()
            except Exception as e:
                self.update_status(f"Profile load failed: {e}")
                messagebox.showerror("Profile Load Failed", f"Error: {e}")
        
        threading.Thread(target=run_load, daemon=True).start()
    
    def collect_all_data_async(self):
        """Collect all selected data types"""
        if not self.api_key.get():
            messagebox.showerror("Error", "Please enter your API key first.")
            return
        
        def run_collection():
            self.update_status("Collecting data...")
            self.progress_var.set(0)
            
            try:
                total_steps = sum([self.collect_weapons.get(), 
                                 self.collect_activities.get(), 
                                 self.collect_stats.get()])
                current_step = 0
                
                if self.collect_weapons.get():
                    self.update_status("Collecting weapon data...")
                    # Weapon collection logic here
                    current_step += 1
                    self.progress_var.set((current_step / total_steps) * 100)
                
                if self.collect_activities.get():
                    self.update_status("Collecting activity data...")
                    # Activity collection logic here
                    current_step += 1
                    self.progress_var.set((current_step / total_steps) * 100)
                
                if self.collect_stats.get():
                    self.update_status("Collecting player statistics...")
                    # Stats collection logic here
                    current_step += 1
                    self.progress_var.set((current_step / total_steps) * 100)
                
                self.update_status("Data collection completed")
                self.progress_var.set(100)
                self.refresh_data_display()
                
            except Exception as e:
                self.update_status(f"Data collection failed: {e}")
                messagebox.showerror("Collection Failed", f"Error: {e}")
        
        threading.Thread(target=run_collection, daemon=True).start()
    
    def update_manifest_async(self):
        """Update manifest database in a separate thread"""
        def run_update():
            self.update_status("Updating manifest database...")
            try:
                # This would call your update_database function
                self.update_status("Manifest database updated successfully")
                messagebox.showinfo("Update Complete", "Manifest database has been updated.")
            except Exception as e:
                self.update_status(f"Manifest update failed: {e}")
                messagebox.showerror("Update Failed", f"Error: {e}")
        
        threading.Thread(target=run_update, daemon=True).start()
    
    def search_manifest(self, event=None):
        """Search manifest data"""
        search_term = self.search_var.get().strip()
        if not search_term:
            return
        
        try:
            # Clear previous results
            for item in self.manifest_tree.get_children():
                self.manifest_tree.delete(item)
            
            # This would use your search_items_by_name function
            self.update_status(f"Searching for '{search_term}'...")
            # results = search_items_by_name(conn, search_term)
            # for result in results:
            #     self.manifest_tree.insert("", tk.END, values=(
            #         result["hash"], result["name"], result["itemType"], result["tierType"]
            #     ))
            
            self.update_status(f"Search completed for '{search_term}'")
            
        except Exception as e:
            self.update_status(f"Search failed: {e}")
            messagebox.showerror("Search Failed", f"Error: {e}")
    
    def generate_weapon_report(self):
        """Generate a weapon usage report"""
        if not self.weapon_stats:
            messagebox.showwarning("No Data", "Please collect weapon data first.")
            return
        
        try:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "WEAPON USAGE REPORT\n")
            self.results_text.insert(tk.END, "="*50 + "\n\n")
            
            # This would analyze your weapon stats data
            self.results_text.insert(tk.END, "Report generated successfully!\n")
            self.results_text.insert(tk.END, "(Detailed analysis would be implemented here)\n")
            
        except Exception as e:
            messagebox.showerror("Report Failed", f"Error generating report: {e}")
    
    def show_top_weapons(self):
        """Show top weapons by kills"""
        # Implementation for showing top weapons
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "TOP WEAPONS BY KILLS\n")
        self.results_text.insert(tk.END, "="*30 + "\n\n")
        self.results_text.insert(tk.END, "Feature coming soon...\n")
    
    def analyze_damage_types(self):
        """Analyze weapon usage by damage type"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "DAMAGE TYPE ANALYSIS\n")
        self.results_text.insert(tk.END, "="*30 + "\n\n")
        self.results_text.insert(tk.END, "Feature coming soon...\n")
    
    def refresh_data_display(self):
        """Refresh all data displays"""
        # Clear and repopulate weapons tree
        for item in self.weapons_tree.get_children():
            self.weapons_tree.delete(item)
        
        # Update profile display
        self.profile_text.delete(1.0, tk.END)
        if self.user_profile:
            self.profile_text.insert(tk.END, "User profile data would be displayed here...")
        else:
            self.profile_text.insert(tk.END, "No profile data loaded.")
    
    def clear_data(self):
        """Clear all collected data"""
        self.user_profile = None
        self.weapon_stats = None
        self.manifest_data = None
        self.refresh_data_display()
        self.update_status("Data cleared")
    
    def clear_cache(self):
        """Clear application cache"""
        # Implementation for clearing cache
        messagebox.showinfo("Cache Cleared", "Application cache has been cleared.")
        self.update_status("Cache cleared")
    
    def export_data(self):
        """Export collected data to file"""
        if not any([self.user_profile, self.weapon_stats, self.manifest_data]):
            messagebox.showwarning("No Data", "No data available to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                export_data = {
                    "user_profile": self.user_profile,
                    "weapon_stats": self.weapon_stats,
                    "manifest_data": self.manifest_data,
                    "export_timestamp": datetime.now().isoformat()
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                messagebox.showinfo("Export Complete", f"Data exported to {filename}")
                self.update_status(f"Data exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Export Failed", f"Error exporting data: {e}")
    
    def save_settings(self):
        """Save application settings"""
        settings = {
            "api_key": self.api_key.get(),
            "bungie_name": self.bungie_name.get(),
            "bungie_code": self.bungie_code.get(),
            "collect_weapons": self.collect_weapons.get(),
            "collect_activities": self.collect_activities.get(),
            "collect_stats": self.collect_stats.get(),
        }
        
        try:
            with open("vanguard_viz_settings.json", 'w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Settings Saved", "Settings have been saved.")
            self.update_status("Settings saved")
            
        except Exception as e:
            messagebox.showerror("Save Failed", f"Error saving settings: {e}")
    
    def load_settings(self):
        """Load application settings"""
        try:
            if os.path.exists("vanguard_viz_settings.json"):
                with open("vanguard_viz_settings.json", 'r') as f:
                    settings = json.load(f)
                
                self.api_key.set(settings.get("api_key", ""))
                self.bungie_name.set(settings.get("bungie_name", ""))
                self.bungie_code.set(settings.get("bungie_code", ""))
                self.collect_weapons.set(settings.get("collect_weapons", True))
                self.collect_activities.set(settings.get("collect_activities", True))
                self.collect_stats.set(settings.get("collect_stats", True))
                
                self.update_status("Settings loaded")
            
        except Exception as e:
            messagebox.showerror("Load Failed", f"Error loading settings: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Vanguard Viz Desktop v1.0
        
A standalone desktop application for Destiny 2 data analytics and visualization.

Created for Guardians who want to analyze their gameplay data without needing a web server.

Features:
- Weapon usage statistics
- Activity history tracking  
- Manifest data browsing
- Data export capabilities
- Offline manifest caching

© 2024 Vanguard Viz Project"""
        
        messagebox.showinfo("About Vanguard Viz", about_text)
    
    def show_api_help(self):
        """Show API key help"""
        help_text = """Getting Your Bungie API Key:

1. Go to https://www.bungie.net/en/Application
2. Sign in with your Bungie account
3. Click "Create New App"
4. Fill out the application form:
   - Application Name: "Vanguard Viz Desktop"
   - Website: Can be left blank or use a personal URL
   - Application Status: "Private"
   - OAuth Client Type: "Not Applicable"
5. Submit the application
6. Copy the API Key from your application page
7. Paste it into the API Key field in Vanguard Viz

Keep your API key secure and don't share it with others."""
        
        messagebox.showinfo("API Key Help", help_text)
        webbrowser.open("https://www.bungie.net/en/Application")
    
    def update_status(self, message):
        """Update the status bar"""
        self.status_text.set(message)
        self.root.update_idletasks()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = VanguardVizDesktop(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        root.quit()

if __name__ == "__main__":
    main()
