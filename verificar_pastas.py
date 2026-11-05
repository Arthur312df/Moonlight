import os

print("🔍 A procurar pelo ficheiro voices-1.0.bin no disco...")
encontrado = False

for raiz, dirs, arquivos in os.walk(r"C:\Moonlight"):
    for arquivo in arquivos:
        if "voice" in arquivo.lower() or arquivo.endswith(".bin"):
            caminho_completo = os.path.join(raiz, arquivo)
            print(f"🎯 Encontrado: {caminho_completo}")
            encontrado = True

if not encontrado:
    print("❌ O ficheiro de vozes não foi encontrado dentro de C:\\Moonlight. Precisamos de o colocar na pasta Audio!")