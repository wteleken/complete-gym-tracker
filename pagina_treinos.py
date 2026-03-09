import streamlit as st
from sqlmgnt import *
# from database import adicionar_treino, listar_treinos, listar_exercicios, deletar_treino_completo

def render_adicionar_treino():
    st.markdown("""
    <style>
    .tr-header {
        font-size: 1.6rem;
        font-weight: 800;
        color: #FF0000;
        letter-spacing: -0.5px;
        margin-bottom: 0.2rem;
    }
    .tr-sub {
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .ex-row {
        background: #1a1a1a;
        border-radius: 10px;
        padding: 0.65rem 1rem;
        margin-bottom: 0.4rem;
        border-left: 3px solid #FF0000;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .treino-card {
        background: #1a1a1a;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #FF0000;
    }
    .treino-card-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #fff;
        margin-bottom: 0.4rem;
    }
    .treino-card-ex {
        font-size: 0.82rem;
        color: #aaa;
        margin: 2px 0;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #2a2a2a;
        margin: 1.5rem 0;
    }
    .badge-series {
        background: #FF0000;
        color: #fff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 20px;
        margin-left: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="tr-header">Treinos</div>', unsafe_allow_html=True)
    st.markdown('<div class="tr-sub">Monte seus planos de treino com os exercícios disponíveis</div>', unsafe_allow_html=True)

    # ── Carregar exercícios disponíveis ───────────────────────────────────────
    exercicios_db = listar_exercicios()  # [(id, nome, foco, data_criacao)]
    if not exercicios_db:
        st.warning("⚠️ Nenhum exercício cadastrado. Cadastre exercícios primeiro na aba 'Exercícios'.")
        return

    opcoes_ex = {f"{nome} ({foco})": (nome, foco) for (_, nome, foco, *_) in exercicios_db}

    # ── Estado da sessão para o builder ──────────────────────────────────────
    if "novo_treino_nome" not in st.session_state:
        st.session_state.novo_treino_nome = ""
    if "novo_treino_exercicios" not in st.session_state:
        # lista de dicts: {"label": str, "nome": str, "foco": str, "series": int}
        st.session_state.novo_treino_exercicios = []

    # ── Formulário ────────────────────────────────────────────────────────────
    st.markdown("#### ➕ Novo treino")

    st.text_input(
        "Nome do treino",
        placeholder="Ex: Treino A – Peito e Tríceps",
        key="novo_treino_nome_input"
    )

    st.markdown("**Adicionar exercícios ao treino:**")

    # Filtro de músculo antes do selectbox de exercício
    focos_no_db = sorted(set(foco for (_, _, foco, *_) in exercicios_db))
    col_foco_filtro, col_ex, col_series, col_add = st.columns([2, 4, 1, 1])
    with col_foco_filtro:
        foco_filtro_tr = st.selectbox("Músculo", ["Todos"] + focos_no_db, key="tr_foco_filtro")

    # Filtra as opções de exercício pelo músculo selecionado
    if foco_filtro_tr == "Todos":
        opcoes_filtradas = opcoes_ex
    else:
        opcoes_filtradas = {k: v for k, v in opcoes_ex.items() if v[1] == foco_filtro_tr}

    with col_ex:
        ex_selecionado = st.selectbox(
            "Exercício",
            list(opcoes_filtradas.keys()) if opcoes_filtradas else ["Nenhum exercício neste grupo"],
            key="tr_ex_select"
        )
    with col_series:
        num_series = st.number_input("Séries", min_value=1, max_value=20, value=3, step=1, key="tr_num_series")
    with col_add:
        st.markdown("<div style='margin-top:1.85rem'>", unsafe_allow_html=True)
        if st.button("➕ Add", use_container_width=True, key="btn_add_ex_treino"):
            if ex_selecionado not in opcoes_filtradas:
                st.warning("Selecione um exercício válido.")
                st.stop()
            nome_ex, foco_ex = opcoes_filtradas[ex_selecionado]
            # Verificar se já foi adicionado
            ja_existe = any(e["nome"] == nome_ex for e in st.session_state.novo_treino_exercicios)
            if ja_existe:
                st.warning(f"'{nome_ex}' já está no treino.")
            else:
                st.session_state.novo_treino_exercicios.append({
                    "label": ex_selecionado,
                    "nome": nome_ex,
                    "foco": foco_ex,
                    "series": int(num_series)
                })
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Preview dos exercícios adicionados ───────────────────────────────────
    if st.session_state.novo_treino_exercicios:
        st.markdown(f"**{len(st.session_state.novo_treino_exercicios)} exercício(s) no treino:**")

        for i, ex in enumerate(st.session_state.novo_treino_exercicios):
            col_info, col_s, col_rem = st.columns([5, 2, 1])
            with col_info:
                st.markdown(
                    f"<div class='ex-row'>"
                    f"  <span style='color:#fff;font-weight:700'>{ex['nome']}</span>"
                    f"  <span style='color:#888;font-size:0.8rem'>({ex['foco']})</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_s:
                # Permitir ajustar séries inline
                nova_series = st.number_input(
                    "Séries", min_value=1, max_value=20,
                    value=ex["series"], step=1,
                    key=f"series_inline_{i}",
                    label_visibility="collapsed"
                )
                st.session_state.novo_treino_exercicios[i]["series"] = int(nova_series)
            with col_rem:
                if st.button("✕", key=f"rem_ex_{i}", help="Remover"):
                    st.session_state.novo_treino_exercicios.pop(i)
                    st.rerun()

        # Reordenar (subir/descer)
        st.markdown("<div style='font-size:0.8rem;color:#666;margin-top:-0.3rem'>Você pode reordenar arrastando ou removendo e re-adicionando.</div>", unsafe_allow_html=True)

        st.markdown("")
        col_salvar, col_limpar, _ = st.columns([2, 1, 3])
        with col_salvar:
            if st.button("💾 Salvar treino", type="primary", use_container_width=True, key="btn_salvar_treino"):
                nome_treino = st.session_state.get("novo_treino_nome_input", "").strip()
                if not nome_treino:
                    st.error("Digite o nome do treino.")
                elif not st.session_state.novo_treino_exercicios:
                    st.error("Adicione pelo menos um exercício.")
                else:
                    sucesso = True
                    for ex in st.session_state.novo_treino_exercicios:
                        resultado = adicionar_treino(
                            treino=nome_treino,
                            exercicio=ex["nome"],
                            foco=ex["foco"],
                            series=ex["series"]
                        )
                        if not resultado:
                            sucesso = False
                    if sucesso:
                        st.success(f"✓ Treino '{nome_treino}' salvo com {len(st.session_state.novo_treino_exercicios)} exercícios!")
                        st.session_state.novo_treino_exercicios = []
                        st.rerun()
                    else:
                        st.error("Erro ao salvar treino.")
        with col_limpar:
            if st.button("🗑️ Limpar", use_container_width=True, key="btn_limpar_treino"):
                st.session_state.novo_treino_exercicios = []
                st.rerun()
    else:
        st.info("Adicione exercícios ao treino usando o seletor acima.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Treinos existentes ────────────────────────────────────────────────────
    st.markdown("#### 📋 Treinos cadastrados")

    todos_treinos = listar_treinos()  # [(id, treino, exercicio, foco, series, data_criacao)]
    if not todos_treinos:
        st.info("Nenhum treino cadastrado ainda.")
        return

    # Agrupar por nome do treino
    por_treino = {}
    for (tid, treino_nome, exercicio, foco, series, _) in todos_treinos:
        por_treino.setdefault(treino_nome, []).append({
            "id": tid, "exercicio": exercicio, "foco": foco, "series": series
        })

    for treino_nome, exercicios in por_treino.items():
        with st.expander(f"{treino_nome}  ({len(exercicios)} exercícios)"):
            for ex in exercicios:
                st.markdown(
                    f"<div class='treino-card-ex'>• <b>{ex['exercicio']}</b> "
                    f"<span style='color:#888'>({ex['foco']})</span>"
                    f"<span class='badge-series'>{ex['series']} séries</span></div>",
                    unsafe_allow_html=True
                )
            st.markdown("")
            if st.button(f"🗑️ Deletar treino '{treino_nome}'", key=f"del_treino_{treino_nome}", type="secondary"):
                deletar_treino_completo(treino_nome)
                st.success(f"Treino '{treino_nome}' deletado.")
                st.rerun()