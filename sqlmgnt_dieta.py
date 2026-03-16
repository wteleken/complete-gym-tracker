"""
sqlmgnt_dieta.py — GymTracker
Camada de dados para Dieta e Peso usando Supabase.
"""


from datetime import datetime, timedelta
import streamlit as st
from supabase import Client


@st.cache_resource
def _get_client() -> Client:
    from supabase import create_client
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def _sb() -> Client:
    return _get_client()


# ── Campos de macros (mesma ordem das tabelas do Supabase) ────────────────────
MACRO_FIELDS = [
    "calorias",
    "carboidratos",
    "acucares",
    "acucares_adicionados",
    "proteinas",
    "gorduras_totais",
    "gorduras_saturadas",
    "gorduras_trans",
    "fibras",
    "sodio",
]

MACRO_LABELS = {
    "calorias":            "Calorias (kcal)",
    "carboidratos":        "Carboidratos (g)",
    "acucares":            "Açúcares (g)",
    "acucares_adicionados":"Açúcares adicionados (g)",
    "proteinas":           "Proteínas (g)",
    "gorduras_totais":     "Gorduras totais (g)",
    "gorduras_saturadas":  "Gorduras saturadas (g)",
    "gorduras_trans":      "Gorduras trans (g)",
    "fibras":              "Fibras (g)",
    "sodio":               "Sódio (mg)",
}

# ==============================================================================
# ALIMENTOS
# ==============================================================================

def adicionar_alimento(nome, porcao_g, **macros):
    """
    macros: calorias, carboidratos, acucares, acucares_adicionados, proteinas,
            gorduras_totais, gorduras_saturadas, gorduras_trans, fibras, sodio
    """
    try:
        payload = {"nome": nome, "porcao_g": porcao_g}
        for field in MACRO_FIELDS:
            payload[field] = macros.get(field, 0)
        res = _sb().table("alimento").insert(payload).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"✗ Erro ao adicionar alimento: {e}")
        return None


def listar_alimentos():
    """Retorna lista de dicts com todos os campos do alimento."""
    try:
        rows = _sb().table("alimento").select("*").order("nome").execute().data
        return rows
    except Exception as e:
        print(f"✗ Erro ao listar alimentos: {e}")
        return []


def obter_alimento_por_nome(nome):
    try:
        res = _sb().table("alimento").select("*").eq("nome", nome).limit(1).execute().data
        return res[0] if res else None
    except Exception as e:
        print(f"✗ Erro ao obter alimento: {e}")
        return None


