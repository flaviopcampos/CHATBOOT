# 🏥 Chatbot Clínica Espaço Vida

Um chatbot inteligente e completo para clínicas de reabilitação, com suporte a múltiplas plataformas, análise de sentimentos, sistema de tickets e integração com CRM.

## 🚀 Funcionalidades

### ✅ Implementadas

- **🤖 Chatbot Inteligente**: Respostas contextuais sobre tratamentos, internação, convênios e emergências
- **🎫 Sistema de Tickets**: Criação automática de tickets baseada em urgência e palavras-chave
- **👨‍💼 Dashboard Administrativo**: Interface completa para gerenciamento
- **🔐 Sistema de Autenticação**: Login seguro para administradores
- **💾 Histórico Persistente**: Armazenamento completo de conversas
- **📱 Integração WhatsApp**: Via Twilio para atendimento direto
- **📲 Integração Telegram**: Bot nativo do Telegram
- **🌐 Widget para Website**: Código pronto para integração
- **❤️ Análise de Sentimentos**: Detecção automática de emoções e urgência
- **🌍 Suporte Multilíngue**: Português, Inglês, Espanhol, Francês, Alemão, Italiano
- **🔗 Integração CRM**: HubSpot, Salesforce, Pipedrive, Zoho, RD Station
- **📧 Notificações por Email**: Alertas automáticos para casos urgentes
- **📊 Relatórios e Estatísticas**: Análises detalhadas de atendimento
- **🔄 Backup Automático**: Sistema de backup dos dados

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Banco de Dados**: SQLite
- **IA**: OpenAI GPT, Google Gemini, Hugging Face
- **Integrações**: Twilio (WhatsApp), Telegram Bot API
- **Análise**: TextBlob, LangDetect
- **Autenticação**: Flask-Login, Bcrypt
- **Email**: SMTP (Gmail, Outlook, etc.)

## 📋 Pré-requisitos

- Python 3.8+
- Conta OpenAI (opcional)
- Conta Google Cloud (opcional)
- Conta Twilio (para WhatsApp)
- Token do Telegram Bot (para Telegram)
- Contas nos CRMs desejados
- Conta de email para notificações

## 🛠️ Instalação

### 1. Clone ou baixe o projeto
```bash
git clone <url-do-repositorio>
cd chatbot-clinica-reabilitacao
```

### 2. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações Básicas
SECRET_KEY=sua_chave_secreta_muito_segura_aqui
AI_PROVIDER=openai  # openai, gemini, huggingface

# OpenAI
OPENAI_API_KEY=sk-...

# Google Gemini
GEMINI_API_KEY=AIza...

# Hugging Face
HUGGINGFACE_API_KEY=hf_...

# Email (para notificações)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app
ADMIN_EMAIL=admin@clinica.com

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+5511999999999

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# CRM - HubSpot
HUBSPOT_API_KEY=pat-na1-...

# CRM - Salesforce
SALESFORCE_CLIENT_ID=...
SALESFORCE_CLIENT_SECRET=...
SALESFORCE_USERNAME=...
SALESFORCE_PASSWORD=...
SALESFORCE_SECURITY_TOKEN=...

# CRM - Pipedrive
PIPEDRIVE_API_KEY=...

# CRM - Zoho
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REFRESH_TOKEN=...

# CRM - RD Station
RDSTATION_CLIENT_ID=...
RDSTATION_CLIENT_SECRET=...
```

### 5. Execute a aplicação
```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 🎯 Como Usar

### 🔐 Primeiro Acesso
1. Acesse `http://localhost:5000/admin`
2. Faça login com as credenciais padrão:
   - **Usuário**: `admin`
   - **Senha**: `admin123`
3. **IMPORTANTE**: Altere a senha padrão imediatamente!

### 💬 Chatbot
1. Acesse `http://localhost:5000`
2. Digite sua pergunta no campo de texto
3. Pressione Enter ou clique em "Enviar"
4. O chatbot responderá automaticamente com análise de sentimentos

### 👨‍💼 Dashboard Administrativo
1. Acesse `http://localhost:5000/admin` (login necessário)
2. Visualize estatísticas em tempo real
3. Gerencie tickets criados
4. Configure integrações
5. Exporte conversas em CSV
6. Realize backups manuais

## 🧠 Conhecimento do Chatbot

O chatbot possui conhecimento especializado sobre:

### Tratamentos Oferecidos
- Desintoxicação médica supervisionada
- Terapia individual e em grupo
- Programa de 12 Passos
- Terapia Cognitivo-Comportamental (TCC)
- Terapia familiar
- Atividades terapêuticas (arte, música, esporte)
- Acompanhamento psiquiátrico
- Suporte nutricional

