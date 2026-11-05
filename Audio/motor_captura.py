import logging
import time
import numpy as np
import sounddevice as sd
from collections import deque

class MotorCaptura:
    def __init__(self, sample_rate=16000, device_index=None, threshold=0.015, silencia_segundos=1.5):
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.threshold = threshold
        self.silencia_segundos = silencia_segundos
        logging.info("🎙️ [Motor Captura]: Inicializado com sucesso.")

    def ouvir_ate_silencio(self):
        frames_por_bloco = int(self.sample_rate * 0.1)  # blocos de 100ms
        tamanho_buffer = 5  # 0.5s de margem antes de falar
        buffer_circular = deque(maxlen=tamanho_buffer)
        
        audio_gravado = []
        a_gravar = False
        tempo_silencio_inicio = None

        # Garante que tenta reiniciar o stream se houver qualquer soluço do USB
        while True:
            try:
                with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                                    device=self.device_index, dtype='float32') as stream:
                    
                    logging.info("👂 [Motor Captura]: À escuta de voz (VAD ativo)...")
                    
                    while True:
                        try:
                            bloco, overflow = stream.read(frames_por_bloco)
                        except Exception:
                            # Se houver um overflow ou soluço momentâneo do hardware, repete o ciclo do bloco
                            continue
                            
                        bloco_flat = bloco.flatten()
                        energia = np.sqrt(np.mean(bloco_flat**2))
                        
                        if not a_gravar:
                            buffer_circular.append(bloco_flat)
                            if energia > self.threshold:
                                logging.info("🎙️ [Motor Captura]: Voz detetada! A gravar...")
                                a_gravar = True
                                audio_gravado.extend(list(buffer_circular))
                                buffer_circular.clear()
                        else:
                            audio_gravado.append(bloco_flat)
                            if energia < self.threshold:
                                if tempo_silencio_inicio is None:
                                    tempo_silencio_inicio = time.time()
                                elif time.time() - tempo_silencio_inicio >= self.silencia_segundos:
                                    logging.info("🎙️ [Motor Captura]: Fim de frase detetado por silêncio.")
                                    break
                            else:
                                tempo_silencio_inicio = None
                    break # Sai do while exterior se terminou a captação com sucesso
                    
            except Exception as e:
                # Se o dispositivo USB falhar momentaneamente, aguarda 0.5s e tenta reabrir o stream automaticamente
                time.sleep(0.5)
                continue

        if len(audio_gravado) > 0:
            return np.concatenate(audio_gravado)
        return None