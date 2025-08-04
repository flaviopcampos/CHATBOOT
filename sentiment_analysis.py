from textblob import TextBlob
from langdetect import detect
import re

class SentimentAnalyzer:
    def __init__(self):
        self.emergency_keywords = [
            'suicídio', 'suicidio', 'matar', 'morrer', 'morte', 'acabar com tudo',
            'não aguento mais', 'nao aguento mais', 'desespero', 'desesperad',
            'overdose', 'intoxicação', 'intoxicacao', 'crise', 'emergência', 'emergencia',
            'socorro', 'ajuda urgente', 'urgente', 'agora', 'imediatamente'
        ]
        
        self.positive_keywords = [
            'obrigado', 'obrigada', 'agradeco', 'agradeço', 'grato', 'grata',
            'ajudou', 'melhor', 'bem', 'feliz', 'esperança', 'esperanca',
            'otimista', 'confiante', 'motivado', 'motivada', 'positivo', 'positiva'
        ]
        
        self.negative_keywords = [
            'triste', 'deprimido', 'deprimida', 'ansioso', 'ansiosa', 'preocupado',
            'preocupada', 'medo', 'receio', 'nervoso', 'nervosa', 'estressado',
            'estressada', 'cansado', 'cansada', 'frustrado', 'frustrada'
        ]
    
    def detect_language(self, text):
        """Detecta o idioma do texto"""
        try:
            return detect(text)
        except Exception:
            return 'pt'  # Default para português
    
    def clean_text(self, text):
        """Limpa e normaliza o texto"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove caracteres especiais excessivos
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '...', text)
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_sentiment(self, text):
        """Analisa o sentimento do texto"""
        if not text or len(text.strip()) < 3:
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'confidence': 0.0,
                'language': 'unknown',
                'emergency_level': 'low',
                'keywords_found': []
            }
        
        # Limpa o texto
        cleaned_text = self.clean_text(text)
        
        # Detecta idioma
        language = self.detect_language(cleaned_text)
        
        # Análise com TextBlob
        blob = TextBlob(cleaned_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determina sentimento baseado na polaridade
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calcula confiança baseada na subjetividade
        confidence = min(abs(polarity) + subjectivity, 1.0)
        
        # Verifica palavras-chave de emergência
        emergency_level = self._check_emergency_level(cleaned_text.lower())
        
        # Encontra palavras-chave relevantes
        keywords_found = self._find_keywords(cleaned_text.lower())
        
        # Ajusta sentimento baseado em palavras-chave
        if emergency_level == 'high':
            sentiment = 'emergency'
            confidence = max(confidence, 0.8)
        elif any(keyword in cleaned_text.lower() for keyword in self.positive_keywords):
            if sentiment != 'emergency':
                sentiment = 'positive'
                confidence = max(confidence, 0.6)
        elif any(keyword in cleaned_text.lower() for keyword in self.negative_keywords):
            if sentiment != 'emergency':
                sentiment = 'negative'
                confidence = max(confidence, 0.6)
        
        return {
            'sentiment': sentiment,
            'polarity': round(polarity, 3),
            'subjectivity': round(subjectivity, 3),
            'confidence': round(confidence, 3),
            'language': language,
            'emergency_level': emergency_level,
            'keywords_found': keywords_found
        }
    
    def _check_emergency_level(self, text):
        """Verifica o nível de emergência do texto"""
        emergency_count = sum(1 for keyword in self.emergency_keywords if keyword in text)
        
        if emergency_count >= 2:
            return 'high'
        elif emergency_count == 1:
            return 'medium'
        else:
            return 'low'
    
    def _find_keywords(self, text):
        """Encontra palavras-chave relevantes no texto"""
        found_keywords = []
        
        # Verifica palavras de emergência
        for keyword in self.emergency_keywords:
            if keyword in text:
                found_keywords.append(('emergency', keyword))
        
        # Verifica palavras positivas
        for keyword in self.positive_keywords:
            if keyword in text:
                found_keywords.append(('positive', keyword))
        
        # Verifica palavras negativas
        for keyword in self.negative_keywords:
            if keyword in text:
                found_keywords.append(('negative', keyword))
        
        return found_keywords
    
    def get_response_tone(self, sentiment_data):
        """Sugere o tom de resposta baseado na análise de sentimento"""
        sentiment = sentiment_data['sentiment']
        emergency_level = sentiment_data['emergency_level']
        
        if sentiment == 'emergency' or emergency_level == 'high':
            return {
                'tone': 'urgent_supportive',
                'priority': 'high',
                'suggested_actions': [
                    'Oferecer contato imediato',
                    'Mencionar atendimento 24h',
                    'Ser empático e acolhedor',
                    'Não deixar a pessoa sozinha'
                ]
            }
        elif sentiment == 'negative' or emergency_level == 'medium':
            return {
                'tone': 'empathetic_supportive',
                'priority': 'medium',
                'suggested_actions': [
                    'Demonstrar empatia',
                    'Oferecer esperança',
                    'Explicar opções de tratamento',
                    'Agendar avaliação'
                ]
            }
        elif sentiment == 'positive':
            return {
                'tone': 'encouraging_informative',
                'priority': 'normal',
                'suggested_actions': [
                    'Reforçar decisão positiva',
                    'Fornecer informações detalhadas',
                    'Facilitar próximos passos'
                ]
            }
        else:
            return {
                'tone': 'informative_neutral',
                'priority': 'normal',
                'suggested_actions': [
                    'Fornecer informações claras',
                    'Perguntar sobre necessidades específicas',
                    'Oferecer opções de contato'
                ]
            }
    
    def analyze_conversation_trend(self, messages):
        """Analisa a tendência de sentimento ao longo de uma conversa"""
        if not messages:
            return {'trend': 'neutral', 'progression': []}
        
        sentiments = []
        for message in messages:
            analysis = self.analyze_sentiment(message)
            sentiments.append({
                'sentiment': analysis['sentiment'],
                'polarity': analysis['polarity'],
                'emergency_level': analysis['emergency_level']
            })
        
        # Calcula tendência geral
        polarities = [s['polarity'] for s in sentiments]
        avg_polarity = sum(polarities) / len(polarities) if polarities else 0
        
        # Verifica se há emergência em qualquer mensagem
        has_emergency = any(s['emergency_level'] == 'high' for s in sentiments)
        
        if has_emergency:
            trend = 'emergency'
        elif avg_polarity > 0.1:
            trend = 'improving'
        elif avg_polarity < -0.1:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'average_polarity': round(avg_polarity, 3),
            'progression': sentiments,
            'has_emergency': has_emergency
        }