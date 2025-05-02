#!/usr/bin/env python
import os
import sys
import shutil
import time
from datetime import datetime

"""
Database replacement utility for IndustrialItem

This script runs independently of Flask to directly replace the database file.
It should be called by the import_db route in Flask.
"""

def replace_database(uploaded_file_path, instance_path="instance"):
    """
    Replace the main database with the uploaded one
    
    Args:
        uploaded_file_path: Path to the uploaded database file
        instance_path: Path to the Flask instance directory
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Starting database replacement process...")
        
        # Make sure paths exist
        if not os.path.exists(uploaded_file_path):
            print(f"Error: Uploaded file not found at {uploaded_file_path}")
            return False
            
        # Make sure instance directory exists
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print(f"Created instance directory at {instance_path}")
        
        # Database file path
        db_path = os.path.join(instance_path, "inventory.db")
        
        # Create a backup of the current database
        if os.path.exists(db_path):
            backup_name = f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = os.path.join(instance_path, backup_name)
            shutil.copy2(db_path, backup_path)
            print(f"Created backup at {backup_path}")
        
        # Wait a moment to ensure any open connections are released
        time.sleep(1)
        
        # Replace the database file
        shutil.copy2(uploaded_file_path, db_path)
        print(f"Replaced database with {uploaded_file_path}")
        
        # Remove the uploaded file
        os.remove(uploaded_file_path)
        print(f"Removed temporary file {uploaded_file_path}")
        
        return True
        
    except Exception as e:
        print(f"Error replacing database: {str(e)}")
        return False

if __name__ == "__main__":
    # When run as a script, take the path from the command line
    if len(sys.argv) < 2:
        print("Usage: python replace_db.py <path_to_uploaded_file>")
        sys.exit(1)
    
    uploaded_file = sys.argv[1]
    success = replace_database(uploaded_file)
    
    if success:
        print("Database replacement successful!")
        sys.exit(0)
    else:
        print("Database replacement failed!")
        sys.exit(1) 