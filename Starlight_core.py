import os
import json
import urllib.request
import urllib.error
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
        self.api_key = None
        
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
                for sec_val in st.secrets.values():
                    if isinstance(sec_val, dict):
                        for k, v in sec_val.items():
                            if "mistral" in k.lower() or "key" in k.lower():
                                return str(v).strip()
        except Exception as e:
            self.last_error = f"Erro ao ler st.secrets: {e}"

        api_key = os.getenv("MISTRAL_API_KEY")
        return api_key.strip() if api_key else None

    def _init_ai(self):
        """Inicializa a ligação direta à Mistral (Nuvem) ou Ollama (Local)."""
        self.api_key = self._get_api_key()
        is_cloud = "mount/src" in os.getcwd() or os.getenv("STREAMLIT_SHARING_MODE") is not None

        if self.api_key or is_cloud:
            if not self.api_key:
                self.last_error = "Chave MISTRAL_API_KEY não encontrada nos Secrets do Streamlit."
                return
            self.ai_mode = "mistral_api"
            self.last_error = ""
            return

        if not is_cloud:
            try:
                import ollama
                self.ollama = ollama
                self.ai_mode = "ollama"
                self.last_error = ""
            except ImportError:
                self.last_error = "Nem chave da Mistral nem Ollama local disponíveis."

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

                # Chamada direta à API da Mistral sem depender de pacotes externos
                url = "https://api.mistral.ai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                data = json.dumps({
                    "model": "mistral-small-latest",
                    "messages": messages
                }).encode("utf-8")

                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    return res_body["choices"][0]["message"]["content"]

            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8")
                return f"[Erro API Mistral ({e.code})]: Verifica a tua chave nos Secrets. Detalhe: {err_msg}"
            except Exception as e:
                return f"[Erro na Ligação à Mistral]: {str(e)}"
        
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