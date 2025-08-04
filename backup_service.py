import os
import shutil
import schedule
import time
import threading
from datetime import datetime, timedelta
from database import DatabaseManager
from email_service import EmailService
import json
import zipfile

class BackupService:
    def __init__(self, db_manager, email_service):
        self.db_manager = db_manager
        self.email_service = email_service
        self.backup_dir = 'backups'
        self.max_backups = 30  # Manter apenas os últimos 30 backups
        
        # Criar diretório de backup se não existir
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, include_files=True):
        """Cria um backup completo do sistema"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'clinic_backup_{timestamp}'
            backup_path = os.path.join(self.backup_dir, f'{backup_name}.zip')
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup do banco de dados
                db_backup_path = self.db_manager.backup_database(f'temp_db_backup_{timestamp}.db')
                zipf.write(db_backup_path, 'database.db')
                os.remove(db_backup_path)  # Remove arquivo temporário
                
                # Backup dos arquivos de configuração
                if include_files:
                    files_to_backup = [
                        '.env',
                        'app.py',
                        'database.py',
                        'email_service.py',
                        'backup_service.py',
                        'requirements.txt'
                    ]
                    
                    for file_path in files_to_backup:
                        if os.path.exists(file_path):
                            zipf.write(file_path, file_path)
                    
                    # Backup dos templates
                    if os.path.exists('templates'):
                        for root, dirs, files in os.walk('templates'):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, '.')
                                zipf.write(file_path, arcname)
                
                # Adicionar metadados do backup
                metadata = {
                    'backup_date': datetime.now().isoformat(),
                    'backup_type': 'full' if include_files else 'database_only',
                    'statistics': self.db_manager.get_statistics()
                }
                
                zipf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            # Limpar backups antigos
            self.cleanup_old_backups()
            
            # Enviar notificação por email
            self.email_service.send_backup_notification(backup_path, success=True)
            
            print(f"✅ Backup criado com sucesso: {backup_path}")
            return backup_path
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {str(e)}")
            self.email_service.send_backup_notification('', success=False)
            return None
    
    def cleanup_old_backups(self):
        """Remove backups antigos, mantendo apenas os mais recentes"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('clinic_backup_') and file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # Ordenar por data de criação (mais recente primeiro)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remover backups excedentes
            if len(backup_files) > self.max_backups:
                for file_path, _ in backup_files[self.max_backups:]:
                    os.remove(file_path)
                    print(f"🗑️ Backup antigo removido: {file_path}")
                    
        except Exception as e:
            print(f"⚠️ Erro ao limpar backups antigos: {str(e)}")
    
    def restore_backup(self, backup_path):
        """Restaura um backup (use com cuidado!)"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Arquivo de backup não encontrado: {backup_path}")
            
            # Criar backup de segurança antes da restauração
            safety_backup = self.create_backup(include_files=False)
            print(f"🛡️ Backup de segurança criado: {safety_backup}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Restaurar banco de dados
                if 'database.db' in zipf.namelist():
                    zipf.extract('database.db', 'temp_restore')
                    shutil.move('temp_restore/database.db', self.db_manager.db_path)
                    os.rmdir('temp_restore')
                
                # Ler metadados
                if 'backup_metadata.json' in zipf.namelist():
                    metadata_content = zipf.read('backup_metadata.json')
                    metadata = json.loads(metadata_content)
                    print(f"📊 Restaurando backup de: {metadata['backup_date']}")
            
            print(f"✅ Backup restaurado com sucesso: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {str(e)}")
            return False
    
    def schedule_automatic_backups(self):
        """Agenda backups automáticos"""
        # Backup diário às 2:00 AM
        schedule.every().day.at("02:00").do(self.create_backup, include_files=True)
        
        # Backup rápido (apenas banco) a cada 6 horas
        schedule.every(6).hours.do(self.create_backup, include_files=False)
        
        print("📅 Backups automáticos agendados:")
        print("   - Backup completo: diário às 02:00")
        print("   - Backup do banco: a cada 6 horas")
    
    def run_scheduler(self):
        """Executa o agendador de backups em thread separada"""
        def scheduler_thread():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
        
        thread = threading.Thread(target=scheduler_thread, daemon=True)
        thread.start()
        print("🔄 Serviço de backup automático iniciado")
    
    def get_backup_list(self):
        """Retorna lista de backups disponíveis"""
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for file in os.listdir(self.backup_dir):
            if file.startswith('clinic_backup_') and file.endswith('.zip'):
                file_path = os.path.join(self.backup_dir, file)
                file_stats = os.stat(file_path)
                
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'size': file_stats.st_size,
                    'created': datetime.fromtimestamp(file_stats.st_ctime),
                    'size_mb': round(file_stats.st_size / (1024 * 1024), 2)
                })
        
        # Ordenar por data de criação (mais recente primeiro)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def export_conversations_csv(self, start_date=None, end_date=None):
        """Exporta conversas para arquivo CSV"""
        try:
            import csv
            from io import StringIO
            
            conversations = self.db_manager.get_conversations(limit=10000)
            
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
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'conversas_export_{timestamp}.csv'
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                f.write(output.getvalue())
            
            print(f"📊 Conversas exportadas para: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Erro ao exportar conversas: {str(e)}")
            return None
    
    def get_backup_statistics(self):
        """Retorna estatísticas dos backups"""
        backups = self.get_backup_list()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'latest_backup': None,
                'oldest_backup': None
            }
        
        total_size = sum(backup['size'] for backup in backups)
        
        return {
            'total_backups': len(backups),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'latest_backup': backups[0]['created'] if backups else None,
            'oldest_backup': backups[-1]['created'] if backups else None
        }