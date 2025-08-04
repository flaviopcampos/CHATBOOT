import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.clinic_email = os.getenv('CLINIC_EMAIL', self.email_user)
        self.clinic_name = os.getenv('CLINIC_NAME', 'Clínica Espaço Vida')
    
    def send_email(self, to_email, subject, body, is_html=False):
        """Envia um email"""
        try:
            if not self.email_user or not self.email_password:
                print("⚠️ Configurações de email não encontradas - funcionalidade de email desabilitada")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            print(f"✅ Email enviado para {to_email}")
            return True
            
        except Exception as e:
            # Log do erro mas não interrompe o funcionamento
            print(f"⚠️ Email não enviado (configuração pendente): {str(e)[:100]}...")
            return False
    
    def send_ticket_notification(self, ticket_id, title, description, contact_info):
        """Envia notificação de novo ticket"""
        subject = f"🎫 Novo Ticket #{ticket_id} - {self.clinic_name}"
        
        body = f"""
🏥 {self.clinic_name}
📋 NOVO TICKET CRIADO

🆔 Ticket ID: #{ticket_id}
📝 Título: {title}
📄 Descrição: {description}

👤 INFORMAÇÕES DE CONTATO:
{contact_info}

⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🔗 Acesse o dashboard administrativo para mais detalhes:
http://localhost:5000/admin

---
Este é um email automático do sistema de atendimento.
        """
        
        return self.send_email(self.clinic_email, subject, body)
    
    def send_ticket_update_notification(self, ticket_id, status, notes=None):
        """Envia notificação de atualização de ticket"""
        subject = f"🔄 Ticket #{ticket_id} Atualizado - {self.clinic_name}"
        
        body = f"""
🏥 {self.clinic_name}
🔄 TICKET ATUALIZADO

🆔 Ticket ID: #{ticket_id}
📊 Novo Status: {status.upper()}
"""
        
        if notes:
            body += f"\n📝 Observações: {notes}"
        
        body += f"""

⏰ Atualizado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🔗 Acesse o dashboard administrativo:
http://localhost:5000/admin

---
Este é um email automático do sistema de atendimento.
        """
        
        return self.send_email(self.clinic_email, subject, body)
    
    def send_daily_report(self, statistics):
        """Envia relatório diário"""
        subject = f"📊 Relatório Diário - {self.clinic_name} - {datetime.now().strftime('%d/%m/%Y')}"
        
        body = f"""
🏥 {self.clinic_name}
📊 RELATÓRIO DIÁRIO

📅 Data: {datetime.now().strftime('%d/%m/%Y')}

📈 ESTATÍSTICAS:
• Conversas hoje: {statistics.get('conversations_today', 0)}
• Total de conversas: {statistics.get('total_conversations', 0)}
• Total de tickets: {statistics.get('total_tickets', 0)}

🎫 TICKETS POR STATUS:
"""
        
        tickets_by_status = statistics.get('tickets_by_status', {})
        for status, count in tickets_by_status.items():
            body += f"• {status.title()}: {count}\n"
        
        body += f"""

🔗 Dashboard administrativo:
http://localhost:5000/admin

---
Relatório automático gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        """
        
        return self.send_email(self.clinic_email, subject, body)
    
    def send_backup_notification(self, backup_path, success=True):
        """Envia notificação de backup"""
        if success:
            subject = f"✅ Backup Realizado - {self.clinic_name}"
            body = f"""
🏥 {self.clinic_name}
✅ BACKUP REALIZADO COM SUCESSO

📁 Arquivo: {backup_path}
⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

💾 O backup contém:
• Todas as conversas
• Todos os tickets
• Configurações do sistema

---
Backup automático do sistema de atendimento.
            """
        else:
            subject = f"❌ Erro no Backup - {self.clinic_name}"
            body = f"""
🏥 {self.clinic_name}
❌ ERRO AO REALIZAR BACKUP

⏰ Tentativa em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

⚠️ Verifique o sistema e tente novamente.

---
Notificação automática do sistema de atendimento.
            """
        
        return self.send_email(self.clinic_email, subject, body)