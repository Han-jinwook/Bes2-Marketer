from database import db
import json

print("=== 1. Drafts Table Raw Check ===")
try:
    # 가장 최근 5개만 조회
    response = db.client.table("drafts").select("*").order("created_at", desc=True).limit(5).execute()
    drafts = response.data
    print(f"Total rows fetched: {len(drafts)}")
    for d in drafts:
        print(f"- ID: {d.get('id')}")
        print(f"  Type: {d.get('draft_type')}")
        print(f"  Status: {d.get('status')}")
        print(f"  Content Length: {len(d.get('content', ''))}")
        print(f"  Lead ID: {d.get('lead_id')}")
        print(f"  Video ID: {d.get('video_id')}")
except Exception as e:
    print(f"❌ Error checking raw table: {e}")

print("\n=== 2. Detailed Method Check (get_pending_email_drafts_detailed) ===")
try:
    detailed = db.get_pending_email_drafts_detailed()
    print(f"Result Count: {len(detailed)}")
    for d in detailed:
        print(f"- ID: {d.get('id')}")
        # leads와 videos가 잘 join 되었는지 확인
        print(f"  Leads Info: {d.get('leads')}") 
        print(f"  Videos Info: {d.get('videos')}")
except Exception as e:
    print(f"❌ Error running detailed method: {e}")
