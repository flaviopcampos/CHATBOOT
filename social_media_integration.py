from flask import Blueprint, request, jsonify, render_template
import requests
import json
import os
from datetime import datetime
from database import DatabaseManager
from email_service import EmailService
import hashlib
import hmac

# Blueprint para integração com redes sociais
social_bp = Blueprint('social', __name__, url_prefix='/social')

class SocialMediaIntegration:
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.setup_database()
        
        # Configurações do Facebook/Instagram
        self.facebook_config = {
            'app_id': os.getenv('FACEBOOK_APP_ID'),
            'app_secret': os.getenv('FACEBOOK_APP_SECRET'),
            'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN'),
            'verify_token': os.getenv('FACEBOOK_VERIFY_TOKEN'),
            'page_id': os.getenv('FACEBOOK_PAGE_ID')
        }
        
        self.instagram_config = {
            'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
            'business_account_id': os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
        }
    
    def setup_database(self):
        """Configurar tabelas para redes sociais"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de mensagens das redes sociais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    message_id TEXT UNIQUE NOT NULL,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT,
                    message_text TEXT,
                    message_type TEXT DEFAULT 'text',
                    media_url TEXT,
                    timestamp TEXT NOT NULL,
                    is_reply INTEGER DEFAULT 0,
                    reply_to_id TEXT,
                    status TEXT DEFAULT 'received',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de configurações das redes sociais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    config_value TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, config_key)
                )
            ''')
            
            # Tabela de leads das redes sociais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT,
                    user_email TEXT,
                    user_phone TEXT,
                    lead_source TEXT,
                    lead_status TEXT DEFAULT 'new',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de campanhas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    campaign_name TEXT NOT NULL,
                    campaign_type TEXT NOT NULL,
                    target_audience TEXT,
                    message_template TEXT,
                    start_date DATE,
                    end_date DATE,
                    status TEXT DEFAULT 'draft',
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao configurar banco de dados das redes sociais: {e}")
        finally:
            if conn:
                conn.close()
    
    def verify_facebook_webhook(self, verify_token, challenge):
        """Verificar webhook do Facebook"""
        if verify_token == self.facebook_config['verify_token']:
            return challenge
        return None
    
    def verify_facebook_signature(self, payload, signature):
        """Verificar assinatura do Facebook"""
        try:
            expected_signature = hmac.new(
                self.facebook_config['app_secret'].encode('utf-8'),
                payload,
                hashlib.sha1
            ).hexdigest()
            
            return hmac.compare_digest(f"sha1={expected_signature}", signature)
        except Exception as e:
            print(f"Erro ao verificar assinatura: {e}")
            return False
    
    def process_facebook_message(self, message_data):
        """Processar mensagem do Facebook"""
        try:
            messaging = message_data.get('messaging', [])
            
            for message in messaging:
                sender_id = message.get('sender', {}).get('id')
                recipient_id = message.get('recipient', {}).get('id')
                timestamp = message.get('timestamp')
                
                # Verificar se é uma mensagem recebida
                if 'message' in message:
                    msg = message['message']
                    message_id = msg.get('mid')
                    message_text = msg.get('text', '')
                    
                    # Salvar mensagem no banco
                    self.save_social_message(
                        platform='facebook',
                        message_id=message_id,
                        sender_id=sender_id,
                        message_text=message_text,
                        timestamp=timestamp
                    )
                    
                    # Obter informações do usuário
                    user_info = self.get_facebook_user_info(sender_id)
                    
                    # Processar mensagem com chatbot
                    response = self.process_chatbot_response(message_text, user_info)
                    
                    # Enviar resposta
                    if response:
                        self.send_facebook_message(sender_id, response)
                
                # Verificar se é um postback (botão clicado)
                elif 'postback' in message:
                    postback = message['postback']
                    payload = postback.get('payload')
                    
                    # Processar ação do postback
                    self.process_facebook_postback(sender_id, payload)
            
            return True
            
        except Exception as e:
            print(f"Erro ao processar mensagem do Facebook: {e}")
            return False
    
    def get_facebook_user_info(self, user_id):
        """Obter informações do usuário do Facebook"""
        try:
            url = f"https://graph.facebook.com/{user_id}"
            params = {
                'fields': 'first_name,last_name,profile_pic',
                'access_token': self.facebook_config['access_token']
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            
            return {}
            
        except Exception as e:
            print(f"Erro ao obter informações do usuário: {e}")
            return {}
    
    def send_facebook_message(self, recipient_id, message_text):
        """Enviar mensagem pelo Facebook"""
        try:
            url = "https://graph.facebook.com/v18.0/me/messages"
            
            payload = {
                'recipient': {'id': recipient_id},
                'message': {'text': message_text},
                'access_token': self.facebook_config['access_token']
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                # Salvar mensagem enviada
                self.save_social_message(
                    platform='facebook',
                    message_id=f"sent_{datetime.now().timestamp()}",
                    sender_id='bot',
                    message_text=message_text,
                    timestamp=str(int(datetime.now().timestamp() * 1000)),
                    is_reply=1
                )
                return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao enviar mensagem do Facebook: {e}")
            return False
    
    def process_instagram_message(self, message_data):
        """Processar mensagem do Instagram"""
        try:
            # Instagram usa a mesma API do Facebook para mensagens
            return self.process_facebook_message(message_data)
            
        except Exception as e:
            print(f"Erro ao processar mensagem do Instagram: {e}")
            return False
    
    def get_instagram_media_comments(self, media_id):
        """Obter comentários de uma mídia do Instagram"""
        try:
            url = f"https://graph.facebook.com/v18.0/{media_id}/comments"
            params = {
                'fields': 'id,text,username,timestamp',
                'access_token': self.instagram_config['access_token']
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json().get('data', [])
            
            return []
            
        except Exception as e:
            print(f"Erro ao obter comentários do Instagram: {e}")
            return []
    
    def reply_instagram_comment(self, comment_id, reply_text):
        """Responder comentário no Instagram"""
        try:
            url = f"https://graph.facebook.com/v18.0/{comment_id}/replies"
            
            payload = {
                'message': reply_text,
                'access_token': self.instagram_config['access_token']
            }
            
            response = requests.post(url, data=payload)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Erro ao responder comentário do Instagram: {e}")
            return False
    
    def save_social_message(self, platform, message_id, sender_id, message_text, timestamp, is_reply=0, sender_name=None):
        """Salvar mensagem das redes sociais"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO social_messages (
                    platform, message_id, sender_id, sender_name, message_text,
                    timestamp, is_reply
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                platform, message_id, sender_id, sender_name, message_text,
                timestamp, is_reply
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")
            return False
        finally:
            conn.close()
    
    def process_chatbot_response(self, message_text, user_info):
        """Processar resposta do chatbot"""
        try:
            # Respostas automáticas básicas
            message_lower = message_text.lower()
            
            if any(word in message_lower for word in ['oi', 'olá', 'hello', 'hi']):
                name = user_info.get('first_name', 'amigo')
                return f"Olá {name}! 👋 Como posso ajudá-lo hoje? Estou aqui para esclarecer dúvidas sobre nossos serviços da Clínica Espaço Vida."
            
            elif any(word in message_lower for word in ['horário', 'funcionamento', 'aberto']):
                return "🕐 Nosso horário de funcionamento:\n\n📅 Segunda a Sexta: 8h às 18h\n📅 Sábado: 8h às 12h\n📅 Domingo: Fechado\n\nPara agendamentos, entre em contato conosco!"
            
            elif any(word in message_lower for word in ['agendar', 'consulta', 'agendamento']):
                return "📅 Para agendar sua consulta:\n\n1️⃣ Ligue: (11) 1234-5678\n2️⃣ WhatsApp: (11) 9876-5432\n3️⃣ Site: www.clinicaespacovida.com.br\n\nTemos disponibilidade para esta semana! 😊"
            
            elif any(word in message_lower for word in ['preço', 'valor', 'quanto custa']):
                return "💰 Nossos valores:\n\n🔸 Consulta inicial: R$ 150\n🔸 Retorno: R$ 120\n🔸 Terapia individual: R$ 130\n🔸 Terapia em grupo: R$ 80\n\nAceitamos diversos planos de saúde! 💳"
            
            elif any(word in message_lower for word in ['localização', 'endereço', 'onde fica']):
                return "📍 Nossa localização:\n\nRua das Flores, 123\nJardim Esperança\nSão Paulo - SP\nCEP: 01234-567\n\n🚗 Estacionamento gratuito\n🚇 Próximo ao metrô Vila Madalena"
            
            elif any(word in message_lower for word in ['obrigado', 'obrigada', 'thanks', 'valeu']):
                return "😊 Por nada! Estamos sempre aqui para ajudar. Se precisar de mais alguma coisa, é só chamar! \n\nTenha um ótimo dia! 🌟"
            
            else:
                return "Obrigado pela sua mensagem! 😊 Nossa equipe irá analisá-la e responder em breve. Para atendimento imediato, ligue (11) 1234-5678 ou acesse nosso site."
            
        except Exception as e:
            print(f"Erro ao processar resposta do chatbot: {e}")
            return "Obrigado pela sua mensagem! Nossa equipe entrará em contato em breve."
    
    def create_facebook_campaign(self, campaign_data):
        """Criar campanha no Facebook"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO social_campaigns (
                    platform, campaign_name, campaign_type, target_audience,
                    message_template, start_date, end_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'facebook',
                campaign_data['name'],
                campaign_data['type'],
                campaign_data.get('target_audience', ''),
                campaign_data.get('message_template', ''),
                campaign_data.get('start_date'),
                campaign_data.get('end_date'),
                'active'
            ))
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            print(f"Erro ao criar campanha: {e}")
            return None
        finally:
            conn.close()
    
    def get_social_analytics(self, platform, start_date=None, end_date=None):
        """Obter analytics das redes sociais"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Mensagens por dia
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM social_messages
                WHERE platform = ?
                AND (? IS NULL OR DATE(created_at) >= ?)
                AND (? IS NULL OR DATE(created_at) <= ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (platform, start_date, start_date, end_date, end_date))
            
            messages_by_day = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Total de mensagens
            cursor.execute('''
                SELECT COUNT(*) FROM social_messages
                WHERE platform = ?
                AND (? IS NULL OR DATE(created_at) >= ?)
                AND (? IS NULL OR DATE(created_at) <= ?)
            ''', (platform, start_date, start_date, end_date, end_date))
            
            total_messages = cursor.fetchone()[0]
            
            # Usuários únicos
            cursor.execute('''
                SELECT COUNT(DISTINCT sender_id) FROM social_messages
                WHERE platform = ?
                AND (? IS NULL OR DATE(created_at) >= ?)
                AND (? IS NULL OR DATE(created_at) <= ?)
                AND sender_id != 'bot'
            ''', (platform, start_date, start_date, end_date, end_date))
            
            unique_users = cursor.fetchone()[0]
            
            # Taxa de resposta
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN is_reply = 1 THEN 1 END) as replies,
                    COUNT(CASE WHEN is_reply = 0 THEN 1 END) as received
                FROM social_messages
                WHERE platform = ?
                AND (? IS NULL OR DATE(created_at) >= ?)
                AND (? IS NULL OR DATE(created_at) <= ?)
            ''', (platform, start_date, start_date, end_date, end_date))
            
            response_data = cursor.fetchone()
            response_rate = (response_data[0] / response_data[1] * 100) if response_data[1] > 0 else 0
            
            return {
                'total_messages': total_messages,
                'unique_users': unique_users,
                'response_rate': round(response_rate, 2),
                'messages_by_day': messages_by_day
            }
            
        except Exception as e:
            print(f"Erro ao obter analytics: {e}")
            return {}
        finally:
            conn.close()
    
    def get_social_leads(self, platform=None):
        """Obter leads das redes sociais"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if platform:
                cursor.execute('''
                    SELECT * FROM social_leads
                    WHERE platform = ?
                    ORDER BY created_at DESC
                ''', (platform,))
            else:
                cursor.execute('''
                    SELECT * FROM social_leads
                    ORDER BY created_at DESC
                ''')
            
            leads = []
            for row in cursor.fetchall():
                leads.append({
                    'id': row[0],
                    'platform': row[1],
                    'user_id': row[2],
                    'user_name': row[3],
                    'user_email': row[4],
                    'user_phone': row[5],
                    'lead_source': row[6],
                    'lead_status': row[7],
                    'notes': row[8],
                    'created_at': row[9],
                    'updated_at': row[10]
                })
            
            return leads
            
        except Exception as e:
            print(f"Erro ao obter leads: {e}")
            return []
        finally:
            conn.close()

# Instância global
social_integration = SocialMediaIntegration()

# Rotas da API
@social_bp.route('/')
def social_dashboard():
    """Dashboard das redes sociais"""
    return render_template('social_dashboard.html')

@social_bp.route('/facebook/webhook', methods=['GET', 'POST'])
def facebook_webhook():
    """Webhook do Facebook"""
    if request.method == 'GET':
        # Verificação do webhook
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        result = social_integration.verify_facebook_webhook(verify_token, challenge)
        if result:
            return result
        else:
            return 'Forbidden', 403
    
    elif request.method == 'POST':
        # Processar mensagem
        signature = request.headers.get('X-Hub-Signature')
        
        if not social_integration.verify_facebook_signature(request.data, signature):
            return 'Forbidden', 403
        
        data = request.get_json()
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                social_integration.process_facebook_message(entry)
        
        return 'OK', 200

@social_bp.route('/instagram/webhook', methods=['GET', 'POST'])
def instagram_webhook():
    """Webhook do Instagram"""
    # Instagram usa o mesmo webhook do Facebook
    return facebook_webhook()

@social_bp.route('/analytics/<platform>')
def get_analytics(platform):
    """Obter analytics de uma plataforma"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics = social_integration.get_social_analytics(platform, start_date, end_date)
        return jsonify({'success': True, 'analytics': analytics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@social_bp.route('/leads')
def get_leads():
    """Obter leads das redes sociais"""
    try:
        platform = request.args.get('platform')
        leads = social_integration.get_social_leads(platform)
        return jsonify({'success': True, 'leads': leads})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@social_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Criar nova campanha"""
    try:
        data = request.get_json()
        campaign_id = social_integration.create_facebook_campaign(data)
        
        if campaign_id:
            return jsonify({'success': True, 'campaign_id': campaign_id})
        else:
            return jsonify({'success': False, 'error': 'Erro ao criar campanha'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@social_bp.route('/send-message', methods=['POST'])
def send_message():
    """Enviar mensagem manual"""
    try:
        data = request.get_json()
        platform = data.get('platform')
        recipient_id = data.get('recipient_id')
        message = data.get('message')
        
        if platform == 'facebook':
            success = social_integration.send_facebook_message(recipient_id, message)
        else:
            return jsonify({'success': False, 'error': 'Plataforma não suportada'})
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def init_social_media(app):
    """Inicializar integração com redes sociais no app Flask"""
    app.register_blueprint(social_bp)
    return app