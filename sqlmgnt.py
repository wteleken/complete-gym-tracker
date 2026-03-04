import sqlite3
from datetime import datetime
import json

DB_FILE = 'gym_database.db'

def create_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercicio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            foco TEXT NOT NULL,
            distribuicao TEXT NOT NULL DEFAULT '{}',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migração: adicionar coluna se não existir
    for col, default in [("distribuicao", "'{}'"), ("musculos_secundarios", "'[]'")]:
        try:
            cursor.execute(f"ALTER TABLE exercicio ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
        except sqlite3.OperationalError:
            pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            treino TEXT NOT NULL,
            exercicio TEXT NOT NULL,
            foco TEXT NOT NULL,
            series INTEGER NOT NULL DEFAULT 1,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        cursor.execute("ALTER TABLE treino ADD COLUMN series INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE NOT NULL,
            treino TEXT NOT NULL,
            exercicio TEXT NOT NULL,
            peso REAL NOT NULL,
            serie INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            rir INTEGER NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")


# ==============================================================================
# HELPERS INTERNOS
# ==============================================================================

def _parse_distribuicao(dist_json, foco):
    """
    Retorna dict {musculo: fator} onde fator = percentual/100.
    Suporta formato novo (dict JSON) e formato legado (lista JSON de secundários).
    """
    try:
        parsed = json.loads(dist_json) if dist_json else {}
    except Exception:
        parsed = {}

    # Formato novo: {"Peito": 60, "Ombros": 20, "Tríceps": 20}
    if isinstance(parsed, dict) and parsed:
        return {m: pct / 100.0 for m, pct in parsed.items()}

    # Formato legado: lista de secundários → primário 100%, secundários 50%
    if isinstance(parsed, list):
        result = {foco: 1.0}
        for m in parsed:
            result[m] = 0.5
        return result

    # Sem distribuição: 100% no primário
    return {foco: 1.0}

def _get_distribuicao_todos():
    """Retorna dict {nome_exercicio: {musculo: fator}} para todos os exercícios."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nome, foco, distribuicao FROM exercicio")
        rows = cursor.fetchall()
        conn.close()
        return {nome: _parse_distribuicao(dist, foco) for nome, foco, dist in rows}
    except Exception:
        return {}


# ==============================================================================
# EXERCÍCIOS
# ==============================================================================

def adicionar_exercicio(nome, foco, distribuicao=None):
    """
    distribuicao: dict {musculo: percentual} ex: {"Peito": 60, "Tríceps": 20, "Ombros": 20}
    Se None, assume 100% no foco primário.
    """
    try:
        dist = distribuicao if distribuicao else {foco: 100}
        dist_json = json.dumps(dist, ensure_ascii=False)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO exercicio (nome, foco, distribuicao) VALUES (?, ?, ?)',
            (nome, foco, dist_json)
        )
        conn.commit()
        eid = cursor.lastrowid
        conn.close()
        return eid
    except sqlite3.IntegrityError:
        print(f"✗ Exercício '{nome}' já existe")
        return None
    except Exception as e:
        print(f"✗ Erro ao adicionar exercício: {e}")
        return None

def listar_exercicios():
    """Retorna (id, nome, foco, distribuicao_dict, data_criacao)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome, foco, distribuicao, data_criacao FROM exercicio ORDER BY foco, nome')
        rows = cursor.fetchall()
        conn.close()
        result = []
        for (eid, nome, foco, dist_json, dc) in rows:
            dist = _parse_distribuicao(dist_json, foco)
            # Converte fatores de volta para percentuais inteiros para exibição
            dist_pct = {m: int(round(f * 100)) for m, f in dist.items()}
            result.append((eid, nome, foco, dist_pct, dc))
        return result
    except Exception as e:
        print(f"✗ Erro ao listar exercícios: {e}")
        return []

def atualizar_exercicio(exercicio_id, nome, foco, distribuicao=None):
    try:
        dist = distribuicao if distribuicao else {foco: 100}
        dist_json = json.dumps(dist, ensure_ascii=False)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE exercicio SET nome=?, foco=?, distribuicao=? WHERE id=?',
            (nome, foco, dist_json, exercicio_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Erro ao atualizar exercício: {e}")
        return False

def deletar_exercicio(exercicio_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercicio WHERE id = ?', (exercicio_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar exercício: {e}")
        return False


# ==============================================================================
# TREINOS
# ==============================================================================

def adicionar_treino(treino, exercicio, foco, series=1):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO treino (treino, exercicio, foco, series) VALUES (?, ?, ?, ?)',
            (treino, exercicio, foco, series)
        )
        conn.commit()
        tid = cursor.lastrowid
        conn.close()
        return tid
    except Exception as e:
        print(f"✗ Erro ao adicionar treino: {e}")
        return None

def listar_treinos():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, treino, exercicio, foco, series, data_criacao FROM treino')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao listar treinos: {e}")
        return []

def listar_treinos_por_nome(nome_treino):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, treino, exercicio, foco, series, data_criacao FROM treino WHERE treino = ?',
            (nome_treino,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao listar treinos por nome: {e}")
        return []

def deletar_treino(treino_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM treino WHERE id = ?', (treino_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar treino: {e}")
        return False

def deletar_treino_completo(nome_treino):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM treino WHERE treino = ?', (nome_treino,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar treino completo: {e}")
        return False


# ==============================================================================
# HISTÓRICO
# ==============================================================================

def adicionar_historico(data, treino, exercicio, peso, serie, reps, rir):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO historico (data, treino, exercicio, peso, serie, reps, rir) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (data, treino, exercicio, peso, serie, reps, rir)
        )
        conn.commit()
        hid = cursor.lastrowid
        conn.close()
        return hid
    except Exception as e:
        print(f"✗ Erro ao adicionar histórico: {e}")
        return None

def listar_historico():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, data, treino, exercicio, peso, serie, reps, rir FROM historico ORDER BY data DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao listar histórico: {e}")
        return []

def deletar_historico(historico_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM historico WHERE id = ?', (historico_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Erro ao deletar histórico: {e}")
        return False


# ==============================================================================
# FUNÇÕES DE HISTÓRICO POR SÉRIE
# ==============================================================================

def obter_ultimo_historico(exercicio, numero_serie):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM historico WHERE exercicio = ? ORDER BY data_criacao DESC LIMIT 1', (exercicio,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        ultima_data = row[0]
        cursor.execute('''
            SELECT peso, serie, reps, rir, data FROM historico
            WHERE exercicio = ? AND data = ? AND serie = ?
            ORDER BY data_criacao DESC LIMIT 1
        ''', (exercicio, ultima_data, numero_serie))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {'peso': resultado[0], 'serie': resultado[1], 'reps': resultado[2], 'rir': resultado[3], 'data': resultado[4]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter último histórico: {e}")
        return None

def obter_melhor_volume_treino(treino_nome, exercicio, numero_serie):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT data, SUM(peso * reps) FROM historico
            WHERE treino = ? GROUP BY data ORDER BY SUM(peso * reps) DESC LIMIT 1
        ''', (treino_nome,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        melhor_data, volume_total = row
        cursor.execute('''
            SELECT peso, serie, reps, rir, data FROM historico
            WHERE treino = ? AND data = ? AND exercicio = ? AND serie = ?
            ORDER BY data_criacao DESC LIMIT 1
        ''', (treino_nome, melhor_data, exercicio, numero_serie))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {'peso': resultado[0], 'serie': resultado[1], 'reps': resultado[2], 'rir': resultado[3], 'data': resultado[4], 'volume_total': volume_total}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter melhor volume de treino: {e}")
        return None

def obter_melhor_volume_exercicio(exercicio, numero_serie):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT data, SUM(peso * reps) FROM historico
            WHERE exercicio = ? GROUP BY data ORDER BY SUM(peso * reps) DESC LIMIT 1
        ''', (exercicio,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        melhor_data, volume = row
        cursor.execute('''
            SELECT peso, serie, reps, rir, data FROM historico
            WHERE exercicio = ? AND data = ? AND serie = ?
            ORDER BY data_criacao DESC LIMIT 1
        ''', (exercicio, melhor_data, numero_serie))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {'peso': resultado[0], 'serie': resultado[1], 'reps': resultado[2], 'rir': resultado[3], 'data': resultado[4], 'volume': volume}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter melhor volume do exercício: {e}")
        return None

def obter_melhor_volume_serie(exercicio, numero_serie):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT peso, serie, reps, rir, data, (peso * reps) FROM historico
            WHERE exercicio = ? AND serie = ? ORDER BY (peso * reps) DESC LIMIT 1
        ''', (exercicio, numero_serie))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {'peso': resultado[0], 'serie': resultado[1], 'reps': resultado[2], 'rir': resultado[3], 'data': resultado[4], 'volume': resultado[5]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter melhor volume da série: {e}")
        return None

def obter_pr_serie(exercicio, numero_serie):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT peso, serie, reps, rir, data FROM historico
            WHERE exercicio = ? AND serie = ? ORDER BY peso DESC LIMIT 1
        ''', (exercicio, numero_serie))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {'peso': resultado[0], 'serie': resultado[1], 'reps': resultado[2], 'rir': resultado[3], 'data': resultado[4]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter PR da série: {e}")
        return None

def obter_media_ultimos_3_treinos_serie(exercicio, numero_serie):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT peso, reps, rir FROM historico
            WHERE exercicio = ? AND serie = ? ORDER BY data_criacao DESC LIMIT 3
        ''', (exercicio, numero_serie))
        resultados = cursor.fetchall()
        conn.close()
        if not resultados:
            return None
        return {
            'peso': round(sum(r[0] for r in resultados) / len(resultados), 1),
            'reps': round(sum(r[1] for r in resultados) / len(resultados)),
            'rir':  round(sum(r[2] for r in resultados) / len(resultados))
        }
    except Exception as e:
        print(f"✗ Erro ao obter média dos últimos 3 treinos da série: {e}")
        return None

def obter_pr_exercicio(exercicio):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT peso, serie, reps, rir, data FROM historico WHERE exercicio = ? ORDER BY peso DESC LIMIT 1', (exercicio,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return {'peso': resultado[0], 'serie': resultado[1], 'reps': resultado[2], 'rir': resultado[3], 'data': resultado[4]}
        return None
    except Exception as e:
        print(f"✗ Erro ao obter PR do exercício: {e}")
        return None


# ==============================================================================
# ESTATÍSTICAS — usam distribuição percentual real
# ==============================================================================

def _volume_historico_por_exercicio():
    """Retorna dict {exercicio: volume_total} de todo o histórico."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT exercicio, SUM(peso * reps) FROM historico GROUP BY exercicio")
        rows = cursor.fetchall()
        conn.close()
        return {ex: (vol or 0) for ex, vol in rows}
    except Exception:
        return {}

def _volume_historico_por_exercicio_data():
    """Retorna lista [(exercicio, data, volume)] de todo o histórico."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT exercicio, data, SUM(peso * reps) FROM historico GROUP BY exercicio, data ORDER BY data ASC")
        rows = cursor.fetchall()
        conn.close()
        return [(ex, d, vol or 0) for ex, d, vol in rows]
    except Exception:
        return []

def _volume_historico_semanal_por_exercicio():
    """Retorna lista [(exercicio, semana, volume)]."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT exercicio,
                   strftime('%Y-W%W', date(data, '+1 day')) as semana,
                   SUM(peso * reps)
            FROM historico
            GROUP BY exercicio, semana
            ORDER BY semana DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [(ex, s, vol or 0) for ex, s, vol in rows]
    except Exception:
        return []

def obter_stats_gerais():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT data || treino) FROM historico")
        total_sessoes = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(peso * reps) FROM historico")
        volume_total = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(DISTINCT exercicio) FROM historico")
        total_exercicios = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM historico")
        total_series = cursor.fetchone()[0] or 0
        conn.close()
        return {'total_sessoes': total_sessoes, 'volume_total': volume_total,
                'total_exercicios': total_exercicios, 'total_series': total_series}
    except Exception as e:
        print(f"✗ Erro ao obter stats gerais: {e}")
        return {}

def obter_stats_por_treino(treino_nome):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT data), COUNT(*), SUM(peso * reps)
            FROM historico WHERE treino = ?
        """, (treino_nome,))
        row = cursor.fetchone()
        conn.close()
        return {"total_sessoes": row[0] or 0, "total_series": row[1] or 0, "volume_total": row[2] or 0}
    except Exception as e:
        print(f"✗ Erro stats treino: {e}")
        return {}

def obter_stats_por_musculo(foco):
    """Volume e séries atribuídos a um músculo, usando distribuição percentual real."""
    try:
        dist_map = _get_distribuicao_todos()
        vol_por_ex = _volume_historico_por_exercicio()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT exercicio, COUNT(*) FROM historico GROUP BY exercicio")
        series_por_ex = dict(cursor.fetchall())
        conn.close()

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
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(peso * reps) FROM historico WHERE exercicio = ?", (exercicio,))
        row = cursor.fetchone()
        conn.close()
        return {"total_series": row[0] or 0, "volume_total": row[1] or 0}
    except Exception as e:
        print(f"✗ Erro stats exercicio: {e}")
        return {}

def obter_volume_por_data(treino_nome=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if treino_nome:
            cursor.execute('SELECT data, SUM(peso * reps) FROM historico WHERE treino = ? GROUP BY data ORDER BY data ASC', (treino_nome,))
        else:
            cursor.execute('SELECT data, SUM(peso * reps) FROM historico GROUP BY data ORDER BY data ASC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao obter volume por data: {e}")
        return []

def obter_volume_por_data_musculo(foco):
    """Volume por data para um músculo, usando distribuição percentual real."""
    try:
        dist_map = _get_distribuicao_todos()
        raw = _volume_historico_por_exercicio_data()

        datas_vol = {}
        for ex, data, vol in raw:
            dist = dist_map.get(ex, {})
            fator = dist.get(foco, 0.0)
            if fator > 0:
                datas_vol[data] = datas_vol.get(data, 0) + vol * fator

        return sorted(datas_vol.items())
    except Exception as e:
        print(f"✗ Erro volume musculo: {e}")
        return []

def obter_historico_exercicio(exercicio):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT data, serie, peso, reps, rir FROM historico WHERE exercicio = ? ORDER BY data ASC, serie ASC', (exercicio,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao obter histórico do exercício: {e}")
        return []

def obter_historico_exercicio_completo(exercicio):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT data, serie, peso, reps, rir FROM historico WHERE exercicio = ? ORDER BY data ASC, serie ASC', (exercicio,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro histórico exercicio completo: {e}")
        return []

def obter_prs_por_exercicio():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT exercicio, MAX(peso), MAX(reps) FROM historico GROUP BY exercicio ORDER BY MAX(peso) DESC')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao obter PRs: {e}")
        return []

def obter_frequencia_por_semana():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-W%W', data) as semana, COUNT(DISTINCT data || treino)
            FROM historico GROUP BY semana ORDER BY semana ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro ao obter frequência por semana: {e}")
        return []

def obter_focos_disponiveis():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT foco FROM exercicio ORDER BY foco")
        rows = [r[0] for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro focos: {e}")
        return []

def obter_volume_semanal(treino_nome=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if treino_nome:
            cursor.execute("""
                SELECT strftime('%Y-W%W', date(data, '+1 day')) as semana, SUM(peso * reps)
                FROM historico WHERE treino = ? GROUP BY semana ORDER BY semana ASC
            """, (treino_nome,))
        else:
            cursor.execute("""
                SELECT strftime('%Y-W%W', date(data, '+1 day')) as semana, SUM(peso * reps)
                FROM historico GROUP BY semana ORDER BY semana ASC
            """)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"✗ Erro volume semanal: {e}")
        return []

def obter_media_volume_semanal_por_musculo(n_semanas=3):
    """Média de volume semanal por músculo usando distribuição percentual real."""
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
            dist = dist_map.get(ex, {})
            for foco, fator in dist.items():
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
    """Média de volume semanal dos exercícios que contribuem para um músculo."""
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
            dist = dist_map.get(ex, {})
            fator = dist.get(foco, 0.0)
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


if __name__ == "__main__":
    create_database()

def obter_dias_frequentados():
    """Retorna dict {data_str: n_sessoes} de todos os dias com treino registrado."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data, COUNT(DISTINCT treino) as sessoes
            FROM historico GROUP BY data
        """)
        rows = cursor.fetchall()
        conn.close()
        return {data: sessoes for data, sessoes in rows}
    except Exception as e:
        print(f"✗ Erro ao obter dias frequentados: {e}")
        return {}