import sqlite3
import json
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='clinic_chatbot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de conversas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_ip TEXT,
                user_agent TEXT
            )
        ''')
        
        # Tabela de tickets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'aberto',
                priority TEXT DEFAULT 'media',
                contact_name TEXT,
                contact_phone TEXT,
                contact_email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                assigned_to TEXT,
                notes TEXT
            )
        ''')
        
        # Tabela de usuários administrativos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, session_id, user_message, bot_response, user_ip=None, user_agent=None):
        """Salva uma conversa no banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (session_id, user_message, bot_response, user_ip, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_message, bot_response, user_ip, user_agent))
        
        conn.commit()
        conn.close()
    
    def create_ticket(self, session_id, title, description, contact_name=None, contact_phone=None, contact_email=None, priority='media'):
        """Cria um novo ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tickets (session_id, title, description, contact_name, contact_phone, contact_email, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, title, description, contact_name, contact_phone, contact_email, priority))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_tickets(self, status=None, limit=50):
        """Recupera tickets do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
        
        tickets = cursor.fetchall()
        conn.close()
        
        return tickets
    
    def get_tickets_by_session(self, session_id):
        """Recupera tickets de uma sessão específica"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, title, description, status, created_at, contact_name, contact_phone, contact_email, priority
            FROM tickets WHERE session_id = ? ORDER BY created_at DESC
        ''', (session_id,))
        
        tickets = cursor.fetchall()
        conn.close()
        return tickets
    
    def get_ticket_details(self, ticket_id):
        """Recupera detalhes completos de um ticket específico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_id, title, description, status, created_at, updated_at, 
                   contact_name, contact_phone, contact_email, priority, notes
            FROM tickets WHERE id = ?
        ''', (ticket_id,))
        
        ticket = cursor.fetchone()
        
        if ticket:
            # Buscar conversas relacionadas a esta sessão
            cursor.execute('''
                SELECT user_message, bot_response, timestamp
                FROM conversations WHERE session_id = ? ORDER BY timestamp ASC
            ''', (ticket[1],))  # ticket[1] é o session_id
            
            conversations = cursor.fetchall()
            conn.close()
            
            return {
                'ticket': ticket,
                'conversations': conversations
            }
        
        conn.close()
        return None
    
    def update_ticket_status(self, ticket_id, status, notes=None):
        """Atualiza o status de um ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if notes:
            cursor.execute('''
                UPDATE tickets SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, notes, ticket_id))
        else:
            cursor.execute('''
                UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, ticket_id))
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, email, password_hash, role='admin'):
        """Cria um novo usuário administrativo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO admin_users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_user_by_username(self, username):
        """Busca usuário por nome de usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, role, created_at, last_login
            FROM admin_users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user_by_email(self, email):
        """Busca usuário por email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, role, created_at, last_login
            FROM admin_users WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user_by_id(self, user_id):
        """Busca usuário por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, role, created_at, last_login
            FROM admin_users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def authenticate_user(self, username, password):
        """Autentica usuário com bcrypt"""
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        
        user = self.get_user_by_username(username)
        if user and bcrypt.check_password_hash(user[3], password):
            return user
        return None
    
    def update_last_login(self, user_id):
        """Atualiza último login do usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_users(self):
        """Retorna todos os usuários administrativos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, created_at, last_login
            FROM admin_users ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        return users
    
    def get_conversations(self, session_id=None, limit=100):
        """Recupera conversas do banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute('''
                SELECT * FROM conversations WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
            ''', (session_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
        
        conversations = cursor.fetchall()
        conn.close()
        
        return conversations
    
    def backup_database(self, backup_path=None):
        """Cria backup do banco de dados"""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'backup_clinic_chatbot_{timestamp}.db'
        
        # Copia o arquivo do banco de dados
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        return backup_path
    
    def get_statistics(self):
        """Retorna estatísticas do sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de conversas
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        
        # Total de tickets
        cursor.execute('SELECT COUNT(*) FROM tickets')
        total_tickets = cursor.fetchone()[0]
        
        # Tickets por status
        cursor.execute('SELECT status, COUNT(*) FROM tickets GROUP BY status')
        tickets_by_status = dict(cursor.fetchall())
        
        # Conversas hoje
        cursor.execute('''
            SELECT COUNT(*) FROM conversations 
            WHERE DATE(timestamp) = DATE('now')
        ''')
        conversations_today = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_conversations': total_conversations,
            'total_tickets': total_tickets,
            'tickets_by_status': tickets_by_status,
            'conversations_today': conversations_today
        }