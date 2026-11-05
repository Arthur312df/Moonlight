import logging
import time
import queue
import numpy as np
import sounddevice as sd

class MotorCaptura:
    def __init__(self, sample_rate=16000, device_index=None, threshold=0.003, silencia_segundos=1.5):
        self.sample_rate = sample_rate
        self.silencia_segundos = silencia_segundos
        self.threshold = threshold
        self.device_index = device_index
        
        if self.device_index is None:
            try:
                devices = sd.query_devices()
                for idx, dev in enumerate(devices):
                    if dev['max_input_channels'] > 0:
                        self.device_index = idx
                        print(f"🎙️ [Motor Captura]: Microfone detetado -> {dev['name']} (ID: {idx})")
                        break
            except Exception:
                pass
                
        logging.info("🎙️ [Motor Captura]: Inicializado com sucesso.")

    def ouvir_ate_silencio(self):
        q = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                pass
            q.put(indata.copy())

        audio_gravado = []
        a_gravar = False
        tempo_silencio_inicio = None
        buffer_pre_fala = []

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1,
                                device=self.device_index, dtype='float32',
                                callback=callback):
                
                logging.info("👂 [Motor Captura]: À escuta de voz...")

                while True:
                    try:
                        bloco = q.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    bloco_flat = bloco.flatten()
                    energia = np.sqrt(np.mean(bloco_flat**2))

                    if not a_gravar:
                        buffer_pre_fala.append(bloco_flat)
                        if len(buffer_pre_fala) > 5:
                            buffer_pre_fala.pop(0)
                            
                        if energia > self.threshold:
                            print(f"\n🎙️ [Motor Captura]: Voz detetada! (Energia: {energia:.5f}). A gravar...")
                            a_gravar = True
                            audio_gravado.extend(buffer_pre_fala)
                            buffer_pre_fala.clear()
                    else:
                        audio_gravado.append(bloco_flat)
                        if energia < self.threshold:
                            if tempo_silencio_inicio is None:
                                tempo_silencio_inicio = time.time()
                            elif time.time() - tempo_silencio_inicio >= self.silencia_segundos:
                                print("🎙️ [Motor Captura]: Fim de frase detetado por silêncio.")
                                break
                        else:
                            tempo_silencio_inicio = None
                            
        except Exception as e:
            print(f"❌ [Erro no InputStream]: {e}")
            time.sleep(0.5)

        if len(audio_gravado) > 0:
            return np.concatenate(audio_gravado)
        return None