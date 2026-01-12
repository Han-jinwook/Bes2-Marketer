
from database import db
import time

def check_settings():
    print("🕵️ Checking connection to 'settings' table...")
    try:
        # Try to read
        response = db.get_setting("test_key")
        print(f"✅ Connection successful. Value for 'test_key': {response}")
        
        # Try to write
        print("📝 Attempting to write to 'settings' table...")
        db.set_setting("test_key_autosave", "working")
        print("✅ Write successful.")
        
    except Exception as e:
        print(f"❌ Error accessing settings table: {e}")
        print("\n[Possible Causes]")
        print("1. The 'settings' table does not exist. (Did you run the SQL in Supabase?)")
        print("2. Network connectivity issue.")

if __name__ == "__main__":
    check_settings()
