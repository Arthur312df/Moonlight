# 🌙 Moonlight AI - Personal Desktop Assistant

A **Moonlight** é uma assistente pessoal de desktop inteligente, modular e operada por voz, desenvolvida em Python. Ela roda localmente no Windows integrando modelos de linguagem de grande escala (LLMs), reconhecimento de voz neural e automação de sistemas.

## 🚀 Funcionalidades da v1.0
- **🎧 Audição Neural Local:** Processamento de voz ultrarrápido e preciso com `faster-whisper` e filtro de ruído VAD.
- **🧠 Raciocínio Local (Ollama):** Utiliza modelos locais (como o Mistral) para interpretar intenções e gerar comandos estruturados.
- **🎮 Automação de Jogos & Apps:** Indexação automática de aplicativos do Windows e jogos da Steam (com suporte a lançamento direto por AppID).
- **💬 Comunicação Automatizada:** Envio automatizado de mensagens e recados no **WhatsApp Desktop** e **Discord** via atalhos universais de teclado e gerenciamento de foco de janelas (`pygetwindow`).
- **🌐 Pesquisa Web RAG:** Integração com busca na web (`ddgs`) para responder dúvidas atuais e abrir páginas automaticamente no navegador padrão.
- **🗣️ Síntese de Voz:** Resposta falada integrada com motores de áudio em português.

## 🛠️ Tecnologias Utilizadas
- Python
- Faster-Whisper
- Ollama (Mistral)
- PyAutoGUI & PyGetWindow
- SpeechRecognition / SoundDevice

## ⚙️ Instalação e Execução
1. Clone o repositório:
   ```bash
   git clone [https://github.com/SEU_USUARIO/Moonlight.git](https://github.com/SEU_USUARIO/Moonlight.git)
   cd Moonlight