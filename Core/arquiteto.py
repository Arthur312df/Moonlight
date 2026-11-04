# arquiteto.py
import logging
import sys
import os
import numpy as np
import sounddevice as sd
from subsistema_pc import SubsistemaPC

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from kokoro import KPipeline
    KOKORO_DISPONIVEL = True
    logging.info("🔊 [Kokoro TTS]: Módulo Kokoro carregado com sucesso.")
except ImportError as e:
    KOKORO_DISPONIVEL = False
    logging.warning(f"🔊 [Kokoro TTS]: Não foi possível importar o Kokoro: {e}")

class Arquiteto:
    def __init__(self):
        logging.info("🧠 [Cérebro - Arquiteto]: Inicializado e pronto para decidir.")
        self.subsistema_pc = SubsistemaPC()
        
        self.pipeline_tts = None
        if KOKORO_DISPONIVEL:
            try:
                self.pipeline_tts = KPipeline(lang_code='a')
                logging.info("🔊 [Kokoro TTS]: Pipeline de voz inicializado em Inglês!")
            except Exception as e:
                logging.error(f"🔊 [Kokoro TTS]: Erro ao inicializar o KPipeline: {e}")

    def falar(self, texto: str):
        """Método central para acionar a resposta falada (Kokoro TTS)"""
        logging.info(f"🔊 [Moonlight - Falando]: {texto}")
        
        if not self.pipeline_tts:
            logging.warning("🔊 [Kokoro TTS]: Pipeline inativo. A simular fala apenas por log.")
            return

        try:
            generator = self.pipeline_tts(
                texto, voice='af_bella',
                speed=1.0, split_pattern=r'\n+'
            )
            
            for i, (gs, ps, audio) in enumerate(generator):
                if audio is not None and len(audio) > 0:
                    sample_rate = 24000
                    sd.play(audio, sample_rate)
                    sd.wait()
                    
        except Exception as e:
            logging.error(f"🔊 [Erro no TTS/Kokoro]: Falha ao reproduzir áudio: {e}")

    def processar_comando(self, texto: str):
        if not texto:
            return
            
        texto_limpo = texto.lower().strip()
        logging.info(f"🧠 [Cérebro - Arquiteto]: Texto recebido para análise -> '{texto}'")
        
        # 1. Deteção prioritária de aplicativos (para não falhar com "open not bad", etc.)
        mapa_sinonimos = {
            "notepad": "notepad",
            "not bad": "notepad",
            "not pad": "notepad",
            "no pad": "notepad",
            "note pad": "notepad",
            "bloco de notas": "notepad",
            "browser": "browser",
            "navegador": "browser",
            "internet": "browser",
            "google": "browser",
            "steam": "steam",
            "league of legends": "league of legends",
            "lol": "league of legends",
            "blender": "blender",
            "photoshop": "photoshop",
            "explorador": "explorer",
            "pastas": "explorer"
        }
        
        app_alvo = None
        for chave, valor in mapa_sinonimos.items():
            if chave in texto_limpo:
                app_alvo = valor
                break
        
        if app_alvo:
            self.falar(f"Opening {app_alvo} for you.")
            logging.info(f"🧠 [Cérebro]: Intenção detetada. Delegando '{app_alvo}' para o subsistema_pc...")
            sucesso = self.subsistema_pc.abrir_aplicativo(app_alvo)
            
            if not sucesso:
                self.falar(f"Sorry, I couldn't open {app_alvo}.")
            return

        # 2. Verificação de estado / ativação (apenas se não for um comando de app)
        if any(cmd in texto_limpo for cmd in ["moonlight", "hear me", "you there", "can you hear"]):
            self.falar("Yes, I can hear you perfectly. How can I help?")
            return

        # 3. Caso nenhuma intenção seja reconhecida
        logging.info(f"🧠 [Cérebro]: Nenhuma ação mapeada para: '{texto}'")
        self.falar("Sorry, I haven't learned how to do that yet.")