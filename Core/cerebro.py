import os
import datetime
import requests
import numpy as np
import time
import subprocess
import pyautogui
import pyperclip
import re
import sys
import unicodedata
import logging
from difflib import SequenceMatcher
from faster_whisper import WhisperModel
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import ctypes
try:
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False

try:
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080)
except Exception:
    pass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Sistemas.subsistema_web import SubsistemaWeb
from Sistemas.subsistema_pc import SubsistemaPC
from Sistemas.subsistema_whatsapp import SubsistemaWhatsApp

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']

class CerebroLocal:
    def __init__(self, modelo="mistral"):
        self.modelo = modelo
        self.url_ollama = "http://localhost:11434/api/generate"
        self.sintetizador_ref = None
        self.aguardando_resposta_leitura = False
        self.mensagens_pendentes_analise = []
        self.ultimas_mensagens_processadas = {}
        
        print("🎧 [Cérebro]: A carregar audição neural aprimorada na CPU (Faster-Whisper SMALL)...")
        try:
            self.whisper = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
            print("⚡ [Faster-Whisper SMALL]: Carregado com sucesso! (Alta precisão PT-BR)")
        except Exception:
            self.whisper = WhisperModel("base", device="cpu", compute_type="int8")
            print("⚡ [Faster-Whisper BASE]: Carregado em modo de compatibilidade.")

        self.prompt_vocabulario = (
            "Olá Moonlight, bom dia Arthur. Abre o WhatsApp e manda uma mensagem para o contato: "
            "Jô, Jô Eichler, Isis Eichler, Mila, Mila Mamys, Renato, Neto, Doutora Leda, Tia Aninha, Marcelo Frigo, XuimArt. "
            "Abrir Discord, Steam, Overwatch 2, League of Legends, Bloco de Notas, Google Chrome."
        )
        
        self.web = SubsistemaWeb()
        self.pc = SubsistemaPC()
        
        self.whatsapp = SubsistemaWhatsApp(callback_alerta=self.lidar_com_alerta_whatsapp)
        self.whatsapp.iniciar()

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
            "Tu és a Moonlight, assistente de voz inteligente do Arthur.\n"
            "Responde SEMPRE em Português do Brasil de forma curta, direta e natural.\n\n"
            "SE O UTILIZADOR PEDIR UMA AÇÃO, usa APENAS a tag correspondente:\n"
            "1. ABRIR PROGRAMA/JOGO REAL: [ACAO:abrir:nome_do_app]\n"
            "2. PESQUISAR NA INTERNET: [ACAO:pesquisar:termo_da_pesquisa]\n"
            "3. ENVIAR WHATSAPP: [ACAO:whatsapp:NomeDoContato|TextoDaMensagem]\n"
            "   - REGRA ABSOLUTA: Escreve APENAS a mensagem exata pedida pelo Arthur. NUNCA adiciones introduções como 'Oi, sou a Moonlight' ou assinaturas de assistente. O texto enviado deve parecer que foi escrito diretamente pelo Arthur.\n"
            "4. LER CONTATO ESPECÍFICO: [ACAO:ler_contato:NomeDoContato]\n"
            "5. LER NÃO LIDAS GERAIS: [ACAO:ler_whatsapp:geral]\n"
            "6. AGENDAR COMPROMISSO: [ACAO:agendar:Horario|TituloDoEvento]\n"
            "7. CANCELAR COMPROMISSO: [ACAO:cancelar:termo]\n\n"
            "REGRAS CRÍTICAS:\n"
            "- Se a frase pedir para verificar e depois marcar/agendar caso esteja livre (ex: 'vê se tenho compromisso, se não tiver marca às 11h'), deves priorizar a ação de agendamento usando [ACAO:agendar:11:00|Reunião de trabalho].\n"
            "- Se o utilizador pedir para cancelar, apagar ou remover compromissos, usa [ACAO:cancelar:hoje].\n"
        )
        logging.info(f"🧠 [Cérebro]: Inicializado com o modelo '{self.modelo}'.")
        
        # Inicia o monitor de alarmes/avisos da agenda em background
        self.iniciar_monitor_agenda()

    def get_calendar_service(self):
        creds = None
        token_path = 'scheduler_subsystem/token.json'
        credentials_path = 'scheduler_subsystem/Credentials.json'

        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception:
                creds = None
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            
            if not creds:
                if not os.path.exists(credentials_path):
                    raise FileNotFoundError(f"Arquivo '{credentials_path}' não encontrado.")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)

    def criar_compromisso_hoje(self, horario_str, resumo="Compromisso"):
        try:
            service = self.get_calendar_service()
            agora = datetime.datetime.now()
            
            partes = horario_str.split(":")
            hora = int(partes[0])
            minuto = int(partes[1]) if len(partes) > 1 else 0
            
            inicio = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
            fim = inicio + datetime.timedelta(hours=1)
            
            event = {
                'summary': resumo,
                'start': {'dateTime': inicio.isoformat(), 'timeZone': 'America/Sao_Paulo'},
                'end': {'dateTime': fim.isoformat(), 'timeZone': 'America/Sao_Paulo'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 5},
                        {'method': 'email', 'minutes': 5},
                    ],
                },
            }
            
            event_result = service.events().insert(calendarId='primary', body=event).execute()
            return True, event_result.get('summary')
        except Exception as e:
            print(f"Erro ao criar compromisso no Calendar: {e}")
            return False, str(e)

    def cancelar_compromisso_hoje(self, termo_busca=""):
        try:
            service = self.get_calendar_service()
            agora = datetime.datetime.now()
            start_of_day = agora.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
            end_of_day = agora.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            if not events:
                return False, "Arthur, você não tem nenhum compromisso hoje para cancelar."
            
            cancelados = 0
            for event in events:
                event_id = event.get('id')
                summary = event.get('summary', '').lower()
                
                if not termo_busca or termo_busca in summary or termo_busca == "hoje" or termo_busca == "compromisso":
                    service.events().delete(calendarId='primary', eventId=event_id, sendUpdates='all').execute()
                    cancelados += 1
            
            if cancelados > 0:
                return True, f"Pronto, Arthur, cancelei {cancelados} compromisso(s) de hoje."
            else:
                return False, "Não encontrei nenhum compromisso correspondente para cancelar hoje, Arthur."
        except Exception as e:
            print(f"Erro ao cancelar compromisso: {e}")
            return False, "Desculpa, Arthur, não consegui cancelar o compromisso."

    def iniciar_monitor_agenda(self):
        import threading
        def monitorar():
            eventos_avisados = set()
            while True:
                try:
                    now = datetime.datetime.now()
                    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
                    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'
                    
                    service = self.get_calendar_service()
                    events_result = service.events().list(
                        calendarId='primary', timeMin=start_of_day, timeMax=end_of_day,
                        singleEvents=True, orderBy='startTime'
                    ).execute()
                    events = events_result.get('items', [])
                    
                    for event in events:
                        event_id = event.get('id')
                        start_str = event['start'].get('dateTime')
                        if not start_str or event_id in eventos_avisados:
                            continue
                            
                        event_time = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
                        diff_minutos = (event_time - now).total_seconds() / 60
                        
                        if 4.5 <= diff_minutos <= 5.5:
                            titulo = event.get('summary', 'Compromisso')
                            aviso = f"Arthur, atenção! O seu compromisso '{titulo}' começa daqui a 5 minutos."
                            print(f"⏰ [Alerta de Agenda]: {aviso}")
                            self._falar_com_volume_maximo(aviso)
                            eventos_avisados.add(event_id)
                except Exception:
                    pass
                time.sleep(30)

        t = threading.Thread(target=monitorar, daemon=True)
        t.start()
        print("⏰ [Cérebro]: Monitor de alertas da agenda iniciado em background.")

    def _falar_com_volume_maximo(self, texto, visualizador=None):
        if HAS_PYCAW:
            try:
                sessions = AudioUtilities.GetAllSessions()
                pid = os.getpid()
                for session in sessions:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    if session.Process and session.Process.pid == pid:
                        volume.SetMasterVolume(1.0, None)
            except Exception:
                pass

        if self.sintetizador_ref:
            try:
                if visualizador:
                    try:
                        visualizador.set_speaking()
                    except Exception:
                        pass

                self.sintetizador_ref.falar(texto)

                if visualizador:
                    try:
                        visualizador.set_serene()
                    except Exception:
                        pass
            except Exception as e:
                print(f"❌ Erro ao falar com sintetizador: {e}")

    def _normalizar(self, texto):
        if not texto:
            return ""
        t = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()
        t = re.sub(r'\bdr\.?\b', 'doutor', t)
        t = re.sub(r'\bdra\.?\b', 'doutora', t)
        return t

    def _limpar_nome_para_fala(self, nome):
        nome_limpo = nome
        if "|" in nome_limpo:
            partes = [p.strip() for p in nome_limpo.split("|") if p.strip()]
            if len(partes) >= 2 and any(k in partes[-1].lower() for k in ["aviso", "avisos", "geral", "chat", "duvidas", "dúvidas"]):
                nome_limpo = f"{partes[0]} {partes[-1]}"
            else:
                nome_limpo = partes[0]
        nome_limpo = re.sub(r'\bDr\.\s*', 'Doutor ', nome_limpo, flags=re.IGNORECASE)
        nome_limpo = re.sub(r'\bDra\.\s*', 'Doutora ', nome_limpo, flags=re.IGNORECASE)
        return nome_limpo.strip()

    def _eh_grupo(self, remetente):
        rem_l = remetente.lower()
        termos_grupo = ["|", "aviso", "avisos", "grupo", "turma", "canal", "comunidade", "chat", "geral", "promoções", "promocoes"]
        return any(t in rem_l for t in termos_grupo)

    def transcrever_audio(self, audio_np):
        audio_float32 = audio_np.flatten().astype(np.float32)
        segmentos, _ = self.whisper.transcribe(
            audio_float32,
            language="pt",
            initial_prompt=self.prompt_vocabulario,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=450, speech_pad_ms=250)
        )
        texto = " ".join([seg.text for seg in segmentos]).strip()
        
        alucinacoes_whisper = [
            "legendas pela comunidade", "amara.org", "obrigado por assistir",
            "inscreva-se no canal", "subtitles by", "copyright"
        ]
        if any(a in texto.lower() for a in alucinacoes_whisper):
            return ""
        return texto

    def corrigir_transcricao(self, texto):
        correcoes = {
            r'\bum moleque\b': 'Moonlight',
            r'\bmoleque\b': 'Moonlight',
            r'\bamor light\b': 'Moonlight',
            r'\bmoon light\b': 'Moonlight',
            r'\bmunlight\b': 'Moonlight',
            r'\bmulai\b': 'Moonlight',
            r'\bmonlight\b': 'Moonlight',
            r'\bmulher\b': 'Moonlight',
            r'\bartisan\s+rapid\b': 'WhatsApp',
            r'\bartisan\b': 'WhatsApp',
            r'\bwhat\s*s\s*app\b': 'WhatsApp',
            r'\bwhat\s*zap\b': 'WhatsApp',
            r'\bo\s+atizape\b': 'o WhatsApp',
            r'\batizape\b': 'WhatsApp',
            r'\buatisapi\b': 'WhatsApp',
            r'\bzap\s*zap\b': 'WhatsApp',
            r'\bda tu\b': 'do Arthur',
            r'\bdo ator\b': 'do Arthur',
            r'\bartur\b': 'Arthur',
            r'\bjesus\s+eichler\b': 'Isis Eichler',
            r'\beis[,\s]+eis[,\s]+leda\b': 'Isis Eichler',
            r'\beis\s+eichler\b': 'Isis Eichler',
            r'\bisis\s+aisler\b': 'Isis Eichler',
            r'\bisis\s+isler\b': 'Isis Eichler',
            r'\bises\b': 'Isis',
            r'\bshow\b': 'Jô',
            r'\bde show\b': 'da Jô',
            r'\bcontato show\b': 'contato Jô',
            r'\bjo\b': 'Jô',
            r'\bleida\b': 'Leda',
            r'\bmilla\b': 'Mila',
            r'\bcamila\s+mamys\b': 'Mila',
            r'\btiano ninho\b': 'Tia Aninha',
            r'\btia aninha\b': 'Tia Aninha',
            r'\bshui\b': 'XuimArt',
            r'\bxuim\b': 'XuimArt',
            r'\bhipoca\s+de\s+doce\b': 'pipoca doce',
            r'\bhipoca\b': 'pipoca',
            r'\bné,\s*oberst\b': 'não obrigado',
            r'\boberst\b': 'obrigado',
            r'\bmanda\s+o\s+contato[,\s]+manda\s+o\s+mensagem\b': 'manda uma mensagem',
            r'\bmanda\s+o\s+mensagem\b': 'manda uma mensagem'
        }
        texto_corrigido = texto
        for padrao, substituto in correcoes.items():
            texto_corrigido = re.sub(padrao, substituto, texto_corrigido, flags=re.IGNORECASE)
        return texto_corrigido

    def extrair_envio_whatsapp_natural(self, comando):
        cmd = comando.strip()
        if re.match(r'^(?:qual|como|quando|onde|quem|por\s+que|que)\b', cmd, flags=re.IGNORECASE):
            return None, None

        cmd = re.sub(r'^(?:oi|olá|ola|bom\s+dia|boa\s+tarde|boa\s+noite)[\s,.;:!-]+', '', cmd, flags=re.IGNORECASE).strip()
        cmd = re.sub(r'^(?:abre\s+o\s+whatsapp|abriu\s+o?\s*whatsapp|abrir\s+whatsapp|vai\s+no\s+whatsapp|no\s+whatsapp)(?:\s+para\s+mim|\s+pra\s+mim)?[\s,.;:-]*(?:e\s+)?', '', cmd, flags=re.IGNORECASE).strip()

        padroes = [
            r'^(?:manda|envia|escreve|fala|avisa)\s+(?:uma?\s+|a\s+|o\s+)?(?:mensagem|recado|zap)?\s*(?:no\s+whatsapp\s+)?(?:para\s+|pro\s+|pra\s+|no\s+)?([a-zA-ZÀ-ÿ0-9_.\s]{2,25}?)[\s,.]+(?:dizendo|falando|mandando|com\s+o\s+texto|que|assim)[:\s,-]+(.+)',
            r'^(?:para\s+o\s+contato\s+|contato\s+)([a-zA-ZÀ-ÿ0-9_.\s]{2,25}?)[\s,.]+(?:manda|envia|dizendo)[:\s,-]+(.+)'
        ]

        for pat in padroes:
            m = re.search(pat, cmd, flags=re.IGNORECASE)
            if m:
                contato = m.group(1).strip()
                mensagem = m.group(2).strip(" ,.-:")
                
                mensagem = re.sub(r'eu sou a moonlight.*?\.', '', mensagem, flags=re.IGNORECASE).strip()
                
                if contato and mensagem and contato.lower() not in ["arthur", "whatsapp", "zap"]:
                    return contato, mensagem
        return None, None

    def filtrar_mensagens_rapido(self, lista_conversas):
        termos_spam = ["promoções", "promocoes", "deals", "cupom", "publi", "desconto", "oferta", "sorteio", "infobr"]
        importantes = []
        for remetente, preview in lista_conversas:
            texto_combinado = f"{remetente} {preview}".lower()
            if not any(t in texto_combinado for t in termos_spam):
                importantes.append((remetente, preview))
        return importantes

    def avaliar_importancia_e_conteudo(self, remetente, preview):
        if any(t in remetente.lower() for t in ["promoções", "promocoes", "infobr", "oferta", "cupom"]):
            return 1, "Promoções e ofertas"

        if self._eh_grupo(remetente) and not any(u in preview.lower() for u in ["arthur", "urgente", "importante"]):
            return 2, "Aviso de grupo ou comunidade"

        if "nova mensagem ou arquivo" in preview.lower():
            return 3, "Nova mensagem recebida"

        prompt_escala = (
            f"Analisa a seguinte mensagem de WhatsApp recebida de '{remetente}':\n"
            f"\"{preview}\"\n\n"
            f"Classifica a importância desta mensagem de 1 a 5, onde:\n"
            f"5 = Urgente/Crítico (emergências, PIX, prazos imediatos, médicos, hospital)\n"
            f"4 = Importante/Trabalho/Família próxima (projetos, clientes, mãe, pai, Jô)\n"
            f"3 = Pessoal/Rotina (conversas do dia a dia, amigos)\n"
            f"2 = Informativo (avisos de grupos, turmas, canais)\n"
            f"1 = Spam/Promoções (ofertas, cupons, bots)\n\n"
            f"Responde APENAS no formato: NOTA|Resumo curto do assunto em até 8 palavras.\n"
            f"Resposta:"
        )
        payload = {
            "model": self.modelo,
            "prompt": prompt_escala,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 30}
        }
        nota = 3
        resumo = "Mensagem de texto"
        try:
            resp = requests.post(self.url_ollama, json=payload, timeout=5)
            if resp.status_code == 200:
                texto_resp = resp.json().get("response", "").strip()
                if "|" in texto_resp:
                    partes = texto_resp.split("|", 1)
                    num_str = re.search(r'[1-5]', partes[0])
                    nota = int(num_str.group(0)) if num_str else 3
                    resumo = partes[1].strip().strip('"')
        except Exception:
            if any(k in preview.lower() for k in ["urgente", "pix", "agora", "emergência", "hospital"]):
                nota = 5
                resumo = "Possível assunto urgente"

        if self._eh_grupo(remetente) and nota < 5:
            nota = min(2, nota)
            resumo = f"Aviso de grupo: {resumo}"

        return nota, resumo

    def montar_resumo_direto(self, lista_total, importantes):
        total_geral = len(lista_total)
        mensagens_avaliadas = []
        for rem, msg in importantes:
            nota, resumo = self.avaliar_importancia_e_conteudo(rem, msg)
            mensagens_avaliadas.append({
                "remetente": rem,
                "preview": msg,
                "nota": nota,
                "resumo": resumo
            })

        mensagens_avaliadas.sort(key=lambda x: x["nota"], reverse=True)
        self.mensagens_pendentes_analise = [(m["remetente"], m["preview"]) for m in mensagens_avaliadas]

        top = mensagens_avaliadas[0]
        top_nome = self._limpar_nome_para_fala(top["remetente"])

        if len(mensagens_avaliadas) == 1:
            return f"Arthur, você tem 1 mensagem relevante não lida de {top_nome}, falando sobre {top['resumo']}. Quer que eu leia?"

        if top["nota"] >= 4:
            return (
                f"Arthur, você tem {total_geral} conversas não lidas. Atenção: há uma mensagem importante de {top_nome} sobre {top['resumo']}. "
                f"Qual conversa você quer que eu leia primeiro?"
            )
        else:
            return (
                f"Arthur, você tem {total_geral} conversas não lidas. A mais relevante é de {top_nome}. "
                f"Qual delas você quer ouvir primeiro?"
            )

    def selecionar_mensagem_escolhida(self, texto_usuario):
        txt_norm = self._normalizar(texto_usuario)
        if len(self.mensagens_pendentes_analise) == 1:
            if any(k in txt_norm for k in ["sim", "por favor", "pode", "leia", "le", "fala", "manda", "isis", "mila", "leda", "aninha", "jo", "marcelo", "xuim", "neto", "renato"]):
                return 0

        ordens = {
            0: ["primeira", "primeiro", "1", "um", "mais importante", "relevante", "urgente"],
            1: ["segunda", "segundo", "2", "dois"],
            2: ["terceira", "terceiro", "3", "tres"],
            3: ["quarta", "quarto", "4", "quatro"],
            4: ["quinta", "quinto", "5", "cinco"]
        }
        for idx, palavras in ordens.items():
            if any(re.search(rf'\b{p}\b', txt_norm) for p in palavras):
                if idx < len(self.mensagens_pendentes_analise):
                    return idx

        if "ultima" in txt_norm or "ultimo" in txt_norm:
            return len(self.mensagens_pendentes_analise) - 1

        palavras_usuario = [p for p in re.split(r'\W+', txt_norm) if len(p) >= 2 and p not in ["de", "da", "do", "doutor", "doutora", "contato", "mensagem", "ler", "leia", "agora"]]
        
        melhor_idx = None
        maior_similaridade = 0.0

        for idx, (remetente, _) in enumerate(self.mensagens_pendentes_analise):
            rem_norm = self._normalizar(remetente)
            partes_nome = [p for p in re.split(r'[\s|\-_]+', rem_norm) if len(p) >= 2 and p not in ["de", "da", "do", "fd", "avisos", "doutor", "doutora"]]
            
            for parte in partes_nome:
                if re.search(rf'\b{re.escape(parte)}\b', txt_norm) or parte in txt_norm:
                    return idx
                
                for p_usr in palavras_usuario:
                    sim = SequenceMatcher(None, parte, p_usr).ratio()
                    if sim >= 0.65 and sim > maior_similaridade:
                        maior_similaridade = sim
                        melhor_idx = idx

        return melhor_idx

    def lidar_com_alerta_whatsapp(self, remetente, texto_msg):
        if self.ultimas_mensagens_processadas.get(remetente) == texto_msg:
            return
        self.ultimas_mensagens_processadas[remetente] = texto_msg

        print(f"🚨 [WhatsApp Proativo]: Mensagem nova detetada de {remetente}")
        nota, resumo = self.avaliar_importancia_e_conteudo(remetente, texto_msg)
        
        if nota >= 4:
            nome_fala = self._limpar_nome_para_fala(remetente)
            alerta_proativo = f"Arthur, atenção! Chegou uma mensagem importante de {nome_fala}, sobre {resumo}. Quer que eu leia?"
            
            self.mensagens_pendentes_analise = [(remetente, texto_msg)]
            self.aguardando_resposta_leitura = True
            
            if self.sintetizador_ref:
                try:
                    print(f"🤖 [Moonlight Alerta Proativo]: {alerta_proativo}")
                    self._falar_com_volume_maximo(alerta_proativo)
                except Exception:
                    pass
        else:
            print(f"ℹ️ [WhatsApp Proativo]: Mensagem de {remetente} classificada como nível {nota} (alerta de voz ignorado).")

    def extrair_contato_alvo_frase(self, comando):
        if re.search(r'\b(manda|envia|escreve|mandando|enviando|dizendo|perguntando)\b', comando, flags=re.IGNORECASE):
            return None

        padroes = [
            r'contato\s+(?:da\s+|do\s+)?([a-zA-ZÀ-ÿ0-9_.\s]{2,20})',
            r'conversa\s+(?:da\s+|do\s+|com\s+a\s+|com\s+o\s+|com\s+)?([a-zA-ZÀ-ÿ0-9_.\s]{2,20})',
            r'se\s+(?:a\s+|o\s+)([a-zA-ZÀ-ÿ0-9_.]+)\s+(?:mandou|enviou|respondeu|falou)'
        ]
        stopwords = {"whatsapp", "zap", "mensagem", "mensagens", "mim", "voce", "você", "eu", "alguem", "alguém", "importante", "arthur"}
        for pat in padroes:
            m = re.search(pat, comando, flags=re.IGNORECASE)
            if m:
                nome = m.group(1).strip()
                nome = re.sub(r'\s+(e\s+veja|e\s+me\s+fala|no\s+whatsapp|por\s+favor).*$', '', nome, flags=re.IGNORECASE).strip()
                if nome.lower() not in stopwords:
                    return nome
        return None

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
                return caminho
        return None

    def executar_loop_principal(self, motor, sintetizador, visualizador):
        self.sintetizador_ref = sintetizador
        print("🚀 [DEBUG]: O Cérebro entrou no loop principal com sucesso!")
        
        while True:
            try:
                try:
                    visualizador.set_serene()
                except Exception:
                    pass
                    
                if self.aguardando_resposta_leitura:
                    print("\n👂 [Cérebro]: Aguardando você escolher qual mensagem ler...")
                else:
                    print("\n💤 [Cérebro]: À espera de ser chamada (Diz 'Moonlight')...")
                    
                audio_capturado = motor.ouvir_ate_silencio()
                
                if audio_capturado is not None and len(audio_capturado) > 0:
                    try:
                        visualizador.set_listening()
                        
                        texto_bruto = self.transcrever_audio(audio_capturado)
                        if not texto_bruto or len(texto_bruto.strip()) < 2:
                            continue
                            
                        texto_ouvido = self.corrigir_transcricao(texto_bruto)
                        
                        if self.aguardando_resposta_leitura:
                            print(f"🗣️ [Whisper Ouviu (Escolha)]: {texto_ouvido}")
                            texto_lower = self._normalizar(texto_ouvido)
                            
                            if any(re.search(rf'\b{k}\b', texto_lower) for k in ["nao", "nenhuma", "esquece", "deixa", "depois", "parar", "obrigado", "cancelar"]):
                                print("🛑 [Leitura Cancelada]: Utilizador decidiu não ler agora.")
                                self.aguardando_resposta_leitura = False
                                self.mensagens_pendentes_analise.clear()
                                texto_falar = "Perfeito, Arthur. Deixei para depois."
                                print(f"🤖 [Moonlight Falando]: {texto_falar}")
                                self._falar_com_volume_maximo(texto_falar, visualizador)
                                continue

                            if any(re.search(rf'\b{k}\b', texto_lower) for k in ["todas", "tudo", "as outras", "restantes"]):
                                print("👁️ [Leitura Direta]: Utilizador pediu para ler TODAS.")
                                self.aguardando_resposta_leitura = False
                                
                                detalhes_lista = []
                                for rem, msg in self.mensagens_pendentes_analise:
                                    self.ultimas_mensagens_processadas[rem] = msg
                                    self.whatsapp.marcar_como_lida(rem)
                                    detalhes_lista.append(f"A de {self._limpar_nome_para_fala(rem)} diz: {msg}")
                                    time.sleep(0.4)

                                detalhes = ". ".join(detalhes_lista) + ". Marquei todas como lidas, Arthur."
                                self.mensagens_pendentes_analise.clear()
                                print(f"🤖 [Moonlight Falando]: {detalhes}")
                                self._falar_com_volume_maximo(detalhes, visualizador)
                                continue

                            idx_escolhido = self.selecionar_mensagem_escolhida(texto_ouvido)
                            
                            if idx_escolhido is None and any(re.search(rf'\b{k}\b', texto_lower) for k in ["sim", "pode", "leia", "ler", "quero", "manda", "conteudo", "por favor"]):
                                idx_escolhido = 0

                            if idx_escolhido is not None and self.mensagens_pendentes_analise:
                                rem, msg = self.mensagens_pendentes_analise.pop(idx_escolhido)
                                nome_fala = self._limpar_nome_para_fala(rem)
                                self.ultimas_mensagens_processadas[rem] = msg

                                if "nova mensagem ou arquivo" in msg.lower():
                                    print(f"🔍 [Cérebro]: Extraindo conteúdo real da mensagem de {rem}...")
                                    texto_real, msgs_reais = self.whatsapp.solicitar_leitura_contato(rem)
                                    if msgs_reais:
                                        msg = msgs_reais[-1][1]

                                print(f"👁️ [Cérebro]: A marcar mensagem de {rem} como lida...")
                                self.whatsapp.marcar_como_lida(rem)

                                if self.mensagens_pendentes_analise:
                                    restantes_nomes = ", ".join([self._limpar_nome_para_fala(r) for r, _ in self.mensagens_pendentes_analise[:3]])
                                    texto_falar = f"A mensagem de {nome_fala} diz: {msg}. Já marquei como lida. Ainda restam mensagens de {restantes_nomes}. Quer ouvir alguma delas?"
                                else:
                                    texto_falar = f"A mensagem de {nome_fala} diz: {msg}. Já marquei como lida. Essas eram todas as principais, Arthur."
                                    self.aguardando_resposta_leitura = False
                                
                                print(f"🤖 [Moonlight Falando]: {texto_falar}")
                                self._falar_com_volume_maximo(texto_falar, visualizador)
                                continue
                            else:
                                if "moonlight" in texto_lower:
                                    self.aguardando_resposta_leitura = False
                                    self.mensagens_pendentes_analise.clear()
                                else:
                                    nomes_disp = ", ".join([self._limpar_nome_para_fala(r) for r, _ in self.mensagens_pendentes_analise[:3]])
                                    texto_falar = f"Não entendi qual contato, Arthur. Você prefere ouvir de {nomes_disp}, ou cancelar?"
                                    print(f"🤖 [Moonlight Falando]: {texto_falar}")
                                    self._falar_com_volume_maximo(texto_falar, visualizador)
                                    continue

                        primeiras_palavras = re.sub(r'[^\w\s]', '', " ".join(texto_ouvido.lower().split()[:5]))
                        wake_words = ["moonlight", "moon", "light"]
                        
                        wake_encontrada = None
                        for w in wake_words:
                            if re.search(rf'\b{w}\b', primeiras_palavras):
                                wake_encontrada = w
                                break
                                
                        if not wake_encontrada:
                            if "moon" in primeiras_palavras or "light" in primeiras_palavras:
                                wake_encontrada = "moonlight"
                            else:
                                continue

                        print(f"🗣️ [Whisper Ouviu]: {texto_ouvido}")
                        comando = re.sub(rf'^.*?\b({"|".join(wake_words)})[:\s,.:;!?-]*', '', texto_ouvido, count=1, flags=re.IGNORECASE).strip()

                        if not comando or len(comando) < 2:
                            self._falar_com_volume_maximo("Oi Arthur, estou ouvindo.", visualizador)
                            continue

                        cmd_lower = comando.lower()

                        # 1. COMANDO DE DATA APENAS (PRIORIDADE ABSOLUTA)
                        if any(k in cmd_lower for k in [
                            "data de hoje", "dia de hoje", "qual é a data", "que dia é", 
                            "a data de hoje", "qual a data", "que data"
                        ]):
                            hoje = datetime.datetime.now()
                            data_formatada = hoje.strftime("%d/%m/%Y")
                            
                            resposta = f"Arthur, a data de hoje é {data_formatada}."
                                        
                            print(f"🤖 [Moonlight Falando]: {resposta}")
                            self._falar_com_volume_maximo(resposta, visualizador)
                            continue

                        # 2. COMANDO DE HORA APENAS (PRIORIDADE ABSOLUTA)
                        if any(k in cmd_lower for k in [
                            "e a hora", "que horas são", "me diz as horas", "qual é a hora", 
                            "horas agora", "que horas", "a hora de hoje", "hora agora"
                        ]):
                            agora = datetime.datetime.now()
                            hora_formatada = agora.strftime("%H:%M")
                            
                            resposta = f"Arthur, agora são {hora_formatada}."
                                        
                            print(f"🤖 [Moonlight Falando]: {resposta}")
                            self._falar_com_volume_maximo(resposta, visualizador)
                            continue

                        # 3. COMANDO DE CANCELAMENTO DE COMPROMISSOS
                        if any(k in cmd_lower for k in ["cancela", "cancelar", "apaga", "apagar", "remove", "remover"]) and ("compromisso" in cmd_lower or "reunião" in cmd_lower or "reuniao" in cmd_lower or "tudo" in cmd_lower or "esses" in cmd_lower or "dois" in cmd_lower):
                            print(f"📅 [Google Calendar]: A cancelar compromissos de hoje...")
                            _, msg_retorno = self.cancelar_compromisso_hoje()
                            resposta = msg_retorno
                            print(f"🤖 [Moonlight Falando]: {resposta}")
                            self._falar_com_volume_maximo(resposta, visualizador)
                            continue

                        # 4. COMANDO DE AGENDAMENTO CONDICIONAL / DIRETO POR VOZ (BLINDADO E LIMPO)
                        if any(k in cmd_lower for k in ["marca", "agenda", "agendar", "agente"]) and any(h in cmd_lower for h in ["hora", "horas", "h", ":"]):
                            import re as regex_h
                            match_hora = regex_h.search(r'(\d{1,2})(?::(\d{2}))?\s*(?:h|horas)?', cmd_lower)
                            
                            if match_hora:
                                h_num = match_hora.group(1).zfill(2)
                                m_num = match_hora.group(2) if match_hora.group(2) else "00"
                                horario_alvo = f"{h_num}:{m_num}"
                                
                                if "trabalho" in cmd_lower or "reunião" in cmd_lower or "reuniao" in cmd_lower:
                                    titulo_alvo = "Reunião de trabalho"
                                else:
                                    titulo_alvo = "Compromisso"
                                
                                print(f"📅 [Google Calendar]: A criar '{titulo_alvo}' para as {horario_alvo}...")
                                sucesso, _ = self.criar_compromisso_hoje(horario_alvo, titulo_alvo)
                                resposta = f"Pronto, Arthur, agendei '{titulo_alvo}' para as {horario_alvo} de hoje." if sucesso else "Desculpa, Arthur, não consegui criar o evento no calendário."
                                
                                print(f"🤖 [Moonlight Falando]: {resposta}")
                                self._falar_com_volume_maximo(resposta, visualizador)
                                continue

                        # 5. COMANDO DE AGENDA DO GOOGLE CALENDAR
                        if any(k in cmd_lower for k in ["agenda", "compromissos", "o que tenho hoje", "tenho algo hoje"]):
                            hoje = datetime.datetime.now()
                            start_of_day = hoje.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
                            end_of_day = hoje.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'
                            
                            try:
                                service = self.get_calendar_service()
                                events_result = service.events().list(
                                    calendarId='primary',
                                    timeMin=start_of_day,
                                    timeMax=end_of_day,
                                    singleEvents=True,
                                    orderBy='startTime'
                                ).execute()
                                events = events_result.get('items', [])
                                
                                if not events:
                                    resposta = "Arthur, você não tem nenhum compromisso agendado para hoje."
                                else:
                                    resposta = f"Arthur, você tem {len(events)} compromisso(s) hoje:"
                                    for event in events:
                                        start = event['start'].get('dateTime', event['start'].get('date'))
                                        summary = event.get('summary', 'Sem título')
                                        if 'T' in start:
                                            hora = start.split('T')[1][:5]
                                            resposta += f" Às {hora} - {summary}."
                                        else:
                                            resposta += f" Todo o dia - {summary}."
                            except Exception:
                                resposta = "Não consegui aceder ao Google Calendar no momento, Arthur."
                                
                            print(f"🤖 [Moonlight Falando]: {resposta}")
                            self._falar_com_volume_maximo(resposta, visualizador)
                            continue

                        if re.match(r'^(?:oi|olá|ola|bom\s+dia|boa\s+tarde|boa\s+noite|bonitinho|tudo\s+bem|como\s+vai)[\s,?!.]*(?:tudo\s+bem|como\s+vai|com\s+você|contigo)?[\s,?!.]*$', cmd_lower):
                            texto_falar = "Tudo ótimo por aqui, Arthur! Pronta para ajudar. O que vamos fazer?"
                            print(f"🤖 [Moonlight Falando]: {texto_falar}")
                            self._falar_com_volume_maximo(texto_falar, visualizador)
                            continue

                        contato_envio, msg_envio = self.extrair_envio_whatsapp_natural(comando)
                        if contato_envio and msg_envio:
                            print(f"📱 [Ação Direta]: Enviando WhatsApp para '{contato_envio}': {msg_envio}")
                            enviado = self.whatsapp.enviar_mensagem(contato_envio, msg_envio)
                            texto_falar = f"Mensagem enviada para {contato_envio} no WhatsApp, Arthur." if enviado else "O WhatsApp ainda está sincronizando, Arthur."
                            print(f"🤖 [Moonlight Falando]: {texto_falar}")
                            self._falar_com_volume_maximo(texto_falar, visualizador)
                            continue

                        eh_envio_wpp = any(env in cmd_lower for env in ["manda", "envia", "escreve", "diga que", "fala para", "mandando", "perguntando", "dizendo"])
                        contato_especifico = self.extrair_contato_alvo_frase(comando)
                        
                        eh_leitura_wpp = (
                            not eh_envio_wpp
                            and ("whatsapp" in cmd_lower or "zap" in cmd_lower or "não lidas" in cmd_lower or "nao lidas" in cmd_lower or "mensagem" in cmd_lower or "mensagens" in cmd_lower or contato_especifico is not None)
                            and any(p in cmd_lower for p in ["quantas", "ler", "leia", "recebi", "quem", "olha", "veja", "vê", "tem", "preciso", "chegou", "importante", "novas"])
                        )

                        if eh_leitura_wpp:
                            if contato_especifico:
                                matches = [("ler_contato", contato_especifico)]
                            else:
                                matches = [("ler_whatsapp", "geral")]
                            texto_falar = ""
                        else:
                            print("🧠 [Cérebro a pensar...]")
                            payload = {
                                "model": self.modelo,
                                "prompt": f"{self.system_prompt}\n\nUtilizador: {comando}\nMoonlight:",
                                "stream": False,
                                "options": {"temperature": 0.1, "num_predict": 160}
                            }
                            resposta = requests.post(self.url_ollama, json=payload, timeout=60)
                            if resposta.status_code != 200:
                                continue
                            resp_cerebro = resposta.json().get("response", "").strip()
                            print(f"🤖 [Resposta Bruta]: {resp_cerebro}")

                            matches = re.findall(r'\[ACAO:\s*([^:]+):\s*([^\]]+)\]', resp_cerebro, re.IGNORECASE)
                            
                            tem_acao_wpp = any(t.strip().lower() in ["whatsapp", "zap"] for t, _ in matches)
                            if tem_acao_wpp:
                                matches = [(t, a) for t, a in matches if t.strip().lower() != "abrir"]

                            if not matches and ("pesquisar" in resp_cerebro.lower() or "pesquisa" in cmd_lower):
                                termo_busca = re.sub(r'^(?:pesquisa|pesquisar)\s+(?:para\s+mim\s+)?(?:na\s+internet\s+)?(?:sobre\s+|como\s+é\s+que\s+|como\s+)?', '', comando, flags=re.IGNORECASE).strip()
                                if termo_busca:
                                    matches = [("pesquisar", termo_busca)]

                            texto_falar = re.sub(r'\[ACAO:[^\]]+\]', '', resp_cerebro).strip()

                        for tipo, alvo in matches:
                            tipo, alvo = tipo.strip().lower(), alvo.strip()
                            
                            if tipo == "abrir":
                                if alvo.lower() in ["whatsapp", "zap", "artisan_rapid"]:
                                    texto_falar = "O WhatsApp já está conectado e pronto em segundo plano, Arthur."
                                    continue

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
                                        texto_falar = f"Pronto, abri o {alvo}, Arthur."
                                    else:
                                        texto_falar = f"Não encontrei o {alvo} instalado, Arthur."
                                except Exception as ex:
                                    print(f"❌ Erro crítico ao abrir '{alvo}': {ex}")
                                    texto_falar = f"Não consegui abrir o {alvo}, Arthur."
                                time.sleep(1.0)

                            elif tipo == "pesquisar":
                                print(f"🌍 [Executor]: A executar pesquisa web -> {alvo}")
                                texto_falar = self.web.pesquisar_internet(alvo)
                                
                            elif tipo == "escrever":
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

                            elif tipo == "agendar":
                                separador = "|" if "|" in alvo else ":"
                                if separador in alvo:
                                    horario, titulo = alvo.split(separador, 1)
                                    horario = horario.strip()
                                    titulo = titulo.strip()
                                else:
                                    horario = alvo.strip()
                                    titulo = "Compromisso"
                                
                                print(f"📅 [Google Calendar]: Agendando '{titulo}' para as {horario}...")
                                sucesso, _ = self.criar_compromisso_hoje(horario, titulo)
                                texto_falar = f"Pronto, Arthur, agendei '{titulo}' para as {horario} de hoje." if sucesso else "Desculpa, Arthur, não consegui criar o evento no calendário."

                            elif tipo == "cancelar":
                                print(f"📅 [Google Calendar]: A cancelar compromissos...")
                                _, msg_retorno = self.cancelar_compromisso_hoje(alvo)
                                texto_falar = msg_retorno

                            elif tipo in ["whatsapp", "zap"]:
                                separador = "|" if "|" in alvo else (":" if ":" in alvo else "-")
                                if separador in alvo:
                                    contato, msg = alvo.split(separador, 1)
                                    contato = contato.strip()
                                    msg = msg.strip()
                                    
                                    resto_fora = re.sub(r'\[ACAO:[^\]]+\]', '', resp_cerebro).strip()
                                    if resto_fora and len(resto_fora) < 40 and "arthur" not in resto_fora.lower():
                                        msg = f"{msg}. {resto_fora}"

                                    if contato.lower() == "arthur" or "sou a moonlight" in msg.lower():
                                        print("⚠️ [Bloqueio de Alucinação]: O modelo tentou enviar mensagem automática para 'Arthur'. Ignorado.")
                                        texto_falar = "Não consegui identificar o destinatário e a mensagem com clareza, Arthur. Pode repetir?"
                                    else:
                                        enviado = self.whatsapp.enviar_mensagem(contato, msg)
                                        texto_falar = f"Mensagem enviada para {contato} no WhatsApp, Arthur." if enviado else "O WhatsApp ainda está sincronizando, Arthur."

                            elif tipo == "ler_contato":
                                print(f"👁️ [Subsistema WhatsApp]: A verificar conversa específica de '{alvo}'...")
                                texto_falar, msgs_contato = self.whatsapp.solicitar_leitura_contato(alvo)
                                if msgs_contato:
                                    self.mensagens_pendentes_analise = msgs_contato.copy()
                                    for r, m in msgs_contato:
                                        self.ultimas_mensagens_processadas[r] = m
                                    self.whatsapp.marcar_como_lida(alvo)

                            elif tipo == "ler_whatsapp":
                                print("👁️ [Subsistema WhatsApp]: A solicitar leitura inteligente...")
                                resp_bruta, lista_completa = self.whatsapp.solicitar_leitura_contato(None)
                                
                                if not self.whatsapp.estado_whatsapp.get("carregado", False):
                                    texto_falar = resp_bruta
                                elif lista_completa:
                                    importantes = self.filtrar_mensagens_rapido(lista_completa)
                                    if importantes:
                                        texto_falar = self.montar_resumo_direto(lista_completa, importantes)
                                        self.aguardando_resposta_leitura = True
                                    else:
                                        texto_falar = f"Arthur, você tem {len(lista_completa)} conversas não lidas, mas são apenas promoções ou grupos secundários. Quer que eu leia mesmo assim?"
                                        self.mensagens_pendentes_analise = lista_completa.copy()
                                        self.aguardando_resposta_leitura = True
                                else:
                                    texto_falar = resp_bruta

                        if not texto_falar:
                            texto_falar = "Pronto, Arthur."

                        print(f"🤖 [Moonlight Falando]: {texto_falar}")
                        self._falar_com_volume_maximo(texto_falar, visualizador)

                    except Exception as e:
                        print(f"❌ [Erro no processamento de voz]: {e}")
            except Exception as loop_err:
                print(f"❌ [Erro no loop principal do cérebro]: {loop_err}")
                time.sleep(1)