def atualizar_alimento(alimento_id, nome, porcao_g, **macros):
    try:
        payload = {"nome": nome, "porcao_g": porcao_g}
        for field in MACRO_FIELDS:
            payload[field] = macros.get(field, 0)
        _sb().table("alimento").update(payload).eq("id", alimento_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao atualizar alimento: {e}")
        return False


def deletar_alimento(alimento_id):
    try:
        _sb().table("alimento").delete().eq("id", alimento_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar alimento: {e}")
        return False


# ==============================================================================
# REFEIÇÕES
# ==============================================================================

def adicionar_refeicao(nome, data_hora, gramas, **macros):
    """
    data_hora: string ISO ou datetime
    gramas: total de gramas consumidos (para registro direto pode ser 0)
    macros: valores JÁ calculados para a quantidade consumida
    """
    try:
        if isinstance(data_hora, datetime):
            data_hora = data_hora.isoformat()
        payload = {"nome": nome, "data_hora": data_hora, "gramas": gramas}
        for field in MACRO_FIELDS:
            payload[field] = macros.get(field, 0)
        res = _sb().table("refeicao").insert(payload).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"✗ Erro ao adicionar refeição: {e}")
        return None


def listar_refeicoes(data_inicio=None, data_fim=None):
    """Retorna refeições opcionalmente filtradas por intervalo de datas."""
    try:
        q = _sb().table("refeicao").select("*").order("data_hora", desc=True)
        if data_inicio:
            q = q.gte("data_hora", data_inicio)
        if data_fim:
            q = q.lte("data_hora", data_fim)
        return q.execute().data
    except Exception as e:
        print(f"✗ Erro ao listar refeições: {e}")
        return []


def deletar_refeicao(refeicao_id):
    try:
        _sb().table("refeicao").delete().eq("id", refeicao_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar refeição: {e}")
        return False


# ==============================================================================
# PESO
# ==============================================================================

def registrar_peso(data, peso_kg):
    """Insere ou atualiza o peso do dia (upsert por data)."""
    try:
        data_str = data.strftime("%Y-%m-%d") if hasattr(data, "strftime") else str(data)
        # Tenta atualizar primeiro
        existing = _sb().table("peso").select("id").eq("data", data_str).execute().data
        if existing:
            _sb().table("peso").update({"peso_kg": peso_kg}).eq("data", data_str).execute()
        else:
            _sb().table("peso").insert({"data": data_str, "peso_kg": peso_kg}).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao registrar peso: {e}")
        return False


def listar_pesos(data_inicio=None, data_fim=None):
    """Retorna lista de (data_str, peso_kg) ordenada por data."""
    try:
        q = _sb().table("peso").select("data, peso_kg").order("data")
        if data_inicio:
            q = q.gte("data", data_inicio)
        if data_fim:
            q = q.lte("data", data_fim)
        rows = q.execute().data
        return [(r["data"], r["peso_kg"]) for r in rows]
    except Exception as e:
        print(f"✗ Erro ao listar pesos: {e}")
        return []


def obter_peso_por_data(data_str):
    try:
        res = _sb().table("peso").select("peso_kg").eq("data", data_str).limit(1).execute().data
        return res[0]["peso_kg"] if res else None
    except Exception as e:
        print(f"✗ Erro ao obter peso: {e}")
        return None


# ==============================================================================
# ESTATÍSTICAS DE DIETA
# ==============================================================================

def _semana_label(data_str):
    d = datetime.strptime(data_str[:10], "%Y-%m-%d").date()
    d1 = d + timedelta(days=1)
    return d1.strftime("%Y-W%W")


def obter_media_macros_ultimas_semanas(n_semanas=3):
    """
    Retorna dict {macro: media_diaria} calculado sobre as últimas n_semanas.
    A média é por dia (volume total / número de dias com registro).
    """
    try:
        rows = _sb().table("refeicao").select(
            "data_hora, " + ", ".join(MACRO_FIELDS)
        ).execute().data

        if not rows:
            return {}

        # Agrupa por dia
        dias = {}
        for r in rows:
            d = r["data_hora"][:10]
            if d not in dias:
                dias[d] = {f: 0.0 for f in MACRO_FIELDS}
            for f in MACRO_FIELDS:
                dias[d][f] += r[f] or 0

        # Pega as últimas n_semanas de semanas únicas
        semanas = sorted(set(_semana_label(d) for d in dias), reverse=True)[:n_semanas]
        dias_na_janela = [d for d in dias if _semana_label(d) in semanas]

        if not dias_na_janela:
            return {}

        totais = {f: 0.0 for f in MACRO_FIELDS}
        for d in dias_na_janela:
            for f in MACRO_FIELDS:
                totais[f] += dias[d][f]

        n = len(dias_na_janela)
        return {f: round(totais[f] / n, 1) for f in MACRO_FIELDS}
    except Exception as e:
        print(f"✗ Erro ao obter médias de macros: {e}")
        return {}


def obter_macros_por_dia(macro, data_inicio=None, data_fim=None):
    """
    Retorna lista de (data_str, valor) agrupado por dia para um macro específico.
    """
    try:
        q = _sb().table("refeicao").select(f"data_hora, {macro}")
        if data_inicio:
            q = q.gte("data_hora", data_inicio)
        if data_fim:
            q = q.lte("data_hora", data_fim)
        rows = q.execute().data

        agg = {}
        for r in rows:
            d = r["data_hora"][:10]
            agg[d] = agg.get(d, 0) + (r[macro] or 0)

        return sorted(agg.items())
    except Exception as e:
        print(f"✗ Erro ao obter macros por dia: {e}")
        return []