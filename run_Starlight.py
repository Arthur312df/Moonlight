import Starlight_core

print("==================================================")
print("  🌟 StarLight Test Runner (Pronto para Uso) 🌟")
print("==================================================\n")

while True:
    try:
        user_input = input("Você: ")
        if not user_input.strip():
            continue
        if user_input.lower() in ["sair", "exit", "quit", "tchau"]:
            print("StarLight: Até logo!")
            break

        # Processa a mensagem diretamente pelo núcleo carregado
        resposta = Starlight_core.process_query(user_input)
        print(f"StarLight: {resposta}\n")

    except (KeyboardInterrupt, EOFError):
        print("\nStarLight: Sessão encerrada.")
        break