import streamlit as st
from sqlmgnt import *

FOCOS = [
    "Peito", "Costas", "Ombros", "Bíceps", "Tríceps",
    "Antebraço", "Abdômen", "Glúteo", "Quadríceps",
    "Posterior de coxa", "Panturrilha", "Cardio", "Outro"
]

FOCO_CORES = {
    "Peito":               "#e74c3c",
    "Costas":              "#e67e22",
    "Ombros":              "#f1c40f",
    "Bíceps":              "#2ecc71",
    "Tríceps":             "#1abc9c",
    "Antebraço":           "#3498db",
    "Abdômen":             "#9b59b6",
    "Glúteo":              "#e91e63",
    "Quadríceps":          "#ff5722",
    "Posterior de coxa":   "#795548",
    "Panturrilha":         "#607d8b",
    "Cardio":              "#00bcd4",
    "Outro":               "#9e9e9e",
}

def render_adicionar_exercicio():
    st.markdown("""
    <style>
    .ex-header { font-size:1.6rem;font-weight:800;color:#FF0000;letter-spacing:-0.5px;margin-bottom:0.2rem; }
    .ex-sub { color:#888;font-size:0.9rem;margin-bottom:1.5rem; }
    .ex-card {
        display:flex;align-items:center;justify-content:space-between;
        background:#1a1a1a;border-radius:10px;padding:0.75rem 1rem;
        margin-bottom:0.5rem;border-left:4px solid var(--foco-color,#FF0000);transition:background 0.2s;
    }
    .ex-card:hover { background:#222; }
    .ex-name { font-weight:700;font-size:1rem;color:#fff; }
    .ex-foco-badge {
        font-size:0.72rem;font-weight:700;padding:2px 10px;border-radius:20px;
        background:var(--foco-color,#FF0000);color:#111;letter-spacing:0.5px;
    }
    .ex-sec-badge {
        font-size:0.68rem;font-weight:600;padding:2px 8px;border-radius:20px;
        background:#2a2a2a;color:#aaa;margin-left:4px;border:1px solid #444;
    }
    .soma-ok { color:#2ecc71;font-weight:700;font-size:0.9rem; }
    .soma-warn { color:#f1c40f;font-weight:700;font-size:0.9rem; }
    .section-divider { border:none;border-top:1px solid #2a2a2a;margin:1.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ex-header">Exercícios</div>', unsafe_allow_html=True)
    st.markdown('<div class="ex-sub">Cadastre e gerencie sua biblioteca de exercícios</div>', unsafe_allow_html=True)

    # ── Formulário de adição ──────────────────────────────────────────────────
    st.markdown("#### ➕ Novo exercício")

    col_nome, col_foco_pri = st.columns([2, 1])
    with col_nome:
        nome_ex = st.text_input("Nome do exercício", placeholder="Ex: Supino reto com barra", key="ex_nome_input")
    with col_foco_pri:
        foco_primario = st.selectbox("Músculo primário", FOCOS, key="ex_foco_input")

    # Inicializa estado dos músculos no formulário
    if "ex_musculos" not in st.session_state:
        st.session_state.ex_musculos = {foco_primario: 100}
        st.session_state.ex_foco_primario_anterior = foco_primario

    # Se o primário mudou, reinicia o dict
    if st.session_state.get("ex_foco_primario_anterior") != foco_primario:
        st.session_state.ex_musculos = {foco_primario: 100}
        st.session_state.ex_foco_primario_anterior = foco_primario

    # Garante que o primário está no dict
    if foco_primario not in st.session_state.ex_musculos:
        st.session_state.ex_musculos[foco_primario] = 100

    st.markdown("**Distribuição de volume por músculo:**")
    
    # Linha do músculo primário
    col_m, col_p, col_add_rem = st.columns([3, 2, 1])
    with col_m:
        st.markdown(f"<div style='padding:6px 0;color:#fff;font-weight:600'>{foco_primario} <span style='color:#FF0000;font-size:0.75rem'>● primário</span></div>", unsafe_allow_html=True)
    with col_p:
        pct_pri = st.number_input("% primário", min_value=0, max_value=100,
                                   value=st.session_state.ex_musculos.get(foco_primario, 100),
                                   step=5, key=f"pct_{foco_primario}",
                                   label_visibility="collapsed")
        st.session_state.ex_musculos[foco_primario] = pct_pri

    # Linhas dos músculos secundários já adicionados
    musculos_secundarios = [m for m in st.session_state.ex_musculos if m != foco_primario]
    for musculo in musculos_secundarios:
        col_m2, col_p2, col_rem = st.columns([3, 2, 1])
        with col_m2:
            st.markdown(f"<div style='padding:6px 0;color:#ccc;'>{musculo}</div>", unsafe_allow_html=True)
        with col_p2:
            pct = st.number_input(f"% {musculo}", min_value=0, max_value=100,
                                   value=st.session_state.ex_musculos.get(musculo, 50),
                                   step=5, key=f"pct_{musculo}",
                                   label_visibility="collapsed")
            st.session_state.ex_musculos[musculo] = pct
        with col_rem:
            if st.button("✕", key=f"rem_musculo_{musculo}"):
                del st.session_state.ex_musculos[musculo]
                st.rerun()

    # Soma total
    soma = sum(st.session_state.ex_musculos.values())
    classe = "soma-ok" if soma == 100 else "soma-warn"
    st.markdown(f"<span class='{classe}'>Soma total: {soma}%</span>", unsafe_allow_html=True)

    # Adicionar novo músculo secundário
    focos_disponiveis_add = [f for f in FOCOS if f not in st.session_state.ex_musculos]
    if focos_disponiveis_add:
        col_add_sel, col_add_btn = st.columns([3, 1])
        with col_add_sel:
            novo_musculo = st.selectbox("Adicionar músculo secundário", focos_disponiveis_add, key="ex_novo_musculo")
        with col_add_btn:
            st.markdown("<div style='margin-top:1.85rem'>", unsafe_allow_html=True)
            if st.button("➕ Add", key="btn_add_musculo", use_container_width=True):
                st.session_state.ex_musculos[st.session_state.ex_novo_musculo] = 50
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("Adicionar exercício", use_container_width=True, type="primary", key="btn_add_ex"):
            nome_limpo = nome_ex.strip()
            if not nome_limpo:
                st.error("Digite o nome do exercício.")
            elif soma > 100:
                st.error(f"A soma dos percentuais está em {soma}% — reduza antes de salvar.")
            else:
                distribuicao = dict(st.session_state.ex_musculos)
                resultado = adicionar_exercicio(nome_limpo, foco_primario, distribuicao)
                if resultado:
                    st.success(f"✓ '{nome_limpo}' adicionado!")
                    st.session_state.ex_musculos = {}
                    st.rerun()
                else:
                    st.error(f"Exercício '{nome_limpo}' já existe ou houve um erro.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Lista de exercícios cadastrados ──────────────────────────────────────
    st.markdown("#### 📋 Exercícios cadastrados")

    exercicios = listar_exercicios()  # (id, nome, foco, distribuicao_dict, data_criacao)

    if not exercicios:
        st.info("Nenhum exercício cadastrado ainda. Adicione o primeiro acima!")
        return

    por_foco = {}
    for (eid, nome, foco, dist, _) in exercicios:
        por_foco.setdefault(foco, []).append((eid, nome, dist))

    focos_cadastrados = sorted(por_foco.keys())
    foco_filtro = st.multiselect(
        "Filtrar por grupo muscular",
        focos_cadastrados,
        default=focos_cadastrados,
        key="ex_filtro_foco"
    )

    st.markdown(f"**{len(exercicios)} exercício(s) cadastrado(s)**")
    st.markdown("")

    for foco in focos_cadastrados:
        if foco not in foco_filtro:
            continue
        cor = FOCO_CORES.get(foco, "#FF0000")
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:700;color:{cor};"
            f"letter-spacing:1px;text-transform:uppercase;margin:1rem 0 0.4rem;'>{foco}</div>",
            unsafe_allow_html=True
        )
        for eid, nome, dist in por_foco[foco]:
            col_card, col_del = st.columns([10, 1])
            with col_card:
                # Badges: primário em vermelho, secundários em cinza com %
                badges = ""
                for musculo, pct in dist.items():
                    if musculo == foco:
                        badges += f"<span class='ex-foco-badge' style='background:{cor}'>{musculo} {pct}%</span> "
                    else:
                        badges += f"<span class='ex-sec-badge'>{musculo} {pct}%</span>"
                st.markdown(
                    f"<div class='ex-card' style='--foco-color:{cor}'>"
                    f"  <span class='ex-name'>{nome}</span>"
                    f"  <div style='display:flex;align-items:center;flex-wrap:wrap;gap:4px;'>{badges}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_del:
                st.markdown("<div style='margin-top:0.6rem'>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_ex_{eid}", help=f"Deletar '{nome}'"):
                    deletar_exercicio(eid)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)