import os
import subprocess
import glob
import ctypes

class GestorSeguranca:
    def __init__(self):
        self.autorizado_nesta_sessao = False

    def pedir_autorizacao_visual(self, acao_descricao="executar uma ação no sistema"):
        """
        Dispara uma janela nativa do Windows (MessageBox) a pedir confirmação ao utilizador.
        Retorna True se o utilizador aceitar, False caso contrário.
        """
        if self.autorizado_nesta_sessao:
            return True

        # Chama a API nativa do Windows para mostrar uma caixa de confirmação gráfica (Sim/Não)
        titulo = "🌙 Moonlight - Pedido de Permissão"
        mensagem = f"A Moonlight quer aceder ao computador para:\n\n'{acao_descricao}'\n\nPermitir esta ação?"
        
        # MB_YESNO = 0x04, MB_ICONQUESTION = 0x20, IDYES = 6
        resposta = ctypes.windll.user32.MessageBoxW(0, mensagem, titulo, 0x04 | 0x20)
        
        if resposta == 6: # Clicou em "Sim"
            self.autorizado_nesta_sessao = True
            return True
        return False

    def fazer_scan_sistema(self):
        """
        Varre o computador à procura de aplicações comuns, atalhos e ferramentas úteis
        para a Moonlight saber o que pode abrir.
        """
        apps_encontrados = {}
        
        # Locais comuns onde o Windows guarda atalhos de programas
        caminhos_procura = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs\*.lnk"),
            os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs\*.lnk"),
            r"C:\Windows\System32\*.exe"
        ]

        # Lista de aplicações úteis prioritárias para detetar rapidamente
        utilitarios_alvo = {
            "notepad": "Bloco de Notas",
            "calc": "Calculadora",
            "vivaldi": "vivaldi",
            "code": "Visual Studio Code",
            "cmd": "Linha de Comandos"
        }

        # Scan rápido por executáveis conhecidos no Path ou System32
        for chave, nome in utilitarios_alvo.items():
            try:
                # Usa o comando 'where' do Windows para testar se o executável está acessível
                resultado = subprocess.run(["where", chave], capture_output=True, text=True, timeout=1)
                if resultado.returncode == 0:
                    caminho = resultado.stdout.strip().splitlines()[0]
                    apps_encontrados[nome] = caminho
            except Exception:
                pass

        return apps_encontrados