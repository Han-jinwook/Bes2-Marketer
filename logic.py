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
    
    def search_videos(
        self,
        keyword: str,
        max_results: int = 10,
        published_after_days: int = 30,
        order: str = "relevance",
        language: str = "ko"
    ) -> list[dict]:
        """
        키워드로 YouTube 영상 검색 (Strict Mode: Space=AND)
        
        Args:
            keyword: 검색 키워드 (띄어쓰기는 AND 조건으로 처리)
            max_results: 최대 결과 수
            published_after_days: 최근 N일 이내 영상만 검색
            order: 정렬 기준
            language: 검색 언어
            
        Returns:
            검색된 영상 정보 리스트
        """
        # 날짜 필터 계산
        published_after = (
            datetime.utcnow() - timedelta(days=published_after_days)
        ).isoformat() + "Z"
        
        try:
            # 1. YouTube API로 1차 검색 (Broad Match)
            # API는 기본적으로 OR/AND가 섞인 관련성 검색을 하므로, 
            # 넉넉하게 가져온 뒤 파이썬에서 정밀 필터링합니다.
            fetch_limit = min(max_results * 3, 50)  # 필터링을 고려해 3배수 요청
            
            search_response = self.youtube.search().list(
                q=keyword,
                part="snippet",
                type="video",
                maxResults=fetch_limit,
                order=order,
                publishedAfter=published_after,
                relevanceLanguage=language,
                regionCode="KR",
                videoCaption="closedCaption"
            ).execute()
            
            # 2. 정밀 필터링 (Space = AND, Korean Only)
            import re
            def has_korean(text):
                return bool(re.search(r'[가-힣]', text))
            
            required_terms = keyword.split()
            filtered_items = []
            
            for item in search_response.get("items", []):
                snippet = item["snippet"]
                title = snippet["title"]
                description = snippet["description"]
                
                # (1) 한국어 포함 여부 체크
                if not has_korean(title):
                    continue
                
                # (2) AND 조건 체크 (모든 단어가 제목이나 설명에 있어야 함)
                # 대소문자 무시를 위해 lower() 사용
                search_context = (title + " " + description).lower()
                is_match = True
                
                for term in required_terms:
                    if term.lower() not in search_context:
                        is_match = False
                        break
                
                if is_match:
                    filtered_items.append(item)
                    
            # 요청한 개수만큼 자르기
            filtered_items = filtered_items[:max_results]
            search_response["items"] = filtered_items
            
            videos = []
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                
                # 영상 상세 정보 가져오기
                video_details = self._get_video_details(video_id)
                
                videos.append({
                    "video_id": video_id,
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "channel_id": snippet["channelId"],
                    "channel_name": snippet["channelTitle"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                    "video_url": f"https://www.youtube.com/watch?v={video_id}",
                    "view_count": video_details.get("view_count", 0),
                    "like_count": video_details.get("like_count", 0),
                    "comment_count": video_details.get("comment_count", 0),
                    "search_keyword": keyword
                })
            
            return videos
            
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
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
                    "email": self._extract_email(snippet["description"])
                }
        except Exception as e:
            print(f"Error getting channel info: {e}")
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """텍스트에서 이메일 주소 추출"""
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def get_transcript(
        self,
        video_id: str,
        languages: list[str] = ["ko", "en"]
    ) -> Optional[str]:
        """
        영상 자막 추출
        
        Args:
            video_id: YouTube 영상 ID
            languages: 우선순위 언어 목록
            
        Returns:
            자막 전체 텍스트 (없으면 None)
        """
        try:
            # 자막 목록 가져오기
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 수동 생성 자막 우선 시도
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_manually_created_transcript([lang])
                    break
                except NoTranscriptFound:
                    continue
            
            # 수동 자막 없으면 자동 생성 자막 시도
            if not transcript:
                for lang in languages:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        break
                    except NoTranscriptFound:
                        continue
            
            if transcript:
                # 자막 텍스트 추출 및 합치기
                transcript_data = transcript.fetch()
                full_text = " ".join([entry["text"] for entry in transcript_data])
                return full_text
                
        except TranscriptsDisabled:
            print(f"Transcripts disabled for video: {video_id}")
        except VideoUnavailable:
            print(f"Video unavailable: {video_id}")
        except Exception as e:
            print(f"Error getting transcript: {e}")
        
        return None
    
    def get_video_content(self, video_id: str, description: str = "") -> dict:
        """
        영상 콘텐츠 가져오기 (자막 우선, 없으면 설명)
        
        Returns:
            {
                "content": str,  # 자막 또는 설명
                "source": str,   # "transcript" 또는 "description"
            }
        """
        transcript = self.get_transcript(video_id)
        
        if transcript:
            return {
                "content": transcript,
                "source": "transcript"
            }
        else:
            return {
                "content": description,
                "source": "description"
            }
    
    def hunt(
        self,
        keywords: Optional[list[str]] = None,
        max_results_per_keyword: int = 5,
        save_to_db: bool = True
    ) -> list[dict]:
        """
        키워드 기반 영상 사냥 (전체 프로세스)
        
        Args:
            keywords: 검색 키워드 목록 (None이면 config에서 가져옴)
            max_results_per_keyword: 키워드당 최대 결과 수
            save_to_db: DB에 저장 여부
            
        Returns:
            수집된 영상 정보 리스트
        """
        if keywords is None:
            keywords = config.SEARCH_KEYWORDS
        
        all_videos = []
        
        for keyword in keywords:
            print(f"🔍 Searching: {keyword}")
            videos = self.search_videos(keyword, max_results=max_results_per_keyword)
            
            for video in videos:
                # 이미 DB에 있는지 확인
                if save_to_db and db.video_exists(video["video_id"]):
                    print(f"  ⏭️ Skip (already exists): {video['title'][:30]}...")
                    continue
                
                # 자막/설명 가져오기
                content_info = self.get_video_content(
                    video["video_id"],
                    video["description"]
                )
                video["transcript_text"] = content_info["content"]
                video["content_source"] = content_info["source"]
                
                # 채널 정보 가져오기
                channel_info = self.get_channel_info(video["channel_id"])
                if channel_info:
                    video["channel_info"] = channel_info
                
                if save_to_db:
                    # 리드(채널) 저장
                    existing_lead = db.get_lead_by_channel_id(video["channel_id"])
                    if existing_lead:
                        lead_id = existing_lead["id"]
                    else:
                        lead = db.create_lead(
                            channel_name=video["channel_name"],
                            channel_id=video["channel_id"],
                            subscriber_count=channel_info.get("subscriber_count", 0) if channel_info else 0,
                            email=channel_info.get("email") if channel_info else None,
                            keywords=[keyword],
                            channel_url=channel_info.get("channel_url") if channel_info else None,
                            thumbnail_url=channel_info.get("thumbnail_url") if channel_info else None,
                            description=channel_info.get("description") if channel_info else None
                        )
                        lead_id = lead["id"]
                    
                    # 영상 저장
                    db.create_video(
                        video_id=video["video_id"],
                        title=video["title"],
                        lead_id=lead_id,
                        upload_date=video["published_at"][:10],
                        view_count=video["view_count"],
                        like_count=video["like_count"],
                        comment_count=video["comment_count"],
                        video_url=video["video_url"],
                        thumbnail_url=video["thumbnail_url"],
                        transcript_text=video["transcript_text"],
                        search_keyword=keyword
                    )
                    print(f"  ✅ Saved: {video['title'][:40]}...")
                
                all_videos.append(video)
        
        print(f"\n📊 Total collected: {len(all_videos)} videos")
        return all_videos


