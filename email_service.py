
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import config

class EmailSender:
    """Gmail SMTP를 이용한 이메일 발송 클래스"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465  # SSL 포트
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465  # SSL 포트

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        이메일 발송 함수
        """
        # 설정값 동적 로드 (Secrets 변경 시 즉시 반영을 위해)
        sender_email = config.SENDER_EMAIL
        sender_password = config.SENDER_PASSWORD.replace(" ", "") if config.SENDER_PASSWORD else None
        
        # 디버깅: 이메일 설정 확인
        print(f"📧 Attempting to send email from: {sender_email if sender_email else 'None'}")
        
        if not sender_email or not sender_password:
            print("❌ 이메일 설정(SENDER_EMAIL, SENDER_PASSWORD)이 누락되었습니다.")
            return False
            
        # 테스트 모드 확인
        final_to_email = to_email
        final_subject = subject
        
        if config.TEST_MODE:
            print(f"🧪 Test Mode Active: Redirecting email to {config.TEST_EMAIL}")
            final_to_email = config.TEST_EMAIL
            final_subject = f"[TEST MODE] {subject} (Original To: {to_email})"
            
        try:
            # 메시지 구성
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = final_to_email
            msg['Subject'] = final_subject
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
                
            print(f"✅ Email sent successfully to {final_to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

# 싱글톤 인스턴스
emailer = EmailSender()
