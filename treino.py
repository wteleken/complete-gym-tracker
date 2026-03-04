import streamlit as st
import streamlit.components.v1 as components
import os
import json
from datetime import datetime

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="GymTracker",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Imports do banco de dados ─────────────────────────────────────────────────
from sqlmgnt import (
    create_database,
    # Exercícios
    adicionar_exercicio, listar_exercicios, deletar_exercicio,
    # Treinos
    adicionar_treino, listar_treinos, listar_treinos_por_nome,
    deletar_treino, deletar_treino_completo,
    # Histórico
    adicionar_historico, listar_historico, deletar_historico,
    # Histórico inteligente
    obter_ultimo_historico, obter_melhor_volume_treino,
    obter_melhor_volume_exercicio, obter_melhor_volume_serie,
    obter_pr_serie, obter_media_ultimos_3_treinos_serie,
    # Stats
    obter_stats_gerais, obter_stats_por_treino, obter_stats_por_musculo, obter_stats_por_exercicio,
    obter_volume_por_data, obter_volume_por_data_musculo,
    obter_historico_exercicio, obter_historico_exercicio_completo,
    obter_prs_por_exercicio, obter_frequencia_por_semana,
    obter_focos_disponiveis,
)

# Imports das páginas
from pagina_exercicios import render_adicionar_exercicio
from pagina_treinos import render_adicionar_treino
from pagina_estatisticas import render_estatisticas

create_database()

def colapsar_sidebar():
    components.html(
        """<script>
        (function() {
            var btn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"] button');
            if (btn) { btn.click(); }
        })();
        </script>""",
        height=0
    )



# ── Estilo global ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Esconde botão de colapsar sidebar ── */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: 1px solid #222;
}
[data-testid="stSidebar"] * {
    font-family: 'Helvetica Neue', sans-serif;
}

/* Logo */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0 1.5rem;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 1.2rem;
}
.sidebar-logo-icon {
    font-size: 1.8rem;
    line-height: 1;
}
.sidebar-logo-text {
    font-size: 1.3rem;
    font-weight: 900;
    color: #fff;
    letter-spacing: -0.5px;
}
.sidebar-logo-text span {
    color: #FF0000;
}

