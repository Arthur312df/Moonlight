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
        self.ai_mode = "fallback"
        self.last_error = "Nenhum motor inicializado."
        self.gemini_client = None
        
        self._init_ai()
        self.load_memory()

    def _get_api_key(self):
        """Procura a chave nos Secrets do Streamlit ou no .env."""
        api_key = None
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                for k in ["GEMINI_API_KEY", "gemini_api_key", "GOOGLE_API_KEY"]:
                    if k in st.secrets:
                        return str(st.secrets[k]).strip()
                for sec_val in st.secrets.values():
                    if isinstance(sec_val, dict):
                        for k, v in sec_val.items():
                            if "gemini" in k.lower() or "api_key" in k.lower():
                                return str(v).strip()
        except Exception as e:
            self.last_error = f"Erro ao ler st.secrets: {e}"

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return api_key.strip() if api_key else None

    def _init_ai(self):
        """Inicializa o Gemini (Nuvem/Key) ou Ollama (Local)."""
        api_key = self._get_api_key()
        is_cloud = "mount/src" in os.getcwd() or os.getenv("STREAMLIT_SHARING_MODE") is not None

        if api_key or is_cloud:
            try:
                from google import genai
                if not api_key:
                    self.last_error = "Chave GEMINI_API_KEY não encontrada nos Secrets do Streamlit."
                    return
                self.gemini_client = genai.Client(api_key=api_key)
                self.ai_mode = "gemini"
                self.last_error = ""
                return
            except ImportError:
                self.last_error = "A biblioteca 'google-genai' não está instalada no servidor."
                return
            except Exception as e:
                self.last_error = f"Falha ao iniciar cliente Gemini: {str(e)}"
                return

        if not is_cloud:
            try:
                import ollama
                self.ollama = ollama
                self.ai_mode = "ollama"
                self.last_error = ""
            except ImportError:
                self.last_error = "Nem Gemini nem Ollama disponíveis."

    def load_memory(self):
        if Path(self.memory_file).exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception:
                self.memory = {"base_layer": [], "level_2": {}, "level_3": {}}
        else:
            self.memory = {"base_layer": [], "level_2": {}, "level_3": {}}

    def save_memory(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao guardar memória: {e}")

    def generate_response(self, prompt, system_prompt=""):
        if self.ai_mode == "fallback":
            self._init_ai()

        if self.ai_mode == "gemini":
            full_prompt = f"{system_prompt}\n\nUtilizador: {prompt}" if system_prompt else prompt
            # Lista de modelos por ordem de prioridade (incluindo o exigido pela API)
            modelos = ['gemini-3.8-flash', 'gemini-3.0-flash', 'gemini-2.0-flash']
            ultimo_erro = ""
            
            for modelo in modelos:
                try:
                    response = self.gemini_client.models.generate_content(
                        model=modelo,
                        contents=full_prompt
                    )
                    return response.text
                except Exception as e:
                    ultimo_erro = str(e)
                    continue
                    
            return f"[Erro na API do Gemini]: {ultimo_erro}"
        
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
            return f"⚠️ [Diagnóstico StarLight]: {self.last_error}"

    def processar_mensagem(self, prompt, system_prompt=""):
        try:
            return self.generate_response(prompt, system_prompt)
        except Exception as e:
            return f"[Erro Crítico]: {str(e)}"