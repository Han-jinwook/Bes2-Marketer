
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from logic import YouTubeHunter

def test_pipeline():
    print("[TEST] Starting Pipeline Test...")
    hunter = YouTubeHunter()
    
    # 1. Search Test
    keyword = "아이폰 16"
    print(f"\n[Search] Searching for keyword: {keyword}")
    videos = hunter.search_videos(keyword, max_results=1, published_after_days=300)
    
    if not videos:
        print("[Fail] Search failed to find any videos.")
        return
        
    target_video = videos[0]
    vid = target_video["video_id"]
    title = target_video["title"]
    print(f"[Success] Found video: {title} ({vid})")
    
    # 2. Transcript Test
    print(f"\n[Transcript] Fetching transcript for {vid}...")
    transcript = hunter.get_transcript(vid)
    
    if transcript:
        print(f"[Success] Transcript Success! Length: {len(transcript)} chars")
        print(f"Preview: {transcript[:100]}...")
    else:
        print("[Fail] Transcript Failed.")
        print("Possible causes: IP block, No captions, or API restriction.")

if __name__ == "__main__":
    try:
        test_pipeline()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
