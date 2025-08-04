from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import calendar
import json
import os
from database import DatabaseManager
from email_service import EmailService
import uuid

# Blueprint para integração com calendário
calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

class CalendarIntegration:
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.business_hours = {
            'start': 8,  # 8:00
            'end': 18,   # 18:00
            'lunch_start': 12,  # 12:00
            'lunch_end': 13,    # 13:00
            'working_days': [0, 1, 2, 3, 4]  # Segunda a Sexta (0=Segunda)
        }
        self.appointment_duration = 60  # minutos
        self.setup_database()
    
    def setup_database(self):
        """Configurar tabelas do calendário"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de agendamentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id TEXT UNIQUE NOT NULL,
                    patient_name TEXT NOT NULL,
                    patient_email TEXT,
                    patient_phone TEXT,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    status TEXT DEFAULT 'scheduled',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de disponibilidade especial
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS availability_exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    is_available INTEGER DEFAULT 1,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de tipos de serviço
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    description TEXT,
                    price REAL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            
            # Inserir tipos de serviço padrão
            self.insert_default_services(cursor)
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao configurar banco de dados do calendário: {e}")
        finally:
            if conn:
                conn.close()
    
    def insert_default_services(self, cursor):
        """Inserir tipos de serviço padrão"""
        default_services = [
            ('Consulta Inicial', 60, 'Primeira consulta para avaliação', 150.00),
            ('Consulta de Retorno', 45, 'Consulta de acompanhamento', 120.00),
            ('Terapia Individual', 50, 'Sessão de terapia individual', 130.00),
            ('Terapia em Grupo', 90, 'Sessão de terapia em grupo', 80.00),
            ('Avaliação Psicológica', 120, 'Avaliação psicológica completa', 200.00),
            ('Orientação Familiar', 60, 'Orientação para familiares', 140.00)
        ]
        
        for service in default_services:
            cursor.execute('''
                INSERT OR IGNORE INTO service_types (name, duration, description, price)
                VALUES (?, ?, ?, ?)
            ''', service)
    
    def get_available_slots(self, date_str, service_type_id=None):
        """Obter horários disponíveis para uma data"""
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Verificar se é dia útil
            if target_date.weekday() not in self.business_hours['working_days']:
                return []
            
            # Obter duração do serviço
            duration = self.appointment_duration
            if service_type_id:
                service = self.get_service_type(service_type_id)
                if service:
                    duration = service['duration']
            
            # Gerar slots disponíveis
            available_slots = []
            current_time = self.business_hours['start']
            
            while current_time + (duration / 60) <= self.business_hours['end']:
                # Pular horário de almoço
                if (current_time >= self.business_hours['lunch_start'] and 
                    current_time < self.business_hours['lunch_end']):
                    current_time = self.business_hours['lunch_end']
                    continue
                
                time_str = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
                
                # Verificar se horário está ocupado
                if not self.is_slot_occupied(date_str, time_str, duration):
                    available_slots.append({
                        'time': time_str,
                        'duration': duration,
                        'end_time': self.calculate_end_time(time_str, duration)
                    })
                
                current_time += 0.5  # Incremento de 30 minutos
            
            return available_slots
            
        except Exception as e:
            print(f"Erro ao obter slots disponíveis: {e}")
            return []
    
    def is_slot_occupied(self, date_str, time_str, duration):
        """Verificar se um horário está ocupado"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Calcular horário de fim
            end_time = self.calculate_end_time(time_str, duration)
            
            cursor.execute('''
                SELECT COUNT(*) FROM appointments 
                WHERE appointment_date = ? 
                AND status != 'cancelled'
                AND (
                    (appointment_time <= ? AND 
                     time(appointment_time, '+' || 
                          (SELECT duration FROM service_types 
                           WHERE name = appointments.service_type) || ' minutes') > ?)
                    OR
                    (appointment_time < ? AND appointment_time >= ?)
                )
            ''', (date_str, time_str, time_str, end_time, time_str))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            print(f"Erro ao verificar ocupação: {e}")
            return True
        finally:
            conn.close()
    
    def calculate_end_time(self, start_time, duration_minutes):
        """Calcular horário de fim"""
        try:
            start = datetime.strptime(start_time, '%H:%M')
            end = start + timedelta(minutes=duration_minutes)
            return end.strftime('%H:%M')
        except:
            return start_time
    
    def create_appointment(self, appointment_data):
        """Criar novo agendamento"""
        try:
            # Validar dados obrigatórios
            required_fields = ['patient_name', 'appointment_date', 'appointment_time', 'service_type']
            for field in required_fields:
                if not appointment_data.get(field):
                    return {'success': False, 'error': f'{field} é obrigatório'}
            
            # Verificar disponibilidade
            service = self.get_service_by_name(appointment_data['service_type'])
            if not service:
                return {'success': False, 'error': 'Tipo de serviço inválido'}
            
            if self.is_slot_occupied(
                appointment_data['appointment_date'],
                appointment_data['appointment_time'],
                service['duration']
            ):
                return {'success': False, 'error': 'Horário não disponível'}
            
            # Gerar ID único
            appointment_id = str(uuid.uuid4())[:8].upper()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO appointments (
                    appointment_id, patient_name, patient_email, patient_phone,
                    appointment_date, appointment_time, service_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                appointment_id,
                appointment_data['patient_name'],
                appointment_data.get('patient_email'),
                appointment_data.get('patient_phone'),
                appointment_data['appointment_date'],
                appointment_data['appointment_time'],
                appointment_data['service_type'],
                appointment_data.get('notes', '')
            ))
            
            conn.commit()
            
            # Enviar email de confirmação
            if appointment_data.get('patient_email'):
                self.send_appointment_confirmation(appointment_id, appointment_data)
            
            return {
                'success': True,
                'appointment_id': appointment_id,
                'message': 'Agendamento criado com sucesso'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Erro ao criar agendamento: {str(e)}'}
        finally:
            conn.close()
    
    def get_appointment(self, appointment_id):
        """Obter detalhes de um agendamento"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.*, s.duration, s.price 
                FROM appointments a
                LEFT JOIN service_types s ON a.service_type = s.name
                WHERE a.appointment_id = ?
            ''', (appointment_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'appointment_id': row[1],
                    'patient_name': row[2],
                    'patient_email': row[3],
                    'patient_phone': row[4],
                    'appointment_date': row[5],
                    'appointment_time': row[6],
                    'service_type': row[7],
                    'status': row[8],
                    'notes': row[9],
                    'created_at': row[10],
                    'updated_at': row[11],
                    'duration': row[12],
                    'price': row[13]
                }
            
            return None
            
        except Exception as e:
            print(f"Erro ao obter agendamento: {e}")
            return None
        finally:
            conn.close()
    
    def update_appointment_status(self, appointment_id, new_status, notes=None):
        """Atualizar status de um agendamento"""
        try:
            valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']
            if new_status not in valid_statuses:
                return {'success': False, 'error': 'Status inválido'}
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            update_query = '''
                UPDATE appointments 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
            '''
            params = [new_status]
            
            if notes:
                update_query += ', notes = ?'
                params.append(notes)
            
            update_query += ' WHERE appointment_id = ?'
            params.append(appointment_id)
            
            cursor.execute(update_query, params)
            
            if cursor.rowcount > 0:
                conn.commit()
                
                # Enviar notificação por email se necessário
                appointment = self.get_appointment(appointment_id)
                if appointment and appointment['patient_email']:
                    self.send_status_update_email(appointment, new_status)
                
                return {'success': True, 'message': 'Status atualizado com sucesso'}
            else:
                return {'success': False, 'error': 'Agendamento não encontrado'}
            
        except Exception as e:
            return {'success': False, 'error': f'Erro ao atualizar status: {str(e)}'}
        finally:
            conn.close()
    
    def get_appointments_by_date(self, date_str):
        """Obter agendamentos de uma data específica"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.*, s.duration, s.price 
                FROM appointments a
                LEFT JOIN service_types s ON a.service_type = s.name
                WHERE a.appointment_date = ?
                ORDER BY a.appointment_time
            ''', (date_str,))
            
            appointments = []
            for row in cursor.fetchall():
                appointments.append({
                    'id': row[0],
                    'appointment_id': row[1],
                    'patient_name': row[2],
                    'patient_email': row[3],
                    'patient_phone': row[4],
                    'appointment_date': row[5],
                    'appointment_time': row[6],
                    'service_type': row[7],
                    'status': row[8],
                    'notes': row[9],
                    'created_at': row[10],
                    'updated_at': row[11],
                    'duration': row[12],
                    'price': row[13]
                })
            
            return appointments
            
        except Exception as e:
            print(f"Erro ao obter agendamentos: {e}")
            return []
        finally:
            conn.close()
    
    def get_service_types(self):
        """Obter tipos de serviço disponíveis"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM service_types WHERE is_active = 1
                ORDER BY name
            ''')
            
            services = []
            for row in cursor.fetchall():
                services.append({
                    'id': row[0],
                    'name': row[1],
                    'duration': row[2],
                    'description': row[3],
                    'price': row[4],
                    'is_active': row[5]
                })
            
            return services
            
        except Exception as e:
            print(f"Erro ao obter tipos de serviço: {e}")
            return []
        finally:
            conn.close()
    
    def get_service_type(self, service_id):
        """Obter tipo de serviço por ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM service_types WHERE id = ?', (service_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'duration': row[2],
                    'description': row[3],
                    'price': row[4],
                    'is_active': row[5]
                }
            
            return None
            
        except Exception as e:
            print(f"Erro ao obter tipo de serviço: {e}")
            return None
        finally:
            conn.close()
    
    def get_service_by_name(self, service_name):
        """Obter tipo de serviço por nome"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM service_types WHERE name = ?', (service_name,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'duration': row[2],
                    'description': row[3],
                    'price': row[4],
                    'is_active': row[5]
                }
            
            return None
            
        except Exception as e:
            print(f"Erro ao obter tipo de serviço: {e}")
            return None
        finally:
            conn.close()
    
    def send_appointment_confirmation(self, appointment_id, appointment_data):
        """Enviar email de confirmação de agendamento"""
        try:
            subject = f"Confirmação de Agendamento - {appointment_id}"
            
            body = f"""
            Olá {appointment_data['patient_name']},
            
            Seu agendamento foi confirmado com sucesso!
            
            Detalhes do Agendamento:
            - ID: {appointment_id}
            - Data: {appointment_data['appointment_date']}
            - Horário: {appointment_data['appointment_time']}
            - Serviço: {appointment_data['service_type']}
            
            Por favor, chegue 15 minutos antes do horário agendado.
            
            Em caso de dúvidas ou necessidade de reagendamento, entre em contato conosco.
            
            Atenciosamente,
            Clínica Espaço Vida
            """
            
            self.email_service.send_email(
                appointment_data['patient_email'],
                subject,
                body
            )
            
        except Exception as e:
            print(f"Erro ao enviar email de confirmação: {e}")
    
    def send_status_update_email(self, appointment, new_status):
        """Enviar email de atualização de status"""
        try:
            status_messages = {
                'confirmed': 'confirmado',
                'completed': 'concluído',
                'cancelled': 'cancelado',
                'no_show': 'perdido (paciente não compareceu)'
            }
            
            status_text = status_messages.get(new_status, new_status)
            subject = f"Atualização de Agendamento - {appointment['appointment_id']}"
            
            body = f"""
            Olá {appointment['patient_name']},
            
            Seu agendamento foi {status_text}.
            
            Detalhes do Agendamento:
            - ID: {appointment['appointment_id']}
            - Data: {appointment['appointment_date']}
            - Horário: {appointment['appointment_time']}
            - Serviço: {appointment['service_type']}
            - Status: {status_text.title()}
            
            Em caso de dúvidas, entre em contato conosco.
            
            Atenciosamente,
            Clínica Espaço Vida
            """
            
            self.email_service.send_email(
                appointment['patient_email'],
                subject,
                body
            )
            
        except Exception as e:
            print(f"Erro ao enviar email de atualização: {e}")

