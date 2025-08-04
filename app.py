from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for, flash
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime
import json
import uuid
import logging
import requests
from database import DatabaseManager
from email_service import EmailService
from backup_service import BackupService
from auth import init_auth, login_required, admin_required, auth_bp
from sentiment_analysis import SentimentAnalyzer
from multilingual import MultilingualSupport
from integrations import WhatsAppIntegration, TelegramIntegration, WebsiteIntegration
from crm_integration import CRMIntegration
from backup_service import BackupService
from additional_crm_integration import additional_crm_bp, init_additional_crm_tables
from rating_system import rating_bp, init_rating_system
from social_media_integration import social_bp, init_social_media
from business_intelligence import bi_bp, init_bi
from calendar_integration import calendar_bp, init_calendar
from api_rest import api_bp
from voice_chat import voice_bp
import csv
from io import StringIO

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'sua_chave_secreta_aqui')  # Altere para uma chave segura
CORS(app)

# Inicializar autenticação
init_auth(app)

# Inicializar banco de dados
db_manager = DatabaseManager()

# Inicializar tabelas adicionais
init_additional_crm_tables()
init_rating_system(app)
init_social_media(app)
init_bi(app)
init_calendar(app)

# Registrar blueprints
app.register_blueprint(additional_crm_bp)
app.register_blueprint(api_bp)
app.register_blueprint(voice_bp)

# Inicializar serviços
sentiment_analyzer = SentimentAnalyzer()
multilingual = MultilingualSupport()
crm_integration = CRMIntegration()
whatsapp_integration = WhatsAppIntegration()
telegram_integration = TelegramIntegration()
website_integration = WebsiteIntegration()

# Configuração de múltiplas APIs de IA
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # openai, huggingface, gemini

# Inicializa cliente OpenAI (se disponível)
try:
    if AI_PROVIDER == 'openai':
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY', 'sua_api_key_aqui')
        )
except Exception as e:
    print(f"⚠️ OpenAI não disponível: {e}")
    client = None

