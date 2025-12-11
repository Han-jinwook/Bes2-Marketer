"""
Bes2 Marketer - Configuration
환경 변수 로드 및 설정 관리
"""

import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 개발용)
load_dotenv()


def get_secret(key: str, default: str = "") -> str:
    """
    환경 변수 또는 Streamlit Secrets에서 값 가져오기
    Streamlit Cloud 배포 시 st.secrets 사용, 로컬에서는 .env 사용
    """
    # 먼저 환경 변수에서 확인 (로컬 .env)
    value = os.getenv(key, "")
    if value:
        return value
    
    # Streamlit Cloud secrets에서 확인
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    return default


class Config:
    """앱 설정 클래스"""
    
    # Supabase
    SUPABASE_URL: str = get_secret("SUPABASE_URL")
    SUPABASE_KEY: str = get_secret("SUPABASE_KEY")
    
    # Google Gemini
    GEMINI_API_KEY: str = get_secret("GEMINI_API_KEY")
    
    # YouTube Data API
    YOUTUBE_API_KEY: str = get_secret("YOUTUBE_API_KEY")
    
    # 검색 키워드 (Bes2 앱 관련)
    SEARCH_KEYWORDS: list[str] = [
        "사진 정리",
        "사진 용량 부족",
        "핸드폰 용량 정리",
        "갤러리 정리",
        "사진 백업",
        "스마트폰 저장공간",
    ]
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """필수 환경 변수 검증"""
        missing = []
        
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.YOUTUBE_API_KEY:
            missing.append("YOUTUBE_API_KEY")
        
        return len(missing) == 0, missing


config = Config()

