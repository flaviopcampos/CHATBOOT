import os
from twilio.rest import Client
import telebot
from telebot import types
import requests
import json
from datetime import datetime
from database import DatabaseManager
from sentiment_analysis import SentimentAnalyzer

class WhatsAppIntegration:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')
        self.client = None
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        
        self.db = DatabaseManager()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def send_message(self, to_number, message):
        """Envia mensagem via WhatsApp usando Twilio"""
        if not self.client:
            return {'success': False, 'error': 'Twilio não configurado'}
        
        try:
            # Formata número para WhatsApp
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message = self.client.messages.create(
                body=message,
                from_=self.whatsapp_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'status': message.status
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_incoming_message(self, from_number, message_body, message_sid=None):
        """Processa mensagem recebida do WhatsApp"""
        try:
            # Gera session_id baseado no número
            session_id = f"whatsapp_{from_number.replace('whatsapp:', '').replace('+', '')}"
            
            # Análise de sentimento
            sentiment_data = self.sentiment_analyzer.analyze_sentiment(message_body)
            
            # Aqui você integraria com seu chatbot principal
            # Por enquanto, uma resposta simples
            from app import ClinicaChatbot
            chatbot = ClinicaChatbot()
            
            # Tenta obter resposta da IA
            bot_response = None
            if hasattr(chatbot, 'get_response_openai'):
                bot_response = chatbot.get_response_openai(message_body)
            
            if not bot_response:
                bot_response = chatbot.get_response_fallback(message_body)
            
            if not bot_response:
                bot_response = "Olá! Obrigado por entrar em contato com a Clínica Espaço Vida. Em breve um de nossos especialistas entrará em contato. Para emergências, ligue: (27) 999637447"
            
            # Salva conversa no banco
            self.db.save_conversation(
                session_id=session_id,
                user_message=message_body,
                bot_response=bot_response,
                user_ip=from_number
            )
            
            # Cria ticket se necessário
            if sentiment_data['emergency_level'] == 'high' or sentiment_data['sentiment'] == 'emergency':
                self.db.create_ticket(
                    session_id=session_id,
                    title=f"Emergência WhatsApp - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    description=f"Mensagem com alta urgência detectada: {message_body[:200]}...",
                    contact_phone=from_number.replace('whatsapp:', ''),
                    priority='alta'
                )
            
            # Envia resposta
            send_result = self.send_message(from_number, bot_response)
            
            return {
                'success': True,
                'response_sent': send_result['success'],
                'sentiment': sentiment_data,
                'session_id': session_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_broadcast(self, numbers, message):
        """Envia mensagem para múltiplos números"""
        results = []
        for number in numbers:
            result = self.send_message(number, message)
            results.append({'number': number, 'result': result})
        return results

class TelegramIntegration:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot = None
        
        if self.bot_token:
            self.bot = telebot.TeleBot(self.bot_token)
            self.setup_handlers()
        
        self.db = DatabaseManager()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def setup_handlers(self):
        """Configura handlers do bot Telegram"""
        if not self.bot:
            return
        
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = """
🏥 *Bem-vindo à Clínica Espaço Vida!*

Somos especializados em tratamento de dependência química e saúde mental.

📞 *Contato:* (27) 999637447
📧 *Email:* flaviopcampos@gmail.com
🕐 *Atendimento:* 24 horas para emergências

*Como posso ajudá-lo hoje?*
            """
            
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            btn1 = types.KeyboardButton('ℹ️ Informações sobre tratamentos')
            btn2 = types.KeyboardButton('🏥 Como funciona a internação')
            btn3 = types.KeyboardButton('💰 Convênios e valores')
            btn4 = types.KeyboardButton('🚨 Emergência')
            btn5 = types.KeyboardButton('📞 Falar com especialista')
            markup.add(btn1, btn2, btn3, btn4, btn5)
            
            self.bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=markup)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            self.handle_incoming_message(message)
    
    def handle_incoming_message(self, message):
        """Processa mensagem recebida do Telegram"""
        try:
            user_id = message.from_user.id
            username = message.from_user.username or message.from_user.first_name
            message_text = message.text
            
            # Gera session_id baseado no user_id
            session_id = f"telegram_{user_id}"
            
            # Análise de sentimento
            sentiment_data = self.sentiment_analyzer.analyze_sentiment(message_text)
            
            # Respostas para botões específicos
            if message_text == 'ℹ️ Informações sobre tratamentos':
                response = self._get_treatment_info()
            elif message_text == '🏥 Como funciona a internação':
                response = self._get_internation_info()
            elif message_text == '💰 Convênios e valores':
                response = self._get_insurance_info()
            elif message_text == '🚨 Emergência':
                response = self._get_emergency_info()
            elif message_text == '📞 Falar com especialista':
                response = self._get_contact_info()
            else:
                # Integra com chatbot principal
                from app import ClinicaChatbot
                chatbot = ClinicaChatbot()
                
                response = None
                if hasattr(chatbot, 'get_response_openai'):
                    response = chatbot.get_response_openai(message_text)
                
                if not response:
                    response = chatbot.get_response_fallback(message_text)
                
                if not response:
                    response = "Obrigado por sua mensagem! Um especialista entrará em contato em breve."
            
            # Salva conversa
            self.db.save_conversation(
                session_id=session_id,
                user_message=message_text,
                bot_response=response,
                user_ip=f"telegram_{user_id}"
            )
            
            # Cria ticket se emergência
            if sentiment_data['emergency_level'] == 'high':
                self.db.create_ticket(
                    session_id=session_id,
                    title=f"Emergência Telegram - {username}",
                    description=f"Mensagem urgente: {message_text[:200]}...",
                    contact_name=username,
                    priority='alta'
                )
            
            # Envia resposta
            self.bot.reply_to(message, response, parse_mode='Markdown')
            
        except Exception as e:
            self.bot.reply_to(message, "Desculpe, ocorreu um erro. Tente novamente ou entre em contato: (27) 999637447")
    
    def _get_treatment_info(self):
        return """
🏥 *TRATAMENTOS DISPONÍVEIS*

🧠 *Dependência Química:*
• Álcool, cocaína, crack, maconha
• Medicamentos e opioides
• Jogos patológicos

💊 *Metodologias:*
• 12 Passos
• Terapia Cognitivo-Comportamental
• Modelo Minnesota
• Prevenção de Recaída

👥 *Equipe Multidisciplinar:*
• Psiquiatras
• Psicólogos
• Terapeutas
• Enfermeiros
• Assistentes Sociais
        """
    
    def _get_internation_info(self):
        return """
🏥 *COMO FUNCIONA A INTERNAÇÃO*

📋 *Processo:*
• Avaliação médica inicial
• Plano de tratamento personalizado
• Acompanhamento 24h
• Atividades terapêuticas

🏠 *Modalidades:*
• Internação voluntária
• Internação involuntária
• Tratamento ambulatorial

⏰ *Duração:*
• Personalizada conforme necessidade
• Acompanhamento pós-alta
        """
    
    def _get_insurance_info(self):
        return """
💰 *CONVÊNIOS E PAGAMENTO*

🏥 *Convênios Aceitos:*
• Unimed
• Bradesco Saúde
• SulAmérica
• Amil
• Outros convênios médicos

💳 *Formas de Pagamento:*
• Convênio médico
• Particular
• Parcelamento facilitado

📞 *Para orçamento:* (27) 999637447
        """
    
    def _get_emergency_info(self):
        return """
🚨 *ATENDIMENTO DE EMERGÊNCIA*

📞 *CONTATOS URGENTES:*
• Clínica: (27) 999637447
• SAMU: 192
• CVV: 188

🏥 *Serviços 24h:*
• Atendimento de crise
• Internação de urgência
• Suporte familiar
• Remoção especializada

⚠️ *Em caso de risco imediato, procure o hospital mais próximo!*
        """
    
    def _get_contact_info(self):
        return """
📞 *FALAR COM ESPECIALISTA*

🏥 *Clínica Espaço Vida*
📱 *WhatsApp:* (27) 999637447
📧 *Email:* flaviopcampos@gmail.com

🕐 *Horários:*
• Segunda a Sexta: 8h às 18h
• Sábados: 8h às 12h
• Emergências: 24h

💬 *Ou continue conversando aqui mesmo!*
        """
    
    def start_polling(self):
        """Inicia o bot Telegram"""
        if self.bot:
            print("🤖 Bot Telegram iniciado!")
            self.bot.polling(none_stop=True)
        else:
            print("❌ Token do Telegram não configurado")
    
    def send_message(self, chat_id, message):
        """Envia mensagem para um chat específico"""
        if self.bot:
            try:
                self.bot.send_message(chat_id, message, parse_mode='Markdown')
                return {'success': True}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return {'success': False, 'error': 'Bot não configurado'}

class WebsiteIntegration:
    """Classe para integração com websites via widget de chat"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def generate_widget_code(self, website_url, custom_config=None):
        """Gera código do widget para integração em websites"""
        config = {
            'api_url': 'http://localhost:5000',
            'theme': 'light',
            'position': 'bottom-right',
            'welcome_message': 'Olá! Como posso ajudá-lo?',
            'placeholder': 'Digite sua mensagem...',
            'title': 'Clínica Espaço Vida - Atendimento',
            'subtitle': 'Especialistas em dependência química',
            'primary_color': '#007bff',
            'font_family': 'Arial, sans-serif'
        }
        
        if custom_config:
            config.update(custom_config)
        
        widget_code = f"""
<!-- Widget Clínica Espaço Vida -->
<div id="clinica-chat-widget"></div>
<script>
(function() {{
    const config = {json.dumps(config, indent=2)};
    
    // Criar elementos do widget
    const widget = document.getElementById('clinica-chat-widget');
    
    // CSS do widget
    const style = document.createElement('style');
    style.textContent = `
        #clinica-chat-widget {{
            position: fixed;
            {config['position'].replace('-', ': 20px; ').replace('bottom', 'bottom').replace('right', 'right').replace('left', 'left').replace('top', 'top')}: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            z-index: 9999;
            font-family: {config['font_family']};
            display: none;
        }}
        
        .chat-header {{
            background: {config['primary_color']};
            color: white;
            padding: 15px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        
        .chat-messages {{
            height: 350px;
            overflow-y: auto;
            padding: 10px;
        }}
        
        .chat-input {{
            padding: 10px;
            border-top: 1px solid #eee;
        }}
        
        .chat-input input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            outline: none;
        }}
        
        .chat-toggle {{
            position: fixed;
            {config['position'].replace('-', ': 20px; ').replace('bottom', 'bottom').replace('right', 'right').replace('left', 'left').replace('top', 'top')}: 20px;
            width: 60px;
            height: 60px;
            background: {config['primary_color']};
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            z-index: 10000;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }}
        
        .message {{
            margin: 10px 0;
            padding: 8px 12px;
            border-radius: 15px;
            max-width: 80%;
        }}
        
        .message.user {{
            background: {config['primary_color']};
            color: white;
            margin-left: auto;
            text-align: right;
        }}
        
        .message.bot {{
            background: #f1f1f1;
            color: #333;
        }}
    `;
    document.head.appendChild(style);
    
    // HTML do widget
    widget.innerHTML = `
        <div class="chat-header">
            <h4 style="margin: 0;">{config['title']}</h4>
            <small>{config['subtitle']}</small>
        </div>
        <div class="chat-messages" id="chat-messages">
            <div class="message bot">{config['welcome_message']}</div>
        </div>
        <div class="chat-input">
            <input type="text" id="chat-input" placeholder="{config['placeholder']}" />
        </div>
    `;
    
    // Botão toggle
    const toggle = document.createElement('div');
    toggle.className = 'chat-toggle';
    toggle.innerHTML = '💬';
    toggle.onclick = function() {{
        const isVisible = widget.style.display !== 'none';
        widget.style.display = isVisible ? 'none' : 'block';
        toggle.innerHTML = isVisible ? '💬' : '✕';
    }};
    document.body.appendChild(toggle);
    
    // Funcionalidade de chat
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    
    function addMessage(text, isUser = false) {{
        const message = document.createElement('div');
        message.className = `message ${{isUser ? 'user' : 'bot'}}`;
        message.textContent = text;
        messages.appendChild(message);
        messages.scrollTop = messages.scrollHeight;
    }}
    
    function sendMessage() {{
        const text = input.value.trim();
        if (!text) return;
        
        addMessage(text, true);
        input.value = '';
        
        // Enviar para API
        fetch(config.api_url + '/chat', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({{
                message: text,
                source: 'website',
                website_url: '{website_url}'
            }})
        }})
        .then(response => response.json())
        .then(data => {{
            addMessage(data.response || 'Desculpe, ocorreu um erro.');
        }})
        .catch(error => {{
            addMessage('Erro de conexão. Tente novamente.');
        }});
    }}
    
    input.addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') {{
            sendMessage();
        }}
    }});
}})();
</script>
<!-- Fim Widget Clínica Espaço Vida -->
        """
        
        return widget_code
    
    def get_integration_instructions(self):
        """Retorna instruções de integração para websites"""
        return {
            'html_widget': {
                'title': 'Widget HTML/JavaScript',
                'description': 'Adicione o código do widget diretamente no seu site',
                'steps': [
                    '1. Copie o código do widget gerado',
                    '2. Cole antes do fechamento da tag </body>',
                    '3. Configure as opções conforme necessário',
                    '4. Teste a funcionalidade'
                ]
            },
            'wordpress': {
                'title': 'WordPress',
                'description': 'Integração via plugin ou código personalizado',
                'steps': [
                    '1. Acesse Aparência > Editor de Temas',
                    '2. Edite o arquivo footer.php',
                    '3. Adicione o código do widget antes de </body>',
                    '4. Salve as alterações'
                ]
            },
            'react': {
                'title': 'React/Next.js',
                'description': 'Componente React para integração',
                'steps': [
                    '1. Crie um componente ChatWidget',
                    '2. Use useEffect para carregar o script',
                    '3. Adicione o componente no layout',
                    '4. Configure as props necessárias'
                ]
            },
            'api_direct': {
                'title': 'API Direta',
                'description': 'Integração via chamadas HTTP diretas',
                'endpoint': 'POST /chat',
                'example': {
                    'url': 'http://localhost:5000/chat',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'body': {
                        'message': 'Olá, preciso de ajuda',
                        'source': 'website',
                        'website_url': 'https://meusite.com'
                    }
                }
            }
        }