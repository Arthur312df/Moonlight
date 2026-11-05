import pystray
from PIL import Image, ImageDraw
import threading

class MoonlightTray:
    def __init__(self, callback_restaurar, callback_sair):
        self.callback_restaurar = callback_restaurar
        self.callback_sair = callback_sair
        self.icon = None

    def criar_icone_padrao(self):
        # Cria um ícone visual simples (um círculo azul escuro com uma lua/estrela)
        image = Image.new('RGB', (64, 64), color=(15, 15, 20))
        dc = ImageDraw.Draw(image)
        dc.ellipse([16, 16, 48, 48], fill=(0, 220, 255))
        return image

    def iniciar(self):
        imagem_icone = self.criar_icone_padrao()
        
        menu = pystray.Menu(
            pystray.MenuItem('Abrir Interface', self.on_restaurar),
            pystray.MenuItem('Sair da Moonlight', self.on_sair)
        )

        self.icon = pystray.Icon("MoonlightAI", imagem_icone, "Moonlight v1.0", menu)
        
        # Roda o ícone em uma thread separada para não travar o app principal
        thread_tray = threading.Thread(target=self.icon.run, daemon=True)
        thread_tray.start()

    def on_restaurar(self, icon, item):
        if self.callback_restaurar:
            self.callback_restaurar()

    def on_sair(self, icon, item):
        if self.icon:
            self.icon.stop()
        if self.callback_sair:
            self.callback_sair()