# =============================================
# AI Copywriter - Gemini 기반 마케팅 콘텐츠 생성
# =============================================

class AICopywriter:
    """Gemini AI 기반 마케팅 카피라이터"""
    
    # Bes2 마케팅 시스템 프롬프트 - 핵심 철학 반영
    SYSTEM_PROMPT = """너는 '진정성 있는 마케터'야. 단순히 앱을 홍보하는 게 아니라, 구독자들의 돈과 개인정보를 진심으로 아껴주는 '동료'의 입장에서 제안 메일을 써야 해.

═══════════════════════════════════════════════════
🔥 Bes2의 핵심 철학 (이 정신이 글에 녹아들어야 함)
═══════════════════════════════════════════════════

【1. Underdog 정신 - 사용자 편에 선 유일한 앱】
수많은 유료 앱들이 "프리미엄 기능은 결제 후 이용하세요"라고 하고,
거대 클라우드 기업들은 "용량이 부족하시네요, 월 ₩2,900만 내세요"라고 할 때,
우리 Bes2는 오직 사용자 편에 섰다.
→ 100% 무료. 숨겨진 유료 기능 없음. 광고 없음. 평생 무료.
→ 대기업과 싸우는 작은 팀이 만든, 사용자를 위한 앱임을 어필해라.

【2. Privacy First - "당신의 추억은 당신의 폰 안에만"】
다른 사진 정리 앱들은 "AI 분석"을 핑계로 당신의 소중한 사진을 서버로 가져간다.
구글포토, 아이클라우드도 결국 '남의 서버'에 당신의 추억을 맡기는 것이다.
→ Bes2는 서버 전송이 **아예 없다**. 비행기 모드에서도 100% 작동한다.
→ "당신의 추억(사진)은 당신의 폰 안에만 있어야 한다"는 철학을 강조해라.
→ 이건 단순 기능이 아니라, 개인정보 보호에 대한 '신념'이다.

【3. Smart Backdoor Strategy - 똑똑한 클라우드 활용법】
우리는 "구글포토 쓰지 마세요"라고 말하지 않는다.
우리가 말하는 건 "쓰레기 사진까지 백업하느라 돈 낭비하지 마세요"다.
→ 스크린샷, 중복 사진, 흔들린 사진... 이런 쓰레기들이 클라우드 용량을 잡아먹고 있다.
→ Bes2로 먼저 '알맹이'만 남기고, 그 알맹이만 클라우드에 백업하면?
→ 15GB 무료 용량으로도 충분하다. 월 ₩2,900 결제할 필요가 사라진다.
→ 구글포토 사용자는 이 과정이 자동화된다 (원터치 백업).

═══════════════════════════════════════════════════
✍️ 글쓰기 지침
═══════════════════════════════════════════════════

【톤앤매너】
- 광고 냄새가 나면 안 된다. "이거 진짜 좋은 건데 왜 아무도 모르지?" 하는 발견의 기쁨을 전달해라.
- "구독자분들 돈 아껴드리고 싶어서 연락드렸어요" 같은 진정성이 느껴져야 한다.
- 유튜버가 "이거 콘텐츠로 만들면 구독자들한테 진짜 도움 되겠다"고 느끼게 해라.
- 절대 과장하지 마라. 팩트만으로도 충분히 매력적이다.

【필수 포함 요소】
- 영상의 구체적인 내용(자막 기반)을 언급하며 공감대 형성
- Bes2의 3가지 철학 중 최소 2가지 자연스럽게 녹여내기
- 앱 구동 영상 URL: https://bit.ly/sample_video (반드시 포함)
- "협찬/광고가 아닌, 진심으로 구독자분들께 도움 될 것 같아 연락드린다"는 뉘앙스

【피해야 할 것】
- "최고의", "혁신적인", "놀라운" 같은 과장 수식어
- 스팸처럼 느껴지는 직접적인 홍보 문구
- 기능 나열식 설명 (철학과 가치를 전달해야 함)

한국어로 작성할 것."""

    BES2_APP_VIDEO_URL = "https://bit.ly/sample_video"
    
    def __init__(self):
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # 사용 가능한 모델 동적 탐색
        model_name = "models/gemini-pro"  # 기본값
        try:
            print("🤖 Finding available Gemini models...")
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    if "gemini" in m.name:
                        model_name = m.name
                        print(f"✅ Found supported model: {model_name}")
                        break
        except Exception as e:
            print(f"⚠️ Model discovery failed, using default: {e}")

        self.model = genai.GenerativeModel(
            model_name=model_name
        )
        print(f"🚀 AICopywriter initialized with model: {model_name}")
    
    def generate_email(
        self,
        channel_name: str,
        video_title: str,
        video_content: str,
        subscriber_count: int = 0,
        tone: str = "friendly"
    ) -> str:
        """
        맞춤형 제안 이메일 생성
        
        Args:
            channel_name: 유튜버 채널명
            video_title: 영상 제목
            video_content: 영상 자막 또는 설명
            subscriber_count: 구독자 수
            tone: 톤앤매너 (friendly, professional, casual)
            
        Returns:
            생성된 이메일 본문
        """
        # 콘텐츠가 너무 길면 앞부분만 사용
        content_preview = video_content[:3000] if video_content else "내용 없음"
        
        # 시스템 프롬프트와 유저 프롬프트 결합
        prompt = f"""{self.SYSTEM_PROMPT}

---
[작업 요청]
다음 유튜버에게 Bes2 앱을 소개하는 진심 어린 제안 이메일을 작성해줘.

[타겟 유튜버 정보]
- 채널명: {channel_name}
- 구독자 수: {subscriber_count:,}명
- 최근 영상 제목: {video_title}

[영상 내용 (자막/설명) - 이 내용을 구체적으로 언급해서 공감대 형성]
{content_preview}

[이메일 작성 가이드]

1. **도입부**: 영상 내용 중 구체적인 부분을 언급하며 "저도 같은 고민을 했었다"는 공감으로 시작

2. **본론 - 아래 3가지 철학 중 2가지 이상을 자연스럽게 녹여내기**:
   - Underdog 정신: "유료 앱들과 클라우드 기업들이 돈을 요구할 때, 이 앱은 완전 무료예요"
   - Privacy First: "서버 전송이 아예 없어서 비행기 모드에서도 작동해요. 사진이 내 폰 밖으로 안 나가요"
   - Smart Backdoor: "구글포토 용량 결제 전에, 쓰레기 사진부터 정리하면 15GB로도 충분해요"

3. **제안**: "협찬/광고 제안이 아니라, 구독자분들께 진짜 도움 될 것 같아서 연락드렸어요"라는 뉘앙스

4. **마무리**: 앱 구동 영상 URL({self.BES2_APP_VIDEO_URL}) 포함, 부담 없이 확인해보시라는 톤

[톤앤매너]: {tone}
- 광고/스팸 느낌 절대 금지
- "이거 진짜 좋은 건데 왜 아무도 모르지?"하는 발견의 기쁨을 전달
- 과장 수식어(최고의, 혁신적인, 놀라운) 사용 금지

[형식]
- 제목: (매력적이지만 스팸 같지 않게)
- 본문: 400~600자"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Email generation error: {e}")
            return f"[오류] 이메일 생성 실패: {e}"
    
    def generate_comment(
        self,
        video_title: str,
        video_content: str,
        style: str = "helpful"
    ) -> str:
        """
        영상 댓글 초안 생성
        
        Args:
            video_title: 영상 제목
            video_content: 영상 자막 또는 설명
            style: 댓글 스타일 (helpful, enthusiastic, informative)
            
        Returns:
            생성된 댓글 텍스트
        """
        content_preview = video_content[:2000] if video_content else "내용 없음"
        
        # 시스템 프롬프트와 유저 프롬프트 결합
        prompt = f"""{self.SYSTEM_PROMPT}

