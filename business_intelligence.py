from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import json
import sqlite3
from database import DatabaseManager
from collections import defaultdict
import calendar

# Blueprint para Business Intelligence
bi_bp = Blueprint('bi', __name__, url_prefix='/bi')

class BusinessIntelligence:
    def __init__(self):
        self.db = DatabaseManager()
        self.setup_database()
    
    def setup_database(self):
        """Configurar tabelas para BI"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de métricas de performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_date DATE NOT NULL,
                    metric_hour INTEGER,
                    category TEXT,
                    subcategory TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de KPIs (Key Performance Indicators)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kpis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kpi_name TEXT NOT NULL,
                    kpi_value REAL NOT NULL,
                    target_value REAL,
                    period_type TEXT NOT NULL,
                    period_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de relatórios customizados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_name TEXT NOT NULL,
                    report_config TEXT NOT NULL,
                    created_by TEXT,
                    is_public INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao configurar banco de dados do BI: {e}")
        finally:
            if conn:
                conn.close()
    
    def calculate_conversation_metrics(self, start_date=None, end_date=None):
        """Calcular métricas de conversas"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Definir período padrão (últimos 30 dias)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            metrics = {}
            
            # Total de conversas
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE DATE(created_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            metrics['total_conversations'] = cursor.fetchone()[0]
            
            # Conversas por dia
            cursor.execute('''
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM conversations 
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (start_date, end_date))
            metrics['conversations_by_day'] = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Conversas por hora
            cursor.execute('''
                SELECT strftime('%H', created_at) as hour, COUNT(*) as count
                FROM conversations 
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY strftime('%H', created_at)
                ORDER BY hour
            ''', (start_date, end_date))
            metrics['conversations_by_hour'] = [{'hour': int(row[0]), 'count': row[1]} for row in cursor.fetchall()]
            
            # Tempo médio de resposta
            cursor.execute('''
                SELECT AVG(
                    CASE 
                        WHEN response_time IS NOT NULL THEN response_time
                        ELSE 0
                    END
                ) as avg_response_time
                FROM conversations 
                WHERE DATE(created_at) BETWEEN ? AND ?
            ''', (start_date, end_date))
            avg_response = cursor.fetchone()[0]
            metrics['avg_response_time'] = round(avg_response or 0, 2)
            
            # Taxa de satisfação
            cursor.execute('''
                SELECT 
                    AVG(CASE WHEN satisfaction_rating >= 4 THEN 1.0 ELSE 0.0 END) * 100 as satisfaction_rate
                FROM conversations 
                WHERE DATE(created_at) BETWEEN ? AND ? 
                AND satisfaction_rating IS NOT NULL
            ''', (start_date, end_date))
            satisfaction = cursor.fetchone()[0]
            metrics['satisfaction_rate'] = round(satisfaction or 0, 2)
            
            return metrics
            
        except Exception as e:
            print(f"Erro ao calcular métricas de conversas: {e}")
            return {}
        finally:
            conn.close()
    
    def calculate_sentiment_metrics(self, start_date=None, end_date=None):
        """Calcular métricas de sentimento"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            metrics = {}
            
            # Distribuição de sentimentos
            cursor.execute('''
                SELECT sentiment, COUNT(*) as count
                FROM messages 
                WHERE DATE(created_at) BETWEEN ? AND ?
                AND sentiment IS NOT NULL
                GROUP BY sentiment
            ''', (start_date, end_date))
            
            sentiment_distribution = {}
            total_messages = 0
            for row in cursor.fetchall():
                sentiment_distribution[row[0]] = row[1]
                total_messages += row[1]
            
            # Calcular percentuais
            if total_messages > 0:
                for sentiment in sentiment_distribution:
                    sentiment_distribution[sentiment] = {
                        'count': sentiment_distribution[sentiment],
                        'percentage': round((sentiment_distribution[sentiment] / total_messages) * 100, 2)
                    }
            
            metrics['sentiment_distribution'] = sentiment_distribution
            metrics['total_analyzed_messages'] = total_messages
            
            # Evolução do sentimento ao longo do tempo
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    sentiment,
                    COUNT(*) as count
                FROM messages 
                WHERE DATE(created_at) BETWEEN ? AND ?
                AND sentiment IS NOT NULL
                GROUP BY DATE(created_at), sentiment
                ORDER BY date
            ''', (start_date, end_date))
            
            sentiment_evolution = defaultdict(lambda: defaultdict(int))
            for row in cursor.fetchall():
                sentiment_evolution[row[0]][row[1]] = row[2]
            
            metrics['sentiment_evolution'] = dict(sentiment_evolution)
            
            return metrics
            
        except Exception as e:
            print(f"Erro ao calcular métricas de sentimento: {e}")
            return {}
        finally:
            conn.close()
    
    def calculate_appointment_metrics(self, start_date=None, end_date=None):
        """Calcular métricas de agendamentos"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            metrics = {}
            
            # Total de agendamentos
            cursor.execute('''
                SELECT COUNT(*) FROM appointments 
                WHERE appointment_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            metrics['total_appointments'] = cursor.fetchone()[0]
            
            # Agendamentos por status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM appointments 
                WHERE appointment_date BETWEEN ? AND ?
                GROUP BY status
            ''', (start_date, end_date))
            metrics['appointments_by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Taxa de comparecimento
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'no_show' THEN 1 END) as no_show,
                    COUNT(*) as total
                FROM appointments 
                WHERE appointment_date BETWEEN ? AND ?
                AND status IN ('completed', 'no_show')
            ''', (start_date, end_date))
            
            result = cursor.fetchone()
            if result[2] > 0:
                metrics['attendance_rate'] = round((result[0] / result[2]) * 100, 2)
                metrics['no_show_rate'] = round((result[1] / result[2]) * 100, 2)
            else:
                metrics['attendance_rate'] = 0
                metrics['no_show_rate'] = 0
            
            # Agendamentos por tipo de serviço
            cursor.execute('''
                SELECT service_type, COUNT(*) as count
                FROM appointments 
                WHERE appointment_date BETWEEN ? AND ?
                GROUP BY service_type
                ORDER BY count DESC
            ''', (start_date, end_date))
            metrics['appointments_by_service'] = [{'service': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Receita estimada
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN a.status = 'completed' THEN s.price ELSE 0 END) as completed_revenue,
                    SUM(s.price) as total_potential_revenue
                FROM appointments a
                LEFT JOIN service_types s ON a.service_type = s.name
                WHERE a.appointment_date BETWEEN ? AND ?
            ''', (start_date, end_date))
            
            revenue_result = cursor.fetchone()
            metrics['completed_revenue'] = revenue_result[0] or 0
            metrics['potential_revenue'] = revenue_result[1] or 0
            
            return metrics
            
        except Exception as e:
            print(f"Erro ao calcular métricas de agendamentos: {e}")
            return {}
        finally:
            conn.close()
    
    def calculate_multilingual_metrics(self, start_date=None, end_date=None):
        """Calcular métricas multilíngues"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            metrics = {}
            
            # Distribuição de idiomas
            cursor.execute('''
                SELECT language, COUNT(*) as count
                FROM conversations 
                WHERE DATE(created_at) BETWEEN ? AND ?
                AND language IS NOT NULL
                GROUP BY language
                ORDER BY count DESC
            ''', (start_date, end_date))
            metrics['language_distribution'] = [{'language': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            # Traduções realizadas
            cursor.execute('''
                SELECT COUNT(*) FROM messages 
                WHERE DATE(created_at) BETWEEN ? AND ?
                AND translated_text IS NOT NULL
            ''', (start_date, end_date))
            metrics['total_translations'] = cursor.fetchone()[0]
            
            return metrics
            
        except Exception as e:
            print(f"Erro ao calcular métricas multilíngues: {e}")
            return {}
        finally:
            conn.close()
    
    def generate_dashboard_data(self, period='30d'):
        """Gerar dados para dashboard"""
        try:
            # Calcular datas baseado no período
            if period == '7d':
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            elif period == '30d':
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif period == '90d':
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            elif period == '1y':
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            else:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            dashboard_data = {
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'conversations': self.calculate_conversation_metrics(start_date, end_date),
                'sentiment': self.calculate_sentiment_metrics(start_date, end_date),
                'appointments': self.calculate_appointment_metrics(start_date, end_date),
                'multilingual': self.calculate_multilingual_metrics(start_date, end_date),
                'generated_at': datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            print(f"Erro ao gerar dados do dashboard: {e}")
            return {}
    
    def calculate_kpis(self, period='monthly'):
        """Calcular KPIs principais"""
        try:
            kpis = []
            
            # Definir período
            if period == 'daily':
                start_date = datetime.now().strftime('%Y-%m-%d')
                end_date = start_date
            elif period == 'weekly':
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            elif period == 'monthly':
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            else:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Obter métricas
            conversation_metrics = self.calculate_conversation_metrics(start_date, end_date)
            appointment_metrics = self.calculate_appointment_metrics(start_date, end_date)
            sentiment_metrics = self.calculate_sentiment_metrics(start_date, end_date)
            
            # KPI: Total de Conversas
            kpis.append({
                'name': 'Total de Conversas',
                'value': conversation_metrics.get('total_conversations', 0),
                'target': 100,  # Meta configurável
                'unit': 'conversas',
                'trend': 'up',  # Seria calculado comparando com período anterior
                'category': 'engagement'
            })
            
            # KPI: Tempo Médio de Resposta
            kpis.append({
                'name': 'Tempo Médio de Resposta',
                'value': conversation_metrics.get('avg_response_time', 0),
                'target': 30,  # Meta: 30 segundos
                'unit': 'segundos',
                'trend': 'down',  # Menor é melhor
                'category': 'performance'
            })
            
            # KPI: Taxa de Satisfação
            kpis.append({
                'name': 'Taxa de Satisfação',
                'value': conversation_metrics.get('satisfaction_rate', 0),
                'target': 85,  # Meta: 85%
                'unit': '%',
                'trend': 'up',
                'category': 'satisfaction'
            })
            
            # KPI: Taxa de Comparecimento
            kpis.append({
                'name': 'Taxa de Comparecimento',
                'value': appointment_metrics.get('attendance_rate', 0),
                'target': 90,  # Meta: 90%
                'unit': '%',
                'trend': 'up',
                'category': 'appointments'
            })
            
            # KPI: Receita Realizada
            kpis.append({
                'name': 'Receita Realizada',
                'value': appointment_metrics.get('completed_revenue', 0),
                'target': 10000,  # Meta configurável
                'unit': 'R$',
                'trend': 'up',
                'category': 'revenue'
            })
            
            # KPI: Sentimento Positivo
            sentiment_dist = sentiment_metrics.get('sentiment_distribution', {})
            positive_percentage = sentiment_dist.get('positive', {}).get('percentage', 0)
            kpis.append({
                'name': 'Sentimento Positivo',
                'value': positive_percentage,
                'target': 70,  # Meta: 70%
                'unit': '%',
                'trend': 'up',
                'category': 'sentiment'
            })
            
            return kpis
            
        except Exception as e:
            print(f"Erro ao calcular KPIs: {e}")
            return []
    
    def export_report(self, report_type, format_type='json', start_date=None, end_date=None):
        """Exportar relatório em diferentes formatos"""
        try:
            if report_type == 'dashboard':
                data = self.generate_dashboard_data()
            elif report_type == 'conversations':
                data = self.calculate_conversation_metrics(start_date, end_date)
            elif report_type == 'appointments':
                data = self.calculate_appointment_metrics(start_date, end_date)
            elif report_type == 'sentiment':
                data = self.calculate_sentiment_metrics(start_date, end_date)
            elif report_type == 'kpis':
                data = self.calculate_kpis()
            else:
                return None
            
            if format_type == 'json':
                return json.dumps(data, indent=2, ensure_ascii=False)
            elif format_type == 'csv':
                # Implementar conversão para CSV
                return self.convert_to_csv(data)
            else:
                return data
            
        except Exception as e:
            print(f"Erro ao exportar relatório: {e}")
            return None
    
    def convert_to_csv(self, data):
        """Converter dados para formato CSV"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            elif isinstance(data, dict):
                # Converter dict para formato tabular
                writer = csv.writer(output)
                writer.writerow(['Métrica', 'Valor'])
                for key, value in data.items():
                    if isinstance(value, (str, int, float)):
                        writer.writerow([key, value])
            
            return output.getvalue()
            
        except Exception as e:
            print(f"Erro ao converter para CSV: {e}")
            return str(data)

# Instância global
bi = BusinessIntelligence()

# Rotas da API
@bi_bp.route('/')
def bi_dashboard():
    """Dashboard de Business Intelligence"""
    return render_template('bi_dashboard.html')

@bi_bp.route('/dashboard/<period>')
def get_dashboard_data(period):
    """Obter dados do dashboard"""
    try:
        data = bi.generate_dashboard_data(period)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/kpis/<period>')
def get_kpis(period):
    """Obter KPIs"""
    try:
        kpis = bi.calculate_kpis(period)
        return jsonify({'success': True, 'kpis': kpis})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/metrics/conversations')
def get_conversation_metrics():
    """Obter métricas de conversas"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        metrics = bi.calculate_conversation_metrics(start_date, end_date)
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/metrics/sentiment')
def get_sentiment_metrics():
    """Obter métricas de sentimento"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        metrics = bi.calculate_sentiment_metrics(start_date, end_date)
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/metrics/appointments')
def get_appointment_metrics():
    """Obter métricas de agendamentos"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        metrics = bi.calculate_appointment_metrics(start_date, end_date)
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bi_bp.route('/export/<report_type>')
def export_report(report_type):
    """Exportar relatório"""
    try:
        format_type = request.args.get('format', 'json')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        report_data = bi.export_report(report_type, format_type, start_date, end_date)
        
        if report_data is None:
            return jsonify({'success': False, 'error': 'Tipo de relatório inválido'}), 400
        
        if format_type == 'csv':
            from flask import Response
            return Response(
                report_data,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={report_type}_report.csv'}
            )
        else:
            return jsonify({'success': True, 'data': report_data})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def init_bi(app):
    """Inicializar BI no app Flask"""
    app.register_blueprint(bi_bp)
    return app