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
        try:
            self.youtube = build(
                "youtube", "v3",
                developerKey=config.YOUTUBE_API_KEY
            )
        except Exception as e:
            print(f"Warning: Failed to initialize YouTube API: {e}")
            self.youtube = None
    
    def search_videos(self, keyword: str, max_results: int = 10, published_after_days: int = 30, min_view_count: int = 0, require_email: bool = False) -> tuple[list[dict], int, dict]:
        """
        유튜브 영상 검색 (Deep Search 적용)
        - require_email=True 시 이메일 없는 영상은 결과에서 제외
        """
        from database import db
        
        # 1. 날짜 및 초기값 설정
        published_after = (datetime.utcnow() - timedelta(days=published_after_days)).isoformat("T") + "Z"
        print(f"Searching for '{keyword}' after {published_after}...")
        
        
        # [TEMPORARY FIX] DB 중복 체크 비활성화 (데이터 재수집 허용)
        known_ids = set()  # db.get_known_video_ids()
        collected_items = []
        next_page_token = None
        total_results_approx = 0
        
        # 필터링 통계 초기화
        self._temp_filter_stats = {
            "skipped_db": 0,
            "skipped_lang": 0,
            "skipped_negative": 0,
            "skipped_view": 0,
            "skipped_no_email": 0
        }
        
        # [FIX] 채널 이메일 캐시 (중복 스캔 방지)
        self._channel_email_cache = {}
        
        # 2. 1차 검색 (최대 10페이지 = 500개 후보군 탐색)
        for page_num in range(10):
            try:
                search_response = self.youtube.search().list(
                    q=keyword, part="id,snippet", maxResults=50,
                    order="date", publishedAfter=published_after, type="video", pageToken=next_page_token
                ).execute()
                
                # [STATS] 필터링 통계
                filter_stats = getattr(self, "_temp_filter_stats", {
                    "skipped_db": 0, "skipped_lang": 0, "skipped_negative": 0, 
                    "skipped_view": 0, "skipped_no_email": 0
                })
                
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
                    if vid in known_ids: 
                        self._temp_filter_stats["skipped_db"] += 1
                        continue
                    # (2) 한국어 체크 [TEMP DISABLED FOR DEBUG]
                    # if not has_korean(snippet["title"]): 
                    #     self._temp_filter_stats["skipped_lang"] += 1
                    #     continue
                    
                    # (3) [Strict Filter] 키워드 정밀 매칭 & 제외어 필터링
                    
                    # A. 검색 텍스트 (제목 + 설명)
                    text_to_check = (snippet["title"] + " " + snippet["description"]).lower()
                    
                    # B. 제외어 (Negative Keywords) [TEMP DISABLED FOR DEBUG]
                    # negative_keywords = ["맥주", "beer", "날씨", "weather", "하늘", "sky", "빵", "bread"]
                    # if any(neg in text_to_check for neg in negative_keywords):
                    #     self._temp_filter_stats["skipped_negative"] += 1
                    #     continue

                    # [ALL FILTERS REMOVED] 유튜브 API가 주는 걸 그대로 수집
                    
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
                
                print(f"📊 Page {page_num+1} Stats:")
                print(f"   - API returned: {len(items)} items")
                print(f"   - Collected so far: {len(collected_items)}")
                print(f"   - Filter Stats: {self._temp_filter_stats}")
                
                # [DEBUG] UI에도 표시
                import streamlit as st
                st.info(f"📊 Page {page_num+1}: API returned {len(items)}, Collected: {len(collected_items)}")

            except Exception as e:
                import streamlit as st
                st.error(f"⚠️ YouTube API Error (Page {page_num}): {e}")
                print(f"Search API Error: {e}")
                # Don't break immediately, maybe retry? 
                # For now, break to avoid infinite loops if key is dead.
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
                            self._temp_filter_stats["skipped_view"] += 1
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

                        # [NEW] 4. Deep Scan (최신 영상 5개 뒤지기)
                        # 캐시 확인 → 같은 채널은 한 번만 스캔
                        if not email:
                            if cid in self._channel_email_cache:
                                email = self._channel_email_cache[cid]
                                if email:
                                    print(f"   ✅ Found cached email for channel {cid}")
                            else:
                                print(f"Deep scanning channel {cid} for email...")
                                email = self._deep_scan_email(cid)
                                # 캐시 저장 (None이어도 저장해서 재시도 방지)
                                self._channel_email_cache[cid] = email

                            
                            
                        # [REMOVED] 이메일 필수 필터링 제거 - 사용자 요청
                        # 이메일 없어도 모두 수집하고, 나중에 수동으로 입력
                        # if require_email and not email:
                        #     self._temp_filter_stats["skipped_no_email"] += 1
                        #     continue
                            
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
        return final_items, total_results_approx, self._temp_filter_stats
    
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
    
    def _deep_scan_email(self, channel_id: str) -> Optional[str]:
        """[Deep Scan] 채널의 최신 영상 5개를 조회하여 설명글에서 이메일 탐색"""
        try:
            # 1. 채널의 '업로드' 재생목록 ID 가져오기
            ch_resp = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            if not ch_resp["items"]: return None
            
            uploads_playlist_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # 2. 최신 영상 5개 가져오기
            pl_resp = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=5
            ).execute()
            
            # 3. 설명글 스캔
            for item in pl_resp.get("items", []):
                desc = item["snippet"].get("description", "")
                found_email = self._extract_email_from_text(desc)
                if found_email:
                    print(f"   ✨ Deep Scan Success! Found email in video: {item['snippet']['title']}")
                    return found_email
                    
        except Exception as e:
            print(f"Deep scan failed for {channel_id}: {e}")
        
        return None
    
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
        영상 자막 추출 (쿠키 주입으로 IP 차단 완벽 우회)
        Method 1: youtube-transcript-api (cookies.txt)
        Method 2: yt-dlp (cookies.txt + User-Agent)
        """
        import time
        import random
        import os
        import tempfile
        
        # 쿠키 파일 경로 확인 (로컬 + Streamlit Cloud 지원)
        cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        has_cookies = os.path.exists(cookies_path)
        
        # Streamlit Cloud: Secrets에서 쿠키 로드
        if not has_cookies:
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'YOUTUBE_COOKIES' in st.secrets:
                    # 임시 파일로 쿠키 저장
                    cookies_path = os.path.join(tempfile.gettempdir(), 'youtube_cookies.txt')
                    with open(cookies_path, 'w', encoding='utf-8') as f:
                        f.write(st.secrets['YOUTUBE_COOKIES'])
                    has_cookies = True
                    print(f"   🍪 Loaded cookies from Streamlit Secrets")
            except:
                pass
        
        if has_cookies:
            print(f"   🍪 Using cookies for IP bypass")
        else:
            print(f"   ℹ️ No cookies - May face IP blocking")
        
        # 봇 차단 우회용 User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Method 1: youtube-transcript-api (쿠키 주입)
        for attempt in range(2):  # 2번 재시도
            try:
                print(f"[Transcript] Method 1 (Attempt {attempt + 1}): youtube-transcript-api for {video_id}...")
                
                # Rate limiting (너무 빠른 요청 방지)
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    print(f"   ⏳ Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                
                # 쿠키 사용
                if has_cookies:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookies_path)
                else:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                transcript = None

                # 우선순위 언어 시도
                try:
                    transcript = transcript_list.find_transcript(languages)
                    print(f"   ✅ Found transcript in {languages}")
                except:
                    # Fallback: 아무 언어나
                    try:
                        transcript = next(iter(transcript_list))
                        print(f"   ✅ Found fallback transcript: {transcript.language_code}")
                    except:
                        print("   ❌ No transcripts via youtube-transcript-api")
                        continue
  
                if transcript:
                    transcript_data = transcript.fetch()
                    full_text = " ".join([entry["text"] for entry in transcript_data])
                    print(f"   ✅ Transcript extracted ({len(full_text)} chars)")
                    return full_text

            except TranscriptsDisabled:
                print(f"   ❌ Transcripts DISABLED")
                break  # 재시도 불필요
            except VideoUnavailable:
                print(f"   ❌ Video UNAVAILABLE")
                break
            except Exception as e:
                print(f"   ⚠️ Method 1 Attempt {attempt + 1} failed: {e}")
                if attempt == 1:  # 마지막 시도
                    print(f"   → Moving to Method 2...")

        # Method 2: yt-dlp (쿠키 + User-Agent)
        try:
            print(f"[Transcript] Method 2: yt-dlp (IP bypass) for {video_id}...")
            import yt_dlp
            
            # Rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': languages,
                'quiet': True,
                'no_warnings': True,
                'user_agent': random.choice(user_agents),  # User-Agent 스푸핑
            }
            
            # 쿠키 주입
            if has_cookies:
                ydl_opts['cookiefile'] = cookies_path
                print(f"   🍪 Using cookies for yt-dlp")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                # 자막 추출
                if 'subtitles' in info and info['subtitles']:
                    # 수동 자막 우선
                    for lang in languages:
                        if lang in info['subtitles']:
                            subtitle_url = info['subtitles'][lang][0]['url']
                            import requests
                            response = requests.get(subtitle_url, headers={'User-Agent': random.choice(user_agents)})
                            if response.status_code == 200:
                                text = self._parse_subtitle_text(response.text)
                                print(f"   ✅ yt-dlp extracted subtitle ({len(text)} chars)")
                                return text
                
                # 자동 생성 자막
                if 'automatic_captions' in info and info['automatic_captions']:
                    for lang in languages:
                        if lang in info['automatic_captions']:
                            subtitle_url = info['automatic_captions'][lang][0]['url']
                            import requests
                            response = requests.get(subtitle_url, headers={'User-Agent': random.choice(user_agents)})
                            if response.status_code == 200:
                                text = self._parse_subtitle_text(response.text)
                                print(f"   ✅ yt-dlp extracted auto-caption ({len(text)} chars)")
                                return text
                                
        except Exception as e:
            print(f"   ❌ Method 2 (yt-dlp) failed: {e}")
            
        print(f"   ❌ All methods failed for {video_id} (Possible IP block - Try adding cookies.txt)")
        return None
    
    def _parse_subtitle_text(self, subtitle_content: str) -> str:
        """VTT/SRT 자막에서 텍스트만 추출"""
        import re
        # 타임코드 제거 (00:00:00.000 형식)
        text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}.*?\n', '', subtitle_content)
        # 번호 줄 제거
        text = re.sub(r'^\d+\n', '', text, flags=re.MULTILINE)
        # 빈 줄 제거
        text = re.sub(r'\n+', ' ', text)
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


# =============================================
# AI Copywriter - Gemini 기반 분석 및 작성
# =============================================

class AICopywriter:
    """Gemini AI를 이용한 영상 분석 및 마케팅 카피 작성 (Multi-Model Support)"""
    
    # 무료 티어에서 사용 가능한 모델 리스트 (우선순위 순)
    AVAILABLE_MODELS = [
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b',
        'gemini-2.0-flash-lite-preview-02-05',
        'gemini-2.0-flash-exp'
    ]
    
    def __init__(self):
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.api_ready = True
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini API: {e}")
            self.api_ready = False

    def _generate_with_retry(self, prompt: str) -> str:
        """여러 모델을 순회하며 생성 시도 (Fallback Logic)"""
        if not self.api_ready:
            raise Exception("Gemini API Key가 설정되지 않았거나 초기화에 실패했습니다.")

        last_error = None
        
        for model_name in self.AVAILABLE_MODELS:
            try:
                # 모델 동적 로드
                model = genai.GenerativeModel(model_name)
                # print(f"🤖 Trying model: {model_name}...") 
                
                response = model.generate_content(prompt)
                
                if response.text:
                    # 성공 시 바로 반환
                    # print(f"✅ Success with {model_name}")
                    return response.text.strip()
                    
            except Exception as e:
                # print(f"⚠️ Failed with {model_name}: {e}")
                last_error = e
                continue # 다음 모델 시도
        
        # 모든 모델 실패 시
        raise Exception(f"All models failed. Last error: {last_error}")

    def analyze_video(self, video_data: dict, transcript: str) -> dict:
        """영상 내용 분석 (Legacy support)"""
        return {
            "summary": self.summarize_video(transcript),
            "relevance_score": 90
        }

    def summarize_video(self, video_content: str) -> str:
        """영상 내용 3줄 요약"""
        prompt = f'''
        다음 유튜브 영상 자막을 읽고, 핵심 내용을 3줄로 간결하게 요약해줘.
        
        [자막 내용]:
        {video_content[:15000]}
        
        [출력 형식]:
        1. ...
        2. ...
        3. ...
        '''
        try:
            return self._generate_with_retry(prompt)
        except Exception as e:
            return f"요약 실패 (AI Error: {str(e)})"

    def generate_email(self, channel_name: str, video_title: str, video_content: str, subscriber_count: int) -> str:
        """제휴 제안 이메일 생성 (Bes2 철학 반영)"""
        
        prompt = f'''
        당신은 "오직 사용자 편에 선 무료 & 온디바이스 사진 정리 앱, Bes2Gallery(베스트갤러리)"의 개발자이자 마케터입니다.
        유튜버 '{channel_name}'님에게 보낼 진정성 있는 제휴 제안 메일을 작성해주세요.
        
        [Bes2Gallery 핵심 철학]
        1. **Underdog Spirit:** 거대 클라우드 기업들이 돈을 요구할 때, 우리는 무료 & 온디바이스로 사용자 편에 섭니다.
        2. **Privacy First:** "당신의 추억(사진)은 당신의 폰 안에만 있어야 합니다." 서버 전송 0%로 완벽한 보안을 보장합니다.
        3. **Smart Backdoor Strategy:** 구글포토를 쓰지 말라는 게 아닙니다. "쓰레기 사진까지 백업해서 돈 낭비하지 말고, Bes2로 알맹이만 남긴 뒤 똑똑하게 백업하세요."라는 현실적인 솔루션입니다.
        
        [수신자 정보]
        - 채널명: {channel_name} (구독자 {subscriber_count:,}명)
        - 영상 제목: {video_title}
        - 영상 내용(자막 일부): {video_content[:2000]}...
        
        [작성 가이드]
        1. **제목:** 클릭을 유도하되 낚시성이 아닌, 영상 내용과 우리 솔루션의 접점을 언급하세요. (예: "{video_title} 영상 잘 봤습니다. 사진 용량 문제에 대한 새로운 대안을 제안드립니다.")
        2. **도입:** 해당 영상의 내용을 구체적으로 언급하며 진정성 있게 칭찬하고 공감대를 형성하세요.
        3. **본문 (Pain Point & Solution):** 
           - 구독자들이 겪는 '사진 용량 부족', '클라우드 비용 부담', '개인정보 유출 우려'를 짚어주세요.
           - Bes2Gallery가 이 문제를 어떻게 해결하는지(무료, 온디바이스, 스마트 정리) 철학을 녹여 설명하세요.
        4. **제안:** 
            - 단순 광고 요청이 아니라, "구독자분들의 지갑과 프라이버시를 지켜주는 유용한 정보를 소개해주세요"라는 뉘앙스로 접근하세요.
            - "좋은 앱을 발견해서 소개한다"는 느낌으로 가볍게 다뤄주셔도 좋다고 제안하세요. (유료 광고 X, 협찬/이벤트 지원 가능 시사)
        5. **톤앤매너:** 정중하고 예의 바르지만, 우리의 철학에 대한 확신이 느껴지는 당당한 어조. (단순 스팸처럼 보이지 않게 주의)
        '''
        
        try:
            return self._generate_with_retry(prompt)
        except Exception as e:
            return f"[AI 에러] 이메일 생성 실패: {str(e)}"

    def generate_comment(self, channel_name: str, video_title: str, video_content: str) -> str:
        """유튜브 댓글 마케팅 문구 생성"""
        
        prompt = f'''
        유튜버 '{channel_name}'님의 영상 "{video_title}"에 달 유튜브 댓글 3가지를 작성해주세요.
        우리는 "무료 & 온디바이스 사진 정리 앱, Bes2Gallery"입니다.
        
        [영상 내용 요약]:
        {video_content[:1000]}...
        
        [댓글 작성 전략 - 3가지 버전]
        1. **공감형:** 영상 내용에 공감하면서, "사진 정리할 때 진짜 편한 무료 앱이 있더라"고 자연스럽게 추천 (바이럴 느낌).
        2. **정보성:** "구글포토 결제하기 전에 갤러리 정리부터 하는 게 돈 아끼는 팁입니다. Bes2Gallery 써보세요." (경제성 강조).
        3. **보안 강조:** "내 사진 서버에 올리기 찜찜했는데, 폰에서만 정리되는 앱이라 안심되네요." (Privacy 강조).
        
        [주의사항]
        - 너무 노골적인 광고처럼 보이지 않게, 실제 사용자의 후기나 꿀팁 공유처럼 자연스럽게 작성하세요.
        - 이모지(😊, 👍, 📱)를 적절히 섞어주세요.
        - 버전별로 번호를 매겨서 출력해주세요.
        '''
        
        try:
            return self._generate_with_retry(prompt)
        except Exception as e:
            return f"[AI 에러] 댓글 생성 실패: {str(e)}"

    def generate_email_draft(self, video_data: dict, analysis: dict) -> str:
        """Legacy Support Wrapper"""
        # 기존 코드가 이 메서드를 부를 경우를 대비해 generate_email로 연결
        return self.generate_email(
            channel_name=video_data.get('channel_name', ''),
            video_title=video_data.get('title', ''),
            video_content=analysis.get('summary', ''),
            subscriber_count=0
        )

# =============================================
# 인스턴스 생성 (외부 사용용)
# =============================================
hunter = YouTubeHunter()
copywriter = AICopywriter()
