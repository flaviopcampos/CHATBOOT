from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from functools import wraps
import jwt
import datetime
from database import DatabaseManager
from sentiment_analysis import SentimentAnalyzer
from multilingual import MultilingualSupport
from crm_integration import CRMIntegration
import os

# Blueprint para API REST
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_bp)

# Configuração JWT
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = 'HS256'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'message': 'Token é obrigatório'}, 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return {'message': 'Token expirado'}, 401
        except jwt.InvalidTokenError:
            return {'message': 'Token inválido'}, 401
        
        return f(*args, **kwargs)
    return decorated

class AuthAPI(Resource):
    def post(self):
        """Autenticação e geração de token JWT"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return {'message': 'Username e password são obrigatórios'}, 400
        
        db = DatabaseManager()
        user = db.authenticate_user(username, password)
        
        if user:
            token = jwt.encode({
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)
            
            return {
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
            }, 200
        
        return {'message': 'Credenciais inválidas'}, 401

class ConversationsAPI(Resource):
    @token_required
    def get(self):
        """Listar conversas"""
        db = DatabaseManager()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        conversations = db.get_conversations_paginated(page, per_page)
        return {
            'conversations': conversations,
            'page': page,
            'per_page': per_page
        }, 200
    
    @token_required
    def post(self):
        """Criar nova conversa"""
        data = request.get_json()
        message = data.get('message')
        user_id = data.get('user_id', 'api_user')
        
        if not message:
            return {'message': 'Mensagem é obrigatória'}, 400
        
        # Processar mensagem com chatbot
        from app import ClinicaChatbot
        chatbot = ClinicaChatbot()
        response = chatbot.get_response(message, user_id)
        
        return {
            'user_message': message,
            'bot_response': response['response'],
            'sentiment': response.get('sentiment'),
            'language': response.get('language'),
            'urgency': response.get('urgency')
        }, 201

class TicketsAPI(Resource):
    @token_required
    def get(self):
        """Listar tickets"""
        db = DatabaseManager()
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        tickets = db.get_tickets_filtered(status, priority)
        return {'tickets': tickets}, 200
    
    @token_required
    def post(self):
        """Criar novo ticket"""
        data = request.get_json()
        required_fields = ['title', 'description', 'contact_info']
        
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field} é obrigatório'}, 400
        
        db = DatabaseManager()
        ticket_id = db.create_ticket(
            data['title'],
            data['description'],
            data['contact_info'],
            data.get('priority', 'medium'),
            data.get('category', 'general')
        )
        
        return {'ticket_id': ticket_id, 'message': 'Ticket criado com sucesso'}, 201

class SentimentAPI(Resource):
    @token_required
    def post(self):
        """Analisar sentimento de texto"""
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return {'message': 'Texto é obrigatório'}, 400
        
        analyzer = SentimentAnalyzer()
        sentiment = analyzer.analyze_sentiment(text)
        
        return {'sentiment': sentiment}, 200

class TranslationAPI(Resource):
    @token_required
    def post(self):
        """Traduzir texto"""
        data = request.get_json()
        text = data.get('text')
        target_language = data.get('target_language', 'pt')
        
        if not text:
            return {'message': 'Texto é obrigatório'}, 400
        
        multilingual = MultilingualSupport()
        translated = multilingual.translate_response(text, target_language)
        
        return {
            'original_text': text,
            'translated_text': translated,
            'target_language': target_language
        }, 200

class CRMSyncAPI(Resource):
    @token_required
    def post(self):
        """Sincronizar lead com CRM"""
        data = request.get_json()
        required_fields = ['name', 'email', 'phone']
        
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field} é obrigatório'}, 400
        
        crm = CRMIntegration()
        result = crm.sync_lead({
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'source': data.get('source', 'API'),
            'notes': data.get('notes', '')
        })
        
        if result['success']:
            return {'message': 'Lead sincronizado com sucesso', 'crm_id': result.get('crm_id')}, 200
        else:
            return {'message': 'Erro ao sincronizar lead', 'error': result.get('error')}, 500

class StatsAPI(Resource):
    @token_required
    def get(self):
        """Estatísticas do sistema"""
        db = DatabaseManager()
        
        stats = {
            'total_conversations': db.get_total_conversations(),
            'total_tickets': db.get_total_tickets(),
            'open_tickets': db.get_open_tickets_count(),
            'conversations_today': db.get_conversations_today(),
            'sentiment_distribution': db.get_sentiment_distribution(),
            'language_usage': db.get_language_usage_stats()
        }
        
        return {'stats': stats}, 200

# Registrar recursos da API
api.add_resource(AuthAPI, '/auth')
api.add_resource(ConversationsAPI, '/conversations')
api.add_resource(TicketsAPI, '/tickets')
api.add_resource(SentimentAPI, '/sentiment')
api.add_resource(TranslationAPI, '/translate')
api.add_resource(CRMSyncAPI, '/crm/sync')
api.add_resource(StatsAPI, '/stats')

def init_api(app):
    """Inicializar API REST no app Flask"""
    app.register_blueprint(api_bp)
    return app