class ClinicaChatbot:
    def __init__(self):
        self.system_prompt = """
        Você é um assistente virtual especializado em atendimento para uma clínica de reabilitação de dependentes químicos e saúde mental.
        
        NOME DA CLINICA:
        CLINICA ESPAÇO VIDA

        INFORMAÇÕES DA CLÍNICA:
        - Especializada em tratamento de dependência química e transtornos de saúde mental
        - Metodologias: 12 Passos, Terapia Cognitivo-Comportamental (TCC), Modelo Minnesota
        - Equipe multidisciplinar: psiquiatras, psicólogos, terapeutas, enfermeiros, assistentes sociais
        - Tratamentos para: álcool, cocaína, crack, maconha, medicamentos, jogos patológicos
        - Modalidades: internação voluntária e involuntária, ambulatorial
        - Atendimento 24 horas para emergências
        - Acomodações masculinas
        - Aceita convênios médicos
        - E-mail: flaviopcampos@gmail.com
        - Telefone: (27) 999637447
        - Horários: Segunda a Sexta 8h às 18h, Sábados 8h às 12h, Emergências 24h
        
        ABORDAGENS TERAPÊUTICAS:
        - Terapia Cognitivo-Comportamental (TCC): foca em pensamentos, crenças e comportamentos disfuncionais
        - Metodologia 12 Passos: baseada na filosofia de Alcoólicos Anônimos e Narcóticos Anônimos
        - Modelo Minnesota: abordagem biopsicossocial com foco na abstinência total
        - Prevenção de Recaída: estratégias para evitar retorno ao uso
        - Terapia de Grupo: compartilhamento de experiências e apoio mútuo
        - Terapia Individual: atendimento personalizado
        - Terapia Familiar: envolvimento da família no processo de recuperação
        - Atividades ocupacionais e físicas
        
        SINTOMAS DA DEPENDÊNCIA QUÍMICA:
        - Compulsão: desejo incontrolável de usar substâncias
        - Obsessão: pensamentos constantes sobre drogas/álcool
        - Perda de controle: incapacidade de parar ou controlar o uso
        - Tolerância: necessidade de doses maiores
        - Síndrome de abstinência: sintomas físicos e psicológicos ao parar
        - Negligência de responsabilidades
        - Problemas familiares, sociais e profissionais
        - Isolamento social
        - Mudanças de humor e comportamento
        
        INSTRUÇÕES DE ATENDIMENTO:
        1. Seja empático, acolhedor e não julgue
        2. Ofereça esperança e motivação para o tratamento
        3. Explique que dependência química é uma doença tratável
        4. Forneça informações sobre tratamentos disponíveis
        5. Oriente sobre internação voluntária e involuntária
        6. Explique sobre convênios e formas de pagamento
        7. Ofereça contato para agendamento de avaliação
        8. Em casos de emergência, oriente procurar atendimento imediato
        9. Mantenha sigilo e confidencialidade
        10. Encoraje a busca por ajuda profissional
        11. Peça para que a pessoa deixe o nome e o contato dela para que possa ser contactada
        12. Quando a pessoa fornecer o contato, agradeça pelo contato e pergunte se tem mais alguma dúvida. Caso contrário, informe que o atendimento será encerrado
        
        NUNCA:
        - Dê diagnósticos médicos
        - Prescreva medicamentos
        - Substitua consulta médica
        - Julgue ou critique o paciente/família
        - Prometa cura garantida
        
        Responda sempre em português brasileiro, de forma clara e acessível.
        Não utilize:  Entendo que você está buscando informações sobre
        Não utilize: Compreendo que você deseja saber sobre 
        """
        
        self.conversation_history = []
    
    def get_response_openai(self, user_message):
        """
        Gera resposta usando OpenAI GPT
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt}
                ] + self.conversation_history[-10:],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro na API OpenAI: {e}")
            return None
    
    def get_response_huggingface(self, user_message):
        """
        Gera resposta usando Hugging Face (gratuito)
        """
        try:
            # Usando modelo gratuito do Hugging Face
            api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY', '')}"}
            
            # Se não tiver API key, usa modelo público
            if not os.getenv('HUGGINGFACE_API_KEY'):
                api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
                headers = {}
            
            payload = {
                "inputs": f"Contexto: Você é um assistente de uma clínica de reabilitação especializada em dependência química e saúde mental.\n\nPergunta: {user_message}\n\nResposta:",
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').replace(payload['inputs'], '').strip()
            
            return None
        except Exception as e:
            print(f"Erro na API Hugging Face: {e}")
            return None
    
    def get_response_gemini(self, user_message):
        """
        Gera resposta usando Google Gemini (tem versão gratuita)
        """
        try:
            # Implementação básica para Gemini
            # Nota: Requer configuração da API do Google
            api_key = os.getenv('GOOGLE_API_KEY', '')
            if not api_key:
                return None
                
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{self.system_prompt}\n\nUsuário: {user_message}\n\nAssistente:"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500
                }
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            return None
        except Exception as e:
            print(f"Erro na API Gemini: {e}")
            return None
    
    def normalize_text(self, text):
        """
        Normaliza o texto removendo acentos e caracteres especiais
        """
        import unicodedata
        import re
        
        # Remove acentos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Converte para minúsculas
        text = text.lower()
        
        # Remove pontuação e caracteres especiais
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        return text
    
    def contains_keywords(self, text, keywords):
        """
        Verifica se o texto contém alguma das palavras-chave (com normalização)
        """
        normalized_text = self.normalize_text(text)
        
        for keyword in keywords:
            normalized_keyword = self.normalize_text(keyword)
            if normalized_keyword in normalized_text:
                return True
        return False
    
    def get_response_fallback(self, user_message):
        """
        Resposta de fallback quando nenhuma IA está disponível
        """
        # Palavras-chave para tratamentos
        tratamento_keywords = [
            'tratamento', 'terapia', 'ajuda', 'tratar', 'curar', 'cura', 'recuperacao', 'recuperação',
            'reabilitacao', 'reabilitação', 'dependencia', 'dependência', 'vicio', 'vício',
            'drogas', 'alcool', 'álcool', 'medicamento', 'remedio', 'remédio', 'psicologia',
            'psiquiatria', 'medico', 'médico', 'doutor', 'doutora', 'terapeuta'
        ]
        
        # Palavras-chave para internação
        internacao_keywords = [
            'internacao', 'internação', 'internar', 'como funciona', 'funcionamento',
            'processo', 'procedimento', 'admissao', 'admissão', 'entrada', 'ingresso',
            'clinica', 'clínica', 'hospital', 'instituicao', 'instituição', 'centro',
            'unidade', 'estabelecimento', 'local', 'onde', 'endereco', 'endereço'
        ]
        
        # Palavras-chave para convênios e valores
        convenio_keywords = [
            'convenio', 'convênio', 'plano', 'preco', 'preço', 'valor', 'custo', 'quanto custa',
            'pagamento', 'pagar', 'dinheiro', 'financeiro', 'orcamento', 'orçamento',
            'seguro', 'saude', 'saúde', 'unimed', 'bradesco', 'sulamerica', 'amil',
            'particular', 'sus', 'gratuito', 'gratis', 'grátis'
        ]
        
        # Palavras-chave para emergência
        emergencia_keywords = [
            'emergencia', 'emergência', 'urgente', 'urgencia', 'urgência', 'crise',
            'socorro', 'ajuda imediata', 'agora', 'rapido', 'rápido', 'ja', 'já',
            'desespero', 'desesperad', 'suicidio', 'suicídio', 'morte', 'morrer',
            'overdose', 'intoxicacao', 'intoxicação', '24 horas', '24h', 'plantao', 'plantão'
        ]
        
        # Palavras-chave para informações sobre dependência
        dependencia_keywords = [
            'dependente', 'viciado', 'adicto', 'usuario', 'usuário', 'consumidor',
            'crack', 'cocaina', 'cocaína', 'maconha', 'cannabis', 'heroina', 'heroína',
            'ecstasy', 'lsd', 'anfetamina', 'metanfetamina', 'opioides', 'morfina',
            'codeina', 'codeína', 'tramadol', 'rivotril', 'clonazepam', 'alprazolam'
        ]
        
        # Palavras-chave para identificação de sinais de dependência
        identificacao_keywords = [
            'identificar', 'identifico', 'reconhecer', 'perceber', 'notar', 'descobrir',
            'sinais', 'sintomas', 'comportamento', 'mudancas', 'mudanças', 'indicios', 'indícios',
            'como saber', 'como sei', 'como descobrir', 'como perceber', 'como identificar',
            'pessoa viciada', 'alguem viciado', 'alguém viciado', 'familiar viciado',
            'caracteristicas', 'características', 'manifestacoes', 'manifestações',
            'evidencias', 'evidências', 'pistas', 'alertas', 'avisos'
        ]
        
        # Palavras-chave para contato/telefone
        contato_keywords = [
            'telefone', 'fone', 'numero', 'número', 'contato', 'ligar', 'falar',
            'comunicar', 'entrar em contato', 'como falar', 'como ligar',
            'telefone da clinica', 'telefone da clínica', 'numero da clinica', 'número da clínica',
            'contato da clinica', 'contato da clínica', 'como entrar em contato',
            'whatsapp', 'celular', 'fixo', 'ramal', 'atendimento', 'recepcao', 'recepção'
        ]
        
        # Verifica qual categoria de resposta usar
        if self.contains_keywords(user_message, identificacao_keywords):
            return """🔍 **COMO IDENTIFICAR UMA PESSOA VICIADA:**
            
