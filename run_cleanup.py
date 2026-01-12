
from database import db

def run_cleanup():
    print("🧹 Cleaning up database...")
    try:
        # Supabase API로 delete 실행. 
        # 테이블 전체 삭제는 delete()에 조건 없이 실행하면 되지만, 
        # supabase-py 클라이언트에서는 'neq' 등을 이용해 전체 범위를 잡아야 할 수도 있음.
        # 여기서는 가장 확실한 방법인 'video_id'가 NULL이 아닌 모든 것을 지우는 방식 등을 사용.
        # 하지만 더 간단하게는 id가 not null인 것을 지우면 됨.
        
        # 1. Drafts 삭제
        print("   Deleting all drafts...")
        res_drafts = db.client.table("drafts").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"   Deleted drafts count: {len(res_drafts.data) if res_drafts.data else 'Unknown'}")

        # 2. Videos 삭제
        print("   Deleting all videos...")
        res_videos = db.client.table("videos").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"   Deleted videos count: {len(res_videos.data) if res_videos.data else 'Unknown'}")
        
        print("\n✨ Data cleanup complete! (Leads preserved)")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    run_cleanup()
