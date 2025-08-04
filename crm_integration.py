import requests
import json
from datetime import datetime
import os
from database import DatabaseManager

class CRMIntegration:
    def __init__(self):
        self.db = DatabaseManager()
        self.integrations = {
            'salesforce': SalesforceIntegration(),
            'hubspot': HubSpotIntegration(),
            'pipedrive': PipedriveIntegration(),
            'zoho': ZohoIntegration(),
            'rdstation': RDStationIntegration()
        }
    
    def sync_lead(self, lead_data, crm_type='hubspot'):
        """Sincroniza lead com CRM especificado"""
        if crm_type in self.integrations:
            return self.integrations[crm_type].create_lead(lead_data)
        return {'success': False, 'error': 'CRM não suportado'}
    
    def sync_conversation(self, session_id, crm_type='hubspot'):
        """Sincroniza conversa completa com CRM"""
        conversations = self.db.get_conversations(session_id)
        tickets = self.db.get_tickets_by_session(session_id)
        
        conversation_data = {
            'session_id': session_id,
            'messages': conversations,
            'tickets': tickets,
            'timestamp': datetime.now().isoformat()
        }
        
        if crm_type in self.integrations:
            return self.integrations[crm_type].create_activity(conversation_data)
        return {'success': False, 'error': 'CRM não suportado'}
    
    def get_available_crms(self):
        """Retorna CRMs disponíveis e configurados"""
        available = {}
        for crm_name, integration in self.integrations.items():
            available[crm_name] = {
                'name': integration.get_name(),
                'configured': integration.is_configured(),
                'features': integration.get_features()
            }
        return available