---
[작업 요청]
다음 유튜브 영상에 달 댓글을 작성해줘. 광고가 아니라 '진짜 도움 되는 정보 공유'처럼 보여야 해.

[영상 정보]
- 제목: {video_title}
- 내용: {content_preview}

[댓글 작성 가이드]

1. **공감으로 시작**: 영상 내용 중 구체적인 부분에 공감 (예: "말씀하신 구글포토 용량 문제 진짜 공감돼요 ㅠㅠ")

2. **자연스러운 전환**: "저도 똑같은 고민하다가 우연히 발견한 게 있는데요" 형태로 도입

3. **핵심 가치 1~2개만 언급** (택1~2):
   - "완전 무료인데 광고도 없어요" (Underdog)
   - "서버로 사진 안 보내서 찝찝함이 없어요" (Privacy)
   - "이걸로 정리하고 구글포토 백업하니까 15GB로 충분하더라고요" (Smart Backdoor)

4. **링크 자연스럽게**: "영상으로 보시면 바로 이해되실 거예요 → {self.BES2_APP_VIDEO_URL}"

[스타일]: {style}

[주의사항]
- 절대 광고/홍보처럼 보이면 안 됨
- "이 앱 짱이에요!" 같은 과장 금지
- 실제 사용자가 좋은 거 발견해서 공유하는 느낌으로
- 100~150자로 짧고 자연스럽게
- 이모지는 1~2개만 자연스럽게"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Comment generation error: {e}")
            return f"[오류] 댓글 생성 실패: {e}"
    
    def summarize_video(self, video_content: str) -> str:
        """
        영상 내용 요약
        
        Args:
            video_content: 영상 자막 또는 설명
            
        Returns:
            요약된 내용
        """
        if not video_content or len(video_content) < 100:
            return "내용이 부족하여 요약할 수 없습니다."
        
        content_preview = video_content[:5000]
        
        prompt = f"""다음 유튜브 영상 자막/설명을 3~5문장으로 요약해줘.
핵심 주제와 다루는 내용을 간결하게 정리해줘.

[영상 내용]
{content_preview}"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Summary generation error: {e}")
            return f"[오류] 요약 생성 실패: {e}"
    
    def analyze_relevance(self, video_content: str) -> dict:
        """
        Bes2 앱과의 관련성 분석
        
        Args:
            video_content: 영상 자막 또는 설명
            
        Returns:
            {
                "score": float (0~1),
                "reason": str,
                "keywords_found": list[str]
            }
        """
        if not video_content:
            return {"score": 0.0, "reason": "내용 없음", "keywords_found": []}
        
        content_preview = video_content[:3000]
        
        prompt = f"""다음 영상이 'Bes2' 사진 정리 앱 마케팅에 얼마나 적합한지 분석해줘.