⚠️ **Sinais Físicos:**
• Mudanças bruscas de peso (perda ou ganho)
• Olhos vermelhos, pupilas dilatadas ou contraídas
• Tremores nas mãos
• Falta de higiene pessoal
• Marcas de agulhas (no caso de drogas injetáveis)
• Odor estranho na roupa ou hálito
• Sonolência excessiva ou insônia

🧠 **Sinais Comportamentais:**
• Mudanças drásticas de humor
• Isolamento social e familiar
• Mentiras frequentes
• Roubo de dinheiro ou objetos
• Abandono de responsabilidades
• Perda de interesse em atividades antes prazerosas
• Agressividade ou irritabilidade

💼 **Sinais Sociais:**
• Problemas no trabalho ou escola
• Mudança de círculo de amizades
• Problemas financeiros inexplicáveis
• Conflitos familiares constantes
• Negligência com filhos ou família

🚨 **IMPORTANTE:**
Se você identificou esses sinais em alguém próximo, procure ajuda profissional imediatamente.

📞 **Nossa clínica oferece:**
• Avaliação especializada
• Orientação familiar
• Intervenção profissional
• Tratamento personalizado

Ligue: (11) 99999-9999"""
        
        elif self.contains_keywords(user_message, tratamento_keywords + dependencia_keywords):
            # Para perguntas sobre tratamentos, tenta usar IA primeiro para respostas mais detalhadas
            return None  # Retorna None para forçar o uso da IA
        
        elif self.contains_keywords(user_message, internacao_keywords):
            return """Nossa internação funciona da seguinte forma:
            
📋 **Processo de Admissão:**
• Avaliação médica inicial
• Entrevista com psicólogo
• Plano de tratamento personalizado
• Documentação necessária

🏥 **Durante a Internação:**
• Acompanhamento 24h por equipe especializada
• Atividades terapêuticas diárias
• Consultas médicas regulares
• Suporte familiar
• Atividades recreativas

