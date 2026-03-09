import streamlit as st

import os
import json
from datetime import datetime

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="GymTracker",
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
    obter_volume_semanal,
    obter_media_volume_semanal_por_musculo,
    obter_media_volume_semanal_por_exercicio_musculo,
    obter_media_volume_semanal_todos_exercicios,
    obter_dias_frequentados,
)

# Imports das páginas
from pagina_exercicios import render_adicionar_exercicio
from pagina_treinos import render_adicionar_treino
from pagina_estatisticas import render_estatisticas

create_database()

def colapsar_sidebar():
    st.markdown("""
    <script>
    (function() {
        var btn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"] button');
        if (btn) { btn.click(); }
    })();
    </script>
    """, unsafe_allow_html=True)



# ── Estilo global ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
            
/* Esconde tudo no header */
[data-testid="stToolbar"] { visibility: hidden !important; }
[data-testid="stStatusWidget"] { visibility: hidden !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Mostra só o botão >> */
[data-testid="stExpandSidebarButton"] { visibility: visible !important; }
[data-testid="stExpandSidebarButton"] * { visibility: visible !important; }
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

/* ── Mantém 3 colunas lado a lado no mobile (revertido nas outras páginas) ── */
@media (max-width: 1200px) {
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        flex-direction: row !important;
        gap: 0.3rem !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0% !important;
        width: auto !important;
    }
}
/* ── Remove bordas extras do number_input ── */
div[data-testid="stNumberInputContainer"] {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
div[data-testid="stNumberInputContainer"] [data-baseweb="input"] {
    border: 1px solid #444 !important;
    box-shadow: none !important;
    border-radius: 6px !important;
}
/* ── Esconde botões +/- fora da caixa ── */
button[data-testid="stNumberInputStepDown"],
button[data-testid="stNumberInputStepUp"] {
    display: none !important;
}

/* ── Streamlit radio buttons ocultos – usamos botões customizados ── */
div[data-testid="stRadio"] label {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-text">Gym<span>Tracker</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Usamos session_state para controlar a página ativa
    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "Registrar Treino"

    pages = [
        "Registrar Treino",
        "Exercícios",
        "Planos de Treino",
        "Estatísticas",
    ]

    for page_name in pages:
        is_active = st.session_state.pagina_atual == page_name
        active_style = (
            "background:#1e1e1e;color:#fff;border-left:3px solid #FF0000;"
        ) if is_active else ""
        col_btn = st.container()
        if st.button(
            label = page_name,
            key=f"nav_{page_name}",
            use_container_width=True,
            type="secondary",
        ):
            st.session_state.pagina_atual = page_name
            st.session_state._colapsar_sidebar = True
            st.rerun()

    st.markdown("<div style='height:1px;background:#2a2a2a;margin:1rem 0'></div>", unsafe_allow_html=True)

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
    st.markdown('<div class="reg-header">Registrar Treino</div>', unsafe_allow_html=True)
    
    treinos_existentes = list(set(t[1] for t in listar_treinos()))

    if not treinos_existentes:
        st.warning("⚠️ Nenhum plano de treino cadastrado. Crie um na aba 'Planos de Treino'.")
    else:
        treino_selecionado = st.selectbox("Selecione o treino", treinos_existentes)
        exercicios = listar_treinos_por_nome(treino_selecionado)

        if "form_data" not in st.session_state:
            st.session_state.form_data = load_form_data()
        else:
            file_data = load_form_data()
            if file_data:
                for k, v in file_data.items():
                    if k not in st.session_state.form_data:
                        st.session_state.form_data[k] = v

        if "form_reset_counter" not in st.session_state:
            st.session_state.form_reset_counter = 0

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
                            rc = st.session_state.form_reset_counter
                            peso_key = f"peso_{idx}_{aparelho}_{serie_index}"
                            reps_key = f"reps_{idx}_{aparelho}_{serie_index}"
                            rir_key  = f"rir_{idx}_{aparelho}_{serie_index}"
                            peso_wkey = f"w_{rc}_{peso_key}"
                            reps_wkey = f"w_{rc}_{reps_key}"
                            rir_wkey  = f"w_{rc}_{rir_key}"

                            peso_value = st.session_state.form_data.get(peso_key, 0)
                            reps_value = st.session_state.form_data.get(reps_key, 0)
                            rir_value  = st.session_state.form_data.get(rir_key, 0)

                            def _make_saver(wk, dk):
                                def _save():
                                    st.session_state.form_data[dk] = st.session_state[wk]
                                    save_form_data(st.session_state.form_data)
                                return _save

                            label = dict_options[selected]
                            if historico_info:
                                peso_info = f"{historico_info['peso']:.1f}kg"
                                reps_info = f"{int(historico_info['reps'])} reps"
                                rir_info  = f"RIR {int(historico_info['rir'])}"
                            else:
                                peso_info = reps_info = rir_info = "—"

                            # Linha 1: badge série + referência histórica
                            st.markdown(
                                f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>"
                                f"  <div style='background:#FF0000;color:#000;font-weight:900;font-size:0.8rem;"
                                f"              padding:3px 12px;border-radius:20px;'>Série {numero_serie}</div>"
                                f"  <div style='font-size:0.75rem;color:#666;'>{label}</div>"
                                f"  <div style='background:#1a1a1a;border:1px solid #333;border-radius:8px;"
                                f"              padding:4px 12px;font-size:0.78rem;color:#aaa;flex:1;"
                                f"              display:flex;justify-content:space-between;'>"
                                f"    <span><b style='color:#FF0000'>{peso_info}</b></span>"
                                f"    <span><b style='color:#FF0000'>{reps_info}</b></span>"
                                f"    <span><b style='color:#FF0000'>{rir_info}</b></span>"
                                f"  </div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )

                            # Linha 2: inputs peso / reps / RIR
                            col_p, col_r, col_rir = st.columns(3)
                            col_p.number_input("Peso (kg)", key=peso_wkey, value=int(peso_value),
                                               min_value=0, step=1,
                                               on_change=_make_saver(peso_wkey, peso_key))
                            col_r.number_input("Reps", key=reps_wkey, value=int(reps_value),
                                               min_value=0, step=1,
                                               on_change=_make_saver(reps_wkey, reps_key))
                            col_rir.number_input("RIR", key=rir_wkey, value=int(rir_value),
                                                 min_value=0, step=1,
                                                 on_change=_make_saver(rir_wkey, rir_key))
                            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.button("💾 Salvar treino", use_container_width=True, type="primary")
        with col2:
            clear = st.button("🗑️ Limpar", use_container_width=True)

        if clear:
            if "confirmar_clear" not in st.session_state:
                st.session_state.confirmar_clear = False

            if not st.session_state.confirmar_clear:
                st.session_state.confirmar_clear = True
                st.rerun()

        if st.session_state.get("confirmar_clear"):
            st.warning("⚠️ Tem certeza que deseja apagar tudo? Esta ação não pode ser desfeita.")
            col_sim, col_nao, _ = st.columns([1, 1, 4])
            with col_sim:
                if st.button("✅ Sim, limpar", use_container_width=True, type="primary"):
                    clear_form_data()
                    st.session_state.form_data = {}
                    st.session_state.confirmar_clear = False
                    st.session_state.form_reset_counter = st.session_state.get("form_reset_counter", 0) + 1
                    st.rerun()
            with col_nao:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.confirmar_clear = False
                    st.rerun()

        if submit:
            if not st.session_state.get("confirmar_submit"):
                st.session_state.confirmar_submit = True
                st.rerun()

        if st.session_state.get("confirmar_submit"):
            # Conta quantas séries serão salvas (ignora zeros)
            series_validas = 0
            for idx, exercicio in enumerate(exercicios):
                (_, _, aparelho, _, num_series, _) = exercicio
                for serie_index in range(num_series):
                    peso_key = f"peso_{idx}_{aparelho}_{serie_index}"
                    reps_key = f"reps_{idx}_{aparelho}_{serie_index}"
                    p = st.session_state.form_data.get(peso_key, 0)
                    r = st.session_state.form_data.get(reps_key, 0)
                    if not (p == 0 and r == 0):
                        series_validas += 1

            st.info(
                f"💾 Confirma o salvamento do treino **{treino_selecionado}**? "
                f"({series_validas} série(s) com dados serão salvas — séries com peso e reps zero são ignoradas)"
            )
            col_sim2, col_nao2, _ = st.columns([1, 1, 4])
            with col_sim2:
                if st.button("✅ Sim, salvar", use_container_width=True, type="primary"):
                    st.session_state.confirmar_submit = False
                    try:
                        data_treino = datetime.now().strftime("%Y-%m-%d")
                        series_salvas = 0
                        for idx, exercicio in enumerate(exercicios):
                            (_, _, aparelho, _, num_series, _) = exercicio
                            for serie_index in range(num_series):
                                peso_key = f"peso_{idx}_{aparelho}_{serie_index}"
                                reps_key = f"reps_{idx}_{aparelho}_{serie_index}"
                                rir_key  = f"rir_{idx}_{aparelho}_{serie_index}"
                                p = st.session_state.form_data.get(peso_key, 0)
                                r = st.session_state.form_data.get(reps_key, 0)
                                rir = st.session_state.form_data.get(rir_key, 0)

                                # ── Ignora séries com peso=0 E reps=0 ──────
                                if p == 0 and r == 0:
                                    continue

                                adicionar_historico(
                                    data_treino, treino_selecionado, aparelho,
                                    p, serie_index + 1, r, rir,
                                )
                                series_salvas += 1

                        st.session_state.form_data = {}
                        clear_form_data()
                        st.success(f"✓ Treino salvo! {series_salvas} série(s) registrada(s) no histórico.")
                        st.stop()
                    except Exception as e:
                        st.error(f"Erro ao salvar treino: {str(e)}")
            with col_nao2:
                if st.button("❌ Cancelar", use_container_width=True, key="cancel_submit"):
                    st.session_state.confirmar_submit = False
                    st.rerun()

elif pagina == "Exercícios":
    st.markdown("""<style>
    @media (max-width: 1200px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; flex-direction: row !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
    }
    </style>""", unsafe_allow_html=True)
    render_adicionar_exercicio()

elif pagina == "Planos de Treino":
    st.markdown("""<style>
    @media (max-width: 1200px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; flex-direction: row !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
    }
    </style>""", unsafe_allow_html=True)
    render_adicionar_treino()

elif pagina == "Estatísticas":
    st.markdown("""<style>
    @media (max-width: 1200px) {
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; flex-direction: row !important; }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; }
    }
    </style>""", unsafe_allow_html=True)
    render_estatisticas()
