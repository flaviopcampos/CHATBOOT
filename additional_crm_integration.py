from flask import Blueprint, request, jsonify, current_app
import requests
import json
from datetime import datetime, timedelta
import sqlite3
import logging
from typing import Dict, List, Optional, Any
import hashlib
import hmac
import base64
from urllib.parse import urlencode

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

additional_crm_bp = Blueprint('additional_crm', __name__, url_prefix='/additional-crm')

class CRMIntegrationManager:
    """Gerenciador de integrações com CRMs adicionais"""
    
    def __init__(self):
        self.integrations = {
            'pipedrive': PipedriveIntegration(),
            'zoho': ZohoIntegration(),
            'rd_station': RDStationIntegration(),
            'activecompaign': ActiveCampaignIntegration(),
            'mailchimp': MailchimpIntegration(),
            'freshsales': FreshsalesIntegration(),
            'agendor': AgendorIntegration(),
            'moskit': MoskitIntegration()
        }
    
    def get_integration(self, crm_type: str):
        """Obter integração específica"""
        return self.integrations.get(crm_type)
    
    def sync_contact(self, crm_type: str, contact_data: Dict) -> Dict:
        """Sincronizar contato com CRM específico"""
        integration = self.get_integration(crm_type)
        if integration:
            return integration.sync_contact(contact_data)
        return {'success': False, 'error': 'CRM não suportado'}
    
    def create_deal(self, crm_type: str, deal_data: Dict) -> Dict:
        """Criar negócio/oportunidade no CRM"""
        integration = self.get_integration(crm_type)
        if integration:
            return integration.create_deal(deal_data)
        return {'success': False, 'error': 'CRM não suportado'}
    
    def add_activity(self, crm_type: str, activity_data: Dict) -> Dict:
        """Adicionar atividade no CRM"""
        integration = self.get_integration(crm_type)
        if integration:
            return integration.add_activity(activity_data)
        return {'success': False, 'error': 'CRM não suportado'}