### Metodologias
- **Modelo Minnesota**: Baseado na filosofia dos 12 Passos
- **Abordagem Biopsicossocial**: Tratamento integral
- **Terapia Racional Emotiva**: Modificação de pensamentos
- **Comunidade Terapêutica**: Ambiente de apoio mútuo

### Tipos de Dependência
- Alcoolismo
- Dependência de drogas ilícitas
- Dependência de medicamentos
- Transtornos mentais associados

## 🔧 Configuração das Integrações

### 📱 WhatsApp (Twilio)
1. Crie uma conta no [Twilio](https://www.twilio.com)
2. Configure um número do WhatsApp Business
3. Obtenha suas credenciais:
   - Account SID
   - Auth Token
   - Número do WhatsApp
4. Configure o webhook: `https://seudominio.com/webhook/whatsapp`

### 📲 Telegram
1. Converse com [@BotFather](https://t.me/botfather)
2. Crie um novo bot com `/newbot`
3. Obtenha o token do bot
4. Configure o webhook: `https://seudominio.com/webhook/telegram`

### 🌐 Widget para Website
1. Acesse `/admin/integrations`
2. Configure as opções do widget
3. Copie o código HTML/JavaScript gerado
4. Cole no seu website antes do `</body>`

**Exemplo de integração:**
```html
<!-- Widget do Chatbot -->
<div id="chatbot-widget"></div>
<script>
(function() {
    var script = document.createElement('script');
    script.src = 'https://seudominio.com/static/widget.js';
    script.onload = function() {
        ChatbotWidget.init({
            apiUrl: 'https://seudominio.com',
            title: 'Clínica Espaço Vida',
            subtitle: 'Como podemos ajudar?',
            primaryColor: '#007bff',
            position: 'bottom-right'
        });
    };
    document.head.appendChild(script);
})();
</script>
```

### 🔗 Integração com CRM

#### HubSpot
1. Acesse [HubSpot Developers](https://developers.hubspot.com)
2. Crie uma aplicação privada
3. Obtenha a chave de API
4. Configure no dashboard: `/admin/crm`

#### Salesforce
1. Crie uma aplicação conectada no Salesforce
2. Obtenha Client ID, Client Secret e Security Token
3. Configure as credenciais no `.env`

#### Pipedrive
1. Acesse Configurações > Integrações > API
2. Gere uma chave de API
3. Configure no dashboard

#### Zoho CRM
1. Registre uma aplicação no Zoho Developer Console
2. Obtenha Client ID, Client Secret e Refresh Token
3. Configure as credenciais

#### RD Station
1. Acesse o painel de integrações do RD Station
2. Crie uma nova integração
3. Obtenha Client ID e Client Secret

## 📊 Funcionalidades do Dashboard

### 📈 Estatísticas
- **Conversas Hoje**: Número de conversas do dia atual
- **Tickets Abertos**: Quantidade de tickets pendentes
- **Análise de Sentimentos**: Distribuição de emoções
- **Idiomas**: Estatísticas de uso por idioma
- **Gráficos**: Visualização de dados por período

### 🎫 Gestão de Tickets
- **Lista Completa**: Todos os tickets com filtros
- **Detalhes**: Visualização completa da conversa
- **Status**: Atualização de status (Aberto/Em Andamento/Resolvido)
- **Prioridade**: Classificação automática por urgência e sentimento
- **Sincronização CRM**: Leads enviados automaticamente

### 🔧 Integrações
- **WhatsApp/Telegram**: Configuração e teste
- **Widget Website**: Geração de código
- **CRM**: Configuração e sincronização
- **Análise de Sentimentos**: Teste e configuração
- **Multilíngue**: Gerenciamento de idiomas

### 📤 Exportação
- **CSV**: Download de todas as conversas
- **Filtros**: Exportação por período
- **Dados Completos**: Inclui sentimentos e metadados

## ⚙️ Configurações Avançadas

### 📧 Configuração de Email

#### Gmail
1. Ative a verificação em duas etapas
2. Gere uma senha de aplicativo
3. Use a senha de aplicativo no `.env`

#### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USER=seu_email@outlook.com
EMAIL_PASSWORD=sua_senha
```

### 🤖 Configuração de IA

#### OpenAI
- Melhor qualidade de resposta
- Custo por uso
- Requer chave de API

#### Hugging Face
- Gratuito com limitações
- Boa qualidade
- Requer chave de API

#### Google Gemini
- Alternativa ao OpenAI
- Boa performance
- Requer chave de API

## 🔧 Estrutura do Projeto

```
chatbot-clinica-reabilitacao/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── .env                  # Configurações (não versionar)
├── README.md             # Este arquivo
└── templates/
    └── index.html        # Interface do usuário
```

## 🌍 Suporte Multilíngue

O sistema suporta os seguintes idiomas:
- 🇧🇷 Português (padrão)
- 🇺🇸 Inglês
- 🇪🇸 Espanhol
- 🇫🇷 Francês
- 🇩🇪 Alemão
- 🇮🇹 Italiano

### Como usar:
1. **Detecção automática**: O sistema detecta o idioma da mensagem
2. **URL específica**: Acesse `/chat/en` para inglês, `/chat/es` para espanhol, etc.
3. **Configuração**: Gerencie traduções em `/admin/multilingual`

## ❤️ Análise de Sentimentos

O sistema analisa automaticamente:
- **Polaridade**: Positivo, Neutro, Negativo
- **Subjetividade**: Objetivo vs Subjetivo
- **Urgência**: Detecta casos que precisam de atenção imediata
- **Palavras-chave**: Identifica termos importantes
- **Tom sugerido**: Recomenda o tom de resposta

## 🚨 Solução de Problemas

### Erro: "OpenAI API key not found"
- Verifique se o arquivo `.env` existe
- Confirme se a chave está correta
- Reinicie a aplicação

### Erro: "No module named 'xxx'"
```bash
pip install -r requirements.txt
```

### Chatbot não responde
- Verifique a conexão com internet
- Confirme se a chave da API está válida
- Verifique os logs no terminal

### WhatsApp/Telegram não funciona
- Verifique as credenciais no `.env`
- Confirme se os webhooks estão configurados
- Teste a conectividade com as APIs

### CRM não sincroniza
- Verifique as credenciais do CRM
- Confirme se as permissões estão corretas
- Teste a conexão em `/admin/crm`

### Dashboard não carrega
- Confirme se a aplicação está rodando
- Faça login em `/admin`
- Verifique se não há erros no console

### Emails não são enviados
- Verifique as configurações SMTP
- Confirme se a senha de aplicativo está correta
- Teste com outro provedor de email

## 🔒 Segurança

- **Nunca compartilhe** sua chave da API OpenAI
- **Não versione** o arquivo `.env` no Git
- **Use HTTPS** em produção
- **Configure rate limiting** para evitar abuso

## 📝 Changelog

### v3.0.0 - Sistema Completo com Integrações
- ✅ Sistema de autenticação seguro
- ✅ Integração WhatsApp via Twilio
- ✅ Bot nativo do Telegram
- ✅ Widget para websites
- ✅ Análise de sentimentos em tempo real
- ✅ Suporte a 6 idiomas
- ✅ Integração com 5 CRMs principais
- ✅ Dashboard administrativo avançado
- ✅ Histórico persistente completo

### v2.0.0 - Sistema Administrativo
- ✅ Dashboard administrativo completo
- ✅ Sistema de tickets automático
- ✅ Notificações por email
- ✅ Sistema de backup automático
- ✅ Exportação de dados em CSV
- ✅ Interface responsiva
- ✅ Múltiplos provedores de IA

### v1.0.0 - Versão Inicial
- ✅ Chatbot básico
- ✅ Respostas contextuais
- ✅ Interface web simples

## 📋 Roadmap

### ✅ Funcionalidades Implementadas
- [x] Sistema de autenticação de usuários
- [x] Histórico de conversas persistente
- [x] Integração com WhatsApp/Telegram
- [x] Integração com website
- [x] Dashboard administrativo
- [x] Análise de sentimentos
- [x] Suporte a múltiplos idiomas
- [x] Integração com sistemas de CRM

### 🚀 Funcionalidades Implementadas

- [x] **API REST completa** - Endpoints para conversas, tickets, análise de sentimento, tradução e CRM
- [x] **Chatbot por voz** - Reconhecimento e síntese de fala com suporte a múltiplos idiomas
- [x] **Integração com calendário** - Sistema completo de agendamentos com disponibilidade
- [x] **Relatórios avançados com BI** - Dashboard com métricas, KPIs e análises detalhadas
- [x] **Integração com mais CRMs** - Suporte a 8+ CRMs (Pipedrive, Zoho, RD Station, etc.)
- [x] **Integração com Instagram/Facebook** - Automação para redes sociais
- [x] **Sistema de avaliação de atendimento** - NPS, CSAT e alertas de qualidade

### 🔮 Funcionalidades Futuras

- [ ] Aplicativo mobile nativo
- [ ] Chatbot com IA de imagem
- [ ] Integração com WhatsApp Business API oficial
- [ ] Sistema de tickets avançado
- [ ] Automação de workflows
- [ ] Integração com sistemas de pagamento
- [ ] Chat em tempo real para múltiplos agentes
- [ ] Sistema de campanhas de marketing
- [ ] Análise preditiva de vendas
- [ ] Integração com sistemas ERP

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no repositório
- Entre em contato com a equipe de desenvolvimento

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

**Desenvolvido com ❤️ para ajudar pessoas em sua jornada de recuperação**