📍 **Tipos de Internação:**
• Voluntária (com consentimento)
• Involuntária (solicitação familiar)
• Compulsória (determinação judicial)

Para mais detalhes, ligue: (11) 99999-9999"""
        
        elif self.contains_keywords(user_message, convenio_keywords):
            return """💰 **Informações sobre Convênios e Valores:**
            
🏥 **Convênios Aceitos:**
• Unimed
• Bradesco Saúde
• SulAmérica
• Amil
• Golden Cross
• Outros convênios médicos

💳 **Formas de Pagamento:**
• Convênio médico
• Particular
• Parcelamento facilitado
• Cartão de crédito/débito

📋 **Para Verificar:**
• Cobertura do seu plano
• Valores atualizados
• Documentação necessária
• Autorização do convênio

Ligue para verificar: (11) 99999-9999"""
        
        elif self.contains_keywords(user_message, emergencia_keywords):
            return """🚨 **ATENDIMENTO DE EMERGÊNCIA 24H** 🚨
            
⚠️ **Se você ou alguém próximo está em crise:**
            
📞 **LIGUE IMEDIATAMENTE:**
• Clínica: (11) 99999-9999
• SAMU: 192
• Bombeiros: 193
• CVV: 188 (prevenção suicídio)

🏥 **Nossos Serviços de Emergência:**
• Atendimento 24h disponível
• Equipe especializada em crises
• Internação de urgência
• Suporte imediato para famílias
• Remoção especializada

💙 **Não hesite em buscar ajuda!**
Estamos aqui para apoiar você neste momento difícil."""
        
        elif self.contains_keywords(user_message, contato_keywords):
            return """📞 **INFORMAÇÕES DE CONTATO DA CLÍNICA:**
            
🏥 **Nossa Clínica de Reabilitação**

📱 **Telefone Principal:**
• (11) 99999-9999

🕐 **Horários de Atendimento:**
• Segunda a Sexta: 8h às 18h
• Sábados: 8h às 12h
• Emergências: 24h por dia

📋 **Nosso atendimento oferece:**
• Informações sobre tratamentos
• Agendamento de avaliações
• Orientação para famílias
• Suporte em crises
• Esclarecimentos sobre convênios

💬 **Você também pode:**
• Continuar conversando aqui comigo
• Fazer perguntas sobre nossos serviços
• Solicitar informações específicas

📞 **Ligue agora: (11) 99999-9999**
Estamos prontos para ajudar você!"""
        
        else:
            return """👋 **Olá! Sou o assistente virtual da Clínica Espaço Vida.**
            
🏥 **Posso ajudar com informações sobre:**
• Tratamentos disponíveis
• Processo de internação
• Convênios e valores
• Atendimento de emergência
• Tipos de dependência
• Suporte familiar

💬 **Exemplos do que você pode perguntar:**
• "Como funciona o tratamento?"
• "Quais convênios vocês aceitam?"
• "Preciso de ajuda urgente"
• "Como internar alguém?"

📞 **Para atendimento personalizado:**
Ligue: (11) 99999-9999

