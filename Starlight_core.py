import os
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class StarLightCore:
    def __init__(self, memory_file="starlight_memory.json", brain_file="starlight_brain.json"):
        self.memory_file = memory_file
        self.brain_file = brain_file
        
        # Deteta se estamos no Streamlit Cloud ou ambiente de produção na nuvem
        self.is_cloud = (
            "mount/src" in os.getcwd() or 
            os.getenv("STREAMLIT_SHARING_MODE") is not None or 
            os.getenv("GEMINI_API_KEY") is not None
        )
        
        # Inicialização do motor de IA com base no ambiente
        if self.is_cloud:
            try:
                from google import genai
                api_key = os.getenv("GEMINI_API_KEY")
                self.gemini_client = genai.Client(api_key=api_key) if api_key else genai.Client()
                self.ai_mode = "gemini"
            except Exception as e:
                print(f"Erro ao inicializar Gemini na nuvem: {e}")
                self.ai_mode = "fallback"
        else:
            try:
                import ollama
                self.ollama = ollama
                self.ai_mode = "ollama"
            except ImportError:
                print("Biblioteca 'ollama' não encontrada. A operar em modo de fallback.")
                self.ai_mode = "fallback"

        self.load_memory()

    def load_memory(self):
        """Carrega o sistema de memória hierárquica."""
        if Path(self.memory_file).exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception:
                self.memory = {"base_layer": [], "level_2": {}, "level_3": {}}
        else:
            self.memory = {"base_layer": [], "level_2": {}, "level_3": {}}

    def save_memory(self):
        """Guarda o estado atual da memória localmente."""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao guardar memória: {e}")

    def generate_response(self, prompt, system_prompt=""):
        """Gera uma resposta utilizando o motor de IA ativo."""
        if self.ai_mode == "ollama":
            try:
                response = self.ollama.chat(
                    model='mistral',
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ]
                )
                return response['message']['content']
            except Exception as e:
                return f"[Erro Ollama Local]: Certifica-te de que o Ollama está a correr no PC. Detalhe: {str(e)}"
        
        elif self.ai_mode == "gemini":
            try:
                full_prompt = f"{system_prompt}\n\nUtilizador: {prompt}" if system_prompt else prompt
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt
                )
                return response.text
            except Exception as e:
                try:
                    response = self.gemini_client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=full_prompt
                    )
                    return response.text
                except Exception as e2:
                    return f"[Erro Gemini Cloud]: {str(e2)}"
        else:
            return "Modo de IA não configurado corretamente ou dependências em falta."

    def processar_mensagem(self, prompt, system_prompt=""):
        """Método de compatibilidade robusto exigido pela interface starlight_app.py"""
        try:
            return self.generate_response(prompt, system_prompt)
        except Exception as e:
            if self.is_cloud:
                return f"[Erro na Nuvem]: Ocorreu um problema ao comunicar com a IA. Detalhe: {str(e)}. Verifica se configuraste a GEMINI_API_KEY nos Secrets do Streamlit."
            else:
                return f"[Erro Local]: {str(e)}"