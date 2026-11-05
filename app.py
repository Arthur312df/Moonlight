import multiprocessing
from Ui.interface import VisualizadorMoonlight
from Audio.motor_captura import MotorCaptura
from Audio.sintetizador import SintetizadorVoz
from Core.cerebro import CerebroLocal

def main():
    visualizador = VisualizadorMoonlight()
    print("🧠 A carregar Cérebro e Subsistemas...")
    
    try:
        motor = MotorCaptura(sample_rate=16000, device_index=1)
        cerebro = CerebroLocal(modelo="mistral")
        sintetizador = SintetizadorVoz()

        print("🌙 Sistema pronto! O Cérebro assumiu o controlo total.")
        visualizador.start_window()

        # O app entrega tudo ao cérebro e apenas executa o ciclo de vida
        cerebro.executar_loop_principal(motor, sintetizador, visualizador)

    except KeyboardInterrupt:
        print("A encerrar...")
    finally:
        visualizador.fechar()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()