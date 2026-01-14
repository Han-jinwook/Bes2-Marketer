# YouTube 쿠키 추출 가이드

## 방법 1: Chrome 확장 프로그램 (가장 쉬움) ⭐

### 단계:
1. **크롬 웹스토어**에서 "Get cookies.txt LOCALLY" 설치
   - https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. **YouTube 로그인**
   - https://youtube.com 접속
   - 본인 계정으로 로그인

3. **쿠키 추출**
   - 확장 프로그램 아이콘 클릭
   - "Export" 클릭
   - `youtube.com_cookies.txt` 다운로드

4. **파일 이름 변경 및 이동**
   ```
   다운로드한 파일을 d:\Bes2-Marketer\cookies.txt로 이동
   ```

## 방법 2: 수동 추출 (개발자 도구)

### 단계:
1. YouTube 접속 (로그인 상태)
2. F12 → Application → Cookies → https://youtube.com
3. 다음 쿠키 값 복사:
   - `VISITOR_INFO1_LIVE`
   - `YSC`
   - `PREF`
   - `LOGIN_INFO`

4. `d:\Bes2-Marketer\cookies.txt` 생성:
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	VISITOR_INFO1_LIVE	[복사한 값]
.youtube.com	TRUE	/	TRUE	0	YSC	[복사한 값]
.youtube.com	TRUE	/	TRUE	0	PREF	[복사한 값]
.youtube.com	TRUE	/	TRUE	0	LOGIN_INFO	[복사한 값]
```

## 쿠키 유효기간
- 보통 **1~3개월** 유지
- 만료되면 재추출 필요 (증상: 자막 추출 실패)

## Streamlit Cloud 배포 시
- 쿠키를 Secrets에 저장 가능 (자동으로 처리됨)
- 또는 로컬에서만 사용

---

**추천:** 방법 1 (Chrome 확장 프로그램)이 가장 간단합니다!