❓ **Como posso ajudar você hoje?**"""
    
    def get_response(self, user_message, conversation_id=None, language='pt'):
        """
        Método principal que tenta diferentes provedores de IA
        """
        # Análise de sentimentos
        sentiment_result = sentiment_analyzer.analyze_sentiment(user_message)
        
        # Detectar urgência e criar ticket se necessário
        self.detect_urgency_and_create_ticket(user_message, conversation_id, sentiment_result)
        
        # Adiciona mensagem do usuário ao histórico
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "sentiment": sentiment_result
        })
        
        response = None
        
        # Obter prompt do sistema no idioma correto
        system_prompt = multilingual.get_system_prompt(language) if language != 'pt' else self.system_prompt
        
        # Verifica se é uma pergunta sobre tratamentos que precisa de IA
        tratamento_keywords = [
            'tratamento', 'terapia', 'ajuda', 'tratar', 'curar', 'cura', 'recuperacao', 'recuperação',
            'reabilitacao', 'reabilitação', 'dependencia', 'dependência', 'vicio', 'vício',
            'drogas', 'alcool', 'álcool', 'medicamento', 'remedio', 'remédio', 'psicologia',
            'psiquiatria', 'medico', 'médico', 'doutor', 'doutora', 'terapeuta',
            '12 passos', 'doze passos', 'programa', 'como funciona', 'funciona', 'funcionamento',
            'desintoxicacao', 'desintoxicação', 'tcc', 'cognitivo', 'comportamental',
            'individual', 'grupo', 'familiar', 'atividades', 'psiquiatrico', 'psiquiátrico',
            'apoio', 'grupos', 'mais sobre', 'fale mais', 'explique', 'detalhe', 'detalhes'
        ]
        
        dependencia_keywords = [
            'dependente', 'viciado', 'adicto', 'usuario', 'usuário', 'consumidor',
            'crack', 'cocaina', 'cocaína', 'maconha', 'cannabis', 'heroina', 'heroína',
            'ecstasy', 'lsd', 'anfetamina', 'metanfetamina', 'opioides', 'morfina',
            'codeina', 'codeína', 'tramadol', 'rivotril', 'clonazepam', 'alprazolam'
        ]
        
        is_treatment_question = self.contains_keywords(user_message, tratamento_keywords + dependencia_keywords)
        
        # Para perguntas sobre tratamentos, sempre tenta usar IA primeiro
        if is_treatment_question or AI_PROVIDER != 'fallback':
            # Tenta OpenAI primeiro (se configurado)
            if AI_PROVIDER == 'openai' and client:
                response = self.get_response_openai(user_message)
            
            # Se OpenAI falhar, tenta Hugging Face
            if not response:
                response = self.get_response_huggingface(user_message)
            
            # Se Hugging Face falhar, tenta Gemini
            if not response:
                response = self.get_response_gemini(user_message)
        
        # Se todas as IAs falharem, usa resposta de fallback
        if not response:
            response = self.get_response_fallback(user_message)
            
            # Se o fallback retornar None (para tratamentos), usa resposta genérica
            if not response:
                response = """Nossa clínica oferece diversos tratamentos especializados:
            
• Desintoxicação médica supervisionada
• Terapia individual e em grupo
• Programa de 12 Passos
• Terapia Cognitivo-Comportamental (TCC)
• Terapia familiar
• Atividades terapêuticas
• Acompanhamento psiquiátrico
• Grupos de apoio

Tratamos dependência de:
• Álcool e drogas
• Medicamentos
• Jogos e outras compulsões