class BaseCRMIntegration:
    """Classe base para integrações CRM"""
    
    def __init__(self):
        self.base_url = ""
        self.api_key = ""
        self.headers = {}
    
    def authenticate(self) -> bool:
        """Autenticar com o CRM"""
        raise NotImplementedError
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato"""
        raise NotImplementedError
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio"""
        raise NotImplementedError
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade"""
        raise NotImplementedError
    
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Fazer requisição HTTP"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                return {'success': False, 'error': 'Método HTTP não suportado'}
            
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {str(e)}")
            return {'success': False, 'error': str(e)}

class PipedriveIntegration(BaseCRMIntegration):
    """Integração com Pipedrive"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.pipedrive.com/v1"
        self.api_key = self.get_api_key('pipedrive')
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def get_api_key(self, crm_type: str) -> str:
        """Obter API key do banco de dados"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_key FROM crm_configs WHERE crm_type = ? AND active = 1",
                (crm_type,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API key: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com Pipedrive"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        # Verificar se pessoa já existe
        search_result = self.make_request(
            'GET',
            f"persons/search?term={contact_data.get('email', '')}&api_token={self.api_key}"
        )
        
        person_data = {
            'name': contact_data.get('name', ''),
            'email': [contact_data.get('email', '')],
            'phone': [contact_data.get('phone', '')],
            'org_id': contact_data.get('organization_id')
        }
        
        if search_result['success'] and search_result['data'].get('data'):
            # Atualizar pessoa existente
            person_id = search_result['data']['data'][0]['id']
            return self.make_request(
                'PUT',
                f"persons/{person_id}?api_token={self.api_key}",
                person_data
            )
        else:
            # Criar nova pessoa
            return self.make_request(
                'POST',
                f"persons?api_token={self.api_key}",
                person_data
            )
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no Pipedrive"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        deal_payload = {
            'title': deal_data.get('title', 'Novo Negócio'),
            'value': deal_data.get('value', 0),
            'currency': deal_data.get('currency', 'BRL'),
            'person_id': deal_data.get('person_id'),
            'org_id': deal_data.get('organization_id'),
            'pipeline_id': deal_data.get('pipeline_id'),
            'stage_id': deal_data.get('stage_id'),
            'status': 'open',
            'expected_close_date': deal_data.get('expected_close_date')
        }
        
        return self.make_request(
            'POST',
            f"deals?api_token={self.api_key}",
            deal_payload
        )
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no Pipedrive"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        activity_payload = {
            'subject': activity_data.get('subject', 'Atividade do Chatbot'),
            'type': activity_data.get('type', 'call'),
            'due_date': activity_data.get('due_date', datetime.now().strftime('%Y-%m-%d')),
            'due_time': activity_data.get('due_time', '09:00'),
            'person_id': activity_data.get('person_id'),
            'deal_id': activity_data.get('deal_id'),
            'note': activity_data.get('note', '')
        }
        
        return self.make_request(
            'POST',
            f"activities?api_token={self.api_key}",
            activity_payload
        )

class ZohoIntegration(BaseCRMIntegration):
    """Integração com Zoho CRM"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.zohoapis.com/crm/v2"
        self.access_token = self.get_access_token()
        self.headers = {
            'Authorization': f'Zoho-oauthtoken {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_access_token(self) -> str:
        """Obter access token do Zoho"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT access_token FROM crm_configs WHERE crm_type = 'zoho' AND active = 1"
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter access token: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com Zoho"""
        if not self.access_token:
            return {'success': False, 'error': 'Access token não configurado'}
        
        contact_payload = {
            "data": [{
                "First_Name": contact_data.get('first_name', ''),
                "Last_Name": contact_data.get('last_name', ''),
                "Email": contact_data.get('email', ''),
                "Phone": contact_data.get('phone', ''),
                "Lead_Source": "Chatbot",
                "Description": contact_data.get('description', '')
            }]
        }
        
        return self.make_request('POST', 'Contacts', contact_payload)
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no Zoho"""
        if not self.access_token:
            return {'success': False, 'error': 'Access token não configurado'}
        
        deal_payload = {
            "data": [{
                "Deal_Name": deal_data.get('name', 'Novo Negócio'),
                "Amount": deal_data.get('amount', 0),
                "Stage": deal_data.get('stage', 'Qualification'),
                "Contact_Name": deal_data.get('contact_id'),
                "Closing_Date": deal_data.get('closing_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
                "Description": deal_data.get('description', '')
            }]
        }
        
        return self.make_request('POST', 'Deals', deal_payload)
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no Zoho"""
        if not self.access_token:
            return {'success': False, 'error': 'Access token não configurado'}
        
        activity_payload = {
            "data": [{
                "Subject": activity_data.get('subject', 'Atividade do Chatbot'),
                "Activity_Type_Id": activity_data.get('type_id', '1'),
                "Due_Date": activity_data.get('due_date', datetime.now().strftime('%Y-%m-%d')),
                "What_Id": activity_data.get('what_id'),
                "Who_Id": activity_data.get('who_id'),
                "Description": activity_data.get('description', '')
            }]
        }
        
        return self.make_request('POST', 'Tasks', activity_payload)

class RDStationIntegration(BaseCRMIntegration):
    """Integração com RD Station"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.rd.services"
        self.access_token = self.get_access_token()
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_access_token(self) -> str:
        """Obter access token do RD Station"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT access_token FROM crm_configs WHERE crm_type = 'rd_station' AND active = 1"
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter access token: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com RD Station"""
        if not self.access_token:
            return {'success': False, 'error': 'Access token não configurado'}
        
        contact_payload = {
            "email": contact_data.get('email', ''),
            "name": contact_data.get('name', ''),
            "mobile_phone": contact_data.get('phone', ''),
            "tags": ["chatbot", "lead"],
            "cf_custom_field_api_identifier": contact_data.get('custom_field', ''),
            "legal_bases": [{
                "category": "communications",
                "type": "consent",
                "status": "granted"
            }]
        }
        
        return self.make_request('PATCH', 'platform/contacts/email:' + contact_data.get('email', ''), contact_payload)
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no RD Station"""
        if not self.access_token:
            return {'success': False, 'error': 'Access token não configurado'}
        
        deal_payload = {
            "deal": {
                "name": deal_data.get('name', 'Novo Negócio'),
                "deal_stage_id": deal_data.get('stage_id', 1),
                "deal_source_id": deal_data.get('source_id', 1),
                "contact_id": deal_data.get('contact_id'),
                "user_id": deal_data.get('user_id'),
                "amount": deal_data.get('amount', 0),
                "prediction_date": deal_data.get('prediction_date')
            }
        }
        
        return self.make_request('POST', 'platform/deals', deal_payload)
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no RD Station"""
        # RD Station não tem API específica para atividades
        # Vamos criar um evento personalizado
        event_payload = {
            "event_type": "CHATBOT_ACTIVITY",
            "event_family": "CDP",
            "payload": {
                "email": activity_data.get('email', ''),
                "activity_type": activity_data.get('type', 'interaction'),
                "activity_description": activity_data.get('description', ''),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return self.make_request('POST', 'platform/events', event_payload)

class ActiveCampaignIntegration(BaseCRMIntegration):
    """Integração com ActiveCampaign"""
    
    def __init__(self):
        super().__init__()
        self.api_url = self.get_api_url()
        self.api_key = self.get_api_key('activecompaign')
        self.base_url = f"https://{self.api_url}.api-us1.com/api/3"
        self.headers = {
            'Api-Token': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_api_url(self) -> str:
        """Obter URL da API do ActiveCampaign"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_url FROM crm_configs WHERE crm_type = 'activecompaign' AND active = 1"
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API URL: {str(e)}")
            return ""
    
    def get_api_key(self, crm_type: str) -> str:
        """Obter API key do banco de dados"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_key FROM crm_configs WHERE crm_type = ? AND active = 1",
                (crm_type,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API key: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com ActiveCampaign"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        contact_payload = {
            "contact": {
                "email": contact_data.get('email', ''),
                "firstName": contact_data.get('first_name', ''),
                "lastName": contact_data.get('last_name', ''),
                "phone": contact_data.get('phone', ''),
                "fieldValues": [
                    {
                        "field": "1",  # Campo personalizado
                        "value": "Chatbot Lead"
                    }
                ]
            }
        }
        
        return self.make_request('POST', 'contacts', contact_payload)
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no ActiveCampaign"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        deal_payload = {
            "deal": {
                "title": deal_data.get('title', 'Novo Negócio'),
                "description": deal_data.get('description', ''),
                "account": deal_data.get('account_id'),
                "contact": deal_data.get('contact_id'),
                "value": deal_data.get('value', 0),
                "currency": deal_data.get('currency', 'brl'),
                "group": deal_data.get('pipeline_id', '1'),
                "stage": deal_data.get('stage_id', '1'),
                "owner": deal_data.get('owner_id', '1'),
                "status": 0  # 0 = open, 1 = won, 2 = lost
            }
        }
        
        return self.make_request('POST', 'deals', deal_payload)
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no ActiveCampaign"""
        # ActiveCampaign usa "deal notes" para atividades
        note_payload = {
            "note": {
                "note": activity_data.get('note', 'Atividade do Chatbot'),
                "reltype": activity_data.get('rel_type', 'Deal'),
                "relid": activity_data.get('rel_id')
            }
        }
        
        return self.make_request('POST', 'notes', note_payload)

class MailchimpIntegration(BaseCRMIntegration):
    """Integração com Mailchimp"""
    
    def __init__(self):
        super().__init__()
        self.api_key = self.get_api_key('mailchimp')
        self.datacenter = self.api_key.split('-')[-1] if self.api_key else 'us1'
        self.base_url = f"https://{self.datacenter}.api.mailchimp.com/3.0"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_api_key(self, crm_type: str) -> str:
        """Obter API key do banco de dados"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_key FROM crm_configs WHERE crm_type = ? AND active = 1",
                (crm_type,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API key: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com Mailchimp"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        list_id = contact_data.get('list_id', self.get_default_list_id())
        email_hash = hashlib.md5(contact_data.get('email', '').lower().encode()).hexdigest()
        
        member_payload = {
            "email_address": contact_data.get('email', ''),
            "status": "subscribed",
            "merge_fields": {
                "FNAME": contact_data.get('first_name', ''),
                "LNAME": contact_data.get('last_name', ''),
                "PHONE": contact_data.get('phone', '')
            },
            "tags": ["chatbot", "lead"]
        }
        
        return self.make_request('PUT', f'lists/{list_id}/members/{email_hash}', member_payload)
    
    def get_default_list_id(self) -> str:
        """Obter ID da lista padrão"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT list_id FROM crm_configs WHERE crm_type = 'mailchimp' AND active = 1"
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter list ID: {str(e)}")
            return ""
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Mailchimp não suporta deals diretamente"""
        return {'success': False, 'error': 'Mailchimp não suporta criação de deals'}
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade como evento no Mailchimp"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        event_payload = {
            "name": activity_data.get('event_name', 'chatbot_activity'),
            "properties": {
                "activity_type": activity_data.get('type', 'interaction'),
                "description": activity_data.get('description', ''),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        email_hash = hashlib.md5(activity_data.get('email', '').lower().encode()).hexdigest()
        list_id = activity_data.get('list_id', self.get_default_list_id())
        
        return self.make_request(
            'POST',
            f'lists/{list_id}/members/{email_hash}/events',
            event_payload
        )

class FreshsalesIntegration(BaseCRMIntegration):
    """Integração com Freshsales"""
    
    def __init__(self):
        super().__init__()
        self.domain = self.get_domain()
        self.api_key = self.get_api_key('freshsales')
        self.base_url = f"https://{self.domain}.freshsales.io/api"
        self.headers = {
            'Authorization': f'Token token={self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_domain(self) -> str:
        """Obter domínio do Freshsales"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT domain FROM crm_configs WHERE crm_type = 'freshsales' AND active = 1"
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter domínio: {str(e)}")
            return ""
    
    def get_api_key(self, crm_type: str) -> str:
        """Obter API key do banco de dados"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_key FROM crm_configs WHERE crm_type = ? AND active = 1",
                (crm_type,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API key: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com Freshsales"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        contact_payload = {
            "contact": {
                "first_name": contact_data.get('first_name', ''),
                "last_name": contact_data.get('last_name', ''),
                "email": contact_data.get('email', ''),
                "mobile_number": contact_data.get('phone', ''),
                "lead_source_id": contact_data.get('lead_source_id', 1),
                "tags": ["chatbot", "lead"]
            }
        }
        
        return self.make_request('POST', 'contacts', contact_payload)
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no Freshsales"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        deal_payload = {
            "deal": {
                "name": deal_data.get('name', 'Novo Negócio'),
                "amount": deal_data.get('amount', 0),
                "deal_stage_id": deal_data.get('stage_id', 1),
                "deal_reason_id": deal_data.get('reason_id', 1),
                "deal_type_id": deal_data.get('type_id', 1),
                "contact_id": deal_data.get('contact_id'),
                "sales_account_id": deal_data.get('account_id'),
                "owner_id": deal_data.get('owner_id'),
                "expected_close": deal_data.get('expected_close')
            }
        }
        
        return self.make_request('POST', 'deals', deal_payload)
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no Freshsales"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        activity_payload = {
            "sales_activity": {
                "title": activity_data.get('title', 'Atividade do Chatbot'),
                "description": activity_data.get('description', ''),
                "sales_activity_type_id": activity_data.get('type_id', 1),
                "targetable_type": activity_data.get('targetable_type', 'Contact'),
                "targetable_id": activity_data.get('targetable_id'),
                "owner_id": activity_data.get('owner_id'),
                "from_date": activity_data.get('from_date', datetime.now().isoformat()),
                "end_date": activity_data.get('end_date', datetime.now().isoformat())
            }
        }
        
        return self.make_request('POST', 'sales_activities', activity_payload)

class AgendorIntegration(BaseCRMIntegration):
    """Integração com Agendor"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.agendor.com.br/v3"
        self.api_key = self.get_api_key('agendor')
        self.headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_api_key(self, crm_type: str) -> str:
        """Obter API key do banco de dados"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_key FROM crm_configs WHERE crm_type = ? AND active = 1",
                (crm_type,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API key: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com Agendor"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        person_payload = {
            "name": contact_data.get('name', ''),
            "cpf": contact_data.get('cpf', ''),
            "description": contact_data.get('description', ''),
            "birthday": contact_data.get('birthday', ''),
            "ownerUser": contact_data.get('owner_user_id'),
            "contact": {
                "email": contact_data.get('email', ''),
                "work": contact_data.get('phone', ''),
                "mobile": contact_data.get('mobile', ''),
                "fax": contact_data.get('fax', ''),
                "facebook": contact_data.get('facebook', ''),
                "twitter": contact_data.get('twitter', ''),
                "instagram": contact_data.get('instagram', ''),
                "linked_in": contact_data.get('linkedin', ''),
                "skype": contact_data.get('skype', ''),
                "website": contact_data.get('website', '')
            },
            "address": {
                "postal_code": contact_data.get('postal_code', ''),
                "country": contact_data.get('country', 'Brasil'),
                "district": contact_data.get('district', ''),
                "state": contact_data.get('state', ''),
                "street_name": contact_data.get('street_name', ''),
                "street_number": contact_data.get('street_number', ''),
                "additional_info": contact_data.get('additional_info', ''),
                "city": contact_data.get('city', '')
            }
        }
        
        return self.make_request('POST', 'people', person_payload)
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no Agendor"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        deal_payload = {
            "title": deal_data.get('title', 'Novo Negócio'),
            "description": deal_data.get('description', ''),
            "value": deal_data.get('value', 0),
            "person": deal_data.get('person_id'),
            "organization": deal_data.get('organization_id'),
            "products": deal_data.get('products', []),
            "category": deal_data.get('category_id'),
            "stage": deal_data.get('stage_id'),
            "ownerUser": deal_data.get('owner_user_id'),
            "startDate": deal_data.get('start_date', datetime.now().strftime('%Y-%m-%d')),
            "endDate": deal_data.get('end_date')
        }
        
        return self.make_request('POST', 'deals', deal_payload)
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no Agendor"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        task_payload = {
            "text": activity_data.get('text', 'Atividade do Chatbot'),
            "type": activity_data.get('type', 1),  # 1 = call, 2 = email, etc.
            "datetime": activity_data.get('datetime', datetime.now().isoformat()),
            "done": activity_data.get('done', False),
            "deal": activity_data.get('deal_id'),
            "person": activity_data.get('person_id'),
            "organization": activity_data.get('organization_id'),
            "user": activity_data.get('user_id')
        }
        
        return self.make_request('POST', 'tasks', task_payload)

class MoskitIntegration(BaseCRMIntegration):
    """Integração com Moskit CRM"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.moskitcrm.com/v2"
        self.api_key = self.get_api_key('moskit')
        self.headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_api_key(self, crm_type: str) -> str:
        """Obter API key do banco de dados"""
        try:
            conn = sqlite3.connect('chatbot.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT api_key FROM crm_configs WHERE crm_type = ? AND active = 1",
                (crm_type,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else ""
        except Exception as e:
            logger.error(f"Erro ao obter API key: {str(e)}")
            return ""
    
    def sync_contact(self, contact_data: Dict) -> Dict:
        """Sincronizar contato com Moskit"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        contact_payload = {
            "name": contact_data.get('name', ''),
            "email": contact_data.get('email', ''),
            "phone": contact_data.get('phone', ''),
            "mobile": contact_data.get('mobile', ''),
            "company_name": contact_data.get('company_name', ''),
            "job_title": contact_data.get('job_title', ''),
            "website": contact_data.get('website', ''),
            "address": contact_data.get('address', ''),
            "city": contact_data.get('city', ''),
            "state": contact_data.get('state', ''),
            "country": contact_data.get('country', 'Brasil'),
            "zip_code": contact_data.get('zip_code', ''),
            "tags": "chatbot,lead",
            "custom_fields": contact_data.get('custom_fields', {})
        }
        
        return self.make_request('POST', 'contacts', contact_payload)
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """Criar negócio no Moskit"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        deal_payload = {
            "title": deal_data.get('title', 'Novo Negócio'),
            "description": deal_data.get('description', ''),
            "value": deal_data.get('value', 0),
            "contact_id": deal_data.get('contact_id'),
            "company_id": deal_data.get('company_id'),
            "funnel_step_id": deal_data.get('funnel_step_id', 1),
            "user_id": deal_data.get('user_id'),
            "expected_closure": deal_data.get('expected_closure'),
            "custom_fields": deal_data.get('custom_fields', {})
        }
        
        return self.make_request('POST', 'deals', deal_payload)
    
    def add_activity(self, activity_data: Dict) -> Dict:
        """Adicionar atividade no Moskit"""
        if not self.api_key:
            return {'success': False, 'error': 'API key não configurada'}
        
        activity_payload = {
            "title": activity_data.get('title', 'Atividade do Chatbot'),
            "description": activity_data.get('description', ''),
            "activity_type_id": activity_data.get('type_id', 1),
            "contact_id": activity_data.get('contact_id'),
            "deal_id": activity_data.get('deal_id'),
            "user_id": activity_data.get('user_id'),
            "due_date": activity_data.get('due_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "done": activity_data.get('done', False)
        }
        
        return self.make_request('POST', 'activities', activity_payload)

# Instância global do gerenciador
crm_manager = CRMIntegrationManager()

# Rotas da API
@additional_crm_bp.route('/sync-contact', methods=['POST'])
def sync_contact():
    """Sincronizar contato com CRM"""
    try:
        data = request.get_json()
        crm_type = data.get('crm_type')
        contact_data = data.get('contact_data', {})
        
        if not crm_type:
            return jsonify({'success': False, 'error': 'Tipo de CRM não especificado'})
        
        result = crm_manager.sync_contact(crm_type, contact_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar contato: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@additional_crm_bp.route('/create-deal', methods=['POST'])
def create_deal():
    """Criar negócio no CRM"""
    try:
        data = request.get_json()
        crm_type = data.get('crm_type')
        deal_data = data.get('deal_data', {})
        
        if not crm_type:
            return jsonify({'success': False, 'error': 'Tipo de CRM não especificado'})
        
        result = crm_manager.create_deal(crm_type, deal_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao criar negócio: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@additional_crm_bp.route('/add-activity', methods=['POST'])
def add_activity():
    """Adicionar atividade no CRM"""
    try:
        data = request.get_json()
        crm_type = data.get('crm_type')
        activity_data = data.get('activity_data', {})
        
        if not crm_type:
            return jsonify({'success': False, 'error': 'Tipo de CRM não especificado'})
        
        result = crm_manager.add_activity(crm_type, activity_data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar atividade: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@additional_crm_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Testar conexão com CRM"""
    try:
        data = request.get_json()
        crm_type = data.get('crm_type')
        
        if not crm_type:
            return jsonify({'success': False, 'error': 'Tipo de CRM não especificado'})
        
        integration = crm_manager.get_integration(crm_type)
        if not integration:
            return jsonify({'success': False, 'error': 'CRM não suportado'})
        
        # Teste básico fazendo uma requisição simples
        if hasattr(integration, 'test_connection'):
            result = integration.test_connection()
        else:
            # Teste genérico
            result = integration.make_request('GET', '')
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@additional_crm_bp.route('/supported-crms', methods=['GET'])
def get_supported_crms():
    """Obter lista de CRMs suportados"""
    try:
        crms = [
            {
                'id': 'pipedrive',
                'name': 'Pipedrive',
                'description': 'CRM focado em vendas com pipeline visual',
                'features': ['contacts', 'deals', 'activities', 'organizations']
            },
            {
                'id': 'zoho',
                'name': 'Zoho CRM',
                'description': 'Suite completa de CRM e automação',
                'features': ['contacts', 'deals', 'tasks', 'campaigns']
            },
            {
                'id': 'rd_station',
                'name': 'RD Station',
                'description': 'Plataforma de automação de marketing',
                'features': ['contacts', 'deals', 'events', 'campaigns']
            },
            {
                'id': 'activecompaign',
                'name': 'ActiveCampaign',
                'description': 'Automação de marketing e vendas',
                'features': ['contacts', 'deals', 'automations', 'campaigns']
            },
            {
                'id': 'mailchimp',
                'name': 'Mailchimp',
                'description': 'Plataforma de email marketing',
                'features': ['contacts', 'campaigns', 'automations', 'events']
            },
            {
                'id': 'freshsales',
                'name': 'Freshsales',
                'description': 'CRM da Freshworks',
                'features': ['contacts', 'deals', 'activities', 'accounts']
            },
            {
                'id': 'agendor',
                'name': 'Agendor',
                'description': 'CRM brasileiro para pequenas e médias empresas',
                'features': ['contacts', 'deals', 'tasks', 'organizations']
            },
            {
                'id': 'moskit',
                'name': 'Moskit CRM',
                'description': 'CRM brasileiro com foco em vendas',
                'features': ['contacts', 'deals', 'activities', 'companies']
            }
        ]
        
        return jsonify({'success': True, 'crms': crms})
        
    except Exception as e:
        logger.error(f"Erro ao obter CRMs suportados: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Função para inicializar tabelas
def init_additional_crm_tables():
    """Inicializar tabelas para CRMs adicionais"""
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # Tabela de configurações de CRM
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crm_type TEXT NOT NULL,
                api_key TEXT,
                api_url TEXT,
                access_token TEXT,
                refresh_token TEXT,
                domain TEXT,
                list_id TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de sincronizações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_syncs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crm_type TEXT NOT NULL,
                sync_type TEXT NOT NULL,
                local_id TEXT,
                remote_id TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de logs de integração
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crm_integration_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crm_type TEXT NOT NULL,
                action TEXT NOT NULL,
                request_data TEXT,
                response_data TEXT,
                status TEXT,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Tabelas de CRM adicionais inicializadas com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar tabelas de CRM: {str(e)}")

if __name__ == '__main__':
    init_additional_crm_tables()