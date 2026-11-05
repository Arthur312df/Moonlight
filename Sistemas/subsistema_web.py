import warnings
warnings.filterwarnings("ignore")
from ddgs import DDGS
import webbrowser
import urllib.parse

class SubsistemaWeb:
    def __init__(self):
        print("🌍 [Subsistema Web]: Módulo de internet inicializado com sucesso.")

    def pesquisar(self, termo, abrir_navegador=True):
        """Faz a busca na web via DDGS, abre a página no browser e retorna o resumo para voz."""
        print(f"🔍 [Subsistema Web]: A pesquisar -> '{termo}'")
        try:
            resultados = []
            primeiro_link = None
            busca = DDGS().text(termo, region='pt-br', max_results=3)
            
            for r in busca:
                titulo = r.get('title', '')
                corpo = r.get('body', '')
                link = r.get('href', '')
                
                if link and not primeiro_link:
                    primeiro_link = link
                if corpo:
                    resultados.append(f"{titulo}: {corpo}")
            
            # Abre a página no navegador padrão
            if abrir_navegador:
                if primeiro_link:
                    print(f"🌐 [Subsistema Web]: A abrir página -> {primeiro_link}")
                    webbrowser.open(primeiro_link)
                else:
                    url_google = f"https://www.google.com/search?q={urllib.parse.quote(termo)}"
                    print(f"🌐 [Subsistema Web]: A abrir pesquisa no Google -> {url_google}")
                    webbrowser.open(url_google)

            if resultados:
                texto_final = " | ".join(resultados)
                print(f"📄 [Dados da Web]: {texto_final[:180]}...")
                return texto_final
                
            print("⚠️ [Subsistema Web]: A busca não retornou textos diretos.")
            return "Abri a pesquisa no seu navegador."
        except Exception as e:
            print(f"❌ Erro no Subsistema Web: {e}")
            if abrir_navegador:
                url_google = f"https://www.google.com/search?q={urllib.parse.quote(termo)}"
                webbrowser.open(url_google)
            return "Abri a pesquisa diretamente no seu navegador."