class BaseCRMIntegration:
    """Classe base para integrações CRM"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = None
        self.headers = {}
    
    def is_configured(self):
        """Verifica se a integração está configurada"""
        return bool(self.api_key)
    
    def get_name(self):
        """Retorna nome do CRM"""
        return "Base CRM"
    
    def get_features(self):
        """Retorna funcionalidades suportadas"""
        return ['leads', 'contacts', 'activities']
    
    def create_lead(self, lead_data):
        """Cria lead no CRM"""
        raise NotImplementedError
    
    def create_contact(self, contact_data):
        """Cria contato no CRM"""
        raise NotImplementedError
    
    def create_activity(self, activity_data):
        """Cria atividade no CRM"""
        raise NotImplementedError

class HubSpotIntegration(BaseCRMIntegration):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('HUBSPOT_API_KEY')
        self.base_url = 'https://api.hubapi.com'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_name(self):
        return "HubSpot"
    
    def create_lead(self, lead_data):
        """Cria lead no HubSpot"""
        if not self.is_configured():
            return {'success': False, 'error': 'HubSpot não configurado'}
        
        url = f'{self.base_url}/crm/v3/objects/contacts'
        
        # Mapear dados para formato HubSpot
        hubspot_data = {
            'properties': {
                'email': lead_data.get('email', ''),
                'firstname': lead_data.get('name', '').split(' ')[0] if lead_data.get('name') else '',
                'lastname': ' '.join(lead_data.get('name', '').split(' ')[1:]) if lead_data.get('name') else '',
                'phone': lead_data.get('phone', ''),
                'company': 'Clínica Espaço Vida - Lead Chatbot',
                'lifecyclestage': 'lead',
                'lead_source': lead_data.get('source', 'chatbot'),
                'hs_lead_status': 'NEW',
                'message': lead_data.get('message', ''),
                'chat_session_id': lead_data.get('session_id', ''),
                'urgency_level': lead_data.get('urgency', 'medium')
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=hubspot_data)
            
            if response.status_code == 201:
                contact_data = response.json()
                return {
                    'success': True,
                    'contact_id': contact_data['id'],
                    'crm': 'hubspot'
                }
            else:
                return {
                    'success': False,
                    'error': f'Erro HubSpot: {response.status_code} - {response.text}'
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_activity(self, activity_data):
        """Cria atividade/nota no HubSpot"""
        if not self.is_configured():
            return {'success': False, 'error': 'HubSpot não configurado'}
        
        # Primeiro, encontrar ou criar o contato
        contact_id = self._find_or_create_contact(activity_data)
        
        if not contact_id:
            return {'success': False, 'error': 'Não foi possível criar/encontrar contato'}
        
        # Criar nota com a conversa
        url = f'{self.base_url}/crm/v3/objects/notes'
        
        conversation_text = self._format_conversation(activity_data['messages'])
        
        note_data = {
            'properties': {
                'hs_note_body': conversation_text,
                'hs_timestamp': datetime.now().isoformat()
            },
            'associations': [
                {
                    'to': {'id': contact_id},
                    'types': [{'associationCategory': 'HUBSPOT_DEFINED', 'associationTypeId': 202}]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=note_data)
            
            if response.status_code == 201:
                return {'success': True, 'note_id': response.json()['id']}
            else:
                return {'success': False, 'error': f'Erro ao criar nota: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _find_or_create_contact(self, activity_data):
        """Encontra ou cria contato baseado na sessão"""
        # Implementação simplificada - em produção, seria mais robusta
        session_id = activity_data.get('session_id')
        
        # Buscar tickets para obter informações de contato
        tickets = activity_data.get('tickets', [])
        
        contact_data = {
            'session_id': session_id,
            'source': 'chatbot'
        }
        
        if tickets:
            ticket = tickets[0]  # Usar primeiro ticket
            contact_data.update({
                'name': ticket[6] if len(ticket) > 6 else '',  # contact_name
                'phone': ticket[7] if len(ticket) > 7 else '',  # contact_phone
                'email': ticket[8] if len(ticket) > 8 else ''   # contact_email
            })
        
        result = self.create_lead(contact_data)
        return result.get('contact_id') if result.get('success') else None
    
    def _format_conversation(self, messages):
        """Formata conversa para o CRM"""
        formatted = "=== CONVERSA CHATBOT CLÍNICA ESPAÇO VIDA ===\n\n"
        
        for message in messages:
            timestamp = message[4] if len(message) > 4 else 'N/A'
            user_msg = message[2] if len(message) > 2 else ''
            bot_msg = message[3] if len(message) > 3 else ''
            
            formatted += f"[{timestamp}] USUÁRIO: {user_msg}\n"
            formatted += f"[{timestamp}] BOT: {bot_msg}\n\n"
        
        return formatted

class SalesforceIntegration(BaseCRMIntegration):
    def __init__(self):
        super().__init__()
        self.client_id = os.getenv('SALESFORCE_CLIENT_ID')
        self.client_secret = os.getenv('SALESFORCE_CLIENT_SECRET')
        self.username = os.getenv('SALESFORCE_USERNAME')
        self.password = os.getenv('SALESFORCE_PASSWORD')
        self.security_token = os.getenv('SALESFORCE_SECURITY_TOKEN')
        self.instance_url = os.getenv('SALESFORCE_INSTANCE_URL', 'https://login.salesforce.com')
        self.access_token = None
    
    def get_name(self):
        return "Salesforce"
    
    def is_configured(self):
        return bool(self.client_id and self.client_secret and self.username and self.password)
    
    def _authenticate(self):
        """Autentica com Salesforce"""
        if self.access_token:
            return True
        
        auth_url = f'{self.instance_url}/services/oauth2/token'
        auth_data = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': f'{self.password}{self.security_token}'
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            if response.status_code == 200:
                auth_result = response.json()
                self.access_token = auth_result['access_token']
                self.instance_url = auth_result['instance_url']
                self.headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                return True
        except Exception as e:
            print(f"Erro na autenticação Salesforce: {e}")
        
        return False
    
    def create_lead(self, lead_data):
        """Cria lead no Salesforce"""
        if not self._authenticate():
            return {'success': False, 'error': 'Falha na autenticação Salesforce'}
        
        url = f'{self.instance_url}/services/data/v52.0/sobjects/Lead/'
        
        salesforce_data = {
            'FirstName': lead_data.get('name', '').split(' ')[0] if lead_data.get('name') else 'Lead',
            'LastName': ' '.join(lead_data.get('name', '').split(' ')[1:]) if lead_data.get('name') else 'Chatbot',
            'Email': lead_data.get('email', ''),
            'Phone': lead_data.get('phone', ''),
            'Company': 'Clínica Espaço Vida - Lead',
            'LeadSource': 'Chatbot',
            'Status': 'Open - Not Contacted',
            'Description': lead_data.get('message', ''),
            'Rating': 'Hot' if lead_data.get('urgency') == 'high' else 'Warm'
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=salesforce_data)
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'lead_id': response.json()['id'],
                    'crm': 'salesforce'
                }
            else:
                return {
                    'success': False,
                    'error': f'Erro Salesforce: {response.status_code} - {response.text}'
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_activity(self, activity_data):
        """Cria atividade no Salesforce"""
        # Implementação similar ao HubSpot, adaptada para Salesforce
        return {'success': False, 'error': 'Implementação em desenvolvimento'}

class PipedriveIntegration(BaseCRMIntegration):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('PIPEDRIVE_API_KEY')
        self.base_url = 'https://api.pipedrive.com/v1'
    
    def get_name(self):
        return "Pipedrive"
    
    def create_lead(self, lead_data):
        """Cria lead no Pipedrive"""
        if not self.is_configured():
            return {'success': False, 'error': 'Pipedrive não configurado'}
        
        url = f'{self.base_url}/leads?api_token={self.api_key}'
        
        pipedrive_data = {
            'title': f"Lead Chatbot - {lead_data.get('name', 'Anônimo')}",
            'person_name': lead_data.get('name', ''),
            'organization_name': 'Clínica Espaço Vida - Lead',
            'phone': lead_data.get('phone', ''),
            'email': lead_data.get('email', ''),
            'note': lead_data.get('message', ''),
            'source_name': 'Chatbot'
        }
        
        try:
            response = requests.post(url, json=pipedrive_data)
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'lead_id': response.json()['data']['id'],
                    'crm': 'pipedrive'
                }
            else:
                return {
                    'success': False,
                    'error': f'Erro Pipedrive: {response.status_code} - {response.text}'
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_activity(self, activity_data):
        """Cria atividade no Pipedrive"""
        return {'success': False, 'error': 'Implementação em desenvolvimento'}

class ZohoIntegration(BaseCRMIntegration):
    def __init__(self):
        super().__init__()
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')
        self.base_url = 'https://www.zohoapis.com/crm/v2'
        self.access_token = None
    
    def get_name(self):
        return "Zoho CRM"
    
    def is_configured(self):
        return bool(self.client_id and self.client_secret and self.refresh_token)
    
    def create_lead(self, lead_data):
        """Cria lead no Zoho CRM"""
        return {'success': False, 'error': 'Implementação em desenvolvimento'}
    
    def create_activity(self, activity_data):
        """Cria atividade no Zoho CRM"""
        return {'success': False, 'error': 'Implementação em desenvolvimento'}

class RDStationIntegration(BaseCRMIntegration):
    def __init__(self):
        super().__init__()
        self.client_id = os.getenv('RDSTATION_CLIENT_ID')
        self.client_secret = os.getenv('RDSTATION_CLIENT_SECRET')
        self.base_url = 'https://api.rd.services'
        self.access_token = None
    
    def get_name(self):
        return "RD Station"
    
    def is_configured(self):
        return bool(self.client_id and self.client_secret)
    
    def create_lead(self, lead_data):
        """Cria lead no RD Station"""
        if not self.is_configured():
            return {'success': False, 'error': 'RD Station não configurado'}
        
        # RD Station usa eventos para criar leads
        url = f'{self.base_url}/platform/events'
        
        rd_data = {
            'event_type': 'CONVERSION',
            'event_family': 'CDP',
            'payload': {
                'conversion_identifier': 'chatbot-lead',
                'name': lead_data.get('name', ''),
                'email': lead_data.get('email', ''),
                'phone': lead_data.get('phone', ''),
                'cf_message': lead_data.get('message', ''),
                'cf_source': 'Chatbot Clínica Espaço Vida',
                'cf_urgency': lead_data.get('urgency', 'medium')
            }
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=rd_data)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'event_uuid': response.json().get('event_uuid'),
                    'crm': 'rdstation'
                }
            else:
                return {
                    'success': False,
                    'error': f'Erro RD Station: {response.status_code} - {response.text}'
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_activity(self, activity_data):
        """Cria atividade no RD Station"""
        return {'success': False, 'error': 'RD Station não suporta atividades via API pública'}

def get_crm_config_template():
    """Retorna template de configuração para CRMs"""
    return {
        'hubspot': {
            'required_env_vars': ['HUBSPOT_API_KEY'],
            'description': 'Token de API privada do HubSpot',
            'setup_url': 'https://developers.hubspot.com/docs/api/private-apps'
        },
        'salesforce': {
            'required_env_vars': [
                'SALESFORCE_CLIENT_ID',
                'SALESFORCE_CLIENT_SECRET',
                'SALESFORCE_USERNAME',
                'SALESFORCE_PASSWORD',
                'SALESFORCE_SECURITY_TOKEN'
            ],
            'description': 'Configuração OAuth2 do Salesforce',
            'setup_url': 'https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_understanding_authentication.htm'
        },
        'pipedrive': {
            'required_env_vars': ['PIPEDRIVE_API_KEY'],
            'description': 'Token de API do Pipedrive',
            'setup_url': 'https://developers.pipedrive.com/docs/api/v1/getting-started'
        },
        'zoho': {
            'required_env_vars': [
                'ZOHO_CLIENT_ID',
                'ZOHO_CLIENT_SECRET',
                'ZOHO_REFRESH_TOKEN'
            ],
            'description': 'Configuração OAuth2 do Zoho CRM',
            'setup_url': 'https://www.zoho.com/crm/developer/docs/api/v2/oauth-overview.html'
        },
        'rdstation': {
            'required_env_vars': [
                'RDSTATION_CLIENT_ID',
                'RDSTATION_CLIENT_SECRET'
            ],
            'description': 'Configuração OAuth2 do RD Station',
            'setup_url': 'https://developers.rdstation.com/pt-BR/reference/authentication'
        }
    }