Para mais informações, entre em contato: (11) 99999-9999"""
        
        # Traduzir resposta se necessário
        if language != 'pt':
            response = multilingual.translate_response(response, language)
        
        # Adiciona resposta ao histórico
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def detect_urgency_and_create_ticket(self, user_message, session_id, sentiment_result=None):
        """Detecta urgência na mensagem e cria ticket automaticamente"""
        try:
            # Palavras-chave de alta prioridade
            high_priority_keywords = [
                'emergência', 'urgente', 'socorro', 'ajuda', 'crise',
                'overdose', 'suicídio', 'morte', 'morrer', 'desespero',
                'não aguento', 'vou me matar', 'acabar com tudo'
            ]
            
            # Palavras-chave de média prioridade
            medium_priority_keywords = [
                'internação', 'internar', 'tratamento', 'dependência',
                'vício', 'drogas', 'álcool', 'bebida', 'cocaína',
                'crack', 'maconha', 'remédio', 'medicamento'
            ]
            
            user_input_lower = user_message.lower()
            priority = 'baixa'
            
            # Verificar prioridade baseada em palavras-chave
            if any(keyword in user_input_lower for keyword in high_priority_keywords):
                priority = 'alta'
            elif any(keyword in user_input_lower for keyword in medium_priority_keywords):
                priority = 'média'
            
            # Ajustar prioridade baseada na análise de sentimentos
            if sentiment_result:
                if sentiment_result.get('polarity', 0) < -0.5 and sentiment_result.get('emergency_keywords'):
                    priority = 'alta'
                elif sentiment_result.get('polarity', 0) < -0.3:
                    if priority == 'baixa':
                        priority = 'média'
            
            # Sincronizar com CRM se configurado
            try:
                lead_data = {
                    'session_id': session_id,
                    'message': user_message,
                    'urgency': priority,
                    'source': 'chatbot',
                    'sentiment': sentiment_result
                }
                crm_result = crm_integration.sync_lead(lead_data)
                if crm_result.get('success'):
                    print(f"Lead sincronizado com CRM: {crm_result}")
            except Exception as e:
                print(f"Erro ao sincronizar com CRM: {e}")
                        
        except Exception as e:
            print(f"Erro ao detectar urgência e criar ticket: {e}")
    
    def save_conversation(self, conversation_id):
        """Salva a conversa em arquivo para análise posterior"""
        try:
            filename = f"conversations/conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("conversations", exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.conversation_history
                }, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erro ao salvar conversa: {e}")

# Instância global do chatbot e serviços
chatbot = ClinicaChatbot()
db_manager = DatabaseManager()
email_service = EmailService()
backup_service = BackupService(db_manager, email_service)

# Iniciar serviço de backup automático
backup_service.schedule_automatic_backups()
backup_service.run_scheduler()

@app.route('/')
def index():
    # Gera ID único para a conversa
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Garantir que o request seja tratado como UTF-8
        if request.content_type and 'charset' not in request.content_type:
            request.charset = 'utf-8'
        
        data = request.get_json(force=True)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        conversation_id = session.get('conversation_id')
        
        # Obtém resposta do chatbot
        bot_response = chatbot.get_response(user_message, conversation_id)
        
        # Salva a conversa no banco de dados
        try:
            user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            user_agent = request.headers.get('User-Agent')
            db_manager.save_conversation(session_id or conversation_id, user_message, bot_response, user_ip, user_agent)
        except Exception as e:
            print(f"Erro ao salvar conversa: {e}")
        
        # Criar ticket automaticamente para cada nova conversa (primeira mensagem)
        try:
            # Verifica se já existe um ticket para esta sessão
            existing_tickets = db_manager.get_tickets_by_session(session_id or conversation_id)
            
            if not existing_tickets:
                # Determina a prioridade baseada no conteúdo da mensagem
                priority = 'alta' if any(keyword in user_message.lower() for keyword in ['urgente', 'emergência', 'ajuda imediata', 'socorro']) else 'media'
                
                # Cria o ticket automaticamente
                ticket_id = db_manager.create_ticket(
                    session_id=session_id or conversation_id,
                    title=f"Nova conversa - {user_message[:50]}{'...' if len(user_message) > 50 else ''}",
                    description=f"Primeira mensagem: {user_message}",
                    priority=priority
                )
                
                # Tentar enviar notificação por email (não bloqueia se falhar)
                try:
                    contact_info = f"Session ID: {session_id or conversation_id}\nIP: {user_ip}\nUser Agent: {user_agent}"
                    email_service.send_ticket_notification(ticket_id, f"Nova conversa iniciada", user_message, contact_info)
                except Exception as email_error:
                    print(f"⚠️ Notificação de novo ticket por email falhou: {email_error}")
                
                print(f"✅ Ticket #{ticket_id} criado automaticamente para sessão {session_id or conversation_id}")
                
        except Exception as e:
            print(f"Erro ao criar ticket automático: {e}")
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id or conversation_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Erro no endpoint /chat: {e}")
        return jsonify({
            'error': 'Erro interno do servidor',
            'response': 'Desculpe, ocorreu um erro. Tente novamente ou entre em contato conosco.'
        }), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reinicia a conversa"""
    try:
        # Salva conversa atual antes de resetar
        conversation_id = session.get('conversation_id')
        if conversation_id and chatbot.conversation_history:
            chatbot.save_conversation(conversation_id)
        
        # Reseta o histórico
        chatbot.conversation_history = []
        
        # Gera novo ID de conversa
        session['conversation_id'] = str(uuid.uuid4())
        
        return jsonify({'status': 'success', 'message': 'Conversa reiniciada'})
        
    except Exception as e:
        print(f"Erro ao resetar conversa: {e}")
        return jsonify({'error': 'Erro ao resetar conversa'}), 500

@app.route('/health')
def health_check():
    """Endpoint para verificar se a aplicação está funcionando"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Chatbot Clínica Espaço Vida'
    })

# ROTAS DO DASHBOARD ADMINISTRATIVO

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Dashboard administrativo"""
    try:
        statistics = db_manager.get_statistics()
        tickets = db_manager.get_tickets(limit=10)
        conversations = db_manager.get_conversations(limit=10)
        
        return render_template('admin.html', 
                             statistics=statistics, 
                             tickets=tickets, 
                             conversations=conversations)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return f"Erro ao carregar dashboard: {str(e)}", 500

