import tkinter as tk
from tkinter import scrolledtext, font, messagebox
import urllib.request
import json
import webbrowser
import Starlight_core

VERSAO_ATUAL = "1.2"
GITHUB_VERSION_URL = "https://api.github.com/repos/Arthur312df/Starlight/releases/latest"

def verificar_atualizacao(manual=False):
    try:
        req = urllib.request.urlopen(GITHUB_VERSION_URL, timeout=3)
        data = json.loads(req.read().decode('utf-8'))
        versao_remota = data.get("version")
        url_download = data.get("download_url")
        changelog = data.get("changelog", "Novas melhorias disponíveis.")

        if versao_remota != VERSAO_ATUAL:
            resposta = messagebox.askyesno(
                "Atualização Disponível! 🚀",
                f"Uma nova versão ({versao_remota}) da StarLight está disponível!\n\nNovidades:\n{changelog}\n\nDeseja baixar agora?"
            )
            if resposta:
                webbrowser.open(url_download)
        elif manual:
            messagebox.showinfo("Tudo em ordem", "Você já está usando a versão mais recente da StarLight!")
    except Exception as e:
        if manual:
            messagebox.showerror("Erro", f"Não foi possível verificar atualizações.\nDetalhes: {e}")

def enviar_mensagem(event=None):
    texto_usuario = entrada_texto.get().strip()
    if not texto_usuario:
        return
    
    print(f"[CHAT GUI] Você -> {texto_usuario}")
    
    # Exibe o balão do usuário (alinhado à direita)
    adicionar_balao("Você", texto_usuario, "usuario")
    entrada_texto.delete(0, tk.END)
    
    # Processa a resposta
    resposta = Starlight_core.process_query(texto_usuario)
    
    print(f"[CHAT GUI] StarLight -> {resposta}\n")
    
    # Exibe o balão da StarLight (alinhado à esquerda)
    adicionar_balao("StarLight", resposta, "starlight")

def adicionar_balao(remetente, texto, tipo):
    chat_log.config(state=tk.NORMAL)
    
    if tipo == "usuario":
        chat_log.insert(tk.END, f"\n {remetente} \n", "nome_e")
        chat_log.insert(tk.END, f" {texto} \n\n", "msg_e")
    else:
        chat_log.insert(tk.END, f"\n {remetente} \n", "nome_w")
        chat_log.insert(tk.END, f" {texto} \n\n", "msg_w")
        
    chat_log.config(state=tk.DISABLED)
    chat_log.see(tk.END)

# Configuração da Janela Principal
root = tk.Tk()
root.title("StarLight v1.2 - Assistente Pessoal")
root.geometry("680x750")
root.configure(bg="#1e1e1e")

# Estilos de Fonte
fonte_chat = font.Font(family="Segoe UI", size=11)
fonte_entrada = font.Font(family="Segoe UI", size=11)
fonte_titulo = font.Font(family="Segoe UI", size=12, weight="bold")

# Cabeçalho Superior
topo_frame = tk.Frame(root, bg="#252526", height=50)
topo_frame.pack(fill=tk.X, padx=0, pady=0)
topo_frame.pack_propagate(False)

label_titulo = tk.Label(topo_frame, text=" 🌟 StarLight v1.2", bg="#252526", fg="#ffffff", font=fonte_titulo)
label_titulo.pack(side=tk.LEFT, padx=15)

# Botão de Atualização no Cabeçalho
botao_update = tk.Button(topo_frame, text="🔄 Verificar Atualizações", bg="#333333", fg="#4ec9b0", font=("Segoe UI", 9, "bold"), bd=0, padx=10, command=lambda: verificar_atualizacao(manual=True))
botao_update.pack(side=tk.RIGHT, padx=15)

# Área de Histórico do Chat
chat_log = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="#181818", fg="#ffffff", font=fonte_chat, bd=0, highlightthickness=0)
chat_log.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)
chat_log.config(state=tk.DISABLED)

# Configuração dos Balões de Conversa
chat_log.tag_config("nome_w", foreground="#9cdcfe", font=("Segoe UI", 9, "bold"), lmargin1=15, lmargin2=15)
chat_log.tag_config("msg_w", background="#2d2d2d", foreground="#f1f1f1", lmargin1=15, lmargin2=15, rmargin=120, spacing1=4, spacing2=4)

chat_log.tag_config("nome_e", foreground="#4ec9b0", font=("Segoe UI", 9, "bold"), justify="right", rmargin=15)
chat_log.tag_config("msg_e", background="#005fb8", foreground="#ffffff", justify="left", lmargin1=120, rmargin=15, spacing1=4, spacing2=4)

# Frame inferior (Entrada e Botão)
frame_inferior = tk.Frame(root, bg="#1e1e1e")
frame_inferior.pack(padx=15, pady=(0, 15), fill=tk.X)

entrada_texto = tk.Entry(frame_inferior, bg="#2d2d2d", fg="#ffffff", font=fonte_entrada, bd=0, insertbackground="white")
entrada_texto.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
entrada_texto.bind("<Return>", enviar_mensagem)

botao_enviar = tk.Button(frame_inferior, text="Enviar", bg="#007acc", fg="#ffffff", font=fonte_entrada, bd=0, padx=22, pady=8, command=enviar_mensagem)
botao_enviar.pack(side=tk.RIGHT)

# Mensagem inicial de boas-vindas
adicionar_balao("StarLight", "Olá! Sou a StarLight v1.2. Pronta para conversar, pesquisar na web ou fazer contas com você!", "starlight")

root.mainloop()