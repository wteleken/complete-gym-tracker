"""
pagina_dieta.py — GymTracker
Página de Dieta & Peso
"""

import streamlit as st
from datetime import datetime, date
from sqlmgnt_dieta import (
    MACRO_FIELDS, MACRO_LABELS,
    adicionar_alimento, listar_alimentos, deletar_alimento, obter_alimento_por_nome,
    adicionar_refeicao, listar_refeicoes, deletar_refeicao,
    registrar_peso, listar_pesos, obter_peso_por_data,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _divider():
    st.markdown('<hr style="border:none;border-top:1px solid #2a2a2a;margin:1.2rem 0">', unsafe_allow_html=True)


def _section_title(title):
    st.markdown(
        f"<div style='font-size:1rem;font-weight:700;color:#ccc;margin-bottom:0.5rem'>{title}</div>",
        unsafe_allow_html=True
    )


def _calcular_macros_para_gramas(alimento: dict, gramas: float) -> dict:
    """Escala os macros do alimento para a quantidade em gramas."""
    fator = gramas / (alimento["porcao_g"] or 100)
    return {f: round((alimento.get(f) or 0) * fator, 2) for f in MACRO_FIELDS}


# ── Render principal ──────────────────────────────────────────────────────────

def render_dieta():
    st.markdown("""
    <style>
    .dieta-header { font-size:1.6rem;font-weight:800;color:#FF0000;letter-spacing:-0.5px;margin-bottom:0.2rem; }
    .dieta-sub    { color:#888;font-size:0.9rem;margin-bottom:1rem; }
    .card-alimento {
        background:#1a1a1a;border-radius:10px;padding:0.9rem 1rem;
        border-left:3px solid #FF0000;margin-bottom:0.5rem;
    }
    .card-alimento .nome { font-weight:700;color:#fff;font-size:0.95rem; }
    .card-alimento .info { color:#777;font-size:0.75rem;margin-top:2px; }
    .card-refeicao {
        background:#1a1a1a;border-radius:10px;padding:0.85rem 1rem;
        border-left:3px solid #444;margin-bottom:0.4rem;
    }
    .card-refeicao .nome { font-weight:700;color:#fff;font-size:0.9rem; }
    .card-refeicao .hora { color:#666;font-size:0.75rem; }
    .card-refeicao .macros { color:#aaa;font-size:0.75rem;margin-top:3px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="dieta-header">Dieta & Peso</div>', unsafe_allow_html=True)
    st.markdown('<div class="dieta-sub">Registre refeições, alimentos e seu peso diário</div>', unsafe_allow_html=True)

    # ── Abas ──────────────────────────────────────────────────────────────────
    if "dieta_aba" not in st.session_state:
        st.session_state.dieta_aba = "Registrar Refeição"

    abas = ["Registrar Refeição", "Peso Diário", "Alimentos", "Histórico"]
    cols_aba = st.columns(len(abas))
    for i, aba in enumerate(abas):
        ativo = st.session_state.dieta_aba == aba
        if cols_aba[i].button(
            f"**{aba}**" if ativo else aba,
            key=f"dieta_aba_{aba}",
            use_container_width=True,
            type="primary" if ativo else "secondary",
        ):
            st.session_state.dieta_aba = aba
            st.rerun()

    _divider()
    aba = st.session_state.dieta_aba

    # ══════════════════════════════════════════════════════════════════════════
    # ABA: REGISTRAR REFEIÇÃO
    # ══════════════════════════════════════════════════════════════════════════
    if aba == "Registrar Refeição":
        _section_title("Nova refeição")

        if "dieta_modo_refeicao" not in st.session_state:
            st.session_state.dieta_modo_refeicao = "Usando alimentos cadastrados"

        modos_ref = ["Usando alimentos cadastrados", "Registro direto"]
        cols_modo_ref = st.columns(2)
        for i, m in enumerate(modos_ref):
            ativo_m = st.session_state.dieta_modo_refeicao == m
            if cols_modo_ref[i].button(
                f"**{m}**" if ativo_m else m,
                key=f"modo_ref_{m}",
                use_container_width=True,
                type="primary" if ativo_m else "secondary",
            ):
                st.session_state.dieta_modo_refeicao = m
                st.rerun()

        modo = st.session_state.dieta_modo_refeicao

        # Data e hora
        col_data, col_hora = st.columns(2)
        with col_data:
            data_ref = st.date_input("Data", value=date.today(), key="ref_data")
        with col_hora:
            hora_ref = st.time_input("Hora", value=datetime.now().time(), key="ref_hora")

        data_hora_dt = datetime.combine(data_ref, hora_ref)

        # ── Modo 1: Alimentos cadastrados ─────────────────────────────────────
        if modo == "Usando alimentos cadastrados":
            alimentos_db = listar_alimentos()
            if not alimentos_db:
                st.info("Nenhum alimento cadastrado. Cadastre na aba 'Alimentos'.")
            else:
                nomes_alimentos = [a["nome"] for a in alimentos_db]
                alimento_map = {a["nome"]: a for a in alimentos_db}

                if "itens_refeicao" not in st.session_state:
                    st.session_state.itens_refeicao = [{"nome": nomes_alimentos[0], "gramas": 100.0}]

                itens = st.session_state.itens_refeicao

                for i, item in enumerate(itens):
                    with st.container():
                        col_n, col_g, col_del = st.columns([3, 2, 1])
                        with col_n:
                            nome_sel = st.selectbox(
                                f"Alimento {i+1}",
                                nomes_alimentos,
                                index=nomes_alimentos.index(item["nome"]) if item["nome"] in nomes_alimentos else 0,
                                key=f"item_nome_{i}",
                            )
                        with col_g:
                            gramas_sel = st.number_input(
                                "Gramas", min_value=0.0, step=5.0,
                                value=float(item["gramas"]),
                                key=f"item_gramas_{i}",
                            )
                        with col_del:
                            st.write("")
                            st.write("")
                            if st.button("✕", key=f"del_item_{i}", use_container_width=True):
                                st.session_state.itens_refeicao.pop(i)
                                st.rerun()

                        item["nome"] = nome_sel
                        item["gramas"] = gramas_sel

                        # Preview de macros do item
                        al = alimento_map.get(nome_sel)
                        if al and gramas_sel > 0:
                            m = _calcular_macros_para_gramas(al, gramas_sel)
                            st.markdown(
                                f"<div style='font-size:0.72rem;color:#666;margin-bottom:6px;'>"
                                f"Cal {m['calorias']:.0f} kcal &nbsp;|&nbsp;"
                                f"Prot {m['proteinas']:.1f}g &nbsp;|&nbsp;"
                                f"Carb {m['carboidratos']:.1f}g &nbsp;|&nbsp;"
                                f"Gord {m['gorduras_totais']:.1f}g"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

                col_add, _ = st.columns([2, 4])
                with col_add:
                    if st.button("＋ Adicionar alimento", use_container_width=True):
                        st.session_state.itens_refeicao.append({"nome": nomes_alimentos[0], "gramas": 100.0})
                        st.rerun()

                # Totais
                if itens:
                    totais = {f: 0.0 for f in MACRO_FIELDS}
                    gramas_total = 0.0
                    nomes_itens = []
                    for item in itens:
                        al = alimento_map.get(item["nome"])
                        if al and item["gramas"] > 0:
                            m = _calcular_macros_para_gramas(al, item["gramas"])
                            for f in MACRO_FIELDS:
                                totais[f] += m[f]
                            gramas_total += item["gramas"]
                            nomes_itens.append(item["nome"])

                    _divider()
                    st.markdown(
                        f"<div style='background:#111;border-radius:10px;padding:0.8rem 1rem;"
                        f"border:1px solid #2a2a2a;margin-bottom:0.8rem;'>"
                        f"<div style='font-size:0.8rem;font-weight:700;color:#FF0000;margin-bottom:6px;'>Totais da refeição</div>"
                        f"<div style='font-size:0.8rem;color:#aaa;display:flex;flex-wrap:wrap;gap:10px;'>"
                        f"<span>Cal <b style='color:#fff'>{totais['calorias']:.0f}</b> kcal</span>"
                        f"<span>Prot <b style='color:#fff'>{totais['proteinas']:.1f}</b>g</span>"
                        f"<span>Carb <b style='color:#fff'>{totais['carboidratos']:.1f}</b>g</span>"
                        f"<span>Gord <b style='color:#fff'>{totais['gorduras_totais']:.1f}</b>g</span>"
                        f"<span>Fibras <b style='color:#fff'>{totais['fibras']:.1f}</b>g</span>"
                        f"<span>Sódio <b style='color:#fff'>{totais['sodio']:.0f}</b>mg</span>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

                    nome_refeicao = " + ".join(nomes_itens) if nomes_itens else "Refeição"

                    if st.button("💾 Salvar refeição", type="primary", use_container_width=False):
                        rid = adicionar_refeicao(
                            nome=nome_refeicao,
                            data_hora=data_hora_dt,
                            gramas=gramas_total,
                            **{f: round(totais[f], 2) for f in MACRO_FIELDS},
                        )
                        if rid:
                            st.success(f"✓ Refeição '{nome_refeicao}' salva!")
                            st.session_state.itens_refeicao = [{"nome": nomes_alimentos[0], "gramas": 100.0}]
                            st.rerun()
                        else:
                            st.error("Erro ao salvar refeição.")

        # ── Modo 2: Registro direto ───────────────────────────────────────────
        else:
            nome_dir = st.text_input("Nome da refeição", placeholder="ex: Frango grelhado", key="dir_nome")
            gramas_dir = st.number_input("Gramas consumidos (total)", min_value=0.0, step=10.0, key="dir_gramas")

            _section_title("Informações nutricionais (para a quantidade acima)")
            cols = st.columns(2)
            macro_vals = {}
            for i, f in enumerate(MACRO_FIELDS):
                col = cols[i % 2]
                macro_vals[f] = col.number_input(
                    MACRO_LABELS[f], min_value=0.0, step=0.1,
                    key=f"dir_macro_{f}",
                )

            if st.button("💾 Salvar refeição", type="primary", key="dir_salvar"):
                if not nome_dir.strip():
                    st.warning("Informe o nome da refeição.")
                else:
                    rid = adicionar_refeicao(
                        nome=nome_dir.strip(),
                        data_hora=data_hora_dt,
                        gramas=gramas_dir,
                        **{f: macro_vals[f] for f in MACRO_FIELDS},
                    )
                    if rid:
                        st.success(f"✓ Refeição '{nome_dir}' salva!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar refeição.")

    # ══════════════════════════════════════════════════════════════════════════
    # ABA: PESO DIÁRIO
    # ══════════════════════════════════════════════════════════════════════════
    elif aba == "Peso Diário":
        _section_title("Registrar peso de hoje")

        data_peso = st.date_input("Data", value=date.today(), key="peso_data")
        peso_atual = obter_peso_por_data(data_peso.strftime("%Y-%m-%d"))

        peso_input = st.number_input(
            "Peso (kg)",
            min_value=20.0, max_value=300.0, step=0.1,
            value=float(peso_atual) if peso_atual else 70.0,
            key="peso_input",
        )

        if peso_atual:
            st.caption(f"Peso já registrado para {data_peso}: **{peso_atual} kg**")

        if st.button("💾 Salvar peso", type="primary"):
            ok = registrar_peso(data_peso, peso_input)
            if ok:
                st.success(f"✓ Peso de {peso_input} kg salvo para {data_peso}!")
                st.rerun()
            else:
                st.error("Erro ao salvar peso.")

        _divider()
        _section_title("Histórico de peso")

        pesos = listar_pesos()
        if pesos:
            import pandas as pd
            import altair as alt
            df_peso = pd.DataFrame(pesos, columns=["Data", "Peso (kg)"])
            df_peso["Data"] = pd.to_datetime(df_peso["Data"])
            df_peso = df_peso.sort_values("Data")
            peso_min = df_peso["Peso (kg)"].min()
            peso_max = df_peso["Peso (kg)"].max()
            y_min = round(peso_min * 0.99, 1)
            y_max = round(peso_max + (peso_max - peso_min) * 0.1 + 0.5, 1)
            chart = (
                alt.Chart(df_peso)
                .mark_line(color="#FF0000", strokeWidth=2, point=alt.OverlayMarkDef(color="#FF0000", size=40))
                .encode(
                    x=alt.X("Data:T", axis=alt.Axis(format="%d/%m", labelColor="#666", tickColor="#333", domainColor="#333")),
                    y=alt.Y("Peso (kg):Q", scale=alt.Scale(domain=[y_min, y_max]),
                            axis=alt.Axis(labelColor="#666", tickColor="#333", domainColor="#333", gridColor="#222")),
                    tooltip=[alt.Tooltip("Data:T", format="%d/%m/%Y"), alt.Tooltip("Peso (kg):Q", format=".1f")],
                )
                .properties(height=240, background="transparent")
                .configure_view(strokeWidth=0)
            )
            st.altair_chart(chart, use_container_width=True)

        else:
            st.info("Nenhum peso registrado ainda.")

    # ══════════════════════════════════════════════════════════════════════════
    # ABA: ALIMENTOS
    # ══════════════════════════════════════════════════════════════════════════
    elif aba == "Alimentos":
        col_left, col_right = st.columns([2, 3])

        with col_left:
            _section_title("Cadastrar alimento")
            nome_al = st.text_input("Nome", placeholder="ex: Arroz branco", key="al_nome")
            porcao = st.number_input("Porção de referência (g)", min_value=1.0, value=100.0, step=1.0, key="al_porcao")

            st.markdown("<div style='font-size:0.8rem;color:#666;margin:6px 0 4px;'>Macros por essa porção:</div>", unsafe_allow_html=True)
            macro_al = {}
            for f in MACRO_FIELDS:
                macro_al[f] = st.number_input(
                    MACRO_LABELS[f], min_value=0.0, step=0.1,
                    key=f"al_macro_{f}",
                )

            if st.button("＋ Cadastrar", type="primary", key="al_cadastrar"):
                if not nome_al.strip():
                    st.warning("Informe o nome do alimento.")
                else:
                    aid = adicionar_alimento(nome_al.strip(), porcao, **{f: macro_al[f] for f in MACRO_FIELDS})
                    if aid:
                        st.success(f"✓ '{nome_al}' cadastrado!")
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar (nome já existe?).")

        with col_right:
            _section_title("Alimentos cadastrados")
            alimentos = listar_alimentos()
            if not alimentos:
                st.info("Nenhum alimento cadastrado.")
            else:
                for al in alimentos:
                    with st.container():
                        col_info, col_del = st.columns([5, 1])
                        with col_info:
                            macros_str = (
                                f"Cal {al.get('calorias', 0):.0f} kcal &nbsp;·&nbsp; "
                                f"Prot {al.get('proteinas', 0):.1f}g &nbsp;·&nbsp; "
                                f"Carb {al.get('carboidratos', 0):.1f}g &nbsp;·&nbsp; "
                                f"Gord {al.get('gorduras_totais', 0):.1f}g"
                            )
                            st.markdown(
                                f"<div class='card-alimento'>"
                                f"  <div class='nome'>{al['nome']}</div>"
                                f"  <div class='info'>Porção: {al['porcao_g']:.0f}g</div>"
                                f"  <div class='info'>{macros_str}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        with col_del:
                            st.write("")
                            st.write("")
                            if st.button("🗑️", key=f"del_al_{al['id']}"):
                                deletar_alimento(al["id"])
                                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # ABA: HISTÓRICO
    # ══════════════════════════════════════════════════════════════════════════
    elif aba == "Histórico":
        _section_title("Refeições registradas")

        import pandas as pd
        from datetime import timedelta

        col_di, col_df = st.columns(2)
        with col_di:
            di = st.date_input("De", value=date.today() - timedelta(days=7), key="hist_di")
        with col_df:
            df_date = st.date_input("Até", value=date.today(), key="hist_df")

        refeicoes = listar_refeicoes(
            data_inicio=di.isoformat(),
            data_fim=df_date.isoformat() + "T23:59:59",
        )

        if not refeicoes:
            st.info("Nenhuma refeição no período selecionado.")
        else:
            # Agrupa por dia
            dias_dict = {}
            for r in refeicoes:
                d = r["data_hora"][:10]
                dias_dict.setdefault(d, []).append(r)

            for d in sorted(dias_dict.keys(), reverse=True):
                refeicoes_do_dia = dias_dict[d]
                total_kcal = sum(r.get("calorias", 0) or 0 for r in refeicoes_do_dia)

                with st.expander(f" {d}  —  {total_kcal:.0f} kcal total"):
                    for r in sorted(refeicoes_do_dia, key=lambda x: x["data_hora"]):
                        hora = r["data_hora"][11:16]
                        macros_str = (
                            f"Cal {r.get('calorias',0):.0f} kcal &nbsp;·&nbsp; "
                            f"Prot {r.get('proteinas',0):.1f}g &nbsp;·&nbsp; "
                            f"Carb {r.get('carboidratos',0):.1f}g &nbsp;·&nbsp; "
                            f"Gord {r.get('gorduras_totais',0):.1f}g &nbsp;·&nbsp; "
                            f"Sódio {r.get('sodio',0):.0f}mg"
                        )
                        col_r, col_del_r = st.columns([6, 1])
                        with col_r:
                            st.markdown(
                                f"<div class='card-refeicao'>"
                                f"  <div style='display:flex;justify-content:space-between;'>"
                                f"    <div class='nome'>{r['nome']}</div>"
                                f"    <div class='hora'>{hora}</div>"
                                f"  </div>"
                                f"  <div class='macros'>{macros_str}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        with col_del_r:
                            if st.button("🗑️", key=f"del_ref_{r['id']}"):
                                deletar_refeicao(r["id"])
                                st.rerun()