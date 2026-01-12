"""
Firebase Firestore Database Manager
Supabase에서 Firebase로 마이그레이션 (2026-01-13)
"""

import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, List, Dict
from datetime import datetime
import os

class Database:
    """Firebase Firestore 데이터베이스 관리 클래스"""
    
    def __init__(self):
        """Firebase 초기화 (로컬 및 Streamlit Cloud 지원)"""
        if not firebase_admin._apps:
            # 1. Streamlit Cloud에서 실행 중인 경우 (st.secrets 사용)
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'firebase' in st.secrets:
                    # Secrets에서 Firebase 인증 정보 로드
                    firebase_creds = dict(st.secrets['firebase'])
                    cred = credentials.Certificate(firebase_creds)
                    firebase_admin.initialize_app(cred)
                    print("✅ Firebase initialized from Streamlit Secrets")
                    self.db = firestore.client()
                    return
            except Exception as e:
                print(f"Streamlit Secrets not found, trying local file... ({e})")
            
            # 2. 로컬 개발 환경 (firebase-key.json 사용)
            try:
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase-key.json')
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    print("✅ Firebase initialized from local JSON file")
                else:
                    raise FileNotFoundError("firebase-key.json not found")
            except Exception as e:
                print(f"❌ Firebase initialization failed: {e}")
                raise
        
        self.db = firestore.client()
        
        # 컬렉션 참조
        self.leads_ref = self.db.collection('leads')
        self.videos_ref = self.db.collection('videos')
        self.drafts_ref = self.db.collection('drafts')
        self.settings_ref = self.db.collection('settings')
    
    # ==================== LEADS (채널 정보) ====================
    
    def create_lead(
        self,
        channel_name: str,
        channel_id: str,
        subscriber_count: int = 0,
        email: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        channel_url: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """새 유튜버(리드) 생성"""
        data = {
            "channel_name": channel_name,
            "channel_id": channel_id,
            "subscriber_count": subscriber_count,
            "email": email,
            "keywords": keywords or [],
            "channel_url": channel_url or f"https://youtube.com/channel/{channel_id}",
            "description": description,
            "status": "new",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = self.leads_ref.document()  # Auto-generate ID
        doc_ref.set(data)
        
        # 생성된 문서 반환
        doc = doc_ref.get()
        return {"id": doc.id, **doc.to_dict()}
    
    def get_lead_by_channel_id(self, channel_id: str) -> Optional[dict]:
        """채널 ID로 리드 조회"""
        docs = self.leads_ref.where('channel_id', '==', channel_id).limit(1).stream()
        for doc in docs:
            return {"id": doc.id, **doc.to_dict()}
        return None
    
    def update_lead(self, lead_id: str, **kwargs) -> dict:
        """리드 정보 업데이트"""
        kwargs['updated_at'] = firestore.SERVER_TIMESTAMP
        self.leads_ref.document(lead_id).update(kwargs)
        
        doc = self.leads_ref.document(lead_id).get()
        return {"id": doc.id, **doc.to_dict()}
    
    def get_all_leads(self) -> List[dict]:
        """모든 리드 조회"""
        docs = self.leads_ref.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    # ==================== VIDEOS (영상 정보) ====================
    
    def create_video(
        self,
        video_id: str,
        title: str,
        lead_id: str,
        upload_date: str,
        view_count: int = 0,
        video_url: Optional[str] = None,
        search_keyword: Optional[str] = None
    ) -> dict:
        """새 영상 생성"""
        data = {
            "video_id": video_id,
            "title": title,
            "lead_id": lead_id,
            "upload_date": upload_date,
            "view_count": view_count,
            "video_url": video_url or f"https://youtube.com/watch?v={video_id}",
            "search_keyword": search_keyword,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        # video_id를 문서 ID로 사용 (중복 방지)
        doc_ref = self.videos_ref.document(video_id)
        doc_ref.set(data, merge=True)  # Upsert
        
        doc = doc_ref.get()
        return {"id": doc.id, **doc.to_dict()}
    
    def get_video_by_video_id(self, video_id: str) -> Optional[dict]:
        """YouTube 영상 ID로 조회"""
        doc = self.videos_ref.document(video_id).get()
        if doc.exists:
            return {"id": doc.id, **doc.to_dict()}
        return None
    
    def get_known_video_ids(self) -> set:
        """이미 DB에 있는 영상 ID 목록"""
        docs = self.videos_ref.stream()
        return {doc.id for doc in docs}
    
    def upsert_scanned_videos(self, videos: list[dict]) -> int:
        """수집된 영상과 채널 정보를 한꺼번에 저장/업데이트"""
        count = 0
        
        for v in videos:
            try:
                # 1. 리드(채널) Upsert
                lead = self.get_lead_by_channel_id(v["channel_id"])
                
                if not lead:
                    lead = self.create_lead(
                        channel_name=v["channel_name"],
                        channel_id=v["channel_id"],
                        subscriber_count=v.get("channel_info", {}).get("subscriber_count", 0),
                        email=v.get("channel_info", {}).get("email")
                    )
                else:
                    # 이메일 등 최신화
                    update_data = {}
                    if not lead.get("email") and v.get("channel_info", {}).get("email"):
                        update_data["email"] = v["channel_info"]["email"]
                    if v.get("channel_info", {}).get("subscriber_count"):
                        update_data["subscriber_count"] = v["channel_info"]["subscriber_count"]
                    
                    if update_data:
                        self.update_lead(lead["id"], **update_data)
                
                # 2. 영상 Upsert
                vc = v.get("view_count", 0)
                if isinstance(vc, str):
                    vc = int(vc.replace(',', '')) if vc.replace(',', '').isdigit() else 0
                
                self.create_video(
                    video_id=v["video_id"],
                    title=v["title"],
                    lead_id=lead["id"],
                    upload_date=v["published_at"][:10],
                    view_count=vc,
                    video_url=v["video_url"],
                    search_keyword=v.get("search_keyword")
                )
                
                count += 1
                
            except Exception as e:
                print(f"Error upserting video {v.get('video_id', 'unknown')}: {e}")
                
        return count
    
    def delete_video_by_video_id(self, video_id: str) -> bool:
        """영상 삭제 (YouTube video_id 기준)"""
        try:
            self.videos_ref.document(video_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting video {video_id}: {e}")
            return False
    
    def get_all_videos(self) -> List[dict]:
        """모든 영상 조회 (lead 정보 포함)"""
        docs = self.videos_ref.stream()
        videos = []
        
        for doc in docs:
            video_data = {"id": doc.id, **doc.to_dict()}
            
            # Lead 정보 조인
            if "lead_id" in video_data:
                lead_doc = self.leads_ref.document(video_data["lead_id"]).get()
                if lead_doc.exists:
                    video_data["lead"] = lead_doc.to_dict()
            
            videos.append(video_data)
        
        return videos
    
    # ==================== DRAFTS (이메일 초안) ====================
    
    def create_draft(
        self,
        video_id: str,
        subject: str,
        body: str,
        model_used: Optional[str] = None
    ) -> dict:
        """이메일 초안 생성"""
        data = {
            "video_id": video_id,
            "subject": subject,
            "body": body,
            "model_used": model_used,
            "status": "draft",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = self.drafts_ref.document()
        doc_ref.set(data)
        
        doc = doc_ref.get()
        return {"id": doc.id, **doc.to_dict()}
    
    def get_drafts_by_video_id(self, video_id: str) -> List[dict]:
        """특정 영상의 모든 초안 조회"""
        docs = self.drafts_ref.where('video_id', '==', video_id).stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    def update_draft(self, draft_id: str, **kwargs) -> dict:
        """초안 업데이트"""
        kwargs['updated_at'] = firestore.SERVER_TIMESTAMP
        self.drafts_ref.document(draft_id).update(kwargs)
        
        doc = self.drafts_ref.document(draft_id).get()
        return {"id": doc.id, **doc.to_dict()}
    
    def get_all_drafts(self) -> List[dict]:
        """모든 초안 조회"""
        docs = self.drafts_ref.stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]
    
    # ==================== SETTINGS (앱 설정) ====================
    
    def get_setting(self, key: str) -> Optional[str]:
        """설정 값 조회"""
        doc = self.settings_ref.document(key).get()
        if doc.exists:
            return doc.to_dict().get("value")
        return None
    
    def set_setting(self, key: str, value: str) -> None:
        """설정 값 저장"""
        data = {
            "value": value,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        self.settings_ref.document(key).set(data, merge=True)
    
    # ==================== STATISTICS ====================
    
    def get_stats(self) -> dict:
        """DB 통계 조회"""
        leads_count = len(list(self.leads_ref.stream()))
        videos_count = len(list(self.videos_ref.stream()))
        drafts_count = len(list(self.drafts_ref.stream()))
        
        # 이메일 있는 리드 수
        leads_with_email = 0
        for doc in self.leads_ref.stream():
            if doc.to_dict().get("email"):
                leads_with_email += 1
        
        return {
            "리드": leads_count,
            "이메일 수집": leads_with_email,
            "영상": videos_count,
            "댓글 초안": drafts_count
        }
