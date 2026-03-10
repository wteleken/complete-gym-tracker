import streamlit as st
import pandas as pd
from sqlmgnt import *

# ── Helpers ───────────────────────────────────────────────────────────────────

def calcular_1rm(peso, reps, rir):
    reps_efetivas = reps + rir
    if reps_efetivas <= 0:
        return 0.0
    return peso * (1 + 0.0333 * reps_efetivas)

def kpi_card(col, value, label):
    col.markdown(
        f"<div class='kpi-card'>"
        f"  <div class='kpi-value'>{value}</div>"
        f"  <div class='kpi-label'>{label}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

def divider():
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

def chart_volume_semanal(volume_data, height=260):
    if volume_data:
        df = pd.DataFrame(volume_data, columns=["Semana", "Volume (kg×reps)"])
        df = df.set_index("Semana")
        st.line_chart(df, color="#FF0000", height=height)
    else:
        st.info("Sem dados suficientes para exibir.")

def chart_barras(data, col_nome, col_valor, height=300):
    if not data:
        st.info("Sem dados suficientes.")
        return
    nomes = [row[0] for row in data]
    valores = [row[1] for row in data]
    df = pd.DataFrame({col_valor: valores}, index=nomes).round(0)
    df.index.name = col_nome
    d = df[col_valor].to_dict()
    st.bar_chart(d, color="#FF0000", height=height, sort=False, horizontal=True)

def render_body_map(dados_musculo):
    """Renderiza mapa do corpo humano colorido por volume muscular.
    dados_musculo: lista de [nome_musculo, volume]
    """
    import streamlit.components.v1 as components
    import json, os
    data_dict = {row[0]: row[1] for row in dados_musculo} if dados_musculo else {}
    data_json = json.dumps(data_dict, ensure_ascii=False)
    template_path = os.path.join(os.path.dirname(__file__), "body_map_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("%%MUSCLE_DATA%%", data_json)
    components.html(html, height=380, scrolling=False)

# ── Render ────────────────────────────────────────────────────────────────────

def render_estatisticas():
    st.markdown("""
    <style>
    .stats-header {
        font-size: 1.6rem; font-weight: 800; color: #FF0000;
        letter-spacing: -0.5px; margin-bottom: 0.2rem;
    }
    .stats-sub { color: #888; font-size: 0.9rem; margin-bottom: 1rem; }
    .kpi-card {
        background: #1a1a1a; border-radius: 12px;
        padding: 1.1rem 1rem; text-align: center;
        border-top: 3px solid #FF0000;
    }
    .kpi-value { font-size: 2rem; font-weight: 900; color: #FF0000; line-height: 1; }
    .kpi-label {
        font-size: 0.78rem; color: #888; margin-top: 0.3rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .section-divider { border: none; border-top: 1px solid #2a2a2a; margin: 1.5rem 0; }
    .chart-title { font-size: 0.95rem; font-weight: 700; color: #ccc; margin-bottom: 0.3rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stats-header">Estatísticas</div>', unsafe_allow_html=True)
    st.markdown('<div class="stats-sub">Acompanhe sua evolução e recordes pessoais</div>', unsafe_allow_html=True)

    stats_gerais = obter_stats_gerais()
    if not stats_gerais or stats_gerais.get("total_series", 0) == 0:
        st.info("Nenhum dado de histórico encontrado. Registre seus primeiros treinos!")
        return

    # ── Seletor de modo ───────────────────────────────────────────────────────
    if "stats_modo" not in st.session_state:
        st.session_state.stats_modo = "Tudo"

    modos = ["Tudo", "Treino", "Músculo", "Exercício", "Frequência"]
    cols_modo = st.columns(len(modos))
    for i, modo in enumerate(modos):
        ativo = st.session_state.stats_modo == modo
        label = f"**{modo}**" if ativo else modo
        if cols_modo[i].button(label, key=f"modo_{modo}", use_container_width=True,
                               type="primary" if ativo else "secondary"):
            st.session_state.stats_modo = modo
            st.rerun()

    divider()
    modo = st.session_state.stats_modo

    # ══════════════════════════════════════════════════════════════════════════
    # MODO: TUDO
    # ══════════════════════════════════════════════════════════════════════════
    if modo == "Tudo":
        col1, col2, col3, col4 = st.columns(4)
        kpi_card(col1, stats_gerais.get("total_sessoes", 0),             "Sessões")
        kpi_card(col2, stats_gerais.get("total_series", 0),              "Séries totais")
        kpi_card(col3, stats_gerais.get("total_exercicios", 0),          "Exercícios treinados")
        kpi_card(col4, f"{stats_gerais.get('volume_total', 0):,.0f} kg", "Volume total (kg×reps)")

        divider()
        st.markdown('<div class="chart-title">Volume semanal</div>', text_alignment="center",
                    unsafe_allow_html=True)
        chart_volume_semanal(obter_volume_semanal())

        divider()
        col1t, col2t = st.columns(2)
        with col1t:
            st.markdown('<div class="chart-title">Mapa muscular — volume médio (AVG 3W)</div>',
                        unsafe_allow_html=True, text_alignment="center")
            render_body_map(obter_media_volume_semanal_por_musculo(n_semanas=3))

        with col2t:
            st.markdown('<div class="chart-title">Volume semanal por músculo (AVG 3W)</div>',
                        unsafe_allow_html=True, text_alignment="center")
            chart_barras(obter_media_volume_semanal_por_musculo(n_semanas=3),
                            "Músculo", "Média Vol. (kg×reps)", height=320)

        divider()

        st.markdown('<div class="chart-title">Volume semanal por exercício (AVG 3W)</div>',
                    unsafe_allow_html=True, text_alignment="center")
        chart_barras(obter_media_volume_semanal_todos_exercicios(n_semanas=3),
                        "Exercício", "Média Vol. (kg×reps)", height=320)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO: TREINO
    # ══════════════════════════════════════════════════════════════════════════
    elif modo == "Treino":
        treinos_nomes = sorted(set(t[1] for t in listar_treinos()))
        if not treinos_nomes:
            st.info("Nenhum treino cadastrado.")
            return

        col_sel, _ = st.columns([2, 4])
        with col_sel:
            treino_sel = st.selectbox("Selecione o treino", treinos_nomes, key="stats_treino_sel")

        stats = obter_stats_por_treino(treino_sel)
        col1, col2 = st.columns(2)
        kpi_card(col1, stats.get("total_sessoes", 0),             "Sessões")
        kpi_card(col2, f"{stats.get('volume_total', 0):,.0f} kg", "Volume total (kg×reps)")

        divider()
        st.markdown(f'<div class="chart-title">Volume semanal - {treino_sel}</div>',
                    unsafe_allow_html=True, text_alignment="center")
        chart_volume_semanal(obter_volume_semanal(treino_nome=treino_sel))

    # ══════════════════════════════════════════════════════════════════════════
    # MODO: MÚSCULO
    # ══════════════════════════════════════════════════════════════════════════
    elif modo == "Músculo":
        focos = obter_focos_disponiveis()
        if not focos:
            st.info("Nenhum grupo muscular cadastrado ainda.")
            return

        col_sel, _ = st.columns([2, 4])
        with col_sel:
            foco_sel = st.selectbox("Selecione o músculo", focos, key="stats_musculo_sel")

        stats = obter_stats_por_musculo(foco_sel)
        col1, col2 = st.columns(2)
        kpi_card(col1, stats.get("total_series", 0),              "Séries totais")
        kpi_card(col2, f"{stats.get('volume_total', 0):,.0f} kg", "Volume total (kg×reps)")

        divider()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown(f'<div class="chart-title">Volume semanal — {foco_sel}</div>', text_alignment= "center",
                        unsafe_allow_html=True)
            chart_volume_semanal(obter_volume_por_data_musculo(foco_sel))
        with col_g2:
            st.markdown(f'<div class="chart-title">Volume semanal por exercício — {foco_sel} (AVG 3W)</div>',
                        unsafe_allow_html=True, text_alignment="center")
            chart_barras(obter_media_volume_semanal_por_exercicio_musculo(foco_sel, n_semanas=3),
                         "Exercício", "Média Vol. (kg×reps)", height=300)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO: FREQUÊNCIA
    # ══════════════════════════════════════════════════════════════════════════
    elif modo == "Frequência":
        from datetime import date, timedelta

        dias = obter_dias_frequentados()

        if not dias:
            st.info("Nenhum treino registrado ainda.")
        else:
            hoje = date.today()
            inicio = hoje - timedelta(days=364)

            datas = sorted(dias.keys())
            total_dias = len(datas)

            streak = 0
            d = hoje
            while d.strftime("%Y-%m-%d") in dias:
                streak += 1
                d -= timedelta(days=1)

            col1, col2, col3 = st.columns(3)
            kpi_card(col1, total_dias, "Dias treinados")
            kpi_card(col2, streak, "Streak atual (dias)")
            kpi_card(col3, len([d for d in datas if d >= (hoje - timedelta(days=30)).strftime("%Y-%m-%d")]), "Treinos último mês")

            divider()
            st.markdown(f'<div class="chart-title">Atividade nos últimos 12 meses<div>', 
                        unsafe_allow_html=True, text_alignment="center")
            st.write("")

            start_monday = inicio - timedelta(days=inicio.weekday())
            weeks = []
            current = start_monday
            while current <= hoje:
                week = []
                for i in range(7):
                    day = current + timedelta(days=i)
                    ds = day.strftime("%Y-%m-%d")
                    week.append((day, ds, dias.get(ds, 0)))
                weeks.append(week)
                current += timedelta(days=7)

            day_labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            month_seen = set()

            # ── Desktop ───────────────────────────────────────────────────────
            cells_by_row = [[] for _ in range(7)]
            for week in weeks:
                for row_idx, (day, ds, count) in enumerate(week):
                    if day < inicio or day > hoje:
                        color = "transparent"; border = "none"; tooltip = ""
                    elif count == 0:
                        color = "#1a1a1a"; border = "1px solid #2a2a2a"; tooltip = ds
                    else:
                        color = "#FF0000"; border = "none"; tooltip = f"{ds}: {count} treino(s)"
                    cells_by_row[row_idx].append((color, border, tooltip, day))

            desktop_html = "<div style='display:flex;gap:6px;align-items:flex-start;overflow-x:auto;padding-bottom:8px;'>"
            desktop_html += "<div style='display:flex;flex-direction:column;gap:3px;padding-top:20px;'>"
            for lbl in day_labels:
                desktop_html += f"<div style='height:13px;width:28px;font-size:0.65rem;color:#555;line-height:13px;'>{lbl}</div>"
            desktop_html += "</div>"

            for w_idx, week in enumerate(weeks):
                first_day = week[0][0]
                month_label = ""
                month_key = first_day.strftime("%Y-%m")
                if month_key not in month_seen and first_day.day <= 7:
                    month_label = first_day.strftime("%b")
                    month_seen.add(month_key)
                desktop_html += "<div style='display:flex;flex-direction:column;gap:3px;'>"
                desktop_html += f"<div style='height:16px;font-size:0.65rem;color:#666;'>{month_label}</div>"
                for row_idx in range(7):
                    color, border, tooltip, day = cells_by_row[row_idx][w_idx]
                    style = f"width:13px;height:13px;border-radius:2px;background:{color};border:{border};flex-shrink:0;"
                    desktop_html += f"<div style='{style}' title='{tooltip}'></div>" if tooltip else f"<div style='{style}'></div>"
                desktop_html += "</div>"
            desktop_html += "</div>"

            # ── Mobile ────────────────────────────────────────────────────────
            mobile_html = "<div style='display:flex;flex-direction:column;align-items:center;'>"
            mobile_html += "<div style='display:flex;gap:4px;margin-bottom:6px;'>"
            for lbl in day_labels:
                mobile_html += f"<div style='width:36px;font-size:0.65rem;color:#555;text-align:center;'>{lbl}</div>"
            mobile_html += "</div>"

            month_seen_m = set()
            for week in reversed(weeks):
                first_day = week[0][0]
                month_key = first_day.strftime("%Y-%m")
                if month_key not in month_seen_m:
                    mobile_html += f"<div style='font-size:0.75rem;font-weight:700;color:#666;margin:10px 0 4px;text-transform:uppercase;letter-spacing:1px;'>{first_day.strftime('%b %Y')}</div>"
                    month_seen_m.add(month_key)
                mobile_html += "<div style='display:flex;gap:4px;margin-bottom:4px;'>"
                for day, ds, count in week:
                    if day < inicio or day > hoje:
                        color = "transparent"; border = "none"; tooltip = ""
                    elif count == 0:
                        color = "#1a1a1a"; border = "1px solid #2a2a2a"; tooltip = ds
                    else:
                        color = "#FF0000"; border = "none"; tooltip = f"{ds}: {count} treino(s)"
                    txt_color = "#000" if color == "#FF0000" else "#444"
                    style = f"width:36px;height:36px;border-radius:4px;background:{color};border:{border};flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:0.65rem;font-weight:700;color:{txt_color};"
                    day_num = day.day if (day >= inicio and day <= hoje) else ""
                    mobile_html += f"<div style='{style}' title='{tooltip}'>{day_num}</div>"
                mobile_html += "</div>"
            mobile_html += "</div>"

            legenda = """
            <div style='display:flex;align-items:center;gap:6px;margin-top:10px;font-size:0.72rem;color:#555;'>
                <div style='width:13px;height:13px;border-radius:2px;background:#1a1a1a;border:1px solid #2a2a2a'></div>
                <span>Sem treino</span>
                <div style='width:13px;height:13px;border-radius:2px;background:#FF0000;margin-left:8px'></div>
                <span>Treinou</span>
            </div>"""

            full_html = f"""
            <div>
                <div class="freq-desktop">{desktop_html}{legenda}</div>
                <div class="freq-mobile">{mobile_html}{legenda}</div>
            </div>
            <style>
                .freq-mobile {{ display: none; }}
                .freq-desktop {{ display: block; }}
                @media (max-width: 768px) {{
                    .freq-mobile {{ display: block; }}
                    .freq-desktop {{ display: none; }}
                }}
            </style>
            """
            st.markdown(full_html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # MODO: EXERCÍCIO
    # ══════════════════════════════════════════════════════════════════════════
    elif modo == "Exercício":
        exercicios_db = listar_exercicios()
        if not exercicios_db:
            st.info("Nenhum exercício cadastrado ainda.")
            return

        opcoes_ex = [nome for (_, nome, _, _, _) in exercicios_db]
        col_sel, _ = st.columns([2, 4])
        with col_sel:

            ex_sel = st.selectbox("Selecione o exercício", opcoes_ex, key="stats_ex_sel")

        stats = obter_stats_por_exercicio(ex_sel)
        col1, col2 = st.columns(2)
        kpi_card(col1, stats.get("total_series", 0),              "Séries totais")
        kpi_card(col2, f"{stats.get('volume_total', 0):,.0f} kg", "Volume total (kg×reps)")

        hist = obter_historico_exercicio_completo(ex_sel)
        if not hist:
            st.info(f"Nenhum histórico registrado para '{ex_sel}' ainda.")
            return

        df = pd.DataFrame(hist, columns=["data", "serie", "peso", "reps", "rir"])
        df["data"] = pd.to_datetime(df["data"])
        df["volume_serie"] = df["peso"] * df["reps"]
        df["1rm_serie"] = df.apply(lambda r: calcular_1rm(r["peso"], r["reps"], r["rir"]), axis=1)

        df_sessao = df.groupby("data").agg(
            volume_total=("volume_serie", "sum"),
            peso_max=("peso", "max"),
            pr_estimado=("1rm_serie", "max"),
        ).reset_index().set_index("data")

        divider()

        tab1, tab2, tab3 = st.tabs([
            "Volume por sessão",
            "Peso máximo por sessão",
            "1RM estimado por sessão",
        ])

        with tab1:
            st.markdown(f'<div class="chart-title">Volume por sessão — {ex_sel}</div>',
                        unsafe_allow_html=True)
            st.line_chart(
                df_sessao[["volume_total"]].rename(columns={"volume_total": "Volume (kg×reps)"}),
                color="#FF0000", height=260
            )
        with tab2:
            st.markdown(f'<div class="chart-title">Peso máximo por sessão — {ex_sel}</div>',
            unsafe_allow_html=True)
            st.line_chart(
                df_sessao[["peso_max"]].rename(columns={"peso_max": "Peso máx (kg)"}),
                color="#FF0000", height=260
            )
        with tab3:
            st.markdown(f'<div class="chart-title">1RM estimado por sessão — {ex_sel}</div>',
            unsafe_allow_html=True)
            st.line_chart(
                df_sessao[["pr_estimado"]].rename(columns={"pr_estimado": "1RM estimado (kg)"}),
                color="#FF0000", height=260
            )
            st.caption("Fórmula de Epley ajustada com RIR:   \n1RM = carga × (1 + 0.0333 × (reps + RIR)) — melhor série do dia")













