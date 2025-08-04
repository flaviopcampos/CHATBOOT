import json
import os
from langdetect import detect
from datetime import datetime

class MultilingualSupport:
    def __init__(self):
        self.translations = {}
        self.default_language = 'pt'
        self.supported_languages = ['pt', 'en', 'es', 'fr', 'it']
        self.load_translations()
    
    def load_translations(self):
        """Carrega traduções dos arquivos JSON"""
        translations_dir = 'translations'
        
        # Criar diretório se não existir
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
        
        # Carregar traduções para cada idioma
        for lang in self.supported_languages:
            file_path = os.path.join(translations_dir, f'{lang}.json')
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    print(f"Erro ao carregar traduções para {lang}: {e}")
                    self.translations[lang] = {}
            else:
                # Criar arquivo de tradução padrão
                self.translations[lang] = self.get_default_translations(lang)
                self.save_translations(lang)
    
    def get_default_translations(self, language):
        """Retorna traduções padrão para um idioma"""
        translations = {
            'pt': {
                'welcome_message': 'Olá! Bem-vindo à Clínica Espaço Vida. Como posso ajudá-lo hoje?',
                'emergency_detected': 'Detectei que você pode estar passando por uma situação de emergência. Nossa equipe está disponível 24h.',
                'contact_info': 'Para contato imediato: (27) 999637447',
                'treatment_info': 'Oferecemos tratamento especializado em dependência química e saúde mental.',
                'insurance_accepted': 'Aceitamos diversos convênios médicos.',
                'schedule_appointment': 'Gostaria de agendar uma avaliação?',
                'thank_you': 'Obrigado por entrar em contato conosco.',
                'error_message': 'Desculpe, ocorreu um erro. Tente novamente.',
                'goodbye': 'Tenha um ótimo dia! Estamos aqui quando precisar.',
                'clinic_name': 'Clínica Espaço Vida',
                'specialties': {
                    'addiction': 'Dependência Química',
                    'mental_health': 'Saúde Mental',
                    'therapy': 'Terapia',
                    'rehabilitation': 'Reabilitação'
                },
                'treatments': {
                    'twelve_steps': '12 Passos',
                    'cbt': 'Terapia Cognitivo-Comportamental',
                    'minnesota_model': 'Modelo Minnesota',
                    'relapse_prevention': 'Prevenção de Recaída'
                },
                'substances': {
                    'alcohol': 'Álcool',
                    'cocaine': 'Cocaína',
                    'crack': 'Crack',
                    'marijuana': 'Maconha',
                    'medications': 'Medicamentos',
                    'gambling': 'Jogos Patológicos'
                },
                'team': {
                    'psychiatrists': 'Psiquiatras',
                    'psychologists': 'Psicólogos',
                    'therapists': 'Terapeutas',
                    'nurses': 'Enfermeiros',
                    'social_workers': 'Assistentes Sociais'
                },
                'schedule': {
                    'weekdays': 'Segunda a Sexta: 8h às 18h',
                    'saturday': 'Sábados: 8h às 12h',
                    'emergency': 'Emergências: 24 horas'
                }
            },
            'en': {
                'welcome_message': 'Hello! Welcome to Clínica Espaço Vida. How can I help you today?',
                'emergency_detected': 'I detected that you might be going through an emergency situation. Our team is available 24/7.',
                'contact_info': 'For immediate contact: +55 (27) 999637447',
                'treatment_info': 'We offer specialized treatment for chemical dependency and mental health.',
                'insurance_accepted': 'We accept various health insurance plans.',
                'schedule_appointment': 'Would you like to schedule an evaluation?',
                'thank_you': 'Thank you for contacting us.',
                'error_message': 'Sorry, an error occurred. Please try again.',
                'goodbye': 'Have a great day! We are here when you need us.',
                'clinic_name': 'Clínica Espaço Vida',
                'specialties': {
                    'addiction': 'Chemical Dependency',
                    'mental_health': 'Mental Health',
                    'therapy': 'Therapy',
                    'rehabilitation': 'Rehabilitation'
                },
                'treatments': {
                    'twelve_steps': '12 Steps',
                    'cbt': 'Cognitive Behavioral Therapy',
                    'minnesota_model': 'Minnesota Model',
                    'relapse_prevention': 'Relapse Prevention'
                },
                'substances': {
                    'alcohol': 'Alcohol',
                    'cocaine': 'Cocaine',
                    'crack': 'Crack',
                    'marijuana': 'Marijuana',
                    'medications': 'Medications',
                    'gambling': 'Pathological Gambling'
                },
                'team': {
                    'psychiatrists': 'Psychiatrists',
                    'psychologists': 'Psychologists',
                    'therapists': 'Therapists',
                    'nurses': 'Nurses',
                    'social_workers': 'Social Workers'
                },
                'schedule': {
                    'weekdays': 'Monday to Friday: 8am to 6pm',
                    'saturday': 'Saturdays: 8am to 12pm',
                    'emergency': 'Emergencies: 24 hours'
                }
            },
            'es': {
                'welcome_message': '¡Hola! Bienvenido a Clínica Espaço Vida. ¿Cómo puedo ayudarte hoy?',
                'emergency_detected': 'Detecté que podrías estar pasando por una situación de emergencia. Nuestro equipo está disponible 24h.',
                'contact_info': 'Para contacto inmediato: +55 (27) 999637447',
                'treatment_info': 'Ofrecemos tratamiento especializado en dependencia química y salud mental.',
                'insurance_accepted': 'Aceptamos varios seguros médicos.',
                'schedule_appointment': '¿Te gustaría programar una evaluación?',
                'thank_you': 'Gracias por contactarnos.',
                'error_message': 'Lo siento, ocurrió un error. Inténtalo de nuevo.',
                'goodbye': '¡Que tengas un gran día! Estamos aquí cuando nos necesites.',
                'clinic_name': 'Clínica Espaço Vida',
                'specialties': {
                    'addiction': 'Dependencia Química',
                    'mental_health': 'Salud Mental',
                    'therapy': 'Terapia',
                    'rehabilitation': 'Rehabilitación'
                },
                'treatments': {
                    'twelve_steps': '12 Pasos',
                    'cbt': 'Terapia Cognitivo-Conductual',
                    'minnesota_model': 'Modelo Minnesota',
                    'relapse_prevention': 'Prevención de Recaídas'
                },
                'substances': {
                    'alcohol': 'Alcohol',
                    'cocaine': 'Cocaína',
                    'crack': 'Crack',
                    'marijuana': 'Marihuana',
                    'medications': 'Medicamentos',
                    'gambling': 'Juego Patológico'
                },
                'team': {
                    'psychiatrists': 'Psiquiatras',
                    'psychologists': 'Psicólogos',
                    'therapists': 'Terapeutas',
                    'nurses': 'Enfermeros',
                    'social_workers': 'Trabajadores Sociales'
                },
                'schedule': {
                    'weekdays': 'Lunes a Viernes: 8h a 18h',
                    'saturday': 'Sábados: 8h a 12h',
                    'emergency': 'Emergencias: 24 horas'
                }
            },
            'fr': {
                'welcome_message': 'Bonjour! Bienvenue à la Clínica Espaço Vida. Comment puis-je vous aider aujourd\'hui?',
                'emergency_detected': 'J\'ai détecté que vous pourriez traverser une situation d\'urgence. Notre équipe est disponible 24h/24.',
                'contact_info': 'Pour un contact immédiat: +55 (27) 999637447',
                'treatment_info': 'Nous offrons un traitement spécialisé en dépendance chimique et santé mentale.',
                'insurance_accepted': 'Nous acceptons diverses assurances médicales.',
                'schedule_appointment': 'Souhaiteriez-vous programmer une évaluation?',
                'thank_you': 'Merci de nous avoir contactés.',
                'error_message': 'Désolé, une erreur s\'est produite. Veuillez réessayer.',
                'goodbye': 'Passez une excellente journée! Nous sommes là quand vous avez besoin de nous.',
                'clinic_name': 'Clínica Espaço Vida',
                'specialties': {
                    'addiction': 'Dépendance Chimique',
                    'mental_health': 'Santé Mentale',
                    'therapy': 'Thérapie',
                    'rehabilitation': 'Réhabilitation'
                },
                'treatments': {
                    'twelve_steps': '12 Étapes',
                    'cbt': 'Thérapie Cognitivo-Comportementale',
                    'minnesota_model': 'Modèle Minnesota',
                    'relapse_prevention': 'Prévention des Rechutes'
                },
                'substances': {
                    'alcohol': 'Alcool',
                    'cocaine': 'Cocaïne',
                    'crack': 'Crack',
                    'marijuana': 'Marijuana',
                    'medications': 'Médicaments',
                    'gambling': 'Jeu Pathologique'
                },
                'team': {
                    'psychiatrists': 'Psychiatres',
                    'psychologists': 'Psychologues',
                    'therapists': 'Thérapeutes',
                    'nurses': 'Infirmiers',
                    'social_workers': 'Travailleurs Sociaux'
                },
                'schedule': {
                    'weekdays': 'Lundi au Vendredi: 8h à 18h',
                    'saturday': 'Samedis: 8h à 12h',
                    'emergency': 'Urgences: 24 heures'
                }
            },
            'it': {
                'welcome_message': 'Ciao! Benvenuto alla Clínica Espaço Vida. Come posso aiutarti oggi?',
                'emergency_detected': 'Ho rilevato che potresti trovarti in una situazione di emergenza. Il nostro team è disponibile 24h.',
                'contact_info': 'Per contatto immediato: +55 (27) 999637447',
                'treatment_info': 'Offriamo trattamento specializzato per dipendenza chimica e salute mentale.',
                'insurance_accepted': 'Accettiamo varie assicurazioni mediche.',
                'schedule_appointment': 'Vorresti programmare una valutazione?',
                'thank_you': 'Grazie per averci contattato.',
                'error_message': 'Scusa, si è verificato un errore. Riprova.',
                'goodbye': 'Buona giornata! Siamo qui quando hai bisogno di noi.',
                'clinic_name': 'Clínica Espaço Vida',
                'specialties': {
                    'addiction': 'Dipendenza Chimica',
                    'mental_health': 'Salute Mentale',
                    'therapy': 'Terapia',
                    'rehabilitation': 'Riabilitazione'
                },
                'treatments': {
                    'twelve_steps': '12 Passi',
                    'cbt': 'Terapia Cognitivo-Comportamentale',
                    'minnesota_model': 'Modello Minnesota',
                    'relapse_prevention': 'Prevenzione delle Ricadute'
                },
                'substances': {
                    'alcohol': 'Alcol',
                    'cocaine': 'Cocaina',
                    'crack': 'Crack',
                    'marijuana': 'Marijuana',
                    'medications': 'Farmaci',
                    'gambling': 'Gioco Patologico'
                },
                'team': {
                    'psychiatrists': 'Psichiatri',
                    'psychologists': 'Psicologi',
                    'therapists': 'Terapeuti',
                    'nurses': 'Infermieri',
                    'social_workers': 'Assistenti Sociali'
                },
                'schedule': {
                    'weekdays': 'Lunedì al Venerdì: 8h alle 18h',
                    'saturday': 'Sabati: 8h alle 12h',
                    'emergency': 'Emergenze: 24 ore'
                }
            }
        }
        
        return translations.get(language, translations['pt'])
    
    def save_translations(self, language):
        """Salva traduções em arquivo JSON"""
        translations_dir = 'translations'
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
        
        file_path = os.path.join(translations_dir, f'{language}.json')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar traduções para {language}: {e}")
    
    def detect_language(self, text):
        """Detecta o idioma do texto"""
        try:
            detected = detect(text)
            return detected if detected in self.supported_languages else self.default_language
        except Exception:
            return self.default_language
    
    def get_translation(self, key, language=None, **kwargs):
        """Obtém tradução para uma chave específica"""
        if language is None:
            language = self.default_language
        
        if language not in self.supported_languages:
            language = self.default_language
        
        # Navegar pela estrutura aninhada de traduções
        translation = self.translations.get(language, {})
        
        # Suporte para chaves aninhadas (ex: 'specialties.addiction')
        keys = key.split('.')
        for k in keys:
            if isinstance(translation, dict) and k in translation:
                translation = translation[k]
            else:
                # Fallback para idioma padrão
                fallback = self.translations.get(self.default_language, {})
                for fk in keys:
                    if isinstance(fallback, dict) and fk in fallback:
                        fallback = fallback[fk]
                    else:
                        return key  # Retorna a chave se não encontrar tradução
                return fallback
        
        # Formatação com parâmetros
        if isinstance(translation, str) and kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                return translation
        
        return translation
    
    def translate_response(self, response, target_language):
        """Traduz uma resposta completa para o idioma alvo"""
        if target_language == self.default_language:
            return response
        
        # Mapeamento de frases comuns para tradução
        common_phrases = {
            'pt': {
                'Olá': self.get_translation('welcome_message', target_language).split('!')[0],
                'Obrigado': self.get_translation('thank_you', target_language).split(' ')[0],
                'Clínica Espaço Vida': self.get_translation('clinic_name', target_language),
                'emergência': self.get_translation('emergency_detected', target_language).split('.')[0],
                'tratamento': self.get_translation('treatment_info', target_language).split('.')[0],
                'convênio': self.get_translation('insurance_accepted', target_language).split('.')[0]
            }
        }
        
        translated_response = response
        
        # Substituir frases comuns
        if self.default_language in common_phrases:
            for pt_phrase, translation in common_phrases[self.default_language].items():
                if pt_phrase in response:
                    translated_response = translated_response.replace(pt_phrase, translation)
        
        return translated_response
    
    def get_system_prompt(self, language):
        """Retorna prompt do sistema no idioma especificado"""
        prompts = {
            'pt': """
            Você é um assistente virtual especializado em atendimento para uma clínica de reabilitação de dependentes químicos e saúde mental.
            Responda sempre em português brasileiro, de forma empática e profissional.
            """,
            'en': """
            You are a virtual assistant specialized in customer service for a chemical dependency and mental health rehabilitation clinic.
            Always respond in English, in an empathetic and professional manner.
            """,
            'es': """
            Eres un asistente virtual especializado en atención al cliente para una clínica de rehabilitación de dependencia química y salud mental.
            Responde siempre en español, de manera empática y profesional.
            """,
            'fr': """
            Vous êtes un assistant virtuel spécialisé dans le service client pour une clinique de réhabilitation de dépendance chimique et de santé mentale.
            Répondez toujours en français, de manière empathique et professionnelle.
            """,
            'it': """
            Sei un assistente virtuale specializzato nel servizio clienti per una clinica di riabilitazione per dipendenza chimica e salute mentale.
            Rispondi sempre in italiano, in modo empatico e professionale.
            """
        }
        
        return prompts.get(language, prompts['pt'])
    
    def get_supported_languages(self):
        """Retorna lista de idiomas suportados"""
        return {
            'pt': 'Português',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'it': 'Italiano'
        }
    
    def add_custom_translation(self, language, key, value):
        """Adiciona tradução personalizada"""
        if language not in self.translations:
            self.translations[language] = {}
        
        # Suporte para chaves aninhadas
        keys = key.split('.')
        current = self.translations[language]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.save_translations(language)
    
    def get_language_stats(self):
        """Retorna estatísticas de uso de idiomas"""
        # Esta função seria implementada com dados do banco
        # Por enquanto, retorna dados simulados
        return {
            'pt': {'usage_count': 150, 'percentage': 75.0},
            'en': {'usage_count': 30, 'percentage': 15.0},
            'es': {'usage_count': 15, 'percentage': 7.5},
            'fr': {'usage_count': 3, 'percentage': 1.5},
            'it': {'usage_count': 2, 'percentage': 1.0}
        }