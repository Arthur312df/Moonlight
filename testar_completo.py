import logging
import io
import wave
import numpy as np
import speech_recognition as sr
from Audio.motor_captura import MotorCaptura
from Audio.sintetizador import SintetizadorVoz
from Core.cerebro import CerebroLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s")

def numpy_para_audio_data(audio_np, sample_rate=16000):
    audio_int16 = (audio_np * 32767).astype(np.int16)
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    wav_io.seek(0)
    
    r = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        return r.record(source)

if __name__ == "__main__":
    print("🚀 A iniciar a Moonlight (Sistema Completo: Voz + Cérebro + Fala)...")
    
    # Inicializa todos os módulos
    motor = MotorCaptura(sample_rate=16000, device_index=1)
    cerebro = CerebroLocal(modelo="mistral")
    sintetizador = SintetizadorVoz()
    recognizer = sr.Recognizer()
    
    print("\n🎙️ [Moonlight Pronta]: Podes falar livremente com a tua assistente...")
    
    while True:
        try:
            # 1. Ouve até haver silêncio (VAD)
            audio_capturado = motor.ouvir_ate_silencio()
            
            if audio_capturado is not None and len(audio_capturado) > 0:
                duracao = len(audio_capturado) / 16000
                print(f"\n📊 Áudio capturado ({duracao:.2f}s). A transcrever...")
                
                try:
                    # 2. Transcreve o áudio
                    audio_data = numpy_para_audio_data(audio_capturado)
                    texto_utilizador = recognizer.recognize_google(audio_data, language="pt-BR")
                    print(f"🗣️ [Tu]: {texto_utilizador}")
                    
                    # 3. Processa no Cérebro (Mistral)
                    print("🧠 [Moonlight a pensar...]")
                    resposta_cerebro = cerebro.pensar(texto_utilizador)
                    print(f"🤖 [Moonlight]: {resposta_cerebro}")
                    
                    # 4. Fala a resposta em voz alta (Kokoro)
                    sintetizador.falar(resposta_cerebro)
                    
                except sr.UnknownValueError:
                    print("⚠️ [Aviso]: Não consegui entender o que disseste.")
                except sr.RequestError as e:
                    print(f"❌ [Erro na API de transcrição]: {e}")
                    
            print("\n--------------------------------------------------")
            print("👂 À escuta da próxima frase...")
            
        except KeyboardInterrupt:
            print("\n🛑 A encerrar a Moonlight. Até breve, Arthur!")
            break