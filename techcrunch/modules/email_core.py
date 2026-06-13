# modules/email_core.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple, Optional
import threading


class EmailManager:
    def __init__(self, config: Dict):
        self.config = config
        self.sent_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test SMTP connection"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.config['smtp_server'], 
                self.config['smtp_port'], 
                context=context, 
                timeout=15
            ) as server:
                server.login(
                    self.config['email_address'], 
                    self.config['email_password']
                )
            return True, "Connection successful"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def send_email(self, to_email: str, subject: str, body: str) -> Tuple[bool, str]:
        """Send a single email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config['email_address']
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", 'utf-8'))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.config['smtp_server'],
                self.config['smtp_port'],
                context=context,
                timeout=30
            ) as server:
                server.login(self.config['email_address'], self.config['email_password'])
                server.send_message(msg)
            
            with self.lock:
                self.sent_count += 1
            return True, "Email sent successfully"
            
        except smtplib.SMTPRecipientsRefused:
            with self.lock:
                self.failed_count += 1
            return False, "Recipient email refused"
        except Exception as e:
            with self.lock:
                self.failed_count += 1
            return False, f"Error: {str(e)}"
    
    def get_stats(self) -> Dict[str, int]:
        """Get email statistics"""
        with self.lock:
            return {
                "sent": self.sent_count,
                "failed": self.failed_count,
                "total": self.sent_count + self.failed_count
            }
    
    def format_email(self, author_info: Dict, template_key: str = "business_insider") -> Tuple[str, str]:
    
          template = self.config['email_templates'].get(template_key, 
                    self.config['email_templates']['default'])
    
          sender_info = self.config.get('sender_info', {})
    
    
          subject = template['subject'].format(
              author_name=author_info.get('name', author_info.get('Author Name', '')),
              publication="Business Insider",
              topic=author_info.get('topic', author_info.get('Primary Topic', ''))
                    )
    
          body = template['body'].format(
              author_name=author_info.get('name', author_info.get('Author Name', '')),
              publication="Business Insider",
              topic=author_info.get('topic', author_info.get('Primary Topic', '')),
              your_name=sender_info.get('your_name', ''),
              your_position=sender_info.get('your_position', ''),
              company_name=sender_info.get('company_name', '')
                      )
    
          return subject, body
    
    def send_to_author(self, author_info: Dict) -> Tuple[bool, str]:
        """Send email to author using template"""
        email = author_info.get('email', '')
        if not email:
            return False, "No email address"
        
        subject, body = self.format_email(author_info)
        return self.send_email(email, subject, body)
