import streamlit as st
from starlight_core import StarLightCore

# Configuração da página
st.set_page_config(
    page_title="StarLight - Assistente Cognitiva", 
    page_icon="🌟", 
    layout="centered"
)

# Inicializa o core da StarLight em cache
@st.cache_resource
def carregar_core():
    return StarLightCore()

core = carregar_core()

# Título principal minimalista
st.title("🌟 StarLight")
st.write("Sistema Cognitivo Autónomo local (Mistral + Memória Hierárquica).")

# ==========================================
# INTERFACE DO CHAT COGNITIVO
# ==========================================
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# Exibe o histórico de mensagens
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# Entrada de texto do utilizador
if prompt := st.chat_input("Digite o seu estímulo para a StarLight..."):
    # Adiciona a mensagem do utilizador ao histórico
    st.session_state.mensagens.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Processa a resposta através do core hierárquico
    with st.chat_message("assistant"):
        with st.spinner("A processar sinapses e núcleos..."):
            resposta = core.processar_mensagem(prompt)
            st.markdown(resposta)
            st.session_state.mensagens.append({"role": "assistant", "content": resposta})