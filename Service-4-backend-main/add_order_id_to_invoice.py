#!/usr/bin/env python3
"""
Script to add order_id column to Invoice table
"""
import sqlite3
import os

def add_order_id_column():
    """Add order_id column to Invoice table"""
    db_path = 'instance/gst_inventory.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if order_id column already exists
        cursor.execute("PRAGMA table_info(invoice)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'order_id' not in columns:
            # Add order_id column (without foreign key constraint for now)
            cursor.execute("ALTER TABLE invoice ADD COLUMN order_id INTEGER")
            print("✅ Added order_id column to Invoice table")
        else:
            print("✅ order_id column already exists in Invoice table")
        
        # Commit changes
        conn.commit()
        conn.close()
        print("✅ Database updated successfully")
        
    except Exception as e:
        print(f"❌ Error updating database: {str(e)}")

if __name__ == "__main__":
    add_order_id_column()
