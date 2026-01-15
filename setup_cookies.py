"""
YouTube 쿠키 생성 & Streamlit Secrets 준비 도구
"""

import os
import sys

def main():
    print("=" * 60)
    print("🍪 YouTube 쿠키 생성 & Secrets 준비 도구")
    print("=" * 60)
    print()
    
    # 1. 쿠키 생성
    print("📌 단계 1: Chrome에서 쿠키 자동 추출")
    print("Chrome을 완전히 종료해주세요... (Enter로 계속)")
    input()
    
    try:
        from cookie_extractor import extract_youtube_cookies
        
        print("🔍 쿠키 추출 중...")
        cookies_txt = extract_youtube_cookies()
        
        if not cookies_txt:
            print("❌ 쿠키 추출 실패!")
            print()
            print("해결 방법:")
            print("1. Chrome을 완전히 종료하세요 (작업 관리자에서도 확인)")
            print("2. YouTube에 로그인되어 있는지 확인하세요")
            print("3. 다시 시도하세요")
            sys.exit(1)
        
        # 로컬 저장
        cookies_path = "cookies.txt"
        with open(cookies_path, 'w', encoding='utf-8') as f:
            f.write(cookies_txt)
        
        print(f"✅ 쿠키 저장 완료: {cookies_path}")
        print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)
    
    # 2. 유효성 검사
    print("📌 단계 2: 쿠키 유효성 테스트")
    
    try:
        from logic import YouTubeHunter
        
        hunter = YouTubeHunter()
        print("🧪 테스트 영상으로 자막 추출 시도...")
        
        # Rick Astley - Never Gonna Give You Up (자막 100% 있음)
        test_result = hunter.get_transcript("dQw4w9WgXcQ")
        
        if test_result and len(test_result) > 100:
            print("✅ 쿠키 유효성 검증 성공!")
            print(f"   (추출된 자막 길이: {len(test_result)} chars)")
        else:
            print("⚠️ 자막 추출 실패 - 쿠키가 유효하지 않을 수 있습니다")
            print("   그래도 계속하시겠습니까? (y/n)")
            if input().lower() != 'y':
                sys.exit(1)
        
        print()
        
    except Exception as e:
        print(f"⚠️ 유효성 검사 중 오류: {e}")
        print("   그래도 계속하시겠습니까? (y/n)")
        if input().lower() != 'y':
            sys.exit(1)
        print()
    
    # 3. Streamlit Secrets 형식으로 출력
    print("📌 단계 3: Streamlit Secrets 복사 준비")
    print()
    print("=" * 60)
    print("📋 아래 내용을 Streamlit Cloud Secrets에 복사하세요:")
    print("=" * 60)
    print()
    
    # TOML 형식으로 출력
    print("YOUTUBE_COOKIES = '''")
    print(cookies_txt.strip())
    print("'''")
    
    print()
    print("=" * 60)
    print()
    
    # 4. 복사 방법 안내
    print("📌 Streamlit Cloud 설정 방법:")
    print()
    print("1. https://share.streamlit.io 접속")
    print("2. Bes2-Marketer 앱 선택")
    print("3. Settings → Secrets 클릭")
    print("4. 위의 내용을 기존 내용 아래에 추가")
    print("5. Save 클릭")
    print()
    
    # 5. 클립보드 복사 (선택사항)
    try:
        import pyperclip
        secrets_content = f"YOUTUBE_COOKIES = '''\n{cookies_txt.strip()}\n'''"
        pyperclip.copy(secrets_content)
        print("✅ 클립보드에 자동 복사됨! (바로 붙여넣기 가능)")
    except:
        print("ℹ️ 수동으로 위 내용을 복사해주세요")
    
    print()
    print("=" * 60)
    print("✅ 완료! Streamlit Cloud Secrets에 붙여넣기만 하면 됩니다!")
    print("=" * 60)

if __name__ == "__main__":
    main()
