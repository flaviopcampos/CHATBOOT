import speech_recognition as sr
import pyttsx3
import threading
import queue
import json
from datetime import datetime
import os
import wave
import pyaudio
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename

# Blueprint para chat por voz
voice_bp = Blueprint('voice', __name__, url_prefix='/voice')

class VoiceChatbot:
    def __init__(self):
        # Inicializar reconhecimento de voz
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Inicializar síntese de voz
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # Configurações
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Calibrar microfone
        self.calibrate_microphone()
    
    def setup_tts(self):
        """Configurar engine de síntese de voz"""
        voices = self.tts_engine.getProperty('voices')
        
        # Tentar encontrar voz em português
        for voice in voices:
            if 'portuguese' in voice.name.lower() or 'brasil' in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        # Configurações de velocidade e volume
        self.tts_engine.setProperty('rate', 180)  # Velocidade da fala
        self.tts_engine.setProperty('volume', 0.9)  # Volume
    
    def calibrate_microphone(self):
        """Calibrar microfone para ruído ambiente"""
        try:
            with self.microphone as source:
                print("🎤 Calibrando microfone para ruído ambiente...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("✅ Calibração concluída")
        except Exception as e:
            print(f"⚠️ Erro na calibração: {e}")
    
    def listen_for_speech(self, timeout=5, phrase_time_limit=10):
        """Escutar e reconhecer fala"""
        try:
            with self.microphone as source:
                print("🎤 Escutando...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            print("🔄 Processando áudio...")
            
            # Tentar reconhecer em português primeiro
            try:
                text = self.recognizer.recognize_google(audio, language='pt-BR')
                return {'success': True, 'text': text, 'language': 'pt-BR'}
            except sr.UnknownValueError:
                # Tentar em inglês se português falhar
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    return {'success': True, 'text': text, 'language': 'en-US'}
                except sr.UnknownValueError:
                    return {'success': False, 'error': 'Não foi possível entender o áudio'}
            
        except sr.WaitTimeoutError:
            return {'success': False, 'error': 'Timeout - nenhuma fala detectada'}
        except sr.RequestError as e:
            return {'success': False, 'error': f'Erro no serviço de reconhecimento: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'Erro inesperado: {e}'}
    
    def speak_text(self, text, language='pt'):
        """Converter texto em fala"""
        try:
            # Ajustar voz baseado no idioma
            if language.startswith('en'):
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'english' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            print(f"🔊 Falando: {text[:50]}...")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Erro na síntese de voz: {e}")
            return {'success': False, 'error': str(e)}
    
    def process_voice_conversation(self, chatbot_instance):
        """Processar conversa completa por voz"""
        try:
            # Escutar entrada do usuário
            speech_result = self.listen_for_speech()
            
            if not speech_result['success']:
                return {
                    'success': False,
                    'error': speech_result['error']
                }
            
            user_text = speech_result['text']
            detected_language = speech_result['language']
            
            print(f"👤 Usuário disse: {user_text}")
            
            # Processar com chatbot
            bot_response = chatbot_instance.get_response(user_text, 'voice_user')
            
            # Falar resposta
            speak_result = self.speak_text(
                bot_response['response'], 
                detected_language
            )
            
            return {
                'success': True,
                'user_input': user_text,
                'bot_response': bot_response['response'],
                'language': detected_language,
                'sentiment': bot_response.get('sentiment'),
                'urgency': bot_response.get('urgency'),
                'speech_success': speak_result['success']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro no processamento: {str(e)}'
            }
    
    def save_audio_file(self, audio_data, filename):
        """Salvar arquivo de áudio"""
        try:
            audio_dir = 'voice_recordings'
            os.makedirs(audio_dir, exist_ok=True)
            
            filepath = os.path.join(audio_dir, secure_filename(filename))
            
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)  # 16kHz
                wf.writeframes(audio_data)
            
            return {'success': True, 'filepath': filepath}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_available_voices(self):
        """Obter vozes disponíveis no sistema"""
        try:
            voices = self.tts_engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            print(f"Erro ao obter vozes: {e}")
            return []
    
    def set_voice_settings(self, voice_id=None, rate=180, volume=0.9):
        """Configurar parâmetros de voz"""
        try:
            if voice_id:
                self.tts_engine.setProperty('voice', voice_id)
            
            self.tts_engine.setProperty('rate', rate)
            self.tts_engine.setProperty('volume', volume)
            
            return {'success': True, 'message': 'Configurações aplicadas'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Instância global do chatbot por voz
voice_chatbot = VoiceChatbot()

@voice_bp.route('/')
def voice_interface():
    """Interface web para chat por voz"""
    return render_template('voice_chat.html')

@voice_bp.route('/listen', methods=['POST'])
def listen_endpoint():
    """Endpoint para escutar fala"""
    try:
        timeout = request.json.get('timeout', 5)
        phrase_limit = request.json.get('phrase_limit', 10)
        
        result = voice_chatbot.listen_for_speech(timeout, phrase_limit)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro no endpoint de escuta: {str(e)}'
        }), 500

@voice_bp.route('/speak', methods=['POST'])
def speak_endpoint():
    """Endpoint para síntese de voz"""
    try:
        data = request.get_json()
        text = data.get('text')
        language = data.get('language', 'pt')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Texto é obrigatório'
            }), 400
        
        result = voice_chatbot.speak_text(text, language)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro na síntese de voz: {str(e)}'
        }), 500

@voice_bp.route('/conversation', methods=['POST'])
def voice_conversation():
    """Endpoint para conversa completa por voz"""
    try:
        from app import ClinicaChatbot
        chatbot = ClinicaChatbot()
        
        result = voice_chatbot.process_voice_conversation(chatbot)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro na conversa por voz: {str(e)}'
        }), 500

@voice_bp.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Upload e processamento de arquivo de áudio"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Arquivo de áudio não encontrado'
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        # Salvar arquivo temporariamente
        temp_dir = 'temp_audio'
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, secure_filename(audio_file.filename))
        audio_file.save(temp_path)
        
        # Processar áudio
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio, language='pt-BR')
            
            # Processar com chatbot
            from app import ClinicaChatbot
            chatbot = ClinicaChatbot()
            bot_response = chatbot.get_response(text, 'voice_upload_user')
            
            # Limpar arquivo temporário
            os.remove(temp_path)
            
            return jsonify({
                'success': True,
                'user_input': text,
                'bot_response': bot_response['response'],
                'sentiment': bot_response.get('sentiment'),
                'urgency': bot_response.get('urgency')
            })
            
        except sr.UnknownValueError:
            os.remove(temp_path)
            return jsonify({
                'success': False,
                'error': 'Não foi possível entender o áudio'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro no processamento de áudio: {str(e)}'
        }), 500

@voice_bp.route('/voices', methods=['GET'])
def get_voices():
    """Obter vozes disponíveis"""
    try:
        voices = voice_chatbot.get_available_voices()
        return jsonify({
            'success': True,
            'voices': voices
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter vozes: {str(e)}'
        }), 500

@voice_bp.route('/settings', methods=['POST'])
def update_voice_settings():
    """Atualizar configurações de voz"""
    try:
        data = request.get_json()
        voice_id = data.get('voice_id')
        rate = data.get('rate', 180)
        volume = data.get('volume', 0.9)
        
        result = voice_chatbot.set_voice_settings(voice_id, rate, volume)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao atualizar configurações: {str(e)}'
        }), 500

def init_voice_chat(app):
    """Inicializar chat por voz no app Flask"""
    app.register_blueprint(voice_bp)
    return app