import os
import logging
import sounddevice as sd
import numpy as np
from kokoro_onnx import Kokoro

class SintetizadorVoz:
    def __init__(self, voz_padrao="pf_dora"):
        self.voz_padrao = voz_padrao
        
        # Diretório atual (Audio/) e diretório raiz (C:\Moonlight)
        diretorio_audio = os.path.dirname(os.path.abspath(__file__))
        diretorio_raiz = os.path.dirname(diretorio_audio)
        
        modelo_path = os.path.join(diretorio_audio, "kokoro-v1.0.fp16.onnx")
        
        # Procura o binário de vozes na raiz ou na pasta Audio
        voces_path_candidatos = [
            os.path.join(diretorio_raiz, "voices-v1.0.bin"),
            os.path.join(diretorio_raiz, "voices-1.0.bin"),
            os.path.join(diretorio_audio, "voices-v1.0.bin"),
            os.path.join(diretorio_audio, "voices-1.0.bin")
        ]
        
        voces_path = None
        for candidato in voces_path_candidatos:
            if os.path.exists(candidato):
                voces_path = candidato
                break
                
        try:
            logging.info("🗣️ [Sintetizador]: A carregar o modelo Kokoro...")
            if not os.path.exists(modelo_path):
                raise FileNotFoundError(f"Ficheiro ONNX não encontrado em: {modelo_path}")
            if not voces_path:
                raise FileNotFoundError("Ficheiro de vozes (.bin) não encontrado na raiz nem na pasta Audio.")
                
            self.kokoro = Kokoro(modelo_path, voces_path)
            logging.info("🗣️ [Sintetizador]: Kokoro inicializado com sucesso!")
        except Exception as e:
            logging.error(f"❌ [Sintetizador]: Erro ao carregar o Kokoro: {e}")
            self.kokoro = None

    def falar(self, texto):
        if not texto or not self.kokoro:
            return
            
        try:
            logging.info(f"🗣️ [Sintetizador]: A sintetizar voz para: '{texto}'")
            samples, sample_rate = self.kokoro.create(
                texto, 
                voice=self.voz_padrao, 
                speed=1.0, 
                lang="pt-br"
            )
            
            if samples is not None and len(samples) > 0:
                sd.play(samples, samplerate=sample_rate)
                sd.wait()
                
        except Exception as e:
            logging.error(f"❌ [Sintetizador]: Erro durante a síntese de voz: {e}")