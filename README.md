# 🚀 Bes2 Marketer

AI 기반 유튜브 마케팅 자동화 웹 앱

## 📋 개요

Bes2 Marketer는 유튜브에서 '사진 정리', '용량 부족' 관련 영상을 자동으로 찾아내고, 해당 유튜버에게 Bes2 앱을 소개하는 맞춤형 이메일과 댓글 초안을 AI로 생성하는 마케팅 자동화 도구입니다.

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Gemini API
- **YouTube**: YouTube Data API v3

## 📁 프로젝트 구조

```
Bes2-Marketer/
├── app.py              # Streamlit 메인 앱
├── config.py           # 환경 설정
├── database.py         # Supabase CRUD 함수
├── schema.sql          # DB 스키마 (Supabase에서 실행)
├── requirements.txt    # Python 패키지
├── env.example         # 환경 변수 예시
└── README.md
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# 저장소 클론 후 디렉토리 이동
cd Bes2-Marketer

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`env.example`을 복사하여 `.env` 파일을 생성하고 API 키를 입력하세요:

```bash
copy env.example .env  # Windows
# cp env.example .env  # Mac/Linux
```

`.env` 파일 내용:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
GEMINI_API_KEY=your-gemini-api-key
YOUTUBE_API_KEY=your-youtube-api-key
```

### 3. Supabase 데이터베이스 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. SQL Editor에서 `schema.sql` 내용 실행
3. Project Settings > API에서 URL과 anon key 복사

### 4. API 키 발급

#### Google Gemini API
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. API 키 생성

#### YouTube Data API
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성
3. YouTube Data API v3 활성화
4. 사용자 인증 정보 > API 키 생성

### 5. 앱 실행

```bash
streamlit run app.py
```

## 📊 데이터베이스 스키마

### leads (유튜버 정보)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | Primary Key |
| channel_name | VARCHAR | 채널명 |
| channel_id | VARCHAR | YouTube 채널 ID |
| subscriber_count | INTEGER | 구독자 수 |
| email | VARCHAR | 이메일 주소 |
| keywords | TEXT[] | 주요 키워드 |
| status | VARCHAR | 상태 (new/contacted/responded/converted/rejected) |

### videos (영상 정보)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | Primary Key |
| lead_id | UUID | 연결된 리드 ID (FK) |
| video_id | VARCHAR | YouTube 영상 ID |
| title | VARCHAR | 영상 제목 |
| transcript_text | TEXT | 자막 전체 텍스트 |
| summary | TEXT | AI 요약 |
| relevance_score | FLOAT | 관련성 점수 (0~1) |

### drafts (마케팅 초안)
| 필드 | 타입 | 설명 |
|------|------|------|
| id | UUID | Primary Key |
| video_id | UUID | 연결된 영상 ID (FK) |
| lead_id | UUID | 연결된 리드 ID (FK) |
| draft_type | VARCHAR | 타입 (email/comment) |
| content | TEXT | 생성된 내용 |
| status | VARCHAR | 상태 (pending/approved/sent/rejected) |

## 🔧 주요 기능

- [ ] 유튜브 영상 검색 및 수집
- [ ] 자막 추출 및 AI 요약
- [ ] 맞춤형 이메일 초안 생성
- [ ] 댓글 초안 생성
- [ ] 리드 관리 대시보드
- [ ] 초안 승인/발송 워크플로우

## 📝 라이선스

MIT License

