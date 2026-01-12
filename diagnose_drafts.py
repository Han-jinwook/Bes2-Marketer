
import os
import sys
from database import db

def diagnose():
    print("=== DATABASE DIAGNOSIS ===")
    
    # 1. Total Counts
    try:
        leads_count = len(db.get_all_leads(limit=1000))
        videos_count = len(db.get_all_videos(limit=1000))
        drafts_count = len(db.get_all_drafts(limit=1000))
        
        print(f"[Counts] Leads: {leads_count}, Videos: {videos_count}, Drafts: {drafts_count}")
    except Exception as e:
        print(f"[Error] Failed to fetch counts: {e}")

    # 2. Check Drafts Content
    print("\n[Check] Validating latest drafts...")
    try:
        drafts = db.get_all_drafts(limit=5)
        for i, d in enumerate(drafts):
            print(f"  Draft #{i+1}: ID={d.get('id')}, Type={d.get('draft_type')}, Status={d.get('status')}, VideoFK={d.get('video_id')}")
    except Exception as e:
        print(f"[Error] Failed to read drafts: {e}")

    # 3. Test the specific problematic query
    print("\n[Check] Testing 'get_pending_email_drafts_detailed' query...")
    try:
        # Manually constructing the query from database.py to verify
        # response = db.client.table("drafts").select("*, videos(*), leads(*)").eq("draft_type", "email").eq("status", "pending").execute()
        
        detailed_drafts = db.get_pending_email_drafts_detailed()
        print(f"  Query returned {len(detailed_drafts)} items.")
        
        if len(detailed_drafts) == 0 and drafts_count > 0:
            print("  ⚠️ WARNING: Drafts exist but detailed query returns 0. Checking relationships...")
            
            # Debug Step: Check if simple join works?
            # Check if video exists for the first draft
            if drafts:
                first_video_id = drafts[0].get("video_id")
                print(f"  First draft video_id (UUID): {first_video_id}")
                video = db.get_video_by_id(first_video_id)
                if video:
                    print(f"  ✅ Associated Video found: {video.get('title')}")
                else:
                    print(f"  ❌ Associated Video NOT found (Broken Link?)")

    except Exception as e:
        print(f"[Error] Detailed query failed: {e}")

if __name__ == "__main__":
    diagnose()
