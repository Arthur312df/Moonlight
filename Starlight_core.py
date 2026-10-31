import os
import json
import time
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
        """Busca a GEMINI_API_KEY nos Secrets do Streamlit ou no .env local."""
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
        except Exception:
            pass

        for k in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            val = os.getenv(k)
            if val:
                return val.strip()
        return None

    def _init_ai(self):
        """Inicializa o Gemini 3.8 na nuvem ou o Ollama localmente."""
        self.api_key = self._get_api_key()
        is_cloud = "mount/src" in os.getcwd() or os.getenv("STREAMLIT_SHARING_MODE") is not None

        if self.api_key or is_cloud:
            if not self.api_key:
                self.last_error = "Chave GEMINI_API_KEY não encontrada nos Secrets do Streamlit Cloud."
                return
            self.ai_mode = "gemini_api"
            self.last_error = ""
            return

        if not is_cloud:
            try:
                import ollama
                self.ollama = ollama
                self.ai_mode = "ollama"
                self.last_error = ""
            except ImportError:
                self.last_error = "Chave Gemini não configurada e Ollama local não encontrado."

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
            print(f"Erro ao salvar memória: {e}")

    def generate_response(self, prompt, system_prompt=""):
        if self.ai_mode == "fallback":
            self._init_ai()

        if self.ai_mode == "gemini_api":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            data = json.dumps(payload).encode("utf-8")
            
            # Tenta até 3 vezes caso dê timeout na rede
            ultimo_erro = ""
            for tentativa in range(3):
                try:
                    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                    # Timeout estendido para 60 segundos
                    with urllib.request.urlopen(req, timeout=60) as response:
                        res_body = json.loads(response.read().decode("utf-8"))
                        return res_body["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    ultimo_erro = str(e)
                    time.sleep(1.5)
                    continue
            
            return f"[Erro de Conexão Gemini após tentativas]: {ultimo_erro}"

        elif self.ai_mode == "ollama":
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = self.ollama.chat(model="mistral", messages=messages)
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