"""
Bes2 Marketer - Core Logic Module
YouTube Hunter + AI Copywriter
"""

from typing import Optional
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import re
import google.generativeai as genai

from config import config
from database import db


# =============================================
# YouTube Hunter - 영상 검색 및 자막 추출
# =============================================

class YouTubeHunter:
    """YouTube 영상 검색 및 자막 추출 클래스"""
    
    def __init__(self):
        self.youtube = build(
            "youtube", "v3",
            developerKey=config.YOUTUBE_API_KEY
        )
    
    def search_videos(self, keyword: str, max_results: int = 10, published_after_days: int = 30, min_view_count: int = 0, require_email: bool = False) -> tuple[list[dict], int]:
        """
        유튜브 영상 검색 (Deep Search 적용)
        - require_email=True 시 이메일 없는 영상은 결과에서 제외
        """
        from database import db
        
        # 1. 날짜 및 초기값 설정
        published_after = (datetime.utcnow() - timedelta(days=published_after_days)).isoformat("T") + "Z"
        print(f"Searching for '{keyword}' after {published_after}...")
        
        known_ids = db.get_known_video_ids()
        collected_items = []
        next_page_token = None
        total_results_approx = 0
        
        # 2. 1차 검색 (최대 10페이지 = 500개 후보군 탐색)
        for page_num in range(10):
            try:
                search_response = self.youtube.search().list(
                    q=keyword, part="id,snippet", maxResults=50,
                    order="date", publishedAfter=published_after, type="video", pageToken=next_page_token
                ).execute()
                
                if page_num == 0:
                    total_results_approx = search_response.get("pageInfo", {}).get("totalResults", 0)

                items = search_response.get("items", [])
                if not items: break
                
                # 필터링 헬퍼
                import re
                def has_korean(text): return bool(re.search(r'[가-힣]', text))
                required_terms = keyword.split()
                
                for item in items:
                    if len(collected_items) >= max_results: break
                    vid = item["id"]["videoId"]
                    snippet = item["snippet"]
                    
                    # (1) DB 중복 체크
                    if vid in known_ids: continue
                    # (2) 한국어 체크
                    if not has_korean(snippet["title"]): continue
                    # (3) 키워드 매칭
                    search_context = (snippet["title"] + " " + snippet["description"]).lower()
                    if not all(term.lower() in search_context for term in required_terms): continue
                    
                    collected_items.append({
                        "video_id": vid,
                        "title": snippet["title"],
                        "description": snippet["description"], # 영상 설명 (이메일 추출용 1순위)
                        "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                        "published_at": snippet["publishedAt"],
                        "channel_id": snippet["channelId"],
                        "channel_name": snippet["channelTitle"],
                        "video_url": f"https://www.youtube.com/watch?v={vid}"
                    })
                
                if len(collected_items) >= max_results: break
                
                next_page_token = search_response.get("nextPageToken")
                if not next_page_token: break
                
                # [Safety] 랜덤 딜레이
                import time, random
                time.sleep(random.uniform(1, 3))
                
                print(f"Page {page_num+1} done. Collected candidates: {len(collected_items)}")

            except Exception as e:
                print(f"Search API Error: {e}")
                break
        
        # 3. 2차 상세 조회 (통계 확인 및 이메일 사냥)
        final_items = []
        if collected_items:
            try:
                # 50개씩 끊어서 처리 (Detail API Quota 절약)
                filtered_candidates = collected_items[:max_results] # 일단 최대치만큼 자름
                chunk_size = 50
                
                for i in range(0, len(filtered_candidates), chunk_size):
                    chunk = filtered_candidates[i:i + chunk_size]
                    video_ids = [v["video_id"] for v in chunk]
                    
                    # (1) 영상 통계 (조회수)
                    stats_resp = self.youtube.videos().list(part="statistics", id=",".join(video_ids)).execute()
                    stats_map = {item["id"]: item["statistics"] for item in stats_resp.get("items", [])}
                    
                    # (2) 채널 정보 (설명글에서 이메일 찾기용 2순위)
                    channel_ids = list({v["channel_id"] for v in chunk})
                    channel_map = {}
                    for k in range(0, len(channel_ids), 50):
                        c_chunk = channel_ids[k:k+50]
                        chan_resp = self.youtube.channels().list(part="statistics,snippet", id=",".join(c_chunk)).execute()
                        for c_item in chan_resp.get("items", []):
                            channel_map[c_item["id"]] = {
                                "subscriber_count": int(c_item["statistics"].get("subscriberCount", 0)),
                                "description": c_item["snippet"].get("description", "")
                            }
                    
                    for v in chunk:
                        vid = v["video_id"]
                        cid = v["channel_id"]
                        
                        # 조회수 필터링
                        view_count = 0
                        if vid in stats_map:
                            view_count = int(stats_map[vid].get("viewCount", 0))
                            v["view_count"] = view_count
                        
                        if min_view_count > 0 and view_count < min_view_count:
                            continue
                            
                        # 이메일 추출 (3단계 전략)
                        chan_info = channel_map.get(cid, {})
                        
                        # 1. 영상 설명
                        email = self._extract_email_from_text(v["description"])
                        
                        # 2. 채널 설명
                        if not email:
                            email = self._extract_email_from_text(chan_info.get("description", ""))
                        
                        # [NEW] 3. DB 조회 (과거 수집 기록)
                        if not email:
                            existing_lead = db.get_lead_by_channel_id(cid)
                            if existing_lead and existing_lead.get("email"):
                                email = existing_lead["email"]

                            
                        # 이메일 필수 필터링
                        if require_email and not email:
                            continue
                            
                        v["channel_info"] = {
                            "subscriber_count": chan_info.get("subscriber_count", 0),
                            "email": email
                        }
                        final_items.append(v)
            
            except Exception as e:
                print(f"Detail API Error: {e}")
                # 에러 나더라도 수집한 건 반환
                return collected_items[:max_results], 0

        # 필터링 후 최종 결과 리턴
        return final_items, total_results_approx
    
    def _extract_email_from_text(self, text: str) -> Optional[str]:
        """텍스트에서 이메일 패턴 추출"""
        if not text:
            return None
        # 이메일 정규식 (간단 버전)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def _get_channel_details(self, channel_id: str) -> dict:
        """채널 상세 정보(설명, 구독자 수) 가져오기"""
        try:
            response = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()
            
            if response["items"]:
                item = response["items"][0]
                return {
                    "description": item["snippet"]["description"],
                    "subscriber_count": int(item["statistics"]["subscriberCount"])
                }
        except:
            pass
        return {"description": "", "subscriber_count": 0}
    
    def _get_video_details(self, video_id: str) -> dict:
        """영상 상세 통계 정보 가져오기"""
        try:
            response = self.youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()
            
            if response["items"]:
                stats = response["items"][0]["statistics"]
                return {
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0))
                }
        except Exception as e:
            print(f"Error getting video details: {e}")
        
        return {}
    
    def get_channel_info(self, channel_id: str) -> Optional[dict]:
        """채널 정보 가져오기"""
        try:
            response = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()
            
            if response["items"]:
                item = response["items"][0]
                snippet = item["snippet"]
                stats = item["statistics"]
                
                return {
                    "channel_id": channel_id,
                    "channel_name": snippet["title"],
                    "description": snippet["description"],
                    "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                    "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                    "subscriber_count": int(stats.get("subscriberCount", 0)),
                    "video_count": int(stats.get("videoCount", 0)),
                    "view_count": int(stats.get("viewCount", 0)),
                    # 이메일 추출 시도 (설명에서)
                    "email": self._extract_email_from_text(snippet["description"])
                }
        except Exception as e:
            print(f"Error getting channel info: {e}")
        
        return None
    
    def get_transcript(
        self,
        video_id: str,
        languages: list[str] = ["ko", "en"]
    ) -> Optional[str]:
        """
        영상 자막 추출 (최대한 강력하게 - Raw 모드)
        """
        try:
            print(f"[Transcript] Fetching for {video_id}...")
            
            # 1. 자막 목록 가져오기
            # (cookies.txt가 있으면 사용하여 IP 차단/연령 제한 우회)
            import os
            cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
            
            if os.path.exists(cookies_path):
                print(f"   🍪 Using cookies from {cookies_path}")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookies_path)
            else:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 2. 우선적으로 수동 생성 자막 찾기
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
                print("   ✅ Found Manual Transcript")
            except NoTranscriptFound:
                # 없으면 자동 생성 자막 찾기
                try:
                    print("   ⚠️ No Manual, trying Auto-generated...")
                    transcript = transcript_list.find_generated_transcript(languages)
                    print("   ✅ Found Auto-generated Transcript")
                except NoTranscriptFound:
                    print("   ❌ No transcript found in requested languages.")
                    return None
            
            # 3. 자막 가져오기
            script = transcript.fetch()
            
            # 텍스트만 합치기
            full_text = " ".join([entry['text'] for entry in script])
            return full_text
            
        except TranscriptsDisabled:
            print(f"   ❌ Transcripts are disabled for video {video_id}")
            return None
        except Exception as e:
            print(f"   ❌ Error fetching transcript: {e}")
            return None


