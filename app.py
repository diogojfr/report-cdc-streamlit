import streamlit as st

# ── Authentication ───────────────────────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Acesso Restrito")
    password = st.text_input("Digite a senha", type="password")
    if st.button("Entrar"):
        if password == "ism@2026":  # Change this to your desired password
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# ── Main App ─────────────────────────────────────────────────────────────
image_url = "logo-ism.png"
st.image(image_url, caption=' ',width='stretch')

st.set_page_config(
    page_title="Easy Pallet – ISM Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


image_url_sidebar = "https://easypallet.com.br/assets/imgs/logos/logo_easypallet.png"
st.sidebar.image(image_url_sidebar, caption=' ', width=250)



# define navigation pages explicitly
pages = [
    st.Page("pages/painel_geral.py", title="📊  Painel Geral"),
    st.Page("pages/painel_montagem.py", title="🔧  Painel Montagem"),
    st.Page("pages/painel_conferencia.py", title="✅  Painel Conferência"),
    st.Page("pages/painel_erros.py", title="⚠️  Painel Erros"),
    st.Page("pages/painel_operacoes.py", title="⏱️  Painel Operações"),
]

current = st.navigation(pages)
current.run()

