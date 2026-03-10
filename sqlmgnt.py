"""
sqlmgnt.py — GymTracker
Camada de dados usando Supabase (substitui SQLite).
Interface de funções 100% compatível com o código original.
"""

import json
import os
from datetime import datetime

from supabase import create_client, Client
import streamlit as st

# ── Conexão ────────────────────────────────────────────────────────────────────

@st.cache_resource
def _get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def _sb() -> Client:
    return _get_client()


def create_database():
    """No-op: tabelas são criadas via SQL Editor no Supabase."""
    pass


# ==============================================================================
# HELPERS INTERNOS
# ==============================================================================

def _parse_distribuicao(dist_json, foco):
    try:
        parsed = json.loads(dist_json) if dist_json else {}
    except Exception:
        parsed = {}

    if isinstance(parsed, dict) and parsed:
        return {m: pct / 100.0 for m, pct in parsed.items()}

    if isinstance(parsed, list):
        result = {foco: 1.0}
        for m in parsed:
            result[m] = 0.5
        return result

    return {foco: 1.0}


def _get_distribuicao_todos():
    try:
        rows = _sb().table("exercicio").select("nome, foco, distribuicao").execute().data
        return {r["nome"]: _parse_distribuicao(r["distribuicao"], r["foco"]) for r in rows}
    except Exception:
        return {}


def _volume_historico_por_exercicio():
    """Retorna dict {exercicio: volume_total}."""
    try:
        rows = _sb().table("historico").select("exercicio, peso, reps").execute().data
        vol = {}
        for r in rows:
            ex = r["exercicio"]
            vol[ex] = vol.get(ex, 0) + r["peso"] * r["reps"]
        return vol
    except Exception:
        return {}


def _volume_historico_por_exercicio_data():
    """Retorna lista [(exercicio, data, volume)]."""
    try:
        rows = _sb().table("historico").select("exercicio, data, peso, reps").execute().data
        agg = {}
        for r in rows:
            k = (r["exercicio"], r["data"])
            agg[k] = agg.get(k, 0) + r["peso"] * r["reps"]
        return [(ex, d, v) for (ex, d), v in sorted(agg.items(), key=lambda x: x[0][1])]
    except Exception:
        return []


def _volume_historico_semanal_por_exercicio():
    """Retorna lista [(exercicio, semana_str, volume)]."""
    try:
        rows = _sb().table("historico").select("exercicio, data, peso, reps").execute().data
        from datetime import date
        import re

        def _semana(data_str):
            d = datetime.strptime(data_str, "%Y-%m-%d").date()
            # Mesmo cálculo do SQLite: strftime('%Y-W%W', date(data, '+1 day'))
            from datetime import timedelta
            d1 = d + timedelta(days=1)
            return d1.strftime("%Y-W%W")

        agg = {}
        for r in rows:
            k = (r["exercicio"], _semana(r["data"]))
            agg[k] = agg.get(k, 0) + r["peso"] * r["reps"]
        return [(ex, s, v) for (ex, s), v in sorted(agg.items(), key=lambda x: x[0][1], reverse=True)]
    except Exception:
        return []


# ==============================================================================
# EXERCÍCIOS
# ==============================================================================

