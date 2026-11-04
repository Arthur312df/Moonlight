import subprocess
import time
import pyautogui
import pyperclip
import os
import pygetwindow as gw

class SubsistemaPC:
    def __init__(self):
        print("💻 [Subsistema PC]: Módulo de automação (Discord & WhatsApp) inicializado.")

    def focar_janela(self, titulo_parcial):
        """Procura uma janela aberta pelo nome, restaura se estiver minimizada e traz para frente."""
        for _ in range(10): # Tenta por até 5 segundos
            janelas = gw.getWindowsWithTitle(titulo_parcial)
            if janelas:
                janela = janelas[0]
                try:
                    if janela.isMinimized:
                        janela.restore()
                    janela.activate()
                    return True
                except Exception:
                    pass
            time.sleep(0.5)
        return False

    def enviar_mensagem_discord(self, contato, mensagem, caminho_discord="discord"):
        """Abre/foca o Discord, busca o contato via Ctrl+K e envia a mensagem."""
        print(f"💬 [Subsistema PC - Discord]: Preparando envio para '{contato}' -> '{mensagem}'")
        try:
            # 1. Tenta focar se já estiver aberto; se não, abre o Discord
            if not self.focar_janela("Discord"):
                update_exe = os.path.expanduser(r"~\AppData\Local\Discord\Update.exe")
                if os.path.exists(update_exe):
                    subprocess.Popen(f'"{update_exe}" --processStart Discord.exe', shell=True)
                else:
                    subprocess.Popen('start discord:', shell=True)
                
                time.sleep(3.0)
                self.focar_janela("Discord")

            time.sleep(1.0)

            # 2. Aperta ESC duas vezes para fechar qualquer janela/modal aberto dentro do Discord
            pyautogui.press('esc')
            time.sleep(0.2)
            pyautogui.press('esc')
            time.sleep(0.3)

            # 3. Aperta Ctrl + K para abrir a busca rápida do Discord
            print(f"⌨️ [Discord]: Buscando contato '{contato}'...")
            pyautogui.hotkey('ctrl', 'k')
            time.sleep(0.8)

            # 4. Cola o nome do contato e aperta Enter
            pyperclip.copy(contato)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1.2)
            pyautogui.press('enter')
            time.sleep(1.0)

            # 5. Cola a mensagem e aperta Enter para enviar
            print(f"📨 [Discord]: Digitando mensagem '{mensagem}'...")
            pyperclip.copy(mensagem)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')

            print("✅ [Discord]: Sequência de envio concluída!")
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem no Discord: {e}")
            return False

    def enviar_mensagem_whatsapp(self, contato, mensagem, caminho_whatsapp="whatsapp:"):
        """Abre/foca o WhatsApp Desktop, busca o contato via Ctrl+F e envia a mensagem."""
        print(f"🟢 [Subsistema PC - WhatsApp]: Preparando envio para '{contato}' -> '{mensagem}'")
        try:
            subprocess.Popen('start whatsapp:', shell=True)
            time.sleep(2.0)
            self.focar_janela("WhatsApp")
            time.sleep(1.5)

            print(f"⌨️ [WhatsApp]: Buscando contato '{contato}'...")
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.6)

            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            pyperclip.copy(contato)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1.5)

            pyautogui.press('down')
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(1.0)

            print(f"📨 [WhatsApp]: Digitando mensagem '{mensagem}'...")
            pyperclip.copy(mensagem)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.4)
            pyautogui.press('enter')

            print("✅ [WhatsApp]: Sequência de envio concluída!")
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem no WhatsApp: {e}")
            return False