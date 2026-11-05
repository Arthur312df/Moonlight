# 🌙 Moonlight AI - Personal Desktop Assistant

A **Moonlight** é uma assistente pessoal de desktop inteligente, modular e operada por voz, desenvolvida em Python. Ela roda localmente no Windows integrando modelos de linguagem de grande escala (LLMs), reconhecimento de voz neural e automação de sistemas.

## 🚀 Funcionalidades da v2.2
- **🎧 Audição Neural Local:** Processamento de voz ultrarrápido e preciso com `faster-whisper` (modo small) e filtro de ruído VAD.
- **🧠 Raciocínio Local (Ollama):** Utiliza modelos locais (como o Mistral) para interpretar intenções, acionar atalhos e gerar comandos estruturados.
- **📅 Gestão do Google Calendar:** 
  - Agendamento de compromissos e reuniões por comando de voz.
  - Cancelamento e remoção de eventos diretamente por voz.
  - Monitor em background (Thread dedicada) que verifica a agenda e emite alertas por voz **5 minutos antes** de cada compromisso começar.
  - Lembretes automáticos nativos injetados via API.
- **💬 Comunicação Automatizada (WhatsApp & Discord):** Envio de mensagens e leitura inteligente de conversas sem introduções robóticas, com foco total na naturalidade.
- **🎮 Automação de Jogos & Apps:** Indexação automática de aplicativos do Windows e jogos da Steam (com lançamento direto por AppID).
- **🌐 Pesquisa Web RAG:** Busca na web para responder dúvidas atuais e abrir páginas no navegador padrão.
- **🗣️ Síntese de Voz & Interface Visual:** Resposta falada otimizada com feedback visual dinâmico na interface (transição correta para o estado `speaking`).

## 🛠️ Tecnologias Utilizadas
- Python
- Faster-Whisper
- Ollama (Mistral)
- Google Calendar API (OAuth2)
- PyAutoGUI, PyGetWindow & Pycaw
- WhatsApp Desktop Automation

## ⚙️ Instalação e Execução
1. Clone o repositório:
   ```bash
   git clone [https://github.com/arthur312df/Moonlight.git](https://github.com/arthur312df/Moonlight.git)
   cd Moonlight