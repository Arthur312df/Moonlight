import os
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("phonemizer").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("faster_whisper").setLevel(logging.ERROR)

import requests
import numpy as np
import time
import subprocess
import pyautogui
import pyperclip
import re
import sys
from faster_whisper import WhisperModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Sistemas.subsistema_web import SubsistemaWeb
from Sistemas.subsistema_pc import SubsistemaPC

class CerebroLocal:
    def __init__(self, modelo="mistral"):
        self.modelo = modelo
        self.url_ollama = "http://localhost:11434/api/generate"
        
        print("🎧 [Cérebro]: A carregar audição neural na CPU (Faster-Whisper)...")
        self.whisper = WhisperModel("base", device="cpu", compute_type="int8")
        print("⚡ [Faster-Whisper]: Carregado com sucesso!")

        # Vocabulário de contexto reforçado
        self.prompt_vocabulario = (
            "Moonlight, Arthur, Jô, Marcelo Frigo, Discord, WhatsApp, Steam, "
            "Overwatch 2, League of Legends, Notepad, Google Chrome, abre o WhatsApp, abre o aplicativo."
        )
        
        self.web = SubsistemaWeb()
        self.pc = SubsistemaPC()
        
        self.apps_indexados = {
            'steam': 'steam://open/main',
            'league of legends': r"C:\Riot Games\League of Legends\LeagueClient.exe",
            'lol': r"C:\Riot Games\League of Legends\LeagueClient.exe",
            'notepad': 'notepad.exe',
            'bloco de notas': 'notepad.exe',
            'calculadora': 'calc.exe',
            'chrome': 'start chrome',
            'google chrome': 'start chrome',
            'discord': 'discord:',
            'whatsapp': 'whatsapp:',
            'zap': 'whatsapp:'
        }
        self.varrer_programas_pc()

        self.system_prompt = (
            "Tu és a Moonlight, a inteligência artificial e assistente pessoal do Arthur.\n"
            "Responde SEMPRE em Português do Brasil de forma curta e direta.\n\n"
            "REGRA PARA MENSAGENS DE CONTATO/AVISO: Sempre que o utilizador pedir para avisar, mandar recado ou dizer que ele quer falar com alguém, a mensagem enviada DEVE incluir a seguinte introdução curta e natural:\n"
            "'Olá! Sou a Moonlight, assistente pessoal do Arthur. Ele pediu para avisar que quer falar com você.' (seguido do motivo ou recado específico, se houver).\n\n"
            "REGRAS DE OURO:\n"
            "1. Abrir jogo ou app: [ACAO:abrir:nome_do_app_ou_jogo]\n"
            "2. Digitar texto avulso: [ACAO:escrever:texto_bem_escrito]\n"
            "3. Mandar mensagem no Discord: [ACAO:discord:nome_do_contato|mensagem_natural_com_introducao]\n"
            "4. Mandar mensagem no WhatsApp: [ACAO:whatsapp:nome_do_contato|mensagem_natural_com_introducao]\n"
            "   Exemplo: Utilizador: 'manda zap para Jô dizendo que ele quer falar com ela' -> "
            "Resposta: [ACAO:whatsapp:Jô|Olá! Sou a Moonlight, assistente pessoal do Arthur. Ele pediu para avisar que quer falar com você.]\n"
            "5. Pesquisar na internet: [ACAO:pesquisar:termo_em_portugues]\n"
        )
        logging.info(f"🧠 [Cérebro]: Inicializado com o modelo '{self.modelo}'.")

    def transcrever_audio(self, audio_np):
        audio_float32 = audio_np.flatten().astype(np.float32)
        
        segmentos, _ = self.whisper.transcribe(
            audio_float32,
            language="pt",
            initial_prompt=self.prompt_vocabulario,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400)
        )
        
        texto = " ".join([seg.text for seg in segmentos]).strip()
        return texto

    def corrigir_transcricao(self, texto):
        correcoes = {
            r'\bum moleque\b': 'a Moonlight',
            r'\bmoleque\b': 'Moonlight',
            r'\bamor light\b': 'Moonlight',
            r'\bmoon light\b': 'Moonlight',
            r'\bmunlight\b': 'Moonlight',
            r'\bmulai\b': 'Moonlight',
            r'\bda tu\b': 'do Arthur',
            r'\bdo ator\b': 'do Arthur',
            r'\bartur\b': 'Arthur'
        }
        texto_corrigido = texto
        for padrao, substituto in correcoes.items():
            texto_corrigido = re.sub(padrao, substituto, texto_corrigido, flags=re.IGNORECASE)
        return texto_corrigido

    def varrer_programas_pc(self):
        print("🔍 [Cérebro]: A atualizar mapeamento de aplicativos e jogos da Steam...")
        pastas = [
            os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expanduser(r"~\Desktop"),
            os.path.expanduser(r"~\OneDrive\Área de Trabalho"),
            os.path.expanduser(r"~\OneDrive\Desktop")
        ]
        for pasta in pastas:
            if os.path.exists(pasta):
                for raiz, _, arquivos in os.walk(pasta):
                    for arq in arquivos:
                        if arq.endswith(('.lnk', '.url', '.exe')):
                            nome_limpo = os.path.splitext(arq)[0].lower()
                            self.apps_indexados[nome_limpo] = os.path.join(raiz, arq)

        pastas_steam = [
            r"C:\Program Files (x86)\Steam\steamapps",
            r"C:\Program Files\Steam\steamapps",
            r"D:\SteamLibrary\steamapps",
            r"E:\SteamLibrary\steamapps",
            r"F:\SteamLibrary\steamapps"
        ]
        
        vdf_path = r"C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf"
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    caminhos_vdf = re.findall(r'"path"\s+"([^"]+)"', f.read())
                    for c in caminhos_vdf:
                        caminho_apps = os.path.join(c.replace("\\\\", "\\"), "steamapps")
                        if caminho_apps not in pastas_steam:
                            pastas_steam.append(caminho_apps)
            except Exception:
                pass

        jogos_steam = 0
        for pasta_s in pastas_steam:
            if os.path.exists(pasta_s):
                for arq in os.listdir(pasta_s):
                    if arq.startswith("appmanifest_") and arq.endswith(".acf"):
                        caminho_acf = os.path.join(pasta_s, arq)
                        try:
                            with open(caminho_acf, "r", encoding="utf-8", errors="ignore") as f:
                                conteudo = f.read()
                                appid = re.search(r'"appid"\s+"(\d+)"', conteudo)
                                nome = re.search(r'"name"\s+"([^"]+)"', conteudo)
                                if appid and nome:
                                    id_jogo = appid.group(1)
                                    nome_jogo = re.sub(r'[®™©]', '', nome.group(1)).strip().lower()
                                    self.apps_indexados[nome_jogo] = f"steam://rungameid/{id_jogo}"
                                    jogos_steam += 1
                        except Exception:
                            pass

        print(f"✅ [Cérebro]: {len(self.apps_indexados)} apps/atalhos indexados (incluindo {jogos_steam} jogos da Steam).")

    def encontrar_app(self, alvo):
        alvo_limpo = re.sub(r'[®™©]', '', alvo).strip().lower()
        if alvo_limpo in self.apps_indexados:
            return self.apps_indexados[alvo_limpo]
            
        for nome_cadastrado, caminho in self.apps_indexados.items():
            if alvo_limpo in nome_cadastrado or nome_cadastrado in alvo_limpo:
                print(f"🎯 [Correspondência Inteligente]: '{alvo}' -> '{nome_cadastrado}'")
                return caminho
                
        return None

    def executar_loop_principal(self, motor, sintetizador, visualizador):
        while visualizador.esta_aberto():
            visualizador.set_serene()
            print("\n💤 [Cérebro]: À espera de ser chamada (Diz 'Moonlight')...")
            audio_capturado = motor.ouvir_ate_silencio()
            
            if not visualizador.esta_aberto():
                break

            if audio_capturado is not None and len(audio_capturado) > 0:
                try:
                    visualizador.set_listening()
                    
                    texto_bruto = self.transcrever_audio(audio_capturado)
                    if not texto_bruto:
                        continue
                        
                    texto_ouvido = self.corrigir_transcricao(texto_bruto)
                    
                    primeiras_palavras = re.sub(r'[^\w\s]', '', " ".join(texto_ouvido.lower().split()[:4]))
                    wake_words = ["moonlight", "moon", "light"]
                    
                    wake_encontrada = None
                    for w in wake_words:
                        if re.search(rf'\b{w}\b', primeiras_palavras):
                            wake_encontrada = w
                            break
                            
                    if not wake_encontrada:
                        continue

                    print(f"🗣️ [Whisper Ouviu]: {texto_ouvido}")
                    comando = re.sub(rf'^.*?\b{wake_encontrada}\b[\s,.:;!?-]*', '', texto_ouvido, count=1, flags=re.IGNORECASE).strip()

                    if not comando or len(comando) < 2:
                        sintetizador.falar("Sim, Arthur?")
                        continue

                    print("🧠 [Cérebro a pensar...]")
                    payload = {
                        "model": self.modelo,
                        "prompt": f"{self.system_prompt}\n\nUtilizador: {comando}\nMoonlight:",
                        "stream": False,
                        "options": {"temperature": 0.15, "num_predict": 160}
                    }
                    
                    resposta = requests.post(self.url_ollama, json=payload, timeout=30)
                    if resposta.status_code == 200:
                        resp_cerebro = resposta.json().get("response", "").strip()
                        print(f"🤖 [Resposta Bruta]: {resp_cerebro}")

                        matches = re.findall(r'\[ACAO:\s*([^:]+):\s*([^\]]+)\]', resp_cerebro, re.IGNORECASE)
                        matches_pesq = re.findall(r'\[ACAO:\s*pesquisa[r]?:\s*([^\]]+)\]', resp_cerebro, re.IGNORECASE)
                        
                        if matches_pesq:
                            termo = matches_pesq[0].strip()
                            dados_web = self.web.pesquisar(termo, abrir_navegador=True)
                            
                            prompt_rag = (
                                f"Contexto encontrado na internet sobre '{termo}':\n{dados_web}\n\n"
                                f"Instrução: Tu és a Moonlight. Usando apenas o contexto acima, explica diretamente para o Arthur sobre '{termo}' em 2 frases curtas em Português do Brasil, avisando brevemente que abriste a página no navegador. "
                                f"PROIBIDO mandar o utilizador pesquisar na internet.\nResposta da Moonlight:"
                            )
                            payload_rag = {
                                "model": self.modelo,
                                "prompt": prompt_rag,
                                "stream": False,
                                "options": {"temperature": 0.2, "num_predict": 160}
                            }
                            resp_rag = requests.post(self.url_ollama, json=payload_rag, timeout=30)
                            if resp_rag.status_code == 200:
                                resp_cerebro = resp_rag.json().get("response", "").strip().strip('"')
                                print(f"🤖 [Resposta Web RAG]: {resp_cerebro}")

                        texto_falar = re.sub(r'\[ACAO:[^\]]+\]', '', resp_cerebro).strip() or "Pronto, Arthur."

                        for tipo, alvo in matches:
                            tipo, alvo = tipo.strip().lower(), alvo.strip()
                            
                            if tipo == "abrir":
                                print(f"💻 [Executor]: A abrir -> {alvo}")
                                try:
                                    real = self.encontrar_app(alvo)
                                    if real:
                                        if real.startswith(("steam://", "http", "whatsapp:", "discord:")):
                                            subprocess.Popen(f'start "" "{real}"', shell=True)
                                        elif real.startswith("start "):
                                            subprocess.Popen(real, shell=True)
                                        elif os.path.exists(real):
                                            os.startfile(real)
                                        else:
                                            subprocess.Popen(f'"{real}"', shell=True)
                                    else:
                                        print(f"⚠️ Aplicativo ou jogo '{alvo}' não encontrado no PC.")
                                        texto_falar = f"Não encontrei o {alvo} instalado, Arthur."
                                except Exception as ex:
                                    print(f"❌ Erro ao abrir: {ex}")
                                time.sleep(1.2)
                                
                            elif tipo == "escrever":
                                print(f"⌨️ [Executor]: A escrever -> {alvo}")
                                time.sleep(0.3)
                                pyperclip.copy(alvo)
                                pyautogui.hotkey('ctrl', 'v')
                                
                            elif tipo == "discord":
                                separador = "|" if "|" in alvo else (":" if ":" in alvo else "-")
                                if separador in alvo:
                                    contato, msg = alvo.split(separador, 1)
                                    caminho_disc = self.apps_indexados.get("discord", "discord:")
                                    self.pc.enviar_mensagem_discord(contato.strip(), msg.strip(), caminho_disc)
                                    texto_falar = f"Mensagem enviada para {contato.strip()} no Discord, Arthur."

                            elif tipo in ["whatsapp", "zap"]:
                                separador = "|" if "|" in alvo else (":" if ":" in alvo else "-")
                                if separador in alvo:
                                    contato, msg = alvo.split(separador, 1)
                                    caminho_wpp = self.apps_indexados.get("whatsapp", "whatsapp:")
                                    self.pc.enviar_mensagem_whatsapp(contato.strip(), msg.strip(), caminho_wpp)
                                    texto_falar = f"Mensagem enviada para {contato.strip()} no WhatsApp, Arthur."

                        print(f"🤖 [Moonlight Falando]: {texto_falar}")
                        visualizador.set_speaking()
                        sintetizador.falar(texto_falar)

                except Exception as e:
                    print(f"❌ [Erro no processamento de voz]: {e}")