@app.route('/admin/statistics')
def admin_statistics():
    """API para estatísticas em tempo real"""
    try:
        statistics = db_manager.get_statistics()
        return jsonify(statistics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/create_ticket', methods=['POST'])
def admin_create_ticket():
    """Criar novo ticket via dashboard"""
    try:
        data = request.get_json()
        
        ticket_id = db_manager.create_ticket(
            session_id=f"admin_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=data.get('title'),
            description=data.get('description'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email'),
            priority=data.get('priority', 'media')
        )
        
        # Tentar enviar notificação por email (não bloqueia se falhar)
        try:
            contact_info = f"Nome: {data.get('contact_name', 'N/A')}\nTelefone: {data.get('contact_phone', 'N/A')}\nEmail: {data.get('contact_email', 'N/A')}"
            email_service.send_ticket_notification(ticket_id, data.get('title'), data.get('description'), contact_info)
        except Exception as e:
            print(f"⚠️ Notificação por email falhou: {e}")
        
        return jsonify({'success': True, 'ticket_id': ticket_id})
        
    except Exception as e:
        print(f"Erro ao criar ticket: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/update_ticket', methods=['POST'])
def admin_update_ticket():
    """Atualizar status do ticket"""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        status = data.get('status')
        notes = data.get('notes')
        
        db_manager.update_ticket_status(ticket_id, status, notes)
        
        # Tentar enviar notificação de atualização (não bloqueia se falhar)
        try:
            email_service.send_ticket_update_notification(ticket_id, status, notes)
        except Exception as e:
            print(f"⚠️ Notificação de atualização por email falhou: {e}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Erro ao atualizar ticket: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/ticket_details/<int:ticket_id>')
def admin_ticket_details(ticket_id):
    """Visualizar detalhes completos de um ticket"""
    try:
        ticket_details = db_manager.get_ticket_details(ticket_id)
        
        if not ticket_details:
            return jsonify({'error': 'Ticket não encontrado'}), 404
        
        return jsonify(ticket_details)
        
    except Exception as e:
        print(f"Erro ao buscar detalhes do ticket: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/backup', methods=['POST'])
def admin_create_backup():
    """Criar backup manual"""
    try:
        backup_path = backup_service.create_backup(include_files=True)
        if backup_path:
            return jsonify({'success': True, 'backup_path': backup_path})
        else:
            return jsonify({'error': 'Falha ao criar backup'}), 500
            
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/send_report', methods=['POST'])
def admin_send_report():
    """Enviar relatório diário por email"""
    try:
        statistics = db_manager.get_statistics()
        
        # Tentar enviar relatório (não falha se email não estiver configurado)
        try:
            success = email_service.send_daily_report(statistics)
            if success:
                return jsonify({'success': True, 'message': 'Relatório enviado por email com sucesso!'})
            else:
                return jsonify({'success': False, 'message': 'Email não configurado. Configure as credenciais SMTP no arquivo .env'})
        except Exception as email_error:
            print(f"⚠️ Erro ao enviar email: {email_error}")
            return jsonify({'success': False, 'message': 'Erro no envio de email. Verifique as configurações SMTP.'})
            
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/export_conversations')
def admin_export_conversations():
    """Exportar conversas para CSV"""
    try:
        conversations = db_manager.get_conversations(limit=10000)
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'ID', 'Session ID', 'Mensagem do Usuário', 'Resposta do Bot', 
            'Data/Hora', 'IP do Usuário', 'User Agent'
        ])
        
        # Dados
        for conv in conversations:
            writer.writerow(conv)
        
        # Preparar resposta
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'conversas_export_{timestamp}.csv'
        
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erro ao exportar conversas: {e}")
        return f"Erro ao exportar: {str(e)}", 500

@app.route('/admin/tickets')
def admin_tickets():
    """API para listar tickets"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        tickets = db_manager.get_tickets(status=status, limit=limit)
        
        return jsonify({
            'tickets': tickets,
            'total': len(tickets)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/conversations')
def admin_conversations():
    """API para listar conversas"""
    try:
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 100))
        
        conversations = db_manager.get_conversations(session_id=session_id, limit=limit)
        
        return jsonify({
            'conversations': conversations,
            'total': len(conversations)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Rotas para integração com WhatsApp
@app.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Webhook para integração com WhatsApp via Twilio"""
    if request.method == 'GET':
        # Verificação do webhook
        return request.args.get('hub.challenge', '')
    
    try:
        return whatsapp_integration.handle_webhook(request)
    except Exception as e:
        logging.error(f"Erro no webhook WhatsApp: {e}")
        return '', 500

# Rotas para integração com Telegram
@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Webhook para integração com Telegram"""
    try:
        return telegram_integration.handle_webhook(request)
    except Exception as e:
        logging.error(f"Erro no webhook Telegram: {e}")
        return '', 500

# Rotas para configuração de integrações
@app.route('/admin/integrations')
@login_required
@admin_required
def admin_integrations():
    """Página de configuração de integrações"""
    return render_template('admin_integrations.html')

@app.route('/admin/integrations/whatsapp/config', methods=['GET', 'POST'])
@login_required
@admin_required
def whatsapp_config():
    """Configuração do WhatsApp"""
    if request.method == 'POST':
        config = request.json
        result = whatsapp_integration.configure(config)
        return jsonify(result)
    
    return jsonify(whatsapp_integration.get_config())

@app.route('/admin/integrations/telegram/config', methods=['GET', 'POST'])
@login_required
@admin_required
def telegram_config():
    """Configuração do Telegram"""
    if request.method == 'POST':
        config = request.json
        result = telegram_integration.configure(config)
        return jsonify(result)
    
    return jsonify(telegram_integration.get_config())

@app.route('/admin/integrations/website/widget')
@login_required
@admin_required
def website_widget():
    """Gera código do widget para website"""
    config = request.args.to_dict()
    widget_code = website_integration.generate_widget_code(config)
    return jsonify({
        'success': True,
        'widget_code': widget_code,
        'instructions': website_integration.get_integration_instructions()
    })

# Rotas para CRM
@app.route('/admin/crm/config')
@login_required
@admin_required
def crm_config():
    """Configuração de CRM"""
    available_crms = crm_integration.get_available_crms()
    return jsonify(available_crms)

@app.route('/admin/crm/sync_lead', methods=['POST'])
@login_required
@admin_required
def sync_lead_to_crm():
    """Sincroniza lead específico com CRM"""
    data = request.json
    crm_type = data.get('crm_type', 'hubspot')
    lead_data = data.get('lead_data', {})
    
    result = crm_integration.sync_lead(lead_data, crm_type)
    return jsonify(result)

@app.route('/admin/crm/sync_conversation', methods=['POST'])
@login_required
@admin_required
def sync_conversation_to_crm():
    """Sincroniza conversa com CRM"""
    data = request.json
    session_id = data.get('session_id')
    crm_type = data.get('crm_type', 'hubspot')
    
    result = crm_integration.sync_conversation(session_id, crm_type)
    return jsonify(result)

# Rotas para análise de sentimentos
@app.route('/admin/sentiment/analyze', methods=['POST'])
@login_required
@admin_required
def analyze_sentiment():
    """Analisa sentimento de uma mensagem"""
    data = request.json
    message = data.get('message', '')
    
    result = sentiment_analyzer.analyze_sentiment(message)
    return jsonify(result)

@app.route('/admin/sentiment/conversation/<session_id>')
@login_required
@admin_required
def analyze_conversation_sentiment(session_id):
    """Analisa sentimento de uma conversa completa"""
    conversations = db_manager.get_conversations(session_id)
    
    if not conversations:
        return jsonify({'error': 'Conversa não encontrada'}), 404
    
    messages = [conv[2] for conv in conversations if conv[2]]  # user messages
    result = sentiment_analyzer.analyze_conversation_trend(messages)
    
    return jsonify(result)

# Rotas para suporte multilíngue
@app.route('/admin/languages')
@login_required
@admin_required
def get_languages():
    """Lista idiomas suportados"""
    languages = multilingual.get_supported_languages()
    return jsonify(languages)

@app.route('/admin/languages/translate', methods=['POST'])
@login_required
@admin_required
def translate_text():
    """Traduz texto para idioma específico"""
    data = request.json
    text = data.get('text', '')
    target_language = data.get('language', 'en')
    
    result = multilingual.translate_response(text, target_language)
    return jsonify({'translated_text': result})

@app.route('/admin/languages/stats')
@login_required
@admin_required
def language_stats():
    """Estatísticas de uso de idiomas"""
    stats = multilingual.get_language_usage_stats()
    return jsonify(stats)

# Rota para chat com suporte a idiomas
@app.route('/chat/<language>', methods=['POST'])
def chat_multilingual(language):
    """Chat com suporte a múltiplos idiomas"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Mensagem não fornecida'}), 400
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Detectar idioma se não especificado
        if language == 'auto':
            language = multilingual.detect_language(user_message)
        
        # Gerar resposta no idioma correto
        chatbot_instance = ClinicaChatbot()
        bot_response = chatbot_instance.get_response(user_message, session_id, language)
        
        # Salvar conversa
        db_manager.save_conversation(
            session_id=session_id,
            user_message=user_message,
            bot_response=bot_response,
            language=language
        )
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id,
            'language': language
        })
        
    except Exception as e:
        logging.error(f"Erro no chat multilíngue: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    print("🏥 Iniciando Chatbot da Clínica Espaço Vida...")
    print("📱 Acesse: http://localhost:5000")
    print("⚠️  Certifique-se de configurar sua OPENAI_API_KEY")
    
    app.run(debug=True, host='0.0.0.0', port=5000)