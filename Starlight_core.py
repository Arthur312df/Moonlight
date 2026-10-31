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
        self.mistral_client = None
        
        self._init_ai()
        self.load_memory()

    def _get_api_key(self):
        """Procura a chave MISTRAL_API_KEY nos Secrets do Streamlit ou no .env."""
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                for k in ["MISTRAL_API_KEY", "mistral_api_key"]:
                    if k in st.secrets:
                        return str(st.secrets[k]).strip()
                # Caso esteja dentro de alguma secção TOML nos Secrets
                for sec_val in st.secrets.values():
                    if isinstance(sec_val, dict):
                        for k, v in sec_val.items():
                            if "mistral" in k.lower() and "key" in k.lower():
                                return str(v).strip()
        except Exception as e:
            self.last_error = f"Erro ao ler st.secrets: {e}"

        api_key = os.getenv("MISTRAL_API_KEY")
        return api_key.strip() if api_key else None

    def _init_ai(self):
        """Inicializa a API da Mistral (Nuvem/Key) ou o Ollama (Local)."""
        api_key = self._get_api_key()
        is_cloud = "mount/src" in os.getcwd() or os.getenv("STREAMLIT_SHARING_MODE") is not None

        if api_key or is_cloud:
            try:
                from mistralai import Mistral
                if not api_key:
                    self.last_error = "Chave MISTRAL_API_KEY não encontrada nos Secrets do Streamlit."
                    return
                self.mistral_client = Mistral(api_key=api_key)
                self.ai_mode = "mistral_api"
                self.last_error = ""
                return
            except ImportError:
                self.last_error = "A biblioteca 'mistralai' não está instalada. Verifica o requirements.txt."
                return
            except Exception as e:
                self.last_error = f"Falha ao iniciar cliente Mistral: {str(e)}"
                return

        # Se estiver a correr localmente sem chave de nuvem, usa o Ollama
        if not is_cloud:
            try:
                import ollama
                self.ollama = ollama
                self.ai_mode = "ollama"
                self.last_error = ""
            except ImportError:
                self.last_error = "Nem API da Mistral nem Ollama local estão disponíveis."

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

        if self.ai_mode == "mistral_api":
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.mistral_client.chat.complete(
                    model="mistral-small-latest",
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"[Erro na API da Mistral]: {str(e)}"
        
        elif self.ai_mode == "ollama":
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.ollama.chat(
                    model="mistral",
                    messages=messages
                )
                return response["message"]["content"]
            except Exception as e:
                return f"[Erro Ollama Local]: {str(e)}"
        else:
            return f"⚠️ [Diagnóstico StarLight]: {self.last_error}"

    def processar_mensagem(self, prompt, system_prompt=""):
        try:
            return self.generate_response(prompt, system_prompt)
        except Exception as e:
            return f"[Erro Crítico]: {str(e)}"