[Bes2 앱 관련 키워드]
사진 정리, 갤러리 정리, 용량 부족, 저장공간, 사진 백업, 구글포토, 아이클라우드, 
중복 사진, 스크린샷 정리, 핸드폰 용량, 클라우드 비용

[영상 내용]
{content_preview}

[응답 형식 - 반드시 아래 JSON 형식으로만 응답]
{{
    "score": 0.0~1.0 사이의 관련성 점수,
    "reason": "판단 이유 한 문장",
    "keywords_found": ["발견된", "관련", "키워드"]
}}"""

        try:
            response = self.model.generate_content(prompt)
            
            # JSON 파싱 시도
            import json
            import re
            
            # JSON 블록 추출
            text = response.text
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "score": float(result.get("score", 0)),
                    "reason": result.get("reason", ""),
                    "keywords_found": result.get("keywords_found", [])
                }
        except Exception as e:
            print(f"Relevance analysis error: {e}")
        
        return {"score": 0.5, "reason": "분석 실패", "keywords_found": []}
    
    def generate_drafts_for_video(
        self,
        video_id: str,
        save_to_db: bool = True
    ) -> dict:
        """
        특정 영상에 대한 이메일 + 댓글 초안 생성
        
        Args:
            video_id: DB의 video UUID
            save_to_db: DB에 저장 여부
            
        Returns:
            {
                "email": str,
                "comment": str,
                "summary": str
            }
        """
        # 영상 정보 가져오기
        video = db.get_video_with_lead(video_id)
        if not video:
            return {"error": "Video not found"}
        
        lead = video.get("leads", {})
        
        # 콘텐츠 준비
        video_content = video.get("transcript_text") or ""
        channel_name = lead.get("channel_name", "유튜버")
        subscriber_count = lead.get("subscriber_count", 0)
        
        # 요약 생성
        summary = self.summarize_video(video_content)
        
        # 이메일 생성
        email = self.generate_email(
            channel_name=channel_name,
            video_title=video["title"],
            video_content=video_content,
            subscriber_count=subscriber_count
        )
        
        # 댓글 생성
        comment = self.generate_comment(
            video_title=video["title"],
            video_content=video_content
        )
        
        # DB 저장
        if save_to_db:
            lead_id = lead.get("id")
            
            # 요약 업데이트
            db.update_video(video_id, summary=summary)
            
            # 이메일 초안 저장
            db.create_draft(
                draft_type="email",
                content=email,
                video_id=video_id,
                lead_id=lead_id,
                tone="friendly"
            )
            
            # 댓글 초안 저장
            db.create_draft(
                draft_type="comment",
                content=comment,
                video_id=video_id,
                lead_id=lead_id,
                tone="helpful"
            )
        
        return {
            "email": email,
            "comment": comment,
            "summary": summary
        }


# =============================================
# 편의 함수 (싱글톤 인스턴스)
# =============================================

# 싱글톤 인스턴스
hunter = YouTubeHunter()
copywriter = AICopywriter()


def run_full_pipeline(
    keywords: Optional[list[str]] = None,
    max_videos: int = 5,
    generate_drafts: bool = True
) -> dict:
    """
    전체 파이프라인 실행
    1. YouTube 검색 및 영상 수집
    2. 관련성 분석
    3. 이메일/댓글 초안 생성
    
    Args:
        keywords: 검색 키워드 (None이면 기본값 사용)
        max_videos: 키워드당 최대 영상 수
        generate_drafts: 초안 생성 여부
        
    Returns:
        실행 결과 요약
    """
    print("🚀 Starting Bes2 Marketer Pipeline...\n")
    
    # 1. 영상 수집
    print("=" * 50)
    print("📹 Phase 1: YouTube Hunting")
    print("=" * 50)
    videos = hunter.hunt(keywords, max_results_per_keyword=max_videos)
    
    if not videos:
        return {"status": "no_videos", "message": "수집된 영상이 없습니다."}
    
    # 2. 관련성 분석 및 초안 생성
    if generate_drafts:
        print("\n" + "=" * 50)
        print("✍️ Phase 2: AI Copywriting")
        print("=" * 50)
        
        # DB에서 최근 저장된 영상 가져오기
        recent_videos = db.get_all_videos(limit=len(videos))
        
        for video in recent_videos:
            print(f"\n📝 Processing: {video['title'][:40]}...")
            
            # 관련성 분석
            relevance = copywriter.analyze_relevance(video.get("transcript_text", ""))
            db.update_video(video["id"], relevance_score=relevance["score"])
            print(f"   관련성: {relevance['score']:.1%} - {relevance['reason']}")
            
            # 관련성 높은 영상만 초안 생성
            if relevance["score"] >= 0.5:
                drafts = copywriter.generate_drafts_for_video(video["id"])
                print(f"   ✅ 이메일/댓글 초안 생성 완료")
            else:
                print(f"   ⏭️ 관련성 낮음 - 초안 생성 스킵")
    
    # 결과 요약
    stats = {
        "videos_collected": len(videos),
        "leads": db.get_lead_stats(),
        "drafts": db.get_draft_stats()
    }
    
    print("\n" + "=" * 50)
    print("📊 Pipeline Complete!")
    print("=" * 50)
    print(f"수집된 영상: {stats['videos_collected']}개")
    print(f"총 리드: {stats['leads']['total']}개")
    print(f"생성된 초안: {stats['drafts']['total']}개")
    
    return stats


# =============================================
# 테스트 코드
# =============================================

if __name__ == "__main__":
    print("🧪 Testing Bes2 Marketer Logic...\n")
    
    # 설정 검증
    is_valid, missing = config.validate()
    if not is_valid:
        print(f"❌ Missing environment variables: {missing}")
        print("Please check your .env file")
        exit(1)
    
    print("✅ Configuration validated\n")
    
    # 간단한 테스트
    print("Testing YouTube search...")
    test_videos = hunter.search_videos("사진 정리", max_results=2)
    
    if test_videos:
        print(f"Found {len(test_videos)} videos")
        for v in test_videos:
            print(f"  - {v['title'][:50]}...")
    else:
        print("No videos found (check your API key)")

