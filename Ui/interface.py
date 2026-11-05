import os
import webview
import multiprocessing
import time
import threading

def _executar_webview(queue_comandos, event_fechar):
    # Obtém o diretório atual do ficheiro interface.py
    diretorio_ui = os.path.dirname(os.path.abspath(__file__))
    caminho_html = os.path.join(diretorio_ui, 'interface_ui.html')

    window = webview.create_window(
        'Moonlight AI', 
        caminho_html,  # <--- Usa o caminho absoluto correto
        width=850, 
        height=850, 
        background_color='#010206',
        frameless=True,
        transparent=True
    )
    # Restante do código...

    def worker_comandos():
        time.sleep(1.5)
        while not event_fechar.is_set():
            try:
                if not queue_comandos.empty():
                    cmd = queue_comandos.get()
                    if cmd == 'speaking':
                        window.evaluate_js("setMode('speaking')")
                    elif cmd == 'idle':
                        window.evaluate_js("setMode('idle')")
                    elif cmd == 'listening':
                        window.evaluate_js("setMode('listening')")
            except Exception:
                pass
            time.sleep(0.05)

    threading.Thread(target=worker_comandos, daemon=True).start()
    
    # Quando a janela fecha, sinalizamos o evento de fecho
    webview.start()
    event_fechar.set()

class VisualizadorMoonlight:
    def __init__(self):
        self.queue_comandos = multiprocessing.Queue()
        self.event_fechar = multiprocessing.Event()
        self.processo_ui = None

    def start_window(self):
        self.processo_ui = multiprocessing.Process(
            target=_executar_webview, 
            args=(self.queue_comandos, self.event_fechar), 
            daemon=True
        )
        self.processo_ui.start()

    def set_serene(self):
        self.queue_comandos.put('idle')

    def set_listening(self):
        self.queue_comandos.put('listening')

    def set_speaking(self):
        self.queue_comandos.put('speaking')

    def esta_aberto(self):
        if self.processo_ui:
            return self.processo_ui.is_alive() and not self.event_fechar.is_set()
        return False

    def fechar(self):
        self.event_fechar.set()
        if self.processo_ui and self.processo_ui.is_alive():
            self.processo_ui.terminate()
            self.processo_ui.join()