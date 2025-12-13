"""
Bes2 Marketer - Streamlit UI
AI 기반 유튜브 마케팅 자동화 대시보드
"""

import streamlit as st
from datetime import datetime
import time
import pandas as pd

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

    st.markdown("---")
    
    # 전략 선택 (Preset)
    st.subheader("🎯 마케팅 작전 선택")
    
    strategy_options = {
        "🦖 올드보이 발굴 (6개월~1년)": {"days": 365, "min_rel": 0, "desc": "오래된 영상까지 모두 수집 (필터링 OFF)"},
        "⚽ 미드필더 장악 (1~6개월)": {"days": 180, "min_rel": 0, "desc": "중간 기간 영상 모두 수집 (필터링 OFF)"},
        "⭐ 라이징 스타 (최근 1개월)": {"days": 30, "min_rel": 0, "desc": "최근 영상 모두 수집 (필터링 OFF)"},
        "☕ 데일리 루틴 (최근 24시간)": {"days": 1, "min_rel": 0, "desc": "오늘 올라온 영상 모두 수집 (필터링 OFF)"}
    }
    
    selected_strategy_name = st.radio(
        "작전명",
        list(strategy_options.keys()),
        index=2, # 기본값: 라이징 스타
        help="원하는 타겟 시기에 맞춰 자동으로 설정이 변경됩니다."
    )
    
    current_strategy = strategy_options[selected_strategy_name]
    
    # 전략 설명 표시
    st.info(f"💡 **Strategy:** {current_strategy['desc']}\n\n"
            f"• 검색 기간: 최근 {current_strategy['days']}일\n"
            f"• 최소 관련도: {current_strategy['min_rel']}점 이상")
    
    # 변수 매핑 (로직 연결용)
    published_after = current_strategy["days"]
    min_relevance = current_strategy["min_rel"]
    
    with st.expander("⚙️ 고급 설정 (수집 양)", expanded=False):
        max_results = st.slider(
            "한번에 수집할 영상 수",
            min_value=10,
            max_value=100,
            value=30,
            step=10,
            help="많을수록 시간이 오래 걸립니다."
        )
    
    st.markdown("---")
    
    # 검색 버튼
    search_clicked = st.button(
        "🚀 작전 개시 (영상 검색)",
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
            
            with st.spinner(f"🔍 '{selected_strategy_name.split()[0]}' 작전 수행 중..."):
                try:
                    all_videos = []
                    progress_bar = st.progress(0)
                    
                    for i, keyword in enumerate(keywords):
                        st.text(f"Scanning: {keyword}")
                        videos = hunter.search_videos(
                            keyword=keyword,
                            max_results=max_results,
                            published_after_days=published_after
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📹 영상 리스트 & 분석",
    "✉️ 이메일 발송 관리",
    "💬 댓글/커뮤니티 마케팅",
    "⚙️ 시스템 관리"
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
    
    # 검색 결과가 있을 경우 (DataFrame View)
    st.markdown("### 📹 영상 검색 결과")
    
    if "search_results" in st.session_state and st.session_state.search_results:
        results = st.session_state.search_results
        
        # 1. DataFrame 변환 for 일괄 선택
        video_data = []
        for v in results:
            video_data.append({
                "선택": False,
                "썸네일": v["thumbnail_url"],
                "제목": v["title"],
                "채널명": v["channel_name"],
                "게시일": v["published_at"][:10],
                "조회수": f"{v['view_count']:,}",
                "video_id": v["video_id"],
                "raw_data": v # 전체 데이터 보존
            })
            
        df_videos = pd.DataFrame(video_data)
        
        # 2. 선택 가능한 테이블 표시
        st.caption(f"총 {len(results)}개의 영상을 찾았습니다. 분석할 영상을 선택하세요.")
        
        edited_videos = st.data_editor(
            df_videos,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", default=False),
                "썸네일": st.column_config.ImageColumn("썸네일", width="small"),
                "제목": st.column_config.TextColumn("제목", width="medium"),
                "video_id": None, # 숨김
                "raw_data": None  # 숨김
            },
            hide_index=True,
            use_container_width=True,
            height=500,
            key="video_selector"
        )
        
        # 3. 일괄 분석 버튼
        selected_rows = edited_videos[edited_videos["선택"]]
        
        if not selected_rows.empty:
            st.markdown("---")
            col_action, col_msg = st.columns([1, 2])
            
            with col_action:
                if st.button(f"🚀 선택한 {len(selected_rows)}개 영상 일괄 분석", type="primary", use_container_width=True):
                    
                    st.info(f"ℹ️ 현재 '관련도 커트라인'은 **{min_relevance}점**입니다. 이보다 낮으면 저장되지 않습니다.")
                    
                    progress_bar = st.progress(0)
                    status_area = st.empty()
                    
                    success_count = 0
                    
                    for idx, row in enumerate(selected_rows.itertuples()):
                        vid = row.video_id
                        # 원본 데이터에서 조회 (DataFrame 데이터 무결성 보장)
                        video = next((v for v in results if v["video_id"] == vid), None)
                        
                        if not video:
                            status_area.error(f"❌ 데이터 매칭 실패: ID {vid}")
                            time.sleep(1)
                            continue
                            
                        v_title = video["title"]
                        
                        # 진행률 업데이트
                        progress = (idx + 1) / len(selected_rows)
                        progress_bar.progress(progress)
                        
                        try:
                            # -----------------------------------------------
                            # [스마트 로직] DB 중복 확인 (비용 절약)
                            # -----------------------------------------------
                            if db.video_exists(vid):
                                # A. 이미 분석된 경우 -> DB에서 로드 (비용 0원)
                                status_area.info(f"💾 [DB 로드] '{v_title}' (비용 0원)")
                                time.sleep(0.5) # UI 반영을 위한 짧은 대기
                                
                                # DB에서 데이터 가져오기
                                db_video = db.get_video_by_video_id(vid)
                                db_drafts = db.get_drafts_by_video(db_video["id"])
                                
                                email_content = ""
                                comment_content = ""
                                
                                for d in db_drafts:
                                    if d["draft_type"] == "email":
                                        email_content = d["content"]
                                    elif d["draft_type"] == "comment":
                                        comment_content = d["content"]
                                
                                # 세션에 로드
                                st.session_state.generated_drafts[vid] = {
                                    "video": video,
                                    "email": email_content,
                                    "comment": comment_content,
                                    "summary": db_video.get("summary", ""),
                                    "relevance": {"score": db_video.get("relevance_score", 0)},
                                    "db_id": next((d["id"] for d in db_drafts if d["draft_type"] == "email"), "") 
                                }
                                success_count += 1
                                
                            else:
                                # B. 새로운 영상 -> AI 분석 (비용 발생)
                                status_area.warning(f"🤖 [AI 분석] '{v_title}' 분석 중...")
                                
                                # 1. 자막 추출
                                transcript = hunter.get_transcript(vid)
                                if not transcript:
                                    st.toast(f"⚠️ 자막 없음: {v_title}", icon="❌")
                                    continue
                                    
                                content = transcript[:15000] # 길이 제한
                                
                                # 2. 적합성 분석
                                relevance = copywriter.analyze_relevance(content)
                                
                                # [스마트 필터] 기준 점수 미달 시 PASS (DB 저장 안 함)
                                if relevance["score"] < min_relevance:
                                    msg = f"📉 점수 미달 ({relevance['score']}점 < {min_relevance}점): {v_title}"
                                    st.toast(msg, icon="🚫")
                                    status_area.warning(msg)
                                    time.sleep(1)
                                    continue
                                
                                # 3. 이메일 & 댓글 생성
                                email = copywriter.generate_email(
                                    channel_name=video["channel_name"],
                                    video_title=video["title"],
                                    video_content=content,
                                    subscriber_count=video.get("channel_info", {}).get("subscriber_count", 0)
                                )
                                comment = copywriter.generate_comment(
                                    channel_name=video["channel_name"],
                                    video_title=video["title"],
                                    video_content=content
                                )
                                summary = copywriter.summarize_video(content)
                                
                                # 4. DB 저장
                                # (1) 리드 저장
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
                                
                                # (2) 영상 저장
                                saved_video = db.create_video(
                                    video_id=vid,
                                    title=v_title,
                                    lead_id=lead_id,
                                    view_count=int(str(video["view_count"]).replace(",", "")), # 콤마 제거
                                    video_url=video["video_url"],
                                    thumbnail_url=video["thumbnail_url"],
                                    transcript_text=content,
                                    summary=summary,
                                    relevance_score=relevance["score"],
                                    search_keyword=video.get("search_keyword", "")
                                )
                                video_db_id = saved_video["id"]
                                
                                # (3) 초안 저장
                                email_draft = db.create_draft(
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
                                
                                # 세션 업데이트
                                st.session_state.generated_drafts[vid] = {
                                    "video": video,
                                    "email": email,
                                    "comment": comment,
                                    "summary": summary,
                                    "relevance": relevance,
                                    "db_id": email_draft["id"]
                                }
                                success_count += 1
                                
                        except Exception as e:
                            print(f"Error processing {vid}: {e}")
                            st.toast(f"❌ 오류 발생: {v_title}", icon="⚠️")
                            
                    status_area.empty()
                    if success_count > 0:
                        st.success(f"✅ 총 {success_count}개 영상 분석 완료! \n\n👉 **'✉️ 이메일 발송 관리'** 탭으로 이동하여 초안을 확인하세요.")
                        st.balloons()
                    else:
                        st.warning("⚠️ 분석된 영상이 없습니다.")

    else:
        st.info("👈 왼쪽 사이드바에서 키워드를 입력하고 검색을 시작하세요.")
    
    st.markdown("---")

# =============================================
# 탭 2: 이메일 발송 관리
# =============================================

with tab2:
    st.markdown("### ✉️ 이메일 일괄 발송 관리")
    
    # 1. 대기 중인 초안 가져오기
    pending_drafts = db.get_pending_email_drafts_detailed()
    
    if not pending_drafts:
        st.info("🎉 전송 대기 중인 이메일이 없습니다. (모두 처리됨)")
        st.markdown("---")
    else:
        # 2. DataFrame 변환
        table_data = []
        for d in pending_drafts:
            vid = d.get("videos", {}) or {}
            lead = d.get("leads", {}) or {}
            
            # 제목 추출
            content = d.get("content", "")
            lines = content.strip().split("\n")
            subject = "제목 없음"
            for line in lines:
                if "제목:" in line or "Subject:" in line:
                    subject = line.replace("제목:", "").replace("Subject:", "").strip()
                    break
            
            table_data.append({
                "선택": False,
                "채널명": lead.get("channel_name", "Unknown"),
                "이메일": lead.get("email", "미확인"),
                "제목(미리보기)": subject[:40] + "..." if len(subject) > 40 else subject,
                "작성일": d.get("created_at", "")[:10],
                "id": d["id"],
                "full_content": content
            })
            
        df = pd.DataFrame(table_data)
        
        # 3. 데이터 에디터 (선택 가능)
        st.caption(f"총 {len(df)}개의 대기 중인 제안서가 있습니다.")
        edited_df = st.data_editor(
            df,
            column_config={
                "선택": st.column_config.CheckboxColumn(
                    "선택",
                    help="전송할 항목 선택",
                    default=False,
                ),
                "id": None, # 숨김
                "full_content": None # 숨김
            },
            hide_index=True,
            use_container_width=True,
            key="email_editor"
        )
        
        # 4. 일괄 전송 버튼
        selected_rows = edited_df[edited_df["선택"]]
        
        col_btn, col_info = st.columns([1, 2])
        
        with col_btn:
            from email_service import emailer
            if st.button(f"🚀 선택한 {len(selected_rows)}건 일괄 전송", type="primary", use_container_width=True, disabled=len(selected_rows)==0):
                if config.TEST_MODE:
                    st.warning(f"🧪 테스트 모드: 실제 수신자 대신 {config.TEST_EMAIL}로 발송됩니다.")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                
                for idx, row in enumerate(selected_rows.itertuples()):
                    current_email = row.이메일
                    current_subject = row._4  # 제목(미리보기), 실제로는 제목 추출 로직을 다시 써야 정확하지만 일단 생략하거나 full_content에서 파싱
                    
                    # 제목 재추출 (정확성을 위해)
                    lines = row.full_content.strip().split("\n")
                    real_subject = "Bes2 제안"
                    real_body = row.full_content
                    for i, line in enumerate(lines):
                        if "제목:" in line or "Subject:" in line:
                            real_subject = line.replace("제목:", "").replace("Subject:", "").strip()
                            real_body = "\n".join(lines[i+1:]).strip()
                            break
                    
                    status_text.text(f"📨 전송 중... ({idx+1}/{len(selected_rows)}): {row.채널명}")
                    
                    # 이메일 주소 확인
                    if not current_email or "@" not in current_email:
                        st.toast(f"❌ {row.채널명}: 이메일 주소 없음", icon="⚠️")
                        continue
                        
                    # 전송 시도
                    if emailer.send_email(current_email, real_subject, real_body):
                        # DB 업데이트
                        db.update_draft_status(row.id, "sent")
                        success_count += 1
                    else:
                        st.toast(f"❌ {row.채널명}: 전송 실패", icon="🚫")
                        
                    progress_bar.progress((idx + 1) / len(selected_rows))
                    time.sleep(0.5) # API 벤 방지용 딜레이
                
                status_text.text(f"✅ 완료! 총 {success_count}건 실패 {len(selected_rows)-success_count}건")
                st.success(f"{success_count}건의 메일이 성공적으로 발송되었습니다.")
                time.sleep(2)
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔍 개별 상세 보기 & 수정")
    # 기존 카드 뷰 (선택된 게 없거나 별도로 수정하고 싶을 때 사용하도록 유지하되 간소화)
    
    # DB에서 다시 로드 (상태 변경 반영을 위해) 혹은 위 데이터 활용
    if not pending_drafts:
        st.write("표시할 항목이 없습니다.")
    else:
        # 간단하게 셀렉트박스로 선택해서 수정할 수 있게 제공
        draft_options = {f"{d['leads'].get('channel_name')} ({d['leads'].get('email')})": d for d in pending_drafts}
        selected_key = st.selectbox("수정할 초안 선택", list(draft_options.keys()))
        
        if selected_key:
            data = draft_options[selected_key]
            d_content = st.text_area("내용 수정", data["content"], height=300, key=f"edit_{data['id']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 수정 저장", key=f"save_{data['id']}"):
                    db.update_draft_content(data["id"], d_content)
                    st.success("저장되었습니다.")
                    time.sleep(1)
                    st.rerun()
            with col2:
                if st.button("🗑️ 삭제", type="secondary", key=f"del_{data['id']}"):
                    db.delete_draft(data["id"])
                    st.warning("삭제되었습니다.")
                    time.sleep(1)
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
# 탭 4: 시스템 진단 (Debug)
# =============================================

with tab4:
    st.markdown("### ⚙️ 데이터베이스 & 시스템 관리")
    
    # 1. 시스템 현황 대시보드
    col1, col2, col3 = st.columns(3)
    
    try:
        stats_lead = db.get_lead_stats()
    except Exception:
        stats_lead = {"total": "-", "new": "-"}
        
    try:
        stats_draft = db.get_draft_stats()
    except Exception:
        stats_draft = {"pending": "-", "sent": "-"}
    
    with col1:
        st.metric("총 발굴 채널 (Leads)", f"{stats_lead['total']}명", f"+{stats_lead['new']} 신규")
    with col2:
        st.metric("발송 완료 (Sent)", f"{stats_draft['email'].get('sent', 0)}건")
    with col3:
        st.metric("대기 중 (Pending)", f"{stats_draft['email'].get('pending', 0)}건")
        
    st.markdown("---")
    
    # 2. 테스트 모드 설정 확인
    st.markdown("#### 🧪 모드 설정")
    if config.TEST_MODE:
        st.info(f"현재 **테스트 모드(Test Mode)** 가 켜져 있습니다.\n\n"
                f"모든 이메일은 실제 수신자 대신 **{config.TEST_EMAIL}**로 발송됩니다.\n"
                f"실제 발송을 하려면 `config.py` 또는 환경변수에서 설정을 변경하세요.")
    else:
        st.error("🚨 현재 **실전 모드(Live Mode)** 입니다! 이메일이 실제 수신자에게 발송됩니다. 주의하세요.")
        
    st.markdown("---")
    
    # 3. DB 데이터 정리 (Cleanup)
    st.markdown("#### 🗑️ 데이터 정리")
    st.caption("오래된 임시 데이터(대기 중인 초안)를 삭제하여 DB 용량을 확보합니다. (발송 완료된 데이터는 보존됩니다)")
    
    if st.button("🧹 7일 이상 지난 대기 데이터 삭제", type="secondary"):
        try:
            # 7일 전 날짜 계산
            cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            # 삭제 쿼리 (status='pending' AND created_at < 7 days ago)
            response = db.client.table("drafts").delete().eq("status", "pending").lt("created_at", cutoff_date).execute()
            
            deleted_count = len(response.data) if response.data else 0
            
            if deleted_count > 0:
                st.success(f"✅ 총 {deleted_count}개의 오래된 임시 데이터를 삭제했습니다.")
                time.sleep(1)
                st.rerun()
            else:
                st.info("깨끗합니다! 삭제할 오래된 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"데이터 삭제 중 오류 발생: {e}")


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