/* Nav items */
.nav-item {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.65rem 0.9rem;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    margin-bottom: 0.2rem;
    text-decoration: none;
    color: #888;
    font-size: 0.95rem;
    font-weight: 500;
}
.nav-item:hover { background: #1e1e1e; color: #fff; }
.nav-item.active {
    background: #1e1e1e;
    color: #fff;
    border-left: 3px solid #FF0000;
}
.nav-icon { font-size: 1.1rem; }

/* Main content */
.main-content {
    padding: 1.5rem 2rem;
}

/* Remove Streamlit default padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1200px;
}

/* Streamlit radio buttons ocultos – usamos botões customizados */
div[data-testid="stRadio"] label {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🏋️</div>
        <div class="sidebar-logo-text">Gym<span>Tracker</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Usamos session_state para controlar a página ativa
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "Registrar Treino"

    pages = [
        ("🏃", "Registrar Treino"),
        ("💪", "Exercícios"),
        ("🏋️", "Planos de Treino"),
        ("📊", "Estatísticas"),
    ]

    for icon, page_name in pages:
        is_active = st.session_state.pagina_atual == page_name
        active_style = (
            "background:#1e1e1e;color:#fff;border-left:3px solid #FF0000;"
        ) if is_active else ""
        col_btn = st.container()
        if st.button(
            f"{icon}  {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.pagina_atual = page_name
            st.session_state._colapsar_sidebar = True
            st.rerun()

    st.markdown("<div style='height:1px;background:#2a2a2a;margin:1rem 0'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color:#444;font-size:0.75rem;text-align:center;padding:0.5rem'>v1.0 · GymTracker</div>",
        unsafe_allow_html=True
    )

# ── Colapsar sidebar se vier de navegação ──
if st.session_state.get('_colapsar_sidebar'):
    st.session_state._colapsar_sidebar = False
    colapsar_sidebar()

# ── Roteamento ────────────────────────────────────────────────────────────────
pagina = st.session_state.pagina_atual

if pagina == "Registrar Treino":
    # ── PÁGINA: Registrar Treino ──────────────────────────────────────────────
    FORM_DATA_FILE = "form_data_backup.json"

    def load_form_data():
        if os.path.exists(FORM_DATA_FILE):
            try:
                with open(FORM_DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_form_data(data):
        try:
            with open(FORM_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    def save_input_value(key):
        if key in st.session_state:
            st.session_state.form_data[key] = st.session_state[key]
            save_form_data(st.session_state.form_data)

    def clear_form_data():
        if os.path.exists(FORM_DATA_FILE):
            try:
                os.remove(FORM_DATA_FILE)
            except Exception:
                pass

    st.markdown("""
    <style>
    .reg-header { font-size:1.6rem;font-weight:800;color:#FF0000;margin-bottom:0.2rem; }
    .reg-sub { color:#888;font-size:0.9rem;margin-bottom:1.5rem; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="reg-header">🏃 Registrar Treino</div>', unsafe_allow_html=True)
    st.markdown('<div class="reg-sub">Registre suas séries, pesos e repetições</div>', unsafe_allow_html=True)

    treinos_existentes = list(set(t[1] for t in listar_treinos()))

    if not treinos_existentes:
        st.warning("⚠️ Nenhum plano de treino cadastrado. Crie um na aba 'Planos de Treino'.")
    else:
        treino_selecionado = st.selectbox("Selecione o treino", treinos_existentes)
        exercicios = listar_treinos_por_nome(treino_selecionado)

        # Carrega do arquivo sempre que form_data não existe no session_state
        # Isso garante persistência ao trocar de aba (o arquivo é a fonte da verdade)
        if "form_data" not in st.session_state:
            st.session_state.form_data = load_form_data()
        else:
            # Sincroniza: se o arquivo tem dados mais recentes (ex: outra aba gravou), usa o arquivo
            file_data = load_form_data()
            if file_data:
                # Mantém o que está na memória mas preenche o que falta do arquivo
                for k, v in file_data.items():
                    if k not in st.session_state.form_data:
                        st.session_state.form_data[k] = v

        options = [
            "Último treino",
            "melhor volume treino (MV T)",
            "melhor volume exercicio (MV E)",
            "melhor volume serie (MV S)",
            "maior peso por série (PR)",
            "Média dos últimos 3 treinos (AVG 3T)"
        ]
        dict_options = {
            "Último treino":                        "Último:",
            "melhor volume treino (MV T)":          "MV T:",
            "melhor volume exercicio (MV E)":       "MV E:",
            "melhor volume serie (MV S)":           "MV S:",
            "maior peso por série (PR)":            "PR:",
            "Média dos últimos 3 treinos (AVG 3T)": "AVG 3T:",
        }

        col1, col2 = st.columns(2)
        with col1:
            selected = st.selectbox("Referência histórica", options, key=f"select_{treino_selecionado}")

        if exercicios:
            for idx, exercicio in enumerate(exercicios):
                (_, _, aparelho, _, num_series, _) = exercicio
                with st.expander(aparelho):
                    for serie_index in range(num_series):
                        numero_serie = serie_index + 1

                        if selected == "Último treino":
                            historico_info = obter_ultimo_historico(aparelho, numero_serie)
                        elif selected == "melhor volume exercicio (MV E)":
                            historico_info = obter_melhor_volume_exercicio(aparelho, numero_serie)
                        elif selected == "melhor volume treino (MV T)":
                            historico_info = obter_melhor_volume_treino(treino_selecionado, aparelho, numero_serie)
                        elif selected == "melhor volume serie (MV S)":
                            historico_info = obter_melhor_volume_serie(aparelho, numero_serie)
                        elif selected == "maior peso por série (PR)":
                            historico_info = obter_pr_serie(aparelho, numero_serie)
                        elif selected == "Média dos últimos 3 treinos (AVG 3T)":
                            historico_info = obter_media_ultimos_3_treinos_serie(aparelho, numero_serie)
                        else:
                            historico_info = None

                        with st.container():
                            col0, colN, col2, col3, col4 = st.columns([1, 2, 4, 4, 4])
                            colN.metric("Série", numero_serie)

                            peso_key = f"peso_{idx}_{aparelho}_{serie_index}"
                            reps_key = f"reps_{idx}_{aparelho}_{serie_index}"
                            rir_key  = f"rir_{idx}_{aparelho}_{serie_index}"

                            peso_value = st.session_state.form_data.get(peso_key, 0)
                            reps_value = st.session_state.form_data.get(reps_key, 0)
                            rir_value  = st.session_state.form_data.get(rir_key, 0)

                            col2.number_input("peso", key=peso_key, value=int(peso_value),
                                              min_value=0, step=1,
                                              on_change=save_input_value, args=(peso_key,))
                            col3.number_input("repetições", key=reps_key, value=int(reps_value),
                                              min_value=0, step=1,
                                              on_change=save_input_value, args=(reps_key,))
                            col4.number_input("RIR", key=rir_key, value=int(rir_value),
                                              min_value=0, step=1,
                                              on_change=save_input_value, args=(rir_key,))

                            col0.markdown(
                                "<div style='background-color:#FF0000;width:30px;height:130px;border-radius:5px;'></div>",
                                unsafe_allow_html=True
                            )
                            label = dict_options[selected]
                            colN.markdown(label)

                            if historico_info:
                                peso_info = f"{label} {historico_info['peso']:.1f}kg"
                                reps_info = f"{label} {int(historico_info['reps'])}"
                                rir_info  = f"{label} {int(historico_info['rir'])}"
                            else:
                                peso_info = reps_info = rir_info = "Sem histórico"

                            for col, info in [(col2, peso_info), (col3, reps_info), (col4, rir_info)]:
                                col.markdown(
                                    f"<div style='background-color:#FF0000;padding:8px;border-radius:5px;color:black;'>{info}</div>",
                                    unsafe_allow_html=True
                                )

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.button("💾 Salvar treino", use_container_width=True, type="primary")
        with col2:
            clear = st.button("🗑️ Limpar", use_container_width=True)

        if clear:
            # Apaga arquivo e session_state completo, força recarga limpa
            clear_form_data()
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        if submit:
            try:
                data_treino = datetime.now().strftime("%Y-%m-%d")
                for idx, exercicio in enumerate(exercicios):
                    (_, _, aparelho, _, num_series, _) = exercicio
                    for serie_index in range(num_series):
                        peso_key = f"peso_{idx}_{aparelho}_{serie_index}"
                        reps_key = f"reps_{idx}_{aparelho}_{serie_index}"
                        rir_key  = f"rir_{idx}_{aparelho}_{serie_index}"
                        adicionar_historico(
                            data_treino, treino_selecionado, aparelho,
                            st.session_state.form_data.get(peso_key, 0),
                            serie_index + 1,
                            st.session_state.form_data.get(reps_key, 1),
                            st.session_state.form_data.get(rir_key, 0),
                        )
                st.session_state.form_data = {}
                clear_form_data()
                st.success("✓ Treino salvo com sucesso no histórico!")
                st.stop()
            except Exception as e:
                st.error(f"Erro ao salvar treino: {str(e)}")

elif pagina == "Exercícios":
    render_adicionar_exercicio()

elif pagina == "Planos de Treino":
    render_adicionar_treino()

elif pagina == "Estatísticas":
    render_estatisticas()