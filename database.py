"""
Bes2 Marketer - Database Module
Supabase 연결 및 CRUD 함수
"""

from datetime import datetime
from typing import Optional
from supabase import create_client, Client
from config import config


class Database:
    """Supabase 데이터베이스 클라이언트"""
    
    def __init__(self):
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )
    
    # =========================================
    # LEADS (유튜버 정보) CRUD
    # =========================================
    
    def create_lead(
        self,
        channel_name: str,
        channel_id: str,
        subscriber_count: int = 0,
        email: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        channel_url: Optional[str] = None,
        # thumbnail_url: Optional[str] = None,  # [REMOVED] leads 테이블에 없는 컬럼
        description: Optional[str] = None
    ) -> dict:
        """새 유튜버(리드) 생성"""
        data = {
            "channel_name": channel_name,
            "channel_id": channel_id,
            "subscriber_count": subscriber_count,
            "email": email,
            "keywords": keywords or [],
            "channel_url": channel_url,
            # "thumbnail_url": thumbnail_url,  # [REMOVED]
            "description": description,
            "status": "new"
        }
        
        response = self.client.table("leads").insert(data).execute()
        return response.data[0] if response.data else {}
    
    def get_lead_by_id(self, lead_id: str) -> Optional[dict]:
        """ID로 리드 조회"""
        response = self.client.table("leads").select("*").eq("id", lead_id).execute()
        return response.data[0] if response.data else None
    
    def get_lead_by_channel_id(self, channel_id: str) -> Optional[dict]:
        """채널 ID로 리드 조회"""
        response = self.client.table("leads").select("*").eq("channel_id", channel_id).execute()
        return response.data[0] if response.data else None
    
    def get_all_leads(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """모든 리드 조회 (필터 및 페이지네이션 지원)"""
        query = self.client.table("leads").select("*")
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        response = query.execute()
        return response.data or []
    
    def update_lead(self, lead_id: str, **kwargs) -> Optional[dict]:
        """리드 정보 업데이트"""
        response = self.client.table("leads").update(kwargs).eq("id", lead_id).execute()
        return response.data[0] if response.data else None
    
    def update_lead_status(self, lead_id: str, status: str) -> Optional[dict]:
        """리드 상태 업데이트"""
        return self.update_lead(lead_id, status=status)
    
    def delete_lead(self, lead_id: str) -> bool:
        """리드 삭제"""
        response = self.client.table("leads").delete().eq("id", lead_id).execute()
        return len(response.data) > 0 if response.data else False
    
    def search_leads(self, keyword: str) -> list[dict]:
        """채널명으로 리드 검색"""
        response = self.client.table("leads").select("*").ilike("channel_name", f"%{keyword}%").execute()
        return response.data or []
    
    # =========================================
    # VIDEOS (영상 정보) CRUD
    # =========================================
    
    def create_video(
        self,
        video_id: str,
        title: str,
        lead_id: Optional[str] = None,
        upload_date: Optional[str] = None,
        view_count: int = 0,
        like_count: int = 0,
        comment_count: int = 0,
        video_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        transcript_text: Optional[str] = None,
        summary: Optional[str] = None,
        relevance_score: float = 0.0,
        search_keyword: Optional[str] = None
    ) -> dict:
        """새 영상 정보 생성"""
        data = {
            "video_id": video_id,
            "title": title,
            "lead_id": lead_id,
            "upload_date": upload_date,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "transcript_text": transcript_text,
            "summary": summary,
            "relevance_score": relevance_score,
            "search_keyword": search_keyword
        }
        
        # None 값 제거
        data = {k: v for k, v in data.items() if v is not None}
        
        response = self.client.table("videos").insert(data).execute()
        return response.data[0] if response.data else {}
    
    def get_video_by_id(self, id: str) -> Optional[dict]:
        """UUID로 영상 조회"""
        response = self.client.table("videos").select("*").eq("id", id).execute()
        return response.data[0] if response.data else None
    
    def upsert_scanned_videos(self, videos: list[dict]) -> int:
        """수집된 영상과 채널 정보를 한꺼번에 저장/업데이트 (Upsert)"""
        count = 0
        video_records = [] # [FIX] 리스트 초기화 추가
        for v in videos:
            try:
                # 1. 리드(채널)Upsert
                # 채널 ID로 기존 리드 확인
                lead = self.get_lead_by_channel_id(v["channel_id"])
                
                if not lead:
                    # 없으면 새로 생성
                    lead = self.create_lead(
                        channel_name=v["channel_name"],
                        channel_id=v["channel_id"],
                        subscriber_count=v.get("channel_info", {}).get("subscriber_count", 0),
                        # thumbnail_url=v.get("thumbnail_url"), # [FIX] leads 테이블에 해당 컬럼 없음
                        email=v.get("channel_info", {}).get("email")
                    )
                else:
                    # 있으면 정보 업데이트 (이메일 등 최신화)
                    update_data = {}
                    if not lead.get("email") and v.get("channel_info", {}).get("email"):
                        update_data["email"] = v["channel_info"]["email"]
                    if v.get("channel_info", {}).get("subscriber_count"):
                        update_data["subscriber_count"] = v["channel_info"]["subscriber_count"]
                    
                    if update_data:
                        self.update_lead(lead["id"], **update_data)
                
                # 2. 영상 Upsert
                # 조회수 숫자 변환
                vc = v.get("view_count", 0)
                if isinstance(vc, str):
                    vc = int(vc.replace(',', '')) if vc.replace(',', '').isdigit() else 0
                
                v_data = {
                    "video_id": v["video_id"],
                    "title": v["title"],
                    "lead_id": lead["id"],
                    "upload_date": v["published_at"][:10],
                    "view_count": vc,
                    "video_url": v["video_url"],
                    "thumbnail_url": v["thumbnail_url"],
                    "search_keyword": v.get("search_keyword")
                }
                video_records.append(v_data)
                
            except Exception as e:
                error_msg = f"Error preparing video data for {v.get('video_id', 'unknown')}: {e}"
                print(error_msg)
                try:
                    import streamlit as st
                    st.error(f"❌ {error_msg}")
                except:
                    pass
                
        # 3. 비디오 대량 Upsert
        if video_records:
            try:
                # print(f"Upserting {len(video_records)} videos...")
                result = self.client.table("videos").upsert(video_records, on_conflict="video_id").execute()
                return len(result.data) if result.data else 0
            except Exception as e:
                # DB 저장 실패 시 원인 파악용 로그
                print(f"❌ DB Video Upsert Error: {e}")
                # Streamlit 환경이라면 화면에도 표시
                try:
                    import streamlit as st
                    st.error(f"❌ DB 저장 실패 (Videos): {e}")
                except:
                    pass
                return 0
        
        return 0

    def get_video_by_video_id(self, video_id: str) -> Optional[dict]:
        """YouTube 영상 ID로 조회"""
        try:
            response = self.client.table("videos").select("*").eq("video_id", video_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching video: {e}")
            return None

    def get_known_video_ids(self) -> set:
        """DB에 저장된 모든 Video ID 조회 (중복 검색 방지용)"""
        try:
            # 1000개 제한이 있을 수 있으니 range를 넉넉하게 잡거나, 일단은 기본으로
            # Supabase default limit might be 1000. For now, simple select is okay.
            response = self.client.table("videos").select("video_id").execute()
            return {item["video_id"] for item in response.data} if response.data else set()
        except Exception as e:
            print(f"Error fetching known video IDs: {e}")
            return set()
    
    def get_videos_by_lead(self, lead_id: str) -> list[dict]:
        """특정 리드의 모든 영상 조회"""
        response = self.client.table("videos").select("*").eq("lead_id", lead_id).order("upload_date", desc=True).execute()
        return response.data or []
    
    def get_all_videos(
        self,
        min_relevance: Optional[float] = None,
        search_keyword: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """모든 영상 조회 (필터 및 페이지네이션 지원)"""
        query = self.client.table("videos").select("*")
        
        if min_relevance is not None:
            query = query.gte("relevance_score", min_relevance)
        
        if search_keyword:
            query = query.eq("search_keyword", search_keyword)
        
        query = query.order("relevance_score", desc=True).range(offset, offset + limit - 1)
        response = query.execute()
        return response.data or []
    
    def update_video(self, id: str, **kwargs) -> Optional[dict]:
        """영상 정보 업데이트"""
        response = self.client.table("videos").update(kwargs).eq("id", id).execute()
        return response.data[0] if response.data else None
    
    def update_video_transcript(self, id: str, transcript_text: str, summary: Optional[str] = None) -> Optional[dict]:
        """영상 자막 및 요약 업데이트"""
        data = {"transcript_text": transcript_text}
        if summary:
            data["summary"] = summary
        return self.update_video(id, **data)
    
    def delete_video(self, id: str) -> bool:
        """영상 삭제"""
        response = self.client.table("videos").delete().eq("id", id).execute()
        return len(response.data) > 0 if response.data else False
    
    def video_exists(self, video_id: str) -> bool:
        """YouTube 영상 ID로 존재 여부 확인"""
        response = self.client.table("videos").select("id").eq("video_id", video_id).execute()
        return len(response.data) > 0 if response.data else False
        
    
    def delete_video_by_video_id(self, video_id: str) -> bool:
        """YouTube 영상 ID로 영상 삭제 (UI 편의용)"""
        response = self.client.table("videos").delete().eq("video_id", video_id).execute()
        return len(response.data) > 0 if response.data else False
    
    # =========================================
    # SETTINGS (설정) CRUD
    # =========================================
    
    def get_setting(self, key: str) -> Optional[str]:
        """설정값 가져오기"""
        try:
            response = self.client.table("settings").select("value").eq("key", key).execute()
            if response.data:
                return response.data[0]["value"]
        except Exception:
            pass # 테이블 없거나 에러 시 None 반환
        return None
        
    def set_setting(self, key: str, value: str):
        """설정값 저장하기 (Upsert)"""
        data = {"key": key, "value": value}
        self.client.table("settings").upsert(data).execute()

    # =========================================
    # DRAFTS (마케팅 초안) CRUD
    # =========================================
    
    def create_draft(
        self,
        draft_type: str,
        content: str,
        video_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        tone: Optional[str] = None,
        language: str = "ko"
    ) -> dict:
        """새 마케팅 초안 생성"""
        if draft_type not in ["email", "comment"]:
            raise ValueError("draft_type must be 'email' or 'comment'")
        
        data = {
            "draft_type": draft_type,
            "content": content,
            "video_id": video_id,
            "lead_id": lead_id,
            "tone": tone,
            "language": language,
            "status": "pending"
        }
        
        # None 값 제거
        data = {k: v for k, v in data.items() if v is not None}
        
        response = self.client.table("drafts").insert(data).execute()
        return response.data[0] if response.data else {}
    
    def get_draft_by_id(self, draft_id: str) -> Optional[dict]:
        """ID로 초안 조회"""
        response = self.client.table("drafts").select("*").eq("id", draft_id).execute()
        return response.data[0] if response.data else None
    
    def get_drafts_by_video(self, video_id: str) -> list[dict]:
        """특정 영상의 모든 초안 조회"""
        response = self.client.table("drafts").select("*").eq("video_id", video_id).order("created_at", desc=True).execute()
        return response.data or []
    
    def get_drafts_by_lead(self, lead_id: str) -> list[dict]:
        """특정 리드의 모든 초안 조회"""
        response = self.client.table("drafts").select("*").eq("lead_id", lead_id).order("created_at", desc=True).execute()
        return response.data or []
    
    def get_all_drafts(
        self,
        draft_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """모든 초안 조회 (필터 및 페이지네이션 지원)"""
        query = self.client.table("drafts").select("*")
        
        if draft_type:
            query = query.eq("draft_type", draft_type)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        response = query.execute()
        return response.data or []
    
    def get_pending_drafts(self, draft_type: Optional[str] = None) -> list[dict]:
        """대기 중인 초안 조회"""
        return self.get_all_drafts(draft_type=draft_type, status="pending")
    
    def get_pending_email_drafts_detailed(self) -> list[dict]:
        """대기 중인 이메일 초안 상세 조회 (영상, 리드 정보 포함)"""
        try:
            response = self.client.table("drafts").select(
                "*, videos(*), leads(*)"
            ).eq("draft_type", "email").eq("status", "pending").order("created_at", desc=True).execute()
            return response.data or []
        except Exception as e:
            print(f"Error fetching detailed drafts: {e}")
            return []
    
    def update_draft(self, draft_id: str, **kwargs) -> Optional[dict]:
        """초안 업데이트"""
        response = self.client.table("drafts").update(kwargs).eq("id", draft_id).execute()
        return response.data[0] if response.data else None
    
    def update_draft_status(self, draft_id: str, status: str) -> Optional[dict]:
        """초안 상태 업데이트"""
        if status not in ["pending", "approved", "sent", "rejected"]:
            raise ValueError("Invalid status. Must be: pending, approved, sent, rejected")
        return self.update_draft(draft_id, status=status)
    
    def update_draft_content(self, draft_id: str, content: str) -> Optional[dict]:
        """초안 내용 업데이트"""
        return self.update_draft(draft_id, content=content)
    
    def delete_draft(self, draft_id: str) -> bool:
        """초안 삭제"""
        response = self.client.table("drafts").delete().eq("id", draft_id).execute()
        return len(response.data) > 0 if response.data else False
    
    # =========================================
    # 통계 및 집계 함수
    # =========================================
    
    def get_lead_stats(self) -> dict:
        """리드 통계 조회"""
        all_leads = self.client.table("leads").select("status").execute()
        
        stats = {
            "total": 0,
            "new": 0,
            "contacted": 0,
            "responded": 0,
            "converted": 0,
            "rejected": 0
        }
        
        if all_leads.data:
            stats["total"] = len(all_leads.data)
            for lead in all_leads.data:
                status = lead.get("status", "new")
                if status in stats:
                    stats[status] += 1
        
        return stats
    
    def get_draft_stats(self) -> dict:
        """초안 통계 조회"""
        all_drafts = self.client.table("drafts").select("draft_type, status").execute()
        
        stats = {
            "total": 0,
            "email": {"total": 0, "pending": 0, "approved": 0, "sent": 0, "rejected": 0},
            "comment": {"total": 0, "pending": 0, "approved": 0, "sent": 0, "rejected": 0}
        }
        
        if all_drafts.data:
            stats["total"] = len(all_drafts.data)
            for draft in all_drafts.data:
                dtype = draft.get("draft_type")
                status = draft.get("status", "pending")
                if dtype in stats:
                    stats[dtype]["total"] += 1
                    if status in stats[dtype]:
                        stats[dtype][status] += 1
        
        return stats
    
    def get_video_count(self) -> int:
        """총 영상 수 조회"""
        response = self.client.table("videos").select("id", count="exact").execute()
        return response.count or 0
    
    # =========================================
    # 관계 조회 (JOIN)
    # =========================================
    
    def get_video_with_lead(self, video_id: str) -> Optional[dict]:
        """영상과 연결된 리드 정보 함께 조회"""
        response = self.client.table("videos").select("*, leads(*)").eq("id", video_id).execute()
        return response.data[0] if response.data else None
    
    def get_draft_with_details(self, draft_id: str) -> Optional[dict]:
        """초안과 연결된 영상, 리드 정보 함께 조회"""
        response = self.client.table("drafts").select("*, videos(*), leads(*)").eq("id", draft_id).execute()
        return response.data[0] if response.data else None
    
    def get_lead_with_videos_and_drafts(self, lead_id: str) -> Optional[dict]:
        """리드와 연결된 모든 영상, 초안 정보 조회"""
        response = self.client.table("leads").select("*, videos(*), drafts(*)").eq("id", lead_id).execute()
        return response.data[0] if response.data else None



    # =========================================
    # APP SETTINGS (설정 관리) CRUD
    # =========================================
    
    def get_app_setting(self, key: str, default: str = "") -> str:
        """설정 값 가져오기"""
        try:
            response = self.client.table("app_settings").select("value").eq("key", key).execute()
            if response.data:
                return response.data[0]["value"]
        except Exception as e:
            print(f"Error fetching setting {key}: {e}")
        return default
    
    def set_app_setting(self, key: str, value: str) -> bool:
        """설정 값 저장하기 (Upsert)"""
        try:
            data = {"key": key, "value": value}
            self.client.table("app_settings").upsert(data, on_conflict="key").execute()
            return True
        except Exception as e:
            print(f"Error saving setting {key}: {e}")
            return False


# 싱글톤 인스턴스
db = Database()


# =========================================
# 테스트 및 유틸리티 함수
# =========================================

def test_connection() -> bool:
    """데이터베이스 연결 테스트"""
    try:
        response = db.client.table("leads").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # 연결 테스트
    print("Testing database connection...")
    if test_connection():
        print("✅ Database connection successful!")
        
        # 통계 출력
        print("\n📊 Current Stats:")
        lead_stats = db.get_lead_stats()
        print(f"  - Total Leads: {lead_stats['total']}")
        
        draft_stats = db.get_draft_stats()
        print(f"  - Total Drafts: {draft_stats['total']}")
        
        video_count = db.get_video_count()
        print(f"  - Total Videos: {video_count}")
    else:
        print("❌ Database connection failed!")
        print("Please check your SUPABASE_URL and SUPABASE_KEY in .env file")

