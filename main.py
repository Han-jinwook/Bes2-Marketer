"""
Bes2 Marketer - Streamlit UI
AI 기반 유튜브 마케팅 자동화 대시보드
"""

# Force Update: Fix KeyError Cache
# Version: 2026-01-13-22:15 (Force Reboot)
import streamlit as st
import pandas as pd
import time


# [Critical Fix] 캐시 강제 삭제 (업데이트 미반영 해결용)
# 주의: set_page_config가 항상 먼저여야 함
st.set_page_config(
    page_title="Bes2 Marketer Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.cache_data.clear()
st.cache_resource.clear()

from datetime import datetime
import time
import pandas as pd

from config import config
from database import db
from logic import hunter, copywriter, AICopywriter

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
# 키워드 저장 관리 (DB 연동)
# =============================================

# =============================================
# Helper: 키워드 로컬 저장 (백업용) -> 실제로는 이미 DB 사용으로 대체됨
# =============================================
def save_keywords(keywords: str):
    pass # No-op (kept for backward compatibility if called elsewhere)

# =============================================
# 세션 상태 초기화
# =============================================

if "search_results" not in st.session_state:
    st.session_state.search_results = []
    
if "saved_keywords" not in st.session_state:
    # [NEW] DB에서 영구 저장된 키워드 불러오기
    saved = db.get_setting("search_keywords")
    if saved:
        st.session_state.saved_keywords = saved
    else:
        st.session_state.saved_keywords = "사진 정리, 갤러리 정리, 용량 부족, 구글포토 백업"
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
    <h1>🚀 Bes2 Marketer Pro <span style='font-size:1.2rem; color:#00FF00; font-weight:bold;'>(v2.3 Deep Search Active)</span></h1>
    <p style='color: white;'>AI 기반 유튜브 마케팅 자동화 대시보드 - <b>Privacy First & Smart Backup</b></p>
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
            save_keywords(keywords_input) # 로컬 저장 (백업용)
            db.set_setting("search_keywords", keywords_input) # DB 저장 (메인)
            st.session_state.saved_keywords = keywords_input
            st.toast("✅ DB에 영구 저장되었습니다!", icon="💾")
            
    with col_save2:
        if st.button("🔄 초기화", use_container_width=True):
            default_kw = "사진 정리, 갤러리 정리, 용량 부족, 구글포토 백업"
            save_keywords(default_kw)
            db.set_setting("search_keywords", default_kw)
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
    
    with st.expander("📊 수집 양 설정 (일일 목표)", expanded=True):
        max_results = st.slider(
            "하루 목표 수집량",
            min_value=100,
            max_value=500,
            value=100,
            step=50,
            help="한 번 서칭할 때 최대 몇 개의 영상을 가져올지 설정합니다."
        )
        # [REMOVED] 이메일 필수 옵션 제거 - 항상 모든 영상 수집
        require_email = False  # 이메일 유무와 관계없이 모든 영상 수집
    
    # [NEW] 최소 조회수 설정 (품질 필터)
    min_view_count = st.select_slider(
        "최소 조회수 (품질 필터)",
        options=[0, 100, 500, 1000, 5000, 10000],
        value=0,  # [FIX] 기본값 0으로 변경 (모든 영상 수집)
        help="이 조회수 미만인 영상은 수집하지 않습니다."
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
                        # Search Videos

                        results = hunter.search_videos(
                            keyword=keyword,
                            max_results=max_results,
                            published_after_days=published_after,
                            min_view_count=min_view_count,
                            require_email=require_email
                        )
                        
                        if len(results) == 3:
                            videos, total_count, filter_stats = results
                        else:
                            videos, total_count = results
                            filter_stats = {}
                        
                        if total_count > 0:
                            st.caption(f"📊 YouTube 검색 결과: 약 {total_count:,}개의 영상이 발견되었습니다.")
                            
                        # [DEBUG] 실제 수집된 개수 표시
                        st.warning(f"🔍 '{keyword}' 검색 완료: **{len(videos)}개** 수집됨 (목표: {max_results}개)")
                            
                        # [UI] 필터링 통계 표시
                        if filter_stats and sum(filter_stats.values()) > 0:
                            with st.expander(f"📉 필터링 상세 내역 (수집 제외됨) - {keyword}", expanded=False):
                                c1, c2, c3, c4, c5 = st.columns(5)
                                c1.metric("DB 중복", filter_stats.get("skipped_db", 0), help="이미 DB에 있어서 건너뜀")
                                c2.metric("언어(非한글)", filter_stats.get("skipped_lang", 0))
                                c3.metric("제외어", filter_stats.get("skipped_negative", 0), help="맥주, 날씨 등 엉뚱한 키워드")
                                c4.metric("조회수 미달", filter_stats.get("skipped_view", 0))
                                c5.metric("이메일 없음", filter_stats.get("skipped_no_email", 0), help="'이메일 필수' 옵션 때문에 제외됨")


                        
                        for video in videos:
                            # 검색 단계에서는 메타데이터만 수집 (자막은 분석 단계에서)
                            # 자막 추출이 느리고 실패할 수 있어서 검색 속도 향상을 위해 제거
                            video["transcript_text"] = ""  # 빈 값으로 초기화
                            video["content_source"] = "not_fetched"
                            
                            # 채널 정보
                            channel_info = hunter.get_channel_info(video["channel_id"])
                            if channel_info:
                                video["channel_info"] = channel_info
                            
                            all_videos.append(video)
                        
                        progress_bar.progress((i + 1) / len(keywords))
                    
                    # 🔍 60개 검색 결과 즉시 DB 저장 (Deep Search 완성)
                    if all_videos:
                        with st.spinner("💾 검색된 모든 영상을 DB에 동기화 중..."):
                            saved_count = db.upsert_scanned_videos(all_videos)
                            st.text(f"Synced {saved_count} videos to DB.")
                    
                    st.session_state.search_results = all_videos
                    st.success(f"✅ {len(all_videos)}개 영상 수집 완료! (DB 동기화 완료)")
                    
                except Exception as e:
                    import traceback
                    st.error(f"❌ 오류 발생: {str(e)}")
                    st.expander("상세 에러 로그 보기").code(traceback.format_exc())
    
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
                    # lead 정보가 없을 수도 있음 (삭제 등)
                    try:
                        lead = db.get_lead_by_id(v["lead_id"])
                    except:
                        lead = None
                
                # 안전하게 데이터 구성
                videos_to_show.append({
                    "video_id": v.get("video_id", ""),
                    "title": v.get("title", "No Title"),
                    "channel_name": lead["channel_name"] if lead else v.get("channel_name", "Unknown"), # DB에 없으면 video 데이터에서 시도
                    "channel_id": lead["channel_id"] if lead else v.get("channel_id", ""),
                    "thumbnail_url": v.get("thumbnail_url", ""),
                    "published_at": v.get("upload_date", ""),
                    "video_url": v.get("video_url", f"https://youtube.com/watch?v={v.get('video_id', '')}"),
                    "view_count": v.get("view_count", 0),
                    "transcript_text": v.get("transcript_text", ""),
                    "summary": v.get("summary", ""),
                    "relevance_score": v.get("relevance_score", 0),
                    "db_id": v.get("id"),
                    "channel_info": {
                        "subscriber_count": lead.get("subscriber_count", 0) if lead else 0,
                        "email": lead.get("email") if lead else None
                    }
                })
        except Exception as e:
            st.info("DB에 저장된 영상이 없습니다.")
    
    # 검색 결과 또는 DB 데이터가 있을 경우 (DataFrame View)
    st.markdown("### 📹 영상 목록")
    
    if videos_to_show:
        results = videos_to_show
        
        # 1. DataFrame 변환 for 일괄 선택
        video_data = []
        for v in results:
            # view_count 안전하게 처리
            view_count = v.get('view_count', 0)
            if isinstance(view_count, str):
                view_count = int(view_count.replace(',', '')) if view_count.replace(',', '').isdigit() else 0


        # [UX] 전체 선택/해제 토글 버튼 (작게)
        if "select_all_toggle" not in st.session_state:
            st.session_state.select_all_toggle = True # 기본값: 전체 선택
            
        col_toggle, _ = st.columns([1, 6])
        btn_label = "⬜ 전체 해제" if st.session_state.select_all_toggle else "✅ 전체 선택"
        if col_toggle.button(btn_label, key="btn_toggle_select", use_container_width=True):
            st.session_state.select_all_toggle = not st.session_state.select_all_toggle
            st.rerun()

        # 1. 시각화용 데이터프레임 변환
        video_data = []
        for v in results:
            selected = st.session_state.select_all_toggle # 토글 상태 반영
            
            # 이메일 표시 (DB 우선 -> 수집된 것 -> 빈 값)
            email_addr = v.get("channel_info", {}).get("email", "")
            
            video_data.append({
                "선택": selected,
                "제목": v.get("title", "No Title"),
                "이메일": email_addr, # [NEW] 직접 편집 가능
                "채널명": v.get("channel_name", "Unknown"),
                "게시일": v.get("published_at", "")[:10] if v.get("published_at") else "",
                "조회수": f"{v.get('view_count', 0):,}",
                "링크": v.get("video_url", ""),
                "video_id": v.get("video_id", ""),
                "raw_data": v # 전체 데이터 보존 (참조용)
            })

        df_videos = pd.DataFrame(video_data)
        
        # 2. 선택 가능한 테이블 표시
        st.caption(f"총 {len(results)}개의 영상을 찾았습니다.")
        st.info("💡 **Tip**: '이메일' 칸을 클릭하여 바로 수정할 수 있습니다. 자동으로 저장됩니다.")
        
        edited_videos = st.data_editor(
            df_videos,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", width="small", default=True),
                "이메일": st.column_config.TextColumn("이메일", width="medium", help="클릭해서 이메일을 입력하세요."),
                "제목": st.column_config.TextColumn("제목", width="large"),
                "채널명": st.column_config.TextColumn("채널명", width="medium"),
                "조회수": st.column_config.TextColumn("조회수", width="small"),
                "게시일": st.column_config.TextColumn("게시일", width="small"),
                "링크": st.column_config.LinkColumn("링크", display_text="보기", width="small"),
                "video_id": None, # 숨김
                "raw_data": None  # 숨김
            },
            hide_index=True,
            use_container_width=True,
            height=600,
            key="video_editor"
        )
        
        # 3. 데이터 변경 감지 및 자동 저장 (Auto-Save)
        if st.session_state.video_editor.get("edited_rows"):
            changes = st.session_state.video_editor["edited_rows"]
            
            # 변경된 행 처리
            for idx_str, updated_cols in changes.items():
                if "이메일" in updated_cols:
                    new_email = updated_cols["이메일"]
                    try:
                        idx = int(idx_str)
                        # 원본 데이터 매칭
                        target_v = video_data[idx]["raw_data"]
                        channel_id = target_v["channel_id"]
                        
                        # DB 업데이트
                        lead = db.get_lead_by_channel_id(channel_id)
                        if lead:
                            db.update_lead(lead["id"], email=new_email)
                            
                            # 세션 상태(메모리)도 동기화하여 UI 즉시 반영
                            # (주의: search_results 내의 모든 해당 채널 영상 업데이트)
                            for vid in st.session_state.search_results:
                                if vid["channel_id"] == channel_id:
                                    if "channel_info" not in vid: vid["channel_info"] = {}
                                    vid["channel_info"]["email"] = new_email
                            
                            st.toast(f"✅ 저장됨: {target_v['channel_name']}", icon="💾")
                            
                    except Exception as e:
                        print(f"Update error: {e}")
                        

        # 4. 액션 버튼 (삭제 & 분석)
        selected_rows = edited_videos[edited_videos["선택"]]
        
        col_del, col_anal = st.columns([1, 4])
        
        with col_del:
            if st.button("🗑️ 선택 삭제", type="secondary", use_container_width=True, disabled=selected_rows.empty):
                with st.spinner("Deleting..."):
                    # 선택된 video_id 목록 추출
                    ids_to_remove = set(selected_rows["video_id"].tolist())
                    
                    # 1. DB에서 실제 삭제
                    deleted_count = 0
                    for vid in ids_to_remove:
                        if db.delete_video_by_video_id(vid):
                            deleted_count += 1
                    
                    # 2. 세션에서 제거 (검색 결과 리스트 동기화)
                    st.session_state.search_results = [
                        v for v in st.session_state.search_results 
                        if v["video_id"] not in ids_to_remove
                    ]
                    
                    # 3. 캐시 삭제 (DB 뷰 갱신용)
                    st.cache_data.clear()
                    
                st.success(f"🗑️ {deleted_count}개 영상이 DB 및 리스트에서 영구 삭제되었습니다.")
                time.sleep(1.5)
                st.rerun()

        with col_anal:
             # 강제 재분석 옵션 추가
            force_analysis = st.checkbox(
                "🔄 이미 완료된 것도 다시 분석하기 (Force Re-run)", 
                value=False,
                key="force_reanalysis_toggle",
                help="체크하면 DB에 이미 저장된 영상이라도 무조건 AI 분석을 다시 수행하고 저장합니다."
            )
            
            if st.button(f"🚀 선택한 {len(selected_rows)}개 영상 일괄 분석", type="primary", use_container_width=True, disabled=selected_rows.empty):
                    
                pass
                    
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
                            # [스마트 로직] DB 상태 확인 (Deep Search 대응)
                            # -----------------------------------------------
                            # 영상이 DB에 있는지 확인
                            db_video = db.get_video_by_video_id(vid)
                            
                            # 이미 분석된 건인지 확인 (초안 존재 여부)
                            is_analyzed = False
                            if db_video:
                                db_drafts = db.get_drafts_by_video(db_video["id"])
                                # 이메일 초안이 있으면 분석 완료된 것으로 간주
                                if any(d.get("draft_type") == "email" for d in db_drafts):
                                    is_analyzed = True

                            if is_analyzed and not force_analysis:
                                # A. 이미 분석된 경우 -> DB에서 로드 (비용 0원)
                                status_area.info(f"💾 [DB 로드] '{v_title}' (비용 0원)")
                                time.sleep(0.5)
                                
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
                                # B. 분석 필요 (신규 영상 OR DB엔 있지만 분석 안된 영상 OR 강제 분석)
                                status_msg = f"🤖 [AI 분석] '{v_title}' 분석 중..."
                                if force_analysis: status_msg += " (강제 재분석)"
                                status_area.warning(status_msg)
                                
                                # 1. 자막 추출
                                transcript = hunter.get_transcript(vid)
                                content = ""
                                content_source = "transcript"
                                
                                if transcript:
                                    content = transcript[:15000]
                                else:
                                    # Fallback: 자막 없으면 설명글 등 메타데이터 사용
                                    # (사용자 요청: 이메일 생성 등 진행을 위해 무조건 분석 시도)
                                    status_area.warning(f"⚠️ 자막 없음 -> 설명글로 대체 분석: {v_title}")
                                    content = video.get("description", "") or video.get("title", "")
                                    content_source = "description"
                                    
                                    # 만약 설명글도 너무 짧으면? (그래도 진행)
                                    if len(content) < 10:
                                        content += " (내용 부족)"

                                # 2. AI 생성 (이메일, 댓글, 요약)
                                email = copywriter.generate_email(
                                    channel_name=video["channel_name"],
                                    video_title=video["title"],
                                    video_content=content,
                                    subscriber_count=(video.get("channel_info") or {}).get("subscriber_count", 0)
                                )
                                comment = copywriter.generate_comment(
                                    channel_name=video["channel_name"],
                                    video_title=video["title"],
                                    video_content=content
                                )
                                summary = copywriter.summarize_video(content)
                                relevance = {"score": 100} # 기본값
                                
                                # 3. DB 저장/업데이트
                                # (1) 리드 확보 (이미 있으면 ID만 가져옴)
                                existing_lead = db.get_lead_by_channel_id(video["channel_id"])
                                if existing_lead:
                                    lead_id = existing_lead["id"]
                                else:
                                    lead = db.create_lead(
                                        channel_name=video["channel_name"],
                                        channel_id=video["channel_id"],
                                        subscriber_count=(video.get("channel_info") or {}).get("subscriber_count", 0),
                                        email=(video.get("channel_info") or {}).get("email"),
                                        keywords=[video.get("search_keyword", "")],
                                    )
                                    lead_id = lead["id"]
                                
                                # (2) 영상 저장 (Upsert Logic)
                                if db_video:
                                    # 이미 DB에 존재하면 -> 내용 업데이트 (자막, 요약 등)
                                    video_db_id = db_video["id"]
                                    saved_video = db.update_video(
                                        video_db_id,
                                        transcript_text=content if content_source == "transcript" else None, # 자막일 때만 저장, 아니면 기존 유지? 아니면 덮어쓰기? 
                                        # 설명글로 대체했으면 transcript 필드에 넣기는 좀 그러니, summary에 설명글 요약 넣거나..
                                        # 일단 transcript_text 컬럼에 넣으면 나중에 헷갈릴 수 있음.
                                        # 하지만 create_video에서는 transcript_text에 넣고 있음. 일관성 유지.
                                        summary=summary,
                                        relevance_score=relevance["score"],
                                        # 필요한 경우 다른 필드도 업데이트
                                    )
                                else:
                                    # 없으면 -> 새로 생성
                                    saved_video = db.create_video(
                                        video_id=vid,
                                        title=v_title,
                                        lead_id=lead_id,
                                        view_count=int(str(video.get("view_count", 0)).replace(",", "")),
                                        video_url=video["video_url"],
                                        thumbnail_url=video.get("thumbnail_url"),
                                        transcript_text=content,
                                        summary=summary,
                                        relevance_score=relevance["score"],
                                        search_keyword=video.get("search_keyword", "")
                                    )
                                
                                if not saved_video:
                                    raise Exception("Video DB Save Failed (Insert/Update returned empty)")
                                video_db_id = saved_video["id"]
                                
                                # (3) 초안 저장 (항상 생성)
                                # 기존 초안 삭제 후 재생성 (강제 분석 시 중복 방지)
                                if force_analysis and db_video:
                                    existing_drafts = db.get_drafts_by_video(video_db_id)
                                    for ed in existing_drafts:
                                        db.delete_draft(ed["id"])

                                # 이메일 초안 저장
                                email_draft = db.save_draft(
                                    video_id=video_db_id,
                                    channel_name=video["channel_name"],
                                    video_title=video["title"],
                                    draft_content=email,
                                    status='generated',
                                    email=(video.get("channel_info") or {}).get("email"),
                                    lead_id=lead_id
                                )
                                if not email_draft:
                                    raise Exception("Email Draft DB Save Failed")

                                # 댓글 초안 저장
                                db.save_draft(
                                    video_id=video_db_id,
                                    channel_name=video["channel_name"],
                                    video_title=f"[댓글] {video['title']}",
                                    draft_content=comment,
                                    status='generated',
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
                            st.error(f"❌ 오류 상세: {e}")
                            
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
    st.markdown("### ✉️ 이메일 발송 관리")
    
    # 1. 대기 중인 초안 로드
    pending_drafts = db.get_pending_email_drafts_detailed()
    

    if not pending_drafts:
        st.info("🎉 전송 대기 중인 이메일이 없습니다! (분석된 영상이 없거나 모두 처리되었습니다.)")
    else:
        # Layout: Left (List) vs Right (Detail)
        col_list, col_detail = st.columns([1, 2])
        
        with col_list:
            st.markdown(f"**📌 대기 목록 ({len(pending_drafts)})**")
            
            # 리스트 아이템 생성
            options = {}
            for d in pending_drafts:
                lead = d.get("leads", {}) or {}
                if isinstance(lead, list): lead = lead[0] if lead else {} # Join 리스트 대응
                
                ch_name = lead.get("channel_name", "Unknown")
                email_exists = bool(lead.get("email"))
                
                # 라벨링
                content = d.get("content") or ""
                is_junk = (
                    content.strip() == "" or 
                    content.startswith("[AI 에러]") or 
                    content.startswith("[오류]") or
                    "404 models/" in content
                )
                
                if is_junk:
                    label_icon = "🗑️" # 쓰레기 데이터
                elif not email_exists:
                    label_icon = "⚠️" # 이메일 없음
                else:
                    label_icon = "📄" # 정상
                
                # 유니크한 키 생성을 위해 ID 일부 포함
                label = f"{label_icon} {ch_name}"
                options[label] = d
            
            selected_label = st.radio(
                "보낼 채널 선택",
                options=list(options.keys()),
                label_visibility="collapsed",
                key="draft_selector"
            )
            
            selected_draft = options[selected_label]

        with col_detail:
            if selected_draft:
                d = selected_draft
                lead = d.get("leads", {}) or {}
                if isinstance(lead, list): lead = lead[0] if lead else {}
                
                current_email = lead.get('email') or ""
                
                st.markdown(f"**받는 사람:** {lead.get('channel_name', 'Unknown')}")
                
                # [NEW] 이메일 직접 수정/입력 기능
                c_mail_input, c_mail_btn = st.columns([3, 1])
                new_email_input = c_mail_input.text_input(
                    "수신 이메일", 
                    value=current_email, 
                    placeholder="이메일이 없습니다. 입력해주세요.",
                    label_visibility="collapsed",
                    key=f"email_input_{d['id']}"
                )
                
                if c_mail_btn.button("저장", key=f"btn_save_mail_{d['id']}"):
                    if new_email_input.strip():
                        db.update_lead(lead['id'], email=new_email_input.strip())
                        st.toast("✅ 이메일 저장 완료!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.toast("⚠️ 이메일을 입력하세요.")


                # 작성일 표시 (Firestore datetime 안전 처리)
                created_at = d.get('created_at', '')
                if created_at:
                    try:
                        created_at_str = created_at.strftime('%Y-%m-%d %H:%M') if hasattr(created_at, 'strftime') else str(created_at)[:16]
                    except:
                        created_at_str = str(created_at)[:16]
                else:
                    created_at_str = "Unknown"
                
                st.caption(f"작성일: {created_at_str}")
                st.markdown("---")
                
                # 본문 에디터
                content = d.get("content") or ""
                
                # 오류 데이터 시각적 경고
                is_junk = (
                    content.strip() == "" or 
                    content.startswith("[AI 에러]") or 
                    content.startswith("[오류]") or
                    "404 models/" in content
                )
                if is_junk:
                    st.error("🚨 AI 생성 중 오류가 발생한 데이터입니다. 삭제해주세요.")
                
                edited_content = st.text_area(
                    "내용 검토 및 수정",
                    value=content,
                    height=500,
                    key=f"editor_{d['id']}"
                )
                
                # 하단 액션 버튼
                st.markdown("---")
                c1, c2, c3 = st.columns([2, 1, 1])
                
                with c1:
                    from email_service import emailer
                    
                    # 제목 추출 로직
                    lines = edited_content.split('\n')
                    subject = "Bes2 제안"
                    for line in lines:
                        if "제목:" in line or "Subject:" in line:
                            subject = line.replace("제목:", "").replace("Subject:", "").strip()
                            break
                            
                    btn_label = "🚀 이메일 전송"
                    
                    # 전송 버튼 활성화 조건: 이메일이 입력되어 있어야 함
                    final_email = new_email_input.strip()
                    can_send = bool(final_email) and not is_junk
                    
                    if config.TEST_MODE:
                        btn_label += " (테스트 모드)"
                        
                    if st.button(btn_label, type="primary", use_container_width=True, key=f"snd_{d['id']}", disabled=not can_send):
                        if config.TEST_MODE:
                            st.toast(f"🧪 테스트 발송: {config.TEST_EMAIL}")
                        
                        if emailer.send_email(final_email, subject, edited_content):
                            db.update_draft_status(d['id'], "sent")
                            st.success(f"✅ 전송 완료! ({final_email})")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("전송 실패. 설정을 확인하세요.")
                        
                        # 만약 이메일이 변경되었는데 저장을 안 눌렀을 수도 있으니, 전송 성공 시 자동 저장 시도
                        if final_email != current_email:
                            db.update_lead(lead['id'], email=final_email)

                with c2:
                    if st.button("💾 본문 저장", use_container_width=True, key=f"sav_{d['id']}"):
                         db.update_draft_content(d['id'], edited_content)
                         st.toast("✅ 내용이 저장되었습니다.")
                         time.sleep(0.5)
                         st.rerun()
                         
                with c3:
                    if st.button("🗑️ 삭제", type="secondary", use_container_width=True, key=f"del_{d['id']}"):
                        db.delete_draft(d['id'])
                        st.toast("🗑️ 삭제되었습니다.")
                        time.sleep(0.5)
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
        stats_draft = {"email": {"pending": 0, "sent": 0}}
    
    with col1:
        st.metric("총 발굴 채널 (Leads)", f"{stats_lead['total']}명", f"+{stats_lead['new']} 신규")
    with col2:
        st.metric("발송 완료 (Sent)", f"{stats_draft.get('email', {}).get('sent', 0)}건")
    with col3:
        st.metric("대기 중 (Pending)", f"{stats_draft.get('email', {}).get('pending', 0)}건")
        
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
    
    st.markdown("---")
    
    # 4. Gemini 모델 작동 테스트
    st.markdown("#### 🤖 AI 모델 테스트")
    st.caption("현재 사용 가능한 Gemini 모델을 확인합니다.")
    
    col_list, col_test = st.columns(2)
    
    with col_list:
        if st.button("📋 사용 가능한 모델 목록 조회", use_container_width=True):
            import google.generativeai as genai
            
            try:
                with st.spinner("모델 목록 조회 중..."):
                    available_models = list(genai.list_models())
                    
                st.success(f"총 {len(available_models)}개의 모델을 찾았습니다:")
                
                for model in available_models:
                    st.code(f"이름: {model.name}\n지원: {', '.join(model.supported_generation_methods)}", language=None)
                    
            except Exception as e:
                st.error(f"모델 목록 조회 실패: {e}")
    
    with col_test:
        if st.button("🔍 모델 테스트 실행", type="primary"):
            import google.generativeai as genai
            
            models_to_test = [
                "gemini-1.5-flash-latest",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            working_model = None
            results = []
            
            with st.spinner("모델 테스트 중..."):
                for model_name in models_to_test:
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        response = test_model.generate_content("안녕")
                        results.append({"model": model_name, "status": "✅ 작동", "response": response.text[:50]})
                        if not working_model:
                            working_model = model_name
                    except Exception as e:
                        results.append({"model": model_name, "status": "❌ 실패", "response": str(e)[:100]})
            
            # 결과 표시
            for r in results:
                if "✅" in r["status"]:
                    st.success(f"**{r['model']}**: {r['status']}")
                else:
                    st.error(f"**{r['model']}**: {r['status']}\n{r['response']}")
            
            if working_model:
                st.balloons()
                st.info(f"🎉 **추천 모델: `{working_model}`**\n\n이 모델명을 `logic.py` 496번째 줄에 고정하세요.")
            else:
                st.warning("⚠️ 모든 모델 실패. API 키 할당량을 확인하세요: https://aistudio.google.com/app/apikey")


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

