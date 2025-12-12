
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import config

class EmailSender:
    """Gmail SMTP를 이용한 이메일 발송 클래스"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465  # SSL 포트
        self.sender_email = config.SENDER_EMAIL
        # 띄어쓰기가 있어도 제거하고 사용
        self.sender_password = config.SENDER_PASSWORD.replace(" ", "") if config.SENDER_PASSWORD else None

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        이메일 발송 함수
        
        Args:
            to_email: 수신자 이메일
            subject: 메일 제목
            body: 메일 본문
            
        Returns:
            성공 여부 True/False
        """
        if not self.sender_email or not self.sender_password:
            print("❌ 이메일 설정(SENDER_EMAIL, SENDER_PASSWORD)이 누락되었습니다.")
            return False
            
        try:
            # 메시지 구성
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

# 싱글톤 인스턴스
emailer = EmailSender()
