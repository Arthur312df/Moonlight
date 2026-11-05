import sys
import os
import threading
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Core.cerebro import CerebroLocal
from Audio.motor_captura import MotorCaptura
from Audio.sintetizador import SintetizadorVoz
from Ui.interface import VisualizadorMoonlight
from Core.sistema_tray import MoonlightTray

def main():
    print("🌙 [Moonlight v1.0]: A iniciar subsistemas do aplicativo...")

    # Instancia os componentes (Burro de carga)
    visualizador = VisualizadorMoonlight()
    motor = MotorCaptura()
    sintetizador = SintetizadorVoz()
    cerebro = CerebroLocal(modelo="mistral")

    def restaurar_janela():
        visualizador.mostrar()

    def sair_aplicacao():
        visualizador.fechar()
        os._exit(0)

    # Inicia a bandeja do sistema
    tray = MoonlightTray(callback_restaurar=restaurar_janela, callback_sair=sair_aplicacao)
    tray.iniciar()
    print("🟢 [App]: Moonlight alojada na bandeja do sistema (System Tray).")

    # Dispara o cérebro em background passando os argumentos corretamente
    thread_cerebro = threading.Thread(
        target=cerebro.executar_loop_principal, 
        args=(motor, sintetizador, visualizador), 
        daemon=True
    )
    thread_cerebro.start()

    # Roda a interface gráfica na thread principal
    try:
        visualizador.start_window()
        while visualizador.esta_aberto():
            time.sleep(0.5)
    except KeyboardInterrupt:
        sair_aplicacao()

if __name__ == "__main__":
    main()