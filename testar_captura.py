import logging
import io
import wave
import numpy as np
import speech_recognition as sr
from Audio.motor_captura import MotorCaptura

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s")

def numpy_para_audio_data(audio_np, sample_rate=16000):
    """Converte o array numpy do nosso motor de captura para o formato que o SpeechRecognition entende."""
    # Normaliza e converte para PCM de 16-bits
    audio_int16 = (audio_np * 32767).astype(np.int16)
    
    # Cria um ficheiro WAV virtual em memória
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 2 bytes para int16
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    
    wav_io.seek(0)
    
    # Retorna o objeto AudioData
    r = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        return r.record(source)

if __name__ == "__main__":
    print("🚀 A iniciar o teste de Captura e Transcrição Inteligente...")
    
    motor = MotorCaptura(sample_rate=16000, device_index=1)
    recognizer = sr.Recognizer()
    
    print("\n🎙️ [Teste Ativo]: Podes falar livremente...")
    print("O sistema vai gravar por VAD e transcrever o que disseste a seguir.")
    
    while True:
        # 1. Captura a voz usando o nosso motor inteligente (para por silêncio)
        audio_capturado = motor.ouvir_ate_silencio()
        
        if audio_capturado is not None and len(audio_capturado) > 0:
            duracao = len(audio_capturado) / 16000
            print(f"\n📊 Áudio capturado ({duracao:.2f}s). A transcrever...")
            
            try:
                # 2. Transmite para o reconhecedor de voz em PT-BR
                audio_data = numpy_para_audio_data(audio_capturado)
                texto = recognizer.recognize_google(audio_data, language="pt-BR")
                
                print(f"🗣️ [Transcrição Exata]: {texto}")
                
            except sr.UnknownValueError:
                print("⚠️ [Aviso]: O áudio foi capturado, mas não foi possível entender as palavras (ruído ou silêncio).")
            except sr.RequestError as e:
                print(f"❌ [Erro na API de transcrição]: {e}")
                
        print("\n--------------------------------------------------")
        print("🎙️ Podes falar outra frase (ou Ctrl+C para sair)...")