def adicionar_exercicio(nome, foco, distribuicao=None):
    try:
        dist = distribuicao if distribuicao else {foco: 100}
        dist_json = json.dumps(dist, ensure_ascii=False)
        res = _sb().table("exercicio").insert({
            "nome": nome, "foco": foco, "distribuicao": dist_json
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"✗ Erro ao adicionar exercício: {e}")
        return None


def listar_exercicios():
    """Retorna (id, nome, foco, distribuicao_pct_dict, data_criacao)"""
    try:
        rows = _sb().table("exercicio").select("*").order("foco").order("nome").execute().data
        result = []
        for r in rows:
            dist = _parse_distribuicao(r["distribuicao"], r["foco"])
            dist_pct = {m: int(round(f * 100)) for m, f in dist.items()}
            result.append((r["id"], r["nome"], r["foco"], dist_pct, r["data_criacao"]))
        return result
    except Exception as e:
        print(f"✗ Erro ao listar exercícios: {e}")
        return []


def atualizar_exercicio(exercicio_id, nome, foco, distribuicao=None):
    try:
        dist = distribuicao if distribuicao else {foco: 100}
        dist_json = json.dumps(dist, ensure_ascii=False)
        _sb().table("exercicio").update({
            "nome": nome, "foco": foco, "distribuicao": dist_json
        }).eq("id", exercicio_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao atualizar exercício: {e}")
        return False


def deletar_exercicio(exercicio_id):
    try:
        _sb().table("exercicio").delete().eq("id", exercicio_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar exercício: {e}")
        return False


# ==============================================================================
# TREINOS
# ==============================================================================

def adicionar_treino(treino, exercicio, foco, series=1):
    try:
        res = _sb().table("treino").insert({
            "treino": treino, "exercicio": exercicio, "foco": foco, "series": series
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"✗ Erro ao adicionar treino: {e}")
        return None


def listar_treinos():
    try:
        rows = _sb().table("treino").select("id, treino, exercicio, foco, series, data_criacao").execute().data
        return [(r["id"], r["treino"], r["exercicio"], r["foco"], r["series"], r["data_criacao"]) for r in rows]
    except Exception as e:
        print(f"✗ Erro ao listar treinos: {e}")
        return []


def listar_treinos_por_nome(nome_treino):
    try:
        rows = _sb().table("treino").select("id, treino, exercicio, foco, series, data_criacao") \
            .eq("treino", nome_treino).execute().data
        return [(r["id"], r["treino"], r["exercicio"], r["foco"], r["series"], r["data_criacao"]) for r in rows]
    except Exception as e:
        print(f"✗ Erro ao listar treinos por nome: {e}")
        return []


def deletar_treino(treino_id):
    try:
        _sb().table("treino").delete().eq("id", treino_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar treino: {e}")
        return False


def deletar_treino_completo(nome_treino):
    try:
        _sb().table("treino").delete().eq("treino", nome_treino).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar treino completo: {e}")
        return False


# ==============================================================================
# HISTÓRICO
# ==============================================================================

def adicionar_historico(data, treino, exercicio, peso, serie, reps, rir):
    try:
        res = _sb().table("historico").insert({
            "data": data, "treino": treino, "exercicio": exercicio,
            "peso": peso, "serie": serie, "reps": reps, "rir": rir
        }).execute()
        return res.data[0]["id"] if res.data else None
    except Exception as e:
        print(f"✗ Erro ao adicionar histórico: {e}")
        return None


def listar_historico():
    try:
        rows = _sb().table("historico").select("id, data, treino, exercicio, peso, serie, reps, rir") \
            .order("data", desc=True).execute().data
        return [(r["id"], r["data"], r["treino"], r["exercicio"], r["peso"], r["serie"], r["reps"], r["rir"]) for r in rows]
    except Exception as e:
        print(f"✗ Erro ao listar histórico: {e}")
        return []


def deletar_historico(historico_id):
    try:
        _sb().table("historico").delete().eq("id", historico_id).execute()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar histórico: {e}")
        return False


# ==============================================================================
# HISTÓRICO POR SÉRIE
# ==============================================================================

def obter_ultimo_historico(exercicio, numero_serie):
    try:
        # Última data com registro desse exercício
        row = _sb().table("historico").select("data") \
            .eq("exercicio", exercicio).order("data_criacao", desc=True).limit(1).execute().data
        if not row:
            return None
        ultima_data = row[0]["data"]

        res = _sb().table("historico").select("peso, serie, reps, rir, data") \
            .eq("exercicio", exercicio).eq("data", ultima_data).eq("serie", numero_serie) \
            .order("data_criacao", desc=True).limit(1).execute().data
        if res:
            r = res[0]
            return {"peso": r["peso"], "serie": r["serie"], "reps": r["reps"], "rir": r["rir"], "data": r["data"]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter último histórico: {e}")
        return None


def obter_melhor_volume_treino(treino_nome, exercicio, numero_serie):
    try:
        rows = _sb().table("historico").select("data, peso, reps") \
            .eq("treino", treino_nome).execute().data
        if not rows:
            return None

        vol_por_data = {}
        for r in rows:
            d = r["data"]
            vol_por_data[d] = vol_por_data.get(d, 0) + r["peso"] * r["reps"]

        melhor_data = max(vol_por_data, key=vol_por_data.get)
        volume_total = vol_por_data[melhor_data]

        res = _sb().table("historico").select("peso, serie, reps, rir, data") \
            .eq("treino", treino_nome).eq("data", melhor_data) \
            .eq("exercicio", exercicio).eq("serie", numero_serie) \
            .order("data_criacao", desc=True).limit(1).execute().data
        if res:
            r = res[0]
            return {"peso": r["peso"], "serie": r["serie"], "reps": r["reps"], "rir": r["rir"], "data": r["data"], "volume_total": volume_total}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter melhor volume de treino: {e}")
        return None


def obter_melhor_volume_exercicio(exercicio, numero_serie):
    try:
        rows = _sb().table("historico").select("data, peso, reps") \
            .eq("exercicio", exercicio).execute().data
        if not rows:
            return None

        vol_por_data = {}
        for r in rows:
            d = r["data"]
            vol_por_data[d] = vol_por_data.get(d, 0) + r["peso"] * r["reps"]

        melhor_data = max(vol_por_data, key=vol_por_data.get)
        volume = vol_por_data[melhor_data]

        res = _sb().table("historico").select("peso, serie, reps, rir, data") \
            .eq("exercicio", exercicio).eq("data", melhor_data).eq("serie", numero_serie) \
            .order("data_criacao", desc=True).limit(1).execute().data
        if res:
            r = res[0]
            return {"peso": r["peso"], "serie": r["serie"], "reps": r["reps"], "rir": r["rir"], "data": r["data"], "volume": volume}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter melhor volume do exercício: {e}")
        return None


def obter_melhor_volume_serie(exercicio, numero_serie):
    try:
        rows = _sb().table("historico").select("peso, serie, reps, rir, data") \
            .eq("exercicio", exercicio).eq("serie", numero_serie).execute().data
        if not rows:
            return None
        best = max(rows, key=lambda r: r["peso"] * r["reps"])
        return {"peso": best["peso"], "serie": best["serie"], "reps": best["reps"],
                "rir": best["rir"], "data": best["data"], "volume": best["peso"] * best["reps"]}
    except Exception as e:
        print(f"✗ Erro ao obter melhor volume da série: {e}")
        return None


def obter_pr_serie(exercicio, numero_serie):
    try:
        res = _sb().table("historico").select("peso, serie, reps, rir, data") \
            .eq("exercicio", exercicio).eq("serie", numero_serie) \
            .order("peso", desc=True).limit(1).execute().data
        if res:
            r = res[0]
            return {"peso": r["peso"], "serie": r["serie"], "reps": r["reps"], "rir": r["rir"], "data": r["data"]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter PR da série: {e}")
        return None


def obter_media_ultimos_3_treinos_serie(exercicio, numero_serie):
    try:
        res = _sb().table("historico").select("peso, reps, rir") \
            .eq("exercicio", exercicio).eq("serie", numero_serie) \
            .order("data_criacao", desc=True).limit(3).execute().data
        if not res:
            return None
        return {
            "peso": round(sum(r["peso"] for r in res) / len(res), 1),
            "reps": round(sum(r["reps"] for r in res) / len(res)),
            "rir":  round(sum(r["rir"]  for r in res) / len(res)),
        }
    except Exception as e:
        print(f"✗ Erro ao obter média dos últimos 3 treinos da série: {e}")
        return None


def obter_pr_exercicio(exercicio):
    try:
        res = _sb().table("historico").select("peso, serie, reps, rir, data") \
            .eq("exercicio", exercicio).order("peso", desc=True).limit(1).execute().data
        if res:
            r = res[0]
            return {"peso": r["peso"], "serie": r["serie"], "reps": r["reps"], "rir": r["rir"], "data": r["data"]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter PR do exercício: {e}")
        return None


# ==============================================================================
# ESTATÍSTICAS
# ==============================================================================

def obter_stats_gerais():
    try:
        rows = _sb().table("historico").select("data, treino, exercicio, peso, reps").execute().data
        sessoes = set((r["data"], r["treino"]) for r in rows)
        exercicios = set(r["exercicio"] for r in rows)
        volume = sum(r["peso"] * r["reps"] for r in rows)
        return {
            "total_sessoes": len(sessoes),
            "volume_total": volume,
            "total_exercicios": len(exercicios),
            "total_series": len(rows),
        }
    except Exception as e:
        print(f"✗ Erro ao obter stats gerais: {e}")
        return {}


def obter_stats_por_treino(treino_nome):
    try:
        rows = _sb().table("historico").select("data, peso, reps") \
            .eq("treino", treino_nome).execute().data
        datas = set(r["data"] for r in rows)
        volume = sum(r["peso"] * r["reps"] for r in rows)
        return {"total_sessoes": len(datas), "total_series": len(rows), "volume_total": volume}
    except Exception as e:
        print(f"✗ Erro stats treino: {e}")
        return {}


def obter_stats_por_musculo(foco):
    try:
        dist_map = _get_distribuicao_todos()
        vol_por_ex = _volume_historico_por_exercicio()

        rows = _sb().table("historico").select("exercicio").execute().data
        series_por_ex = {}
        for r in rows:
            ex = r["exercicio"]
            series_por_ex[ex] = series_por_ex.get(ex, 0) + 1

        volume_total = 0.0
        total_series = 0
        for ex, vol in vol_por_ex.items():
            dist = dist_map.get(ex, {})
            fator = dist.get(foco, 0.0)
            if fator > 0:
                volume_total += vol * fator
                total_series += series_por_ex.get(ex, 0)

        return {"total_series": total_series, "volume_total": volume_total}
    except Exception as e:
        print(f"✗ Erro stats musculo: {e}")
        return {}


def obter_stats_por_exercicio(exercicio):
    try:
        rows = _sb().table("historico").select("peso, reps") \
            .eq("exercicio", exercicio).execute().data
        volume = sum(r["peso"] * r["reps"] for r in rows)
        return {"total_series": len(rows), "volume_total": volume}
    except Exception as e:
        print(f"✗ Erro stats exercicio: {e}")
        return {}


def obter_volume_por_data(treino_nome=None):
    try:
        q = _sb().table("historico").select("data, peso, reps")
        if treino_nome:
            q = q.eq("treino", treino_nome)
        rows = q.order("data").execute().data

        agg = {}
        for r in rows:
            d = r["data"]
            agg[d] = agg.get(d, 0) + r["peso"] * r["reps"]
        return sorted(agg.items())
    except Exception as e:
        print(f"✗ Erro ao obter volume por data: {e}")
        return []


def obter_volume_por_data_musculo(foco):
    try:
        dist_map = _get_distribuicao_todos()
        raw = _volume_historico_por_exercicio_data()

        datas_vol = {}
        for ex, data, vol in raw:
            fator = dist_map.get(ex, {}).get(foco, 0.0)
            if fator > 0:
                datas_vol[data] = datas_vol.get(data, 0) + vol * fator

        return sorted(datas_vol.items())
    except Exception as e:
        print(f"✗ Erro volume musculo: {e}")
        return []


def obter_historico_exercicio(exercicio):
    try:
        rows = _sb().table("historico").select("data, serie, peso, reps, rir") \
            .eq("exercicio", exercicio).order("data").order("serie").execute().data
        return [(r["data"], r["serie"], r["peso"], r["reps"], r["rir"]) for r in rows]
    except Exception as e:
        print(f"✗ Erro ao obter histórico do exercício: {e}")
        return []


def obter_historico_exercicio_completo(exercicio):
    return obter_historico_exercicio(exercicio)


def obter_prs_por_exercicio():
    try:
        rows = _sb().table("historico").select("exercicio, peso, reps").execute().data
        agg = {}
        for r in rows:
            ex = r["exercicio"]
            if ex not in agg:
                agg[ex] = {"peso": r["peso"], "reps": r["reps"]}
            else:
                agg[ex]["peso"] = max(agg[ex]["peso"], r["peso"])
                agg[ex]["reps"] = max(agg[ex]["reps"], r["reps"])
        result = [(ex, v["peso"], v["reps"]) for ex, v in agg.items()]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    except Exception as e:
        print(f"✗ Erro ao obter PRs: {e}")
        return []


def obter_frequencia_por_semana():
    try:
        from datetime import timedelta
        rows = _sb().table("historico").select("data, treino").execute().data

        def _semana(data_str):
            d = datetime.strptime(data_str, "%Y-%m-%d").date()
            return (d + timedelta(days=1)).strftime("%Y-W%W")

        agg = {}
        for r in rows:
            s = _semana(r["data"])
            agg.setdefault(s, set()).add(r["data"] + r["treino"])

        return sorted([(s, len(v)) for s, v in agg.items()])
    except Exception as e:
        print(f"✗ Erro ao obter frequência por semana: {e}")
        return []


def obter_focos_disponiveis():
    try:
        rows = _sb().table("exercicio").select("foco").order("foco").execute().data
        return sorted(set(r["foco"] for r in rows))
    except Exception as e:
        print(f"✗ Erro focos: {e}")
        return []


def obter_volume_semanal(treino_nome=None):
    try:
        from datetime import timedelta
        q = _sb().table("historico").select("data, peso, reps, treino")
        if treino_nome:
            q = q.eq("treino", treino_nome)
        rows = q.order("data").execute().data

        def _semana(data_str):
            d = datetime.strptime(data_str, "%Y-%m-%d").date()
            return (d + timedelta(days=1)).strftime("%Y-W%W")

        agg = {}
        for r in rows:
            s = _semana(r["data"])
            agg[s] = agg.get(s, 0) + r["peso"] * r["reps"]
        return sorted(agg.items())
    except Exception as e:
        print(f"✗ Erro volume semanal: {e}")
        return []


def obter_media_volume_semanal_por_musculo(n_semanas=3):
    try:
        dist_map = _get_distribuicao_todos()
        raw = _volume_historico_semanal_por_exercicio()
        if not raw:
            return []

        semanas = sorted(set(r[1] for r in raw), reverse=True)[:n_semanas]

        vol_foco = {}
        cnt_foco = {}
        for ex, semana, vol in raw:
            if semana not in semanas:
                continue
            for foco, fator in dist_map.get(ex, {}).items():
                if fator > 0:
                    vol_foco[foco] = vol_foco.get(foco, 0) + vol * fator
                    cnt_foco[foco] = cnt_foco.get(foco, 0) + 1

        result = [(f, vol_foco[f] / cnt_foco[f]) for f in vol_foco]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    except Exception as e:
        print(f"✗ Erro média volume por músculo: {e}")
        return []


def obter_media_volume_semanal_por_exercicio_musculo(foco, n_semanas=3):
    try:
        dist_map = _get_distribuicao_todos()
        raw = _volume_historico_semanal_por_exercicio()
        if not raw:
            return []

        semanas = sorted(set(r[1] for r in raw), reverse=True)[:n_semanas]

        vol = {}
        cnt = {}
        for ex, semana, volume in raw:
            if semana not in semanas:
                continue
            fator = dist_map.get(ex, {}).get(foco, 0.0)
            if fator > 0:
                vol[ex] = vol.get(ex, 0) + volume * fator
                cnt[ex] = cnt.get(ex, 0) + 1

        result = [(ex, vol[ex] / cnt[ex]) for ex in vol]
        result.sort(key=lambda x: x[1], reverse=True)
        return result
    except Exception as e:
        print(f"✗ Erro média volume por exercício do músculo: {e}")
        return []


def obter_media_volume_semanal_todos_exercicios(n_semanas=3):
    try:
        raw = _volume_historico_semanal_por_exercicio()
        if not raw:
            return []

        semanas = sorted(set(r[1] for r in raw), reverse=True)[:n_semanas]

        vol = {}
        cnt = {}
        for ex, semana, volume in raw:
            if semana in semanas:
                vol[ex] = vol.get(ex, 0) + volume
                cnt[ex] = cnt.get(ex, 0) + 1

        result = [(ex, vol[ex] / cnt[ex]) for ex in vol]
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:15]
    except Exception as e:
        print(f"✗ Erro média volume todos exercícios: {e}")
        return []


def obter_dias_frequentados():
    try:
        rows = _sb().table("historico").select("data, treino").execute().data
        agg = {}
        for r in rows:
            d = r["data"]
            agg.setdefault(d, set()).add(r["treino"])
        return {d: len(treinos) for d, treinos in agg.items()}
    except Exception as e:
        print(f"✗ Erro ao obter dias frequentados: {e}")
        return {}