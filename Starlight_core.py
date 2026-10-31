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
        
        # Deteta se estamos no Streamlit Cloud
        self.is_cloud = (
            "mount/src" in os.getcwd() or 
            os.getenv("STREAMLIT_SHARING_MODE") is not None
        )
        
        # Obter a chave de API (lendo do st.secrets na nuvem ou do .env localmente)
        api_key = None
        if self.is_cloud:
            try:
                import streamlit as st
                if "GEMINI_API_KEY" in st.secrets:
                    api_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass
        
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")

        # Inicialização do motor de IA
        self.ai_mode = "fallback"
        if api_key:
            try:
                from google import genai
                # Inicialização correta com a chave explícita
                self.gemini_client = genai.Client(api_key=api_key)
                self.ai_mode = "gemini"
            except Exception as e:
                print(f"Erro ao inicializar Gemini: {e}")
        
        if self.ai_mode == "fallback" and not self.is_cloud:
            try:
                import ollama
                self.ollama = ollama
                self.ai_mode = "ollama"
            except ImportError:
                pass

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
        if self.ai_mode == "gemini":
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
        
        elif self.ai_mode == "ollama":
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
                return f"[Erro Ollama Local]: {str(e)}"
        else:
            return "[Erro]: Chave de API do Gemini não detetada. Configura os Secrets no Streamlit Cloud."

    def processar_mensagem(self, prompt, system_prompt=""):
        """Método de compatibilidade robusto exigido pela interface starlight_app.py"""
        try:
            return self.generate_response(prompt, system_prompt)
        except Exception as e:
            return f"[Erro de Execução]: {str(e)}"