# =============================================
# AI Copywriter - Gemini 기반 분석 및 작성
# =============================================

class AICopywriter:
    """Gemini AI를 이용한 영상 분석 및 마케팅 카피 작성"""
    
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        # 최신 모델 사용 (Gemini 1.5 Flash - 빠르고 저렴함)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_video(self, video_data: dict, transcript: str) -> dict:
        """영상 내용 분석 및 트렌드 파악"""
        prompt = f'''
        다음은 유튜브 영상의 정보와 자막입니다.
        
        [제목]: {video_data.get('title')}
        [채널]: {video_data.get('channel_name')}
        [자막 내용]:
        {transcript[:10000]} (중략...)
        
        이 영상을 분석해서 다음 항목을 JSON 형식으로 출력해줘:
        1. summary: 영상 내용 3줄 요약
        2. pain_points: 시청자가 겪고 있는 문제점(Pain Point) 3가지는?
        3. target_audience: 이 영상의 핵심 타겟 시청자층
        4. relevance_score: 이 영상과 '사진 정리/백업 솔루션'의 관련 점수 (0~100점)
        '''
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            print(f"AI Analysis Error: {e}")
            return {"summary": "분석 실패", "relevance_score": 0}

    def generate_email_draft(self, video_data: dict, analysis: dict) -> str:
        """콜드 메일 초안 작성"""
        prompt = f'''
        당신은 "구글 포토 용량 문제를 해결해주는 AI 사진 정리 앱(Bes2Gallery)"의 마케터입니다.
        유튜버 '{video_data.get('channel_name')}'님에게 제휴 제안 메일을 써주세요.
        
        [영상 정보]
        - 제목: {video_data.get('title')}
        - 분석: {analysis.get('summary')}
        - Pain Point: {analysis.get('pain_points')}
        
        [메일 작성 가이드]
        1. 제목은 클릭률이 높게, 영상 내용을 언급하며 자연스럽게.
        2. 서론에서 해당 영상을 잘 봤다는 구체적인 칭찬으로 시작 (진정성).
        3. 본론에서 시청자들이 겪는 '사진 용량 부족' 문제를 짚어주고, 우리 앱이 해결책임을 제시.
        4. 제안: 유료 광고가 아니라 가볍게 소개해주시면 구독자 이벤트를 지원하겠다는 톤으로.
        5. 정중하고 깔끔한 한국어 비즈니스 메일 형식.
        '''
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"작성 실패: {e}"

    def _parse_json_response(self, text: str) -> dict:
        """Gemini 응답에서 JSON 추출 (간단 파싱)"""
        import json
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except:
            return {"summary": text[:200], "relevance_score": 50}

# =============================================
# 인스턴스 생성 (외부 사용용)
# =============================================
hunter = YouTubeHunter()
copywriter = AICopywriter()