# Instância global
calendar_integration = CalendarIntegration()

# Rotas da API
@calendar_bp.route('/')
def calendar_interface():
    """Interface do calendário"""
    return render_template('calendar.html')

@calendar_bp.route('/available-slots/<date>')
def get_available_slots(date):
    """Obter horários disponíveis"""
    try:
        service_type_id = request.args.get('service_type_id')
        slots = calendar_integration.get_available_slots(date, service_type_id)
        return jsonify({'success': True, 'slots': slots})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/appointments', methods=['POST'])
def create_appointment():
    """Criar agendamento"""
    try:
        data = request.get_json()
        result = calendar_integration.create_appointment(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/appointments/<appointment_id>')
def get_appointment(appointment_id):
    """Obter agendamento"""
    try:
        appointment = calendar_integration.get_appointment(appointment_id)
        if appointment:
            return jsonify({'success': True, 'appointment': appointment})
        else:
            return jsonify({'success': False, 'error': 'Agendamento não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/appointments/<appointment_id>/status', methods=['PUT'])
def update_appointment_status(appointment_id):
    """Atualizar status do agendamento"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes')
        
        result = calendar_integration.update_appointment_status(appointment_id, new_status, notes)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/appointments/date/<date>')
def get_appointments_by_date(date):
    """Obter agendamentos por data"""
    try:
        appointments = calendar_integration.get_appointments_by_date(date)
        return jsonify({'success': True, 'appointments': appointments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/service-types')
def get_service_types():
    """Obter tipos de serviço"""
    try:
        services = calendar_integration.get_service_types()
        return jsonify({'success': True, 'services': services})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def init_calendar(app):
    """Inicializar calendário no app Flask"""
    app.register_blueprint(calendar_bp)
    return app