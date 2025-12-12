# 📧 이메일 자동 발송 구현 플랜 (Email Automation Plan)

## 1. 목표 (Goal)
- 현재 "복사 & 붙여넣기" 방식의 반자동 시스템을 **"클릭 한 번으로 발송(One-Click Send)"**하는 전자동 시스템으로 업그레이드.
- 최종적으로는 키워드만 입력하면 검색부터 발송까지 알아서 하는 **AI 에이전트(Full Auto)**를 지향.
- **구분:** 이메일은 자동 발송, 유튜브 댓글은 기존처럼 수동 복사(YouTube 정책상 자동 댓글은 스팸 처리 위험 높음).

---

## 2. 구현 방식 비교 (2가지 옵션)

초기 스타트업/개인 프로젝트 단계에서는 **옵션 A (Gmail SMTP)**를 강력 추천합니다. 무료이고 구현이 빠릅니다.

### 🏷️ 옵션 A: Gmail SMTP (추천 ⭐️)
- **방식:** 본인의 Gmail 계정을 통해 메일을 보냅니다.
- **장점:** 
  - **비용 0원.**
  - 별도의 도메인 인증이나 복잡한 설정 불필요.
  - "보낸 사람"이 실제 내 메일 주소라 수신자가 거부감을 덜 느낌.
- **단점:**
  - 하루 발송 제한 (약 500통). 마케팅 초기 단계에선 충분.
  - 구글 계정 보안 설정에서 '앱 비밀번호(App Password)' 생성 필요.

### 🏷️ 옵션 B: 전문 이메일 API (SendGrid, AWS SES)
- **방식:** 대량 메일 발송 전용 서비스를 이용.
- **장점:** 하루 수만 통 발송 가능, 발송 통계(오픈율 등) 확인 가능.
- **단점:**
  - 도메인 구입 및 인증(DNS 설정) 필수. (초기 세팅 복잡)
  - 유료 과금 발생 가능성.
  - 스팸 필터에 걸릴 확률 관리가 필요.

---

## 3. 구현 로드맵 (Roadmap)

### 1단계: 환경 설정 (.env)
Gmail을 사용하기 위한 보안 설정을 추가합니다.
```env
# .env 파일에 추가될 내용
SENDER_EMAIL=myemail@gmail.com
SENDER_PASSWORD=xxyyzzaabbcc  # 구글 앱 비밀번호 (기존 비번 아님)
```

### 2단계: 백엔드 로직 구현 (`email_service.py`)
`smtplib` 라이브러리를 사용하여 실제 메일을 쏘는 기능을 만듭니다.

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body):
    # Gmail SMTP 서버 접속
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
```

### 3단계: UI 업데이트 (`main.py`)
- [탭 2: 이메일 발송 관리] 화면을 수정합니다.
- 기존 [복사하기] 버튼 옆에 **[🚀 이메일 전송]** 버튼을 추가합니다.
- 전송 성공 시 DB의 상태(`status`)를 `sent`로 자동 업데이트합니다.

---

## 4. 향후 확장성 (Full Auto)
이 기능이 구현되면, 나중에는 아래와 같은 완전 자동화가 가능해집니다.

1.  **스케줄러 도입:** 밤 12시에 봇이 깨어나서 어제 올라온 영상을 검색.
2.  **자동 필터링:** AI가 '관련성 80점 이상'인 영상만 골라냄.
3.  **자동 발송:** 컨펌 없이(또는 관리자에게 알림만 주고) 100점짜리 영상엔 즉시 이메일 발송.
4.  **리포트:** 아침에 사장님께 "어젯밤 5명에게 제안서를 보냈습니다"라고 슬랙/카톡 알림.

---

## 🚀 바로 시작하시겠습니까?
"Gmail 앱 비밀번호"만 발급받아 오시면, 제가 **30분 안에** 위 기능을 코드에 적용해드릴 수 있습니다. 
구글 계정 관리 > 보안 > 2단계 인증 > 앱 비밀번호 에서 발급 가능합니다.
