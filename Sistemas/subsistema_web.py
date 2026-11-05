import os
import subprocess
import urllib.parse
import logging

class SubsistemaWeb:
    def __init__(self):
        logging.info("🌍 [Subsistema Web]: Módulo inicializado.")

    def pesquisar_internet(self, termo):
        """Abre o navegador padrão com uma pesquisa do Google para o termo fornecido."""
        try:
            termo_limpo = termo.strip()
            print(f"🌍 [Subsistema Web]: A pesquisar na internet -> '{termo_limpo}'")
            
            # Codifica o termo para URL de forma segura
            termo_codificado = urllib.parse.quote(termo_limpo)
            url_pesquisa = f"https://www.google.com/search?q={termo_codificado}"
            
            # Abre no navegador padrão do sistema
            subprocess.Popen(f'start "" "{url_pesquisa}"', shell=True)
            return f"Pesquisei por {termo_limpo} na internet, Arthur."
        except Exception as e:
            print(f"❌ [Erro ao pesquisar na internet]: {e}")
            return "Tive um problema ao tentar abrir a pesquisa na internet, Arthur."