"""
Bes2 Marketer - Streamlit UI
AI 기반 유튜브 마케팅 자동화 대시보드
"""

import streamlit as st
from datetime import datetime
import time

from config import config
from database import db, test_connection
from logic import hunter, copywriter, AICopywriter

# =============================================
# 페이지 설정
# =============================================

st.set_page_config(
    page_title="Bes2 Marketer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# 커스텀 CSS
# =============================================

st.markdown("""
<style>
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 헤더 스타일 */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }
    
    /* 카드 스타일 */
    .video-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }
    
    .video-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* 통계 카드 */
    .stat-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.3rem;
    }
    
    /* 복사 버튼 */
    .copy-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* 사이드바 */
    .css-1d391kg {
        background: #f8f9fa;
    }
    
    /* 초안 박스 */
    .draft-box {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    /* 상태 뱃지 */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-new { background: #e3f2fd; color: #1976d2; }
    .status-contacted { background: #fff3e0; color: #f57c00; }
    .status-converted { background: #e8f5e9; color: #388e3c; }
    
    /* 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}  /* Deploy 버튼 숨기기 */
</style>
""", unsafe_allow_html=True)

# =============================================
# 키워드 저장 파일 경로
# =============================================
import json
import os

KEYWORDS_FILE = "saved_keywords.json"

def load_saved_keywords() -> str:
    """저장된 키워드 불러오기"""
    if os.path.exists(KEYWORDS_FILE):
        try:
            with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("keywords", "사진 정리, 갤러리 정리, 용량 부족, 구글포토 백업")
        except:
            pass
    return "사진 정리, 갤러리 정리, 용량 부족, 구글포토 백업"

def save_keywords(keywords: str):
    """키워드 저장하기"""
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        json.dump({"keywords": keywords}, f, ensure_ascii=False, indent=2)

# =============================================
# 세션 상태 초기화
# =============================================

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "saved_keywords" not in st.session_state:
    st.session_state.saved_keywords = load_saved_keywords()
if "selected_video" not in st.session_state:
    st.session_state.selected_video = None
if "generated_drafts" not in st.session_state:
    st.session_state.generated_drafts = {}
if "comment_versions" not in st.session_state:
    st.session_state.comment_versions = {}

# =============================================
# 헤더
# =============================================

st.markdown("""
<div class="main-header">
    <h1>🚀 Bes2 Marketer</h1>
    <p>AI 기반 유튜브 마케팅 자동화 대시보드</p>
</div>
""", unsafe_allow_html=True)

# =============================================
# 사이드바
# =============================================

with st.sidebar:
    st.markdown("## ⚙️ 검색 설정")
    
    # 키워드 입력 (저장된 값 불러오기)
    keywords_input = st.text_area(
        "🔍 검색 키워드",
        value=st.session_state.saved_keywords,
        help="쉼표(,)는 OR, 띄어쓰기는 AND 조건입니다. 예: '사진 정리, 용량 부족' -> ('사진' AND '정리') 또는 ('용량' AND '부족')",
        height=100
    )
    
    # 키워드 저장 버튼
    col_save1, col_save2 = st.columns([1, 1])
    with col_save1:
        if st.button("💾 키워드 저장", use_container_width=True):
            save_keywords(keywords_input)
            st.session_state.saved_keywords = keywords_input
            st.success("✅ 저장됨!")
    with col_save2:
        if st.button("🔄 초기화", use_container_width=True):
            default_kw = "사진 정리, 갤러리 정리, 용량 부족, 구글포토 백업"
            save_keywords(default_kw)
            st.session_state.saved_keywords = default_kw
            st.rerun()
    
    st.markdown("---")
    
    # 검색 기간
    period_options = {
        "최근 1일": 1,
        "최근 1주일": 7,
        "최근 1개월": 30,
        "최근 3개월": 90
    }
    selected_period = st.selectbox(
        "📅 검색 기간",
        options=list(period_options.keys()),
        index=2
    )
    
    # 결과 수
    max_results = st.slider(
        "📊 키워드당 최대 결과",
        min_value=1,
        max_value=20,
        value=5
    )
    
    st.markdown("---")
    
    # 검색 버튼
    search_clicked = st.button(
        "🎯 영상 검색 시작",
        type="primary",
        use_container_width=True
    )
    
    if search_clicked:
        # 환경 변수 검증
        is_valid, missing = config.validate()
        if not is_valid:
            st.error(f"❌ 환경 변수 누락: {', '.join(missing)}")
            st.info("`.env` 파일을 확인해주세요.")
        else:
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            days = period_options[selected_period]
            
            with st.spinner("🔍 유튜브 검색 중..."):
                try:
                    all_videos = []
                    progress_bar = st.progress(0)
                    
                    for i, keyword in enumerate(keywords):
                        st.text(f"검색 중: {keyword}")
                        videos = hunter.search_videos(
                            keyword=keyword,
                            max_results=max_results,
                            published_after_days=days
                        )
                        
                        for video in videos:
                            # 자막/설명 가져오기
                            content = hunter.get_video_content(
                                video["video_id"],
                                video["description"]
                            )
                            video["transcript_text"] = content["content"]
                            video["content_source"] = content["source"]
                            
                            # 채널 정보
                            channel_info = hunter.get_channel_info(video["channel_id"])
                            if channel_info:
                                video["channel_info"] = channel_info
                            
                            all_videos.append(video)
                        
                        progress_bar.progress((i + 1) / len(keywords))
                    
                    st.session_state.search_results = all_videos
                    st.success(f"✅ {len(all_videos)}개 영상 수집 완료!")
                    
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    
    st.markdown("---")
    
    # DB 통계
    st.markdown("### 📊 DB 현황")
    
    try:
        if test_connection():
            lead_stats = db.get_lead_stats()
            draft_stats = db.get_draft_stats()
            video_count = db.get_video_count()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("리드", lead_stats["total"])
                st.metric("영상", video_count)
            with col2:
                st.metric("이메일 초안", draft_stats["email"]["total"])
                st.metric("댓글 초안", draft_stats["comment"]["total"])
        else:
            st.warning("DB 연결 안됨")
    except:
        st.info("DB 설정 필요")

# =============================================
# 메인 탭
# =============================================

tab1, tab2, tab3 = st.tabs([
    "📹 영상 리스트 & 분석",
    "✉️ 이메일 발송 관리",
    "💬 댓글/커뮤니티 마케팅"
])

# =============================================
# 탭 1: 영상 리스트 & 분석
# =============================================

with tab1:
    st.markdown("### 📹 수집된 영상 목록")
    
    # 데이터 소스 선택
    data_source = st.radio(
        "데이터 소스",
        ["🔍 검색 결과", "💾 DB 저장된 영상"],
        horizontal=True
    )
    
    videos_to_show = []
    
    if data_source == "🔍 검색 결과":
        videos_to_show = st.session_state.search_results
    else:
        try:
            db_videos = db.get_all_videos(limit=50)
            for v in db_videos:
                lead = None
                if v.get("lead_id"):
                    lead = db.get_lead_by_id(v["lead_id"])
                videos_to_show.append({
                    "video_id": v["video_id"],
                    "title": v["title"],
                    "channel_name": lead["channel_name"] if lead else "Unknown",
                    "channel_id": lead["channel_id"] if lead else "",
                    "thumbnail_url": v.get("thumbnail_url", ""),
                    "video_url": v.get("video_url", f"https://youtube.com/watch?v={v['video_id']}"),
                    "view_count": v.get("view_count", 0),
                    "transcript_text": v.get("transcript_text", ""),
                    "summary": v.get("summary", ""),
                    "relevance_score": v.get("relevance_score", 0),
                    "db_id": v["id"],
                    "channel_info": {
                        "subscriber_count": lead.get("subscriber_count", 0) if lead else 0,
                        "email": lead.get("email") if lead else None
                    }
                })
        except Exception as e:
            st.info("DB에 저장된 영상이 없습니다.")
    
    if not videos_to_show:
        st.info("👈 사이드바에서 키워드를 입력하고 [영상 검색 시작] 버튼을 눌러주세요.")
    else:
        st.markdown(f"**총 {len(videos_to_show)}개 영상**")
        
        for idx, video in enumerate(videos_to_show):
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if video.get("thumbnail_url"):
                        st.image(video["thumbnail_url"], use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/320x180?text=No+Thumbnail", use_container_width=True)
                
                with col2:
                    st.markdown(f"**{video['title'][:60]}{'...' if len(video['title']) > 60 else ''}**")
                    st.caption(f"📺 {video['channel_name']}")
                    
                    # 통계 정보
                    views = video.get("view_count", 0)
                    subs = video.get("channel_info", {}).get("subscriber_count", 0)
                    
                    info_cols = st.columns(3)
                    with info_cols[0]:
                        st.caption(f"👁️ 조회수: {views:,}")
                    with info_cols[1]:
                        st.caption(f"👥 구독자: {subs:,}")
                    with info_cols[2]:
                        relevance = video.get("relevance_score", 0)
                        if relevance > 0:
                            st.caption(f"🎯 관련성: {relevance:.0%}")
                    
                    # 자막 유무
                    has_transcript = bool(video.get("transcript_text"))
                    st.caption(f"📝 자막: {'✅ 있음' if has_transcript else '❌ 없음 (설명 사용)'}")
                
                with col3:
                    # 분석 버튼
                    if st.button("🤖 분석 & 초안 생성", key=f"analyze_{idx}", use_container_width=True):
                        with st.spinner("AI 분석 중..."):
                            try:
                                # 관련성 분석
                                content = video.get("transcript_text", video.get("description", ""))
                                relevance = copywriter.analyze_relevance(content)
                                
                                # 이메일 생성
                                email = copywriter.generate_email(
                                    channel_name=video["channel_name"],
                                    video_title=video["title"],
                                    video_content=content,
                                    subscriber_count=video.get("channel_info", {}).get("subscriber_count", 0)
                                )
                                
                                # 댓글 생성
                                comment = copywriter.generate_comment(
                                    video_title=video["title"],
                                    video_content=content
                                )
                                
                                # 요약
                                summary = copywriter.summarize_video(content)
                                
                                # 세션에 저장
                                st.session_state.generated_drafts[video["video_id"]] = {
                                    "video": video,
                                    "email": email,
                                    "comment": comment,
                                    "summary": summary,
                                    "relevance": relevance
                                }
                                
                                # DB에 저장 (검색 결과인 경우)
                                if data_source == "🔍 검색 결과":
                                    # 리드 저장
                                    existing_lead = db.get_lead_by_channel_id(video["channel_id"])
                                    if existing_lead:
                                        lead_id = existing_lead["id"]
                                    else:
                                        lead = db.create_lead(
                                            channel_name=video["channel_name"],
                                            channel_id=video["channel_id"],
                                            subscriber_count=video.get("channel_info", {}).get("subscriber_count", 0),
                                            email=video.get("channel_info", {}).get("email"),
                                            keywords=[video.get("search_keyword", "")],
                                        )
                                        lead_id = lead["id"]
                                    
                                    # 영상 저장
                                    if not db.video_exists(video["video_id"]):
                                        saved_video = db.create_video(
                                            video_id=video["video_id"],
                                            title=video["title"],
                                            lead_id=lead_id,
                                            view_count=video.get("view_count", 0),
                                            video_url=video.get("video_url"),
                                            thumbnail_url=video.get("thumbnail_url"),
                                            transcript_text=content,
                                            summary=summary,
                                            relevance_score=relevance["score"]
                                        )
                                        video_db_id = saved_video["id"]
                                    else:
                                        existing = db.get_video_by_video_id(video["video_id"])
                                        video_db_id = existing["id"]
                                    
                                    # 초안 저장
                                    db.create_draft(
                                        draft_type="email",
                                        content=email,
                                        video_id=video_db_id,
                                        lead_id=lead_id
                                    )
                                    db.create_draft(
                                        draft_type="comment",
                                        content=comment,
                                        video_id=video_db_id,
                                        lead_id=lead_id
                                    )
                                
                                st.success("✅ 분석 완료! 탭 2, 3에서 확인하세요.")
                                
                            except Exception as e:
                                st.error(f"오류: {e}")
                    
                    # 유튜브 링크
                    st.link_button("🔗 영상 보기", video.get("video_url", "#"), use_container_width=True)
                
                st.markdown("---")

# =============================================
# 탭 2: 이메일 발송 관리
# =============================================

with tab2:
    st.markdown("### ✉️ 이메일 초안 관리")
    
    # 생성된 초안이 있는지 확인
    drafts = st.session_state.generated_drafts
    
    if not drafts:
        # DB에서 이메일 초안 가져오기
        try:
            db_drafts = db.get_all_drafts(draft_type="email", limit=20)
            if db_drafts:
                st.info("💾 DB에 저장된 이메일 초안을 불러왔습니다.")
                for draft in db_drafts:
                    video = db.get_video_by_id(draft["video_id"]) if draft.get("video_id") else None
                    lead = db.get_lead_by_id(draft["lead_id"]) if draft.get("lead_id") else None
                    
                    if video and lead:
                        drafts[video["video_id"]] = {
                            "video": {
                                "title": video["title"],
                                "channel_name": lead["channel_name"],
                                "video_id": video["video_id"]
                            },
                            "email": draft["content"],
                            "channel_info": {
                                "email": lead.get("email"),
                                "subscriber_count": lead.get("subscriber_count", 0)
                            }
                        }
        except:
            pass
    
    if not drafts:
        st.info("📝 탭 1에서 영상을 선택하고 [분석 & 초안 생성] 버튼을 눌러주세요.")
    else:
        # 초안 선택
        draft_options = {f"{d['video']['channel_name']} - {d['video']['title'][:30]}...": vid 
                        for vid, d in drafts.items() if d.get("email")}
        
        if draft_options:
            selected_draft_key = st.selectbox(
                "📋 이메일 초안 선택",
                options=list(draft_options.keys())
            )
            
            if selected_draft_key:
                selected_vid = draft_options[selected_draft_key]
                draft_data = drafts[selected_vid]
                video_info = draft_data["video"]
                
                st.markdown("---")
                
                # 수신자 정보
                col1, col2 = st.columns(2)
                with col1:
                    channel_name = st.text_input(
                        "👤 유튜버 이름",
                        value=video_info.get("channel_name", ""),
                        key="email_channel_name"
                    )
                with col2:
                    email_addr = st.text_input(
                        "📧 이메일 주소",
                        value=draft_data.get("channel_info", {}).get("email") or "이메일 주소를 입력하세요",
                        key="email_address"
                    )
                
                st.markdown("---")
                
                # 이메일 내용
                email_content = draft_data.get("email", "")
                
                # 제목 추출 (첫 줄이 제목인 경우)
                lines = email_content.strip().split("\n")
                default_subject = ""
                default_body = email_content
                
                for i, line in enumerate(lines):
                    if "제목:" in line or "Subject:" in line:
                        default_subject = line.replace("제목:", "").replace("Subject:", "").strip()
                        default_body = "\n".join(lines[i+1:]).strip()
                        break
                
                email_subject = st.text_input(
                    "📌 이메일 제목",
                    value=default_subject or f"[협업 제안] {channel_name}님께 드리는 무료 앱 소개",
                    key="email_subject"
                )
                
                email_body = st.text_area(
                    "📝 이메일 본문",
                    value=default_body,
                    height=400,
                    key="email_body"
                )
                
                st.markdown("---")
                
                # 버튼들
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    full_email = f"제목: {email_subject}\n\n{email_body}"
                    st.code(full_email[:100] + "...", language=None)
                    
                    if st.button("📋 전체 복사하기", type="primary", use_container_width=True, key="copy_email"):
                        st.code(full_email, language=None)
                        st.success("👆 위 내용을 드래그해서 복사하세요!")
                
                with col2:
                    if st.button("📋 본문만 복사", use_container_width=True, key="copy_body"):
                        st.code(email_body, language=None)
                        st.success("👆 위 내용을 드래그해서 복사하세요!")
                
                with col3:
                    if st.button("🔄 재생성", use_container_width=True, key="regen_email"):
                        with st.spinner("재생성 중..."):
                            new_email = copywriter.generate_email(
                                channel_name=channel_name,
                                video_title=video_info["title"],
                                video_content=draft_data.get("video", {}).get("transcript_text", ""),
                                subscriber_count=draft_data.get("channel_info", {}).get("subscriber_count", 0)
                            )
                            drafts[selected_vid]["email"] = new_email
                            st.rerun()

# =============================================
# 탭 3: 댓글/커뮤니티 마케팅
# =============================================

with tab3:
    st.markdown("### 💬 댓글 & 커뮤니티 마케팅")
    
    drafts = st.session_state.generated_drafts
    
    if not drafts:
        # DB에서 댓글 초안 가져오기
        try:
            db_drafts = db.get_all_drafts(draft_type="comment", limit=20)
            if db_drafts:
                for draft in db_drafts:
                    video = db.get_video_by_id(draft["video_id"]) if draft.get("video_id") else None
                    lead = db.get_lead_by_id(draft["lead_id"]) if draft.get("lead_id") else None
                    
                    if video and lead:
                        vid = video["video_id"]
                        if vid not in drafts:
                            drafts[vid] = {
                                "video": {
                                    "title": video["title"],
                                    "channel_name": lead["channel_name"],
                                    "video_id": vid,
                                    "transcript_text": video.get("transcript_text", "")
                                },
                                "comment": draft["content"]
                            }
        except:
            pass
    
    if not drafts:
        st.info("📝 탭 1에서 영상을 선택하고 [분석 & 초안 생성] 버튼을 눌러주세요.")
    else:
        # 영상 선택
        draft_options = {f"{d['video']['channel_name']} - {d['video']['title'][:30]}...": vid 
                        for vid, d in drafts.items()}
        
        if draft_options:
            selected_draft_key = st.selectbox(
                "📋 대상 영상 선택",
                options=list(draft_options.keys()),
                key="comment_select"
            )
            
            if selected_draft_key:
                selected_vid = draft_options[selected_draft_key]
                draft_data = drafts[selected_vid]
                video_info = draft_data["video"]
                
                st.markdown(f"**선택된 영상:** {video_info['title']}")
                st.markdown("---")
                
                # 댓글 버전 생성 버튼
                if st.button("🎨 3가지 버전 댓글 생성", type="primary", use_container_width=True):
                    with st.spinner("AI가 다양한 버전의 댓글을 생성 중..."):
                        content = video_info.get("transcript_text", "")
                        
                        versions = {}
                        
                        # 진지형 - Privacy First 강조
                        prompt_serious = f"""다음 영상에 달 댓글을 작성해줘. 

[핵심 철학 - 이 관점에서 작성]
"다른 사진 정리 앱들은 AI 분석 핑계로 사진을 서버로 가져가는데, 이 앱은 서버 전송이 아예 없어요.
내 추억이 내 폰 밖으로 안 나간다는 게 제일 마음에 들었어요."

[영상 제목]: {video_info['title']}
[영상 내용]: {content[:1500]}

[스타일]: 진지하고 신뢰감 있는 톤
- 영상 내용 중 구체적인 부분에 공감하며 시작
- Privacy First 철학을 자연스럽게 녹여내기
- "개인정보 걱정 없이 쓸 수 있어서 좋았다"는 뉘앙스
- 앱 구동 영상: https://bit.ly/sample_video
- 120~150자, 광고 느낌 절대 금지"""
                        
                        # 유머형 - Underdog 정신 강조
                        prompt_humor = f"""다음 영상에 달 댓글을 작성해줘.

[핵심 철학 - 이 관점에서 작성]
"유료 앱들은 '프리미엄은 결제하세요'하고, 구글은 '용량 부족하시네요 ₩2,900 내세요'하는데,
이 앱은 진짜 완전 무료에 광고도 없어요. 세상에 이런 앱이 있었나 싶었음 ㅋㅋ"

[영상 제목]: {video_info['title']}
[영상 내용]: {content[:1500]}

[스타일]: 유머러스하고 친근한 톤
- 영상 내용에 재미있게 공감하며 시작
- "대기업들 돈 뜯어가는 거 지쳤는데 이런 앱 발견함" 뉘앙스
- 이모지 2~3개 자연스럽게
- 앱 구동 영상: https://bit.ly/sample_video  
- 120~150자, 과장 금지"""
                        
                        # 정보형 - Smart Backdoor 전략 강조
                        prompt_info = f"""다음 영상에 달 댓글을 작성해줘.

[핵심 철학 - 이 관점에서 작성]
"구글포토 용량 결제하기 전에 이거 먼저 해보세요.
쓰레기 사진(스크린샷, 중복, 흔들린 사진)부터 정리하면 15GB로도 충분하더라고요.
정리하고 나서 알맹이만 백업하니까 클라우드 비용이 0원이 됐어요."

[영상 제목]: {video_info['title']}
[영상 내용]: {content[:1500]}

[스타일]: 실용적인 정보 공유형
- "저도 이 문제로 고민했는데 해결책 찾았어요" 형식
- 구체적인 절약 효과 언급 (클라우드 비용, 용량 등)
- 앱 구동 영상: https://bit.ly/sample_video
- 120~150자, 팩트 기반으로"""
                        
                        try:
                            model = copywriter.model
                            versions["serious"] = model.generate_content(prompt_serious).text
                            versions["humor"] = model.generate_content(prompt_humor).text
                            versions["info"] = model.generate_content(prompt_info).text
                            
                            st.session_state.comment_versions[selected_vid] = versions
                            st.success("✅ 3가지 버전 생성 완료!")
                        except Exception as e:
                            st.error(f"생성 오류: {e}")
                
                st.markdown("---")
                
                # 댓글 버전 표시
                versions = st.session_state.comment_versions.get(selected_vid, {})
                
                # 기본 댓글이 있으면 표시
                if draft_data.get("comment") and not versions:
                    st.markdown("#### 📝 기본 댓글")
                    comment_text = st.text_area(
                        "댓글 내용",
                        value=draft_data["comment"],
                        height=150,
                        key="default_comment",
                        label_visibility="collapsed"
                    )
                    if st.button("📋 복사하기", key="copy_default"):
                        st.code(comment_text, language=None)
                        st.success("👆 위 내용을 드래그해서 복사하세요!")
                
                if versions:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("#### 🎩 진지형")
                        serious_text = st.text_area(
                            "진지형 댓글",
                            value=versions.get("serious", ""),
                            height=200,
                            key="serious_comment",
                            label_visibility="collapsed"
                        )
                        if st.button("📋 복사", key="copy_serious", use_container_width=True):
                            st.code(serious_text, language=None)
                            st.success("👆 복사하세요!")
                    
                    with col2:
                        st.markdown("#### 😄 유머형")
                        humor_text = st.text_area(
                            "유머형 댓글",
                            value=versions.get("humor", ""),
                            height=200,
                            key="humor_comment",
                            label_visibility="collapsed"
                        )
                        if st.button("📋 복사", key="copy_humor", use_container_width=True):
                            st.code(humor_text, language=None)
                            st.success("👆 복사하세요!")
                    
                    with col3:
                        st.markdown("#### 📚 정보형")
                        info_text = st.text_area(
                            "정보형 댓글",
                            value=versions.get("info", ""),
                            height=200,
                            key="info_comment",
                            label_visibility="collapsed"
                        )
                        if st.button("📋 복사", key="copy_info", use_container_width=True):
                            st.code(info_text, language=None)
                            st.success("👆 복사하세요!")
                
                st.markdown("---")
                
                # 커뮤니티 마케팅용 글
                st.markdown("#### 🌐 커뮤니티 마케팅용 글")
                
                if st.button("📝 커뮤니티 글 생성", use_container_width=True):
                    with st.spinner("커뮤니티용 글 생성 중..."):
                        prompt_community = f"""커뮤니티(클리앙, 뽐뿌, 디시인사이드, 에펨코리아 등)에 올릴 '발견 공유' 글을 작성해줘.

[핵심 철학 - 이 3가지가 자연스럽게 녹아들어야 함]

1. Underdog 정신:
"유료 앱들은 맨날 '프리미엄 기능은 결제하세요'하고, 구글/애플은 '용량 부족하시네요, 월 2,900원이요'하잖아요.
근데 이 앱은 진짜 완전 무료에 광고도 없음. 대기업들한테 돈 뜯기는 거 지쳤는데 이런 게 있더라고요."

2. Privacy First:
"다른 사진 정리 앱들은 'AI 분석'한다면서 사진을 서버로 보내는데, 이건 서버 전송이 아예 없어요.
비행기 모드에서도 돌아감. 내 사진이 내 폰 밖으로 안 나간다는 게 제일 마음에 들었음."

3. Smart Backdoor 전략:
"구글포토 용량 결제하기 전에 이거 먼저 해보세요.
스크린샷, 중복 사진, 흔들린 사진 같은 쓰레기부터 정리하면 15GB로도 충분하더라고요.
알맹이만 남기고 백업하니까 클라우드 비용이 0원 됨."

[글 형식]
- 제목: 클릭하고 싶은 제목 (예: "구글포토 용량 결제하려다가 이거 발견함", "사진 3만장 정리한 후기")
- 본문: 300~400자
- "여러분은 어떻게 하세요?" 같은 질문으로 마무리해서 댓글 유도
- 앱 구동 영상: https://bit.ly/sample_video

[주의사항]
- 광고/홍보 티 절대 금지
- 실제 사용자가 좋은 거 발견해서 공유하는 느낌
- "이거 광고 아니고 진짜임" 같은 변명도 금지 (오히려 의심받음)
- 팩트만으로 충분히 매력적"""
                        
                        try:
                            community_post = copywriter.model.generate_content(prompt_community).text
                            st.session_state.community_post = community_post
                        except Exception as e:
                            st.error(f"생성 오류: {e}")
                
                if "community_post" in st.session_state:
                    community_text = st.text_area(
                        "커뮤니티 글",
                        value=st.session_state.community_post,
                        height=250,
                        key="community_text",
                        label_visibility="collapsed"
                    )
                    if st.button("📋 커뮤니티 글 복사", use_container_width=True, key="copy_community"):
                        st.code(community_text, language=None)
                        st.success("👆 위 내용을 드래그해서 복사하세요!")

# =============================================
# 푸터
# =============================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; padding: 1rem;'>"
    "🚀 Bes2 Marketer | AI-Powered YouTube Marketing Automation"
    "</div>",
    unsafe_allow_html=True
)

