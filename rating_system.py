from flask import Blueprint, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta
from database import DatabaseManager
from email_service import EmailService
import json
import statistics

# Blueprint para sistema de avaliação
rating_bp = Blueprint('rating', __name__, url_prefix='/rating')

class RatingSystem:
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.setup_database()
    
    def setup_database(self):
        """Configurar tabelas para sistema de avaliação"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de avaliações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    user_name TEXT,
                    user_email TEXT,
                    user_phone TEXT,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    feedback_text TEXT,
                    service_quality INTEGER CHECK (service_quality >= 1 AND service_quality <= 5),
                    response_time INTEGER CHECK (response_time >= 1 AND response_time <= 5),
                    problem_resolution INTEGER CHECK (problem_resolution >= 1 AND problem_resolution <= 5),
                    recommendation INTEGER CHECK (recommendation >= 1 AND recommendation <= 5),
                    category TEXT DEFAULT 'general',
                    agent_name TEXT,
                    department TEXT,
                    rating_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    follow_up_required INTEGER DEFAULT 0,
                    follow_up_date TIMESTAMP,
                    follow_up_notes TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de perguntas de avaliação customizadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rating_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    question_type TEXT NOT NULL DEFAULT 'rating',
                    options TEXT,
                    is_required INTEGER DEFAULT 1,
                    order_index INTEGER DEFAULT 0,
                    category TEXT DEFAULT 'general',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de respostas customizadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rating_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rating_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    response_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rating_id) REFERENCES ratings (id),
                    FOREIGN KEY (question_id) REFERENCES rating_questions (id)
                )
            ''')
            
            # Tabela de métricas de satisfação
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS satisfaction_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_date DATE NOT NULL,
                    total_ratings INTEGER DEFAULT 0,
                    average_rating REAL DEFAULT 0,
                    nps_score REAL DEFAULT 0,
                    csat_score REAL DEFAULT 0,
                    ratings_1_star INTEGER DEFAULT 0,
                    ratings_2_star INTEGER DEFAULT 0,
                    ratings_3_star INTEGER DEFAULT 0,
                    ratings_4_star INTEGER DEFAULT 0,
                    ratings_5_star INTEGER DEFAULT 0,
                    department TEXT,
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(metric_date, department, agent_name)
                )
            ''')
            
            # Tabela de alertas de qualidade
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    title TEXT NOT NULL,
                    description TEXT,
                    related_rating_id INTEGER,
                    department TEXT,
                    agent_name TEXT,
                    is_resolved INTEGER DEFAULT 0,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (related_rating_id) REFERENCES ratings (id)
                )
            ''')
            
            # Inserir perguntas padrão se não existirem
            cursor.execute('SELECT COUNT(*) FROM rating_questions')
            if cursor.fetchone()[0] == 0:
                default_questions = [
                    ('Como você avalia a qualidade do atendimento?', 'rating', None, 1, 1, 'service'),
                    ('O tempo de resposta foi satisfatório?', 'rating', None, 1, 2, 'response'),
                    ('Seu problema foi resolvido adequadamente?', 'rating', None, 1, 3, 'resolution'),
                    ('Você recomendaria nossos serviços?', 'rating', None, 1, 4, 'recommendation'),
                    ('Deixe um comentário sobre sua experiência:', 'text', None, 0, 5, 'feedback'),
                    ('Qual aspecto mais te impressionou?', 'multiple_choice', 
                     json.dumps(['Rapidez', 'Cordialidade', 'Conhecimento técnico', 'Resolução eficaz', 'Outro']), 
                     0, 6, 'highlights'),
                    ('Como nos conheceu?', 'multiple_choice',
                     json.dumps(['Google', 'Redes sociais', 'Indicação', 'Site', 'WhatsApp', 'Outro']),
                     0, 7, 'source')
                ]
                
                cursor.executemany('''
                    INSERT INTO rating_questions 
                    (question_text, question_type, options, is_required, order_index, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', default_questions)
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao configurar banco de dados de avaliações: {e}")
        finally:
            if conn:
                conn.close()
    
    def create_rating(self, rating_data):
        """Criar nova avaliação"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Inserir avaliação principal
            cursor.execute('''
                INSERT INTO ratings (
                    conversation_id, user_name, user_email, user_phone, rating,
                    feedback_text, service_quality, response_time, problem_resolution,
                    recommendation, category, agent_name, department
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rating_data.get('conversation_id'),
                rating_data.get('user_name'),
                rating_data.get('user_email'),
                rating_data.get('user_phone'),
                rating_data.get('rating'),
                rating_data.get('feedback_text'),
                rating_data.get('service_quality'),
                rating_data.get('response_time'),
                rating_data.get('problem_resolution'),
                rating_data.get('recommendation'),
                rating_data.get('category', 'general'),
                rating_data.get('agent_name'),
                rating_data.get('department')
            ))
            
            rating_id = cursor.lastrowid
            
            # Inserir respostas customizadas se houver
            if 'custom_responses' in rating_data:
                for response in rating_data['custom_responses']:
                    cursor.execute('''
                        INSERT INTO rating_responses (rating_id, question_id, response_value)
                        VALUES (?, ?, ?)
                    ''', (rating_id, response['question_id'], response['value']))
            
            conn.commit()
            
            # Verificar se precisa de follow-up
            if rating_data.get('rating', 5) <= 2:
                self.create_quality_alert(rating_id, 'low_rating', rating_data)
            
            # Atualizar métricas
            self.update_satisfaction_metrics(rating_data.get('department'), rating_data.get('agent_name'))
            
            # Enviar notificação por email se necessário
            if rating_data.get('rating', 5) <= 2:
                self.send_low_rating_notification(rating_id, rating_data)
            
            return rating_id
            
        except Exception as e:
            print(f"Erro ao criar avaliação: {e}")
            return None
        finally:
            conn.close()
    
    def get_rating_form_questions(self, category='general'):
        """Obter perguntas do formulário de avaliação"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, question_text, question_type, options, is_required, order_index, category
                FROM rating_questions
                WHERE (category = ? OR category = 'general') AND is_active = 1
                ORDER BY order_index
            ''', (category,))
            
            questions = []
            for row in cursor.fetchall():
                question = {
                    'id': row[0],
                    'text': row[1],
                    'type': row[2],
                    'options': json.loads(row[3]) if row[3] else None,
                    'required': bool(row[4]),
                    'order': row[5],
                    'category': row[6]
                }
                questions.append(question)
            
            return questions
            
        except Exception as e:
            print(f"Erro ao obter perguntas: {e}")
            return []
        finally:
            conn.close()
    
    def get_ratings_analytics(self, start_date=None, end_date=None, department=None, agent=None):
        """Obter analytics das avaliações"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Construir query base
            where_conditions = ['status = "active"']
            params = []
            
            if start_date:
                where_conditions.append('DATE(rating_date) >= ?')
                params.append(start_date)
            
            if end_date:
                where_conditions.append('DATE(rating_date) <= ?')
                params.append(end_date)
            
            if department:
                where_conditions.append('department = ?')
                params.append(department)
            
            if agent:
                where_conditions.append('agent_name = ?')
                params.append(agent)
            
            where_clause = ' AND '.join(where_conditions)
            
            # Métricas gerais
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total_ratings,
                    AVG(rating) as avg_rating,
                    AVG(service_quality) as avg_service,
                    AVG(response_time) as avg_response,
                    AVG(problem_resolution) as avg_resolution,
                    AVG(recommendation) as avg_recommendation
                FROM ratings
                WHERE {where_clause}
            ''', params)
            
            general_metrics = cursor.fetchone()
            
            # Distribuição de ratings
            cursor.execute(f'''
                SELECT rating, COUNT(*) as count
                FROM ratings
                WHERE {where_clause}
                GROUP BY rating
                ORDER BY rating
            ''', params)
            
            rating_distribution = {str(i): 0 for i in range(1, 6)}
            for row in cursor.fetchall():
                rating_distribution[str(row[0])] = row[1]
            
            # Ratings por dia
            cursor.execute(f'''
                SELECT DATE(rating_date) as date, COUNT(*) as count, AVG(rating) as avg_rating
                FROM ratings
                WHERE {where_clause}
                GROUP BY DATE(rating_date)
                ORDER BY date DESC
                LIMIT 30
            ''', params)
            
            ratings_by_day = []
            for row in cursor.fetchall():
                ratings_by_day.append({
                    'date': row[0],
                    'count': row[1],
                    'avg_rating': round(row[2], 2) if row[2] else 0
                })
            
            # Calcular NPS (Net Promoter Score)
            cursor.execute(f'''
                SELECT recommendation, COUNT(*) as count
                FROM ratings
                WHERE {where_clause} AND recommendation IS NOT NULL
                GROUP BY recommendation
            ''', params)
            
            nps_data = {i: 0 for i in range(1, 6)}
            total_nps_responses = 0
            
            for row in cursor.fetchall():
                nps_data[row[0]] = row[1]
                total_nps_responses += row[1]
            
            if total_nps_responses > 0:
                promoters = nps_data[5] + nps_data[4]  # 4-5 são promotores
                detractors = nps_data[1] + nps_data[2]  # 1-2 são detratores
                nps_score = ((promoters - detractors) / total_nps_responses) * 100
            else:
                nps_score = 0
            
            # CSAT (Customer Satisfaction Score) - % de ratings 4-5
            if general_metrics[0] > 0:
                satisfied_count = rating_distribution['4'] + rating_distribution['5']
                csat_score = (satisfied_count / general_metrics[0]) * 100
            else:
                csat_score = 0
            
            # Top feedbacks positivos e negativos
            cursor.execute(f'''
                SELECT feedback_text, rating, user_name, rating_date
                FROM ratings
                WHERE {where_clause} AND feedback_text IS NOT NULL AND feedback_text != ""
                ORDER BY rating DESC, rating_date DESC
                LIMIT 10
            ''', params)
            
            positive_feedback = []
            negative_feedback = []
            
            for row in cursor.fetchall():
                feedback_item = {
                    'text': row[0],
                    'rating': row[1],
                    'user': row[2],
                    'date': row[3]
                }
                
                if row[1] >= 4:
                    positive_feedback.append(feedback_item)
                elif row[1] <= 2:
                    negative_feedback.append(feedback_item)
            
            return {
                'total_ratings': general_metrics[0] or 0,
                'average_rating': round(general_metrics[1], 2) if general_metrics[1] else 0,
                'average_service': round(general_metrics[2], 2) if general_metrics[2] else 0,
                'average_response': round(general_metrics[3], 2) if general_metrics[3] else 0,
                'average_resolution': round(general_metrics[4], 2) if general_metrics[4] else 0,
                'average_recommendation': round(general_metrics[5], 2) if general_metrics[5] else 0,
                'rating_distribution': rating_distribution,
                'ratings_by_day': ratings_by_day,
                'nps_score': round(nps_score, 2),
                'csat_score': round(csat_score, 2),
                'positive_feedback': positive_feedback[:5],
                'negative_feedback': negative_feedback[:5]
            }
            
        except Exception as e:
            print(f"Erro ao obter analytics: {e}")
            return {}
        finally:
            conn.close()
    
    def create_quality_alert(self, rating_id, alert_type, rating_data):
        """Criar alerta de qualidade"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if alert_type == 'low_rating':
                title = f"Avaliação baixa recebida ({rating_data.get('rating')}/5)"
                description = f"Cliente {rating_data.get('user_name', 'Anônimo')} deu nota {rating_data.get('rating')}/5"
                severity = 'high' if rating_data.get('rating', 5) <= 1 else 'medium'
            
            cursor.execute('''
                INSERT INTO quality_alerts (
                    alert_type, severity, title, description, related_rating_id,
                    department, agent_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_type, severity, title, description, rating_id,
                rating_data.get('department'), rating_data.get('agent_name')
            ))
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            print(f"Erro ao criar alerta: {e}")
            return None
        finally:
            conn.close()
    
    def update_satisfaction_metrics(self, department=None, agent_name=None):
        """Atualizar métricas de satisfação diárias"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            # Calcular métricas do dia
            where_conditions = ['DATE(rating_date) = ?']
            params = [today]
            
            if department:
                where_conditions.append('department = ?')
                params.append(department)
            
            if agent_name:
                where_conditions.append('agent_name = ?')
                params.append(agent_name)
            
            where_clause = ' AND '.join(where_conditions)
            
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    AVG(rating) as avg_rating,
                    AVG(recommendation) as avg_recommendation,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as r1,
                    SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as r2,
                    SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as r3,
                    SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as r4,
                    SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as r5
                FROM ratings
                WHERE {where_clause}
            ''', params)
            
            metrics = cursor.fetchone()
            
            if metrics[0] > 0:  # Se há avaliações hoje
                # Calcular NPS
                promoters = metrics[7] + metrics[6]  # 4-5 estrelas
                detractors = metrics[3] + metrics[4]  # 1-2 estrelas
                nps_score = ((promoters - detractors) / metrics[0]) * 100 if metrics[0] > 0 else 0
                
                # Calcular CSAT
                satisfied = metrics[6] + metrics[7]  # 4-5 estrelas
                csat_score = (satisfied / metrics[0]) * 100 if metrics[0] > 0 else 0
                
                # Inserir ou atualizar métricas
                cursor.execute('''
                    INSERT OR REPLACE INTO satisfaction_metrics (
                        metric_date, total_ratings, average_rating, nps_score, csat_score,
                        ratings_1_star, ratings_2_star, ratings_3_star, ratings_4_star, ratings_5_star,
                        department, agent_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    today, metrics[0], metrics[1], nps_score, csat_score,
                    metrics[3], metrics[4], metrics[5], metrics[6], metrics[7],
                    department, agent_name
                ))
                
                conn.commit()
            
        except Exception as e:
            print(f"Erro ao atualizar métricas: {e}")
        finally:
            conn.close()
    
    def send_low_rating_notification(self, rating_id, rating_data):
        """Enviar notificação de avaliação baixa"""
        try:
            subject = f"⚠️ Avaliação Baixa Recebida - {rating_data.get('rating')}/5 estrelas"
            
            body = f"""
            <h2>Alerta de Qualidade - Avaliação Baixa</h2>
            
            <p><strong>Cliente:</strong> {rating_data.get('user_name', 'Não informado')}</p>
            <p><strong>Avaliação:</strong> {rating_data.get('rating')}/5 estrelas</p>
            <p><strong>Departamento:</strong> {rating_data.get('department', 'Não informado')}</p>
            <p><strong>Agente:</strong> {rating_data.get('agent_name', 'Não informado')}</p>
            <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            {f'<p><strong>Feedback:</strong> {rating_data.get("feedback_text", "")}' if rating_data.get('feedback_text') else ''}
            
            <h3>Detalhes da Avaliação:</h3>
            <ul>
                <li>Qualidade do Serviço: {rating_data.get('service_quality', 'N/A')}/5</li>
                <li>Tempo de Resposta: {rating_data.get('response_time', 'N/A')}/5</li>
                <li>Resolução do Problema: {rating_data.get('problem_resolution', 'N/A')}/5</li>
                <li>Recomendação: {rating_data.get('recommendation', 'N/A')}/5</li>
            </ul>
            
            <p><strong>Ação Recomendada:</strong> Entre em contato com o cliente para follow-up e melhoria do atendimento.</p>
            
            <p>Acesse o dashboard de avaliações para mais detalhes: <a href="http://localhost:5000/rating">Dashboard de Avaliações</a></p>
            """
            
            # Enviar para gerência
            self.email_service.send_email(
                to_email="gerencia@clinicaespacovida.com.br",
                subject=subject,
                body=body
            )
            
        except Exception as e:
            print(f"Erro ao enviar notificação: {e}")
    
    def get_quality_alerts(self, resolved=False):
        """Obter alertas de qualidade"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, alert_type, severity, title, description, department,
                       agent_name, created_at, is_resolved, resolved_by, resolved_at
                FROM quality_alerts
                WHERE is_resolved = ?
                ORDER BY created_at DESC
            ''', (1 if resolved else 0,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'id': row[0],
                    'type': row[1],
                    'severity': row[2],
                    'title': row[3],
                    'description': row[4],
                    'department': row[5],
                    'agent_name': row[6],
                    'created_at': row[7],
                    'is_resolved': bool(row[8]),
                    'resolved_by': row[9],
                    'resolved_at': row[10]
                })
            
            return alerts
            
        except Exception as e:
            print(f"Erro ao obter alertas: {e}")
            return []
        finally:
            conn.close()
    
    def resolve_alert(self, alert_id, resolved_by, notes=None):
        """Resolver alerta de qualidade"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE quality_alerts
                SET is_resolved = 1, resolved_by = ?, resolved_at = ?, resolution_notes = ?
                WHERE id = ?
            ''', (resolved_by, datetime.now(), notes, alert_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"Erro ao resolver alerta: {e}")
            return False
        finally:
            conn.close()

# Instância global
rating_system = RatingSystem()

# Rotas da API
@rating_bp.route('/')
def rating_dashboard():
    """Dashboard de avaliações"""
    return render_template('rating_dashboard.html')

@rating_bp.route('/form')
@rating_bp.route('/form/<category>')
def rating_form(category='general'):
    """Formulário de avaliação"""
    questions = rating_system.get_rating_form_questions(category)
    return render_template('rating_form.html', questions=questions, category=category)

@rating_bp.route('/submit', methods=['POST'])
def submit_rating():
    """Submeter avaliação"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Processar respostas customizadas
        custom_responses = []
        for key, value in data.items():
            if key.startswith('question_'):
                question_id = int(key.replace('question_', ''))
                custom_responses.append({
                    'question_id': question_id,
                    'value': value
                })
        
        data['custom_responses'] = custom_responses
        
        rating_id = rating_system.create_rating(data)
        
        if rating_id:
            return jsonify({
                'success': True,
                'rating_id': rating_id,
                'message': 'Avaliação enviada com sucesso! Obrigado pelo seu feedback.'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar avaliação'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rating_bp.route('/analytics')
def get_analytics():
    """Obter analytics das avaliações"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        department = request.args.get('department')
        agent = request.args.get('agent')
        
        analytics = rating_system.get_ratings_analytics(start_date, end_date, department, agent)
        return jsonify({'success': True, 'analytics': analytics})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rating_bp.route('/alerts')
def get_alerts():
    """Obter alertas de qualidade"""
    try:
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        alerts = rating_system.get_quality_alerts(resolved)
        return jsonify({'success': True, 'alerts': alerts})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rating_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolver alerta"""
    try:
        data = request.get_json()
        resolved_by = data.get('resolved_by')
        notes = data.get('notes')
        
        success = rating_system.resolve_alert(alert_id, resolved_by, notes)
        
        if success:
            return jsonify({'success': True, 'message': 'Alerta resolvido com sucesso'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao resolver alerta'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@rating_bp.route('/questions')
def get_questions():
    """Obter perguntas do formulário"""
    try:
        category = request.args.get('category', 'general')
        questions = rating_system.get_rating_form_questions(category)
        return jsonify({'success': True, 'questions': questions})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def init_rating_system(app):
    """Inicializar sistema de avaliação no app Flask"""
    app.register_blueprint(rating_bp)
    return app