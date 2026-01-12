
import sys
from database import db
import uuid

def test_insert_cycle():
    print("=== TEST INSERT CYCLE ===")
    
    # 1. Fetch an existing lead and video to attach draft to
    videos = db.get_all_videos(limit=1)
    if not videos:
        print("[Error] No videos found in DB to test with. Run search first.")
        return

    video = videos[0]
    lead = db.get_lead_by_id(video["lead_id"])
    
    print(f"[Info] Target Video: {video['title']} ({video['id']})")
    print(f"[Info] Target Lead: {lead['channel_name']} ({lead['id']})")
    
    # 2. Try Insert Draft
    print("\n[Action] Inserting Test Draft...")
    try:
        new_draft = db.create_draft(
            draft_type="email",
            content="[TEST] Debugging Insert",
            video_id=video["id"],
            lead_id=lead["id"]
        )
        print(f"[Result] Create Draft Returned: {new_draft}")
        
        if not new_draft:
             print("[Fail] Create Draft returned empty dict/None.")
             return
             
        draft_id = new_draft.get("id")
        if not draft_id:
             print("[Fail] Draft created but has no ID.")
             return
             
        print(f"[Success] Draft Created with ID: {draft_id}")

        # 3. Try Select Immediately
        print(f"\n[Action] Selecting Draft {draft_id}...")
        fetched = db.get_draft_by_id(draft_id)
        if fetched:
            print(f"[Success] Fetched Draft: {fetched['content']}")
        else:
            print(f"[CRITICAL FAIL] Draft {draft_id} was inserted but cannot be fetched! (RLS blocking SELECT?)")

    except Exception as e:
        print(f"[Error] Insert failed with exception: {e}")

if __name__ == "__main__":
    test_insert_cycle()
