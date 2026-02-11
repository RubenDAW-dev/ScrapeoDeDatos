# -*- coding: utf-8 -*-
"""
Scraper incremental de estadísticas de JUGADORES (FBref - LaLiga)
VERSION FINAL - Maneja MultiIndex headers correctamente
"""

import os
import time
import re
from io import StringIO
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================
# CONFIG
# ============================
FIXTURES_URL = "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
RAW_FILE = "jugadores_raw.csv"

WAIT_FIXTURES_SEC = 25
WAIT_PARTIDO_SEC = 20
RETRIES_POR_PARTIDO = 3
SLEEP_ENTRE_REINTENTOS = 0.8
SLEEP_ENTRE_PARTIDOS = 0.4

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================

def _flatten_columns(df):
    """Aplana columnas MultiIndex de forma robusta."""
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for col_tuple in df.columns:
            parts = [str(x) for x in col_tuple if not (pd.isna(x) or 'Unnamed' in str(x))]
            if len(parts) == 0:
                new_cols.append(str(col_tuple[-1]))
            elif len(parts) == 1:
                new_cols.append(parts[0])
            else:
                new_cols.append('_'.join(parts))
        df.columns = new_cols
    else:
        df.columns = [str(c) for c in df.columns]
    return df


def uncomment_fbref_tables(html):
    """FBref comenta las tablas. Esta función las descomenta."""
    pattern = r'<!--(.*?<table.*?</table>.*?)-->'
    def replace_comment(match):
        return match.group(1)
    return re.sub(pattern, replace_comment, html, flags=re.DOTALL)


# ============================
#  EXTRACCIÓN DE TABLAS
# ============================

def read_player_tables(driver):
    """Extrae TODAS las tablas de jugadores."""
    all_tables = []
    stat_divs = driver.find_elements(By.CSS_SELECTOR, "div[id^='div_stats_']")
    
    print(f"   🔍 Encontrados {len(stat_divs)} divs con id div_stats_*")

    for div in stat_divs:
        try:
            div_id = div.get_attribute("id")
            stat_type = div_id.replace("div_stats_", "")
            
            # Saltar tablas que no son de jugadores
            if any(x in stat_type for x in ['keeper_', 'team_']):
                continue

            html = div.get_attribute("outerHTML")
            html_uncommented = uncomment_fbref_tables(html)
            dfs = pd.read_html(StringIO(html_uncommented))
            
            if not dfs:
                continue
                
            df = dfs[0]
            df = _flatten_columns(df)
            
            if "Player" not in df.columns:
                continue

            # Limpiar
            df = df[df["Player"].notna()]
            df = df[df["Player"] != "Player"]
            df = df[~df["Player"].isin(["Starting XI", "Bench", ""])]
            
            if df.empty:
                continue
            
            # Verificar datos reales
            non_null_cols = df.notna().sum(axis=1)
            if non_null_cols.max() <= 1:
                continue

            # Extraer team hash
            match = re.search(r"stats_(.*?)_", stat_type)
            team_hash = match.group(1) if match else None

            df["team"] = team_hash
            df["stat_type"] = stat_type
            
            print(f"   ✅ {stat_type}: {len(df)} jugadores")
            all_tables.append(df)

        except Exception as e:
            print(f"   ⚠️  Error en {div_id}: {e}")
            continue

    if not all_tables:
        return None

    result = pd.concat(all_tables, ignore_index=True)
    print(f"   📦 Total: {len(result)} filas")
    return result


# ============================
# ALINEACIÓN AL ESQUEMA
# ============================

def alinear_a_esquema(df, schema_cols):
    """Alinea columnas al esquema existente."""
    for c in schema_cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df[schema_cols]


def append_al_csv(df, path, schema_cols):
    """Añade el DF al CSV respetando el esquema."""
    exists = os.path.exists(path) and os.path.getsize(path) > 0

    if exists:
        df2 = alinear_a_esquema(df.copy(), schema_cols)
        df2.to_csv(path, mode="a", index=False, header=False, encoding="utf-8")
        return schema_cols
    else:
        df.to_csv(path, mode="w", index=False, header=True, encoding="utf-8")
        return list(df.columns)


# ============================
# 1) CARGAR ESQUEMA Y URLs PROCESADAS
# ============================
processed_urls = set()
schema_cols = None

if os.path.exists(RAW_FILE) and os.path.getsize(RAW_FILE) > 0:
    try:
        # CRÍTICO: Leer con header MultiIndex [0,1] y luego aplanarlo
        print("📂 Leyendo CSV existente...")
        df_existing = pd.read_csv(RAW_FILE, header=[0, 1], nrows=5)
        
        # Aplanar el MultiIndex del header existente
        df_existing = _flatten_columns(df_existing)
        schema_cols = list(df_existing.columns)
        
        print(f"✔ Esquema detectado: {len(schema_cols)} columnas")
        print(f"  Primeras 10: {schema_cols[:10]}")
        
        # Obtener URLs procesadas (leer con MultiIndex y aplanar)
        df_urls = pd.read_csv(RAW_FILE, header=[0, 1])
        df_urls = _flatten_columns(df_urls)
        
        if "match_url" in df_urls.columns:
            processed_urls = set(df_urls["match_url"].dropna().unique().tolist())
            print(f"✔ Partidos ya procesados: {len(processed_urls)}")
        else:
            print("⚠️  No se encontró columna match_url")
            
    except Exception as e:
        print(f"❌ Error leyendo CSV: {e}")
        print("💡 Tip: Si el CSV está corrupto, bórralo y empieza limpio")
        raise
else:
    print("ℹ️  Primera ejecución: creando jugadores_raw.csv nuevo")

# ============================
# 2) Conectar Selenium
# ============================
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# ============================
# 3) Cargar Fixtures
# ============================
driver.get(FIXTURES_URL)

try:
    fixtures_table = WebDriverWait(driver, WAIT_FIXTURES_SEC).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table[id^='sched_']"))
    )
except:
    print("❌ No apareció la tabla de Fixtures.")
    raise

rows = fixtures_table.find_elements(By.CSS_SELECTOR, "tbody tr")
match_urls = []

for r in rows:
    try:
        a = r.find_element(By.CSS_SELECTOR, 'td[data-stat="match_report"] a[href*="/matches/"]')
        match_urls.append(a.get_attribute("href"))
    except:
        pass

match_urls = list(dict.fromkeys(match_urls))
new_matches = [u for u in match_urls if u not in processed_urls]

print(f"➡️  Partidos con Match Report: {len(match_urls)}")
print(f"🆕 Partidos NUEVOS: {len(new_matches)}")
print("------------------------------------------------------------")

# ============================
# 4) SCRAPING PRINCIPAL
# ============================

total_filas = 0

for i, url in enumerate(new_matches, 1):
    print(f"\n({i}/{len(new_matches)}) {url}")

    try:
        driver.get(url)
    except:
        print("   ❌ Error cargando URL")
        continue

    # Esperar contenido
    try:
        WebDriverWait(driver, WAIT_PARTIDO_SEC).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "div[id^='div_stats_'], .scorebox"
            ))
        )
    except:
        pass

    time.sleep(2)  # Espera para JS

    # Reintentos
    df_players = None
    for retry in range(RETRIES_POR_PARTIDO):
        if retry > 0:
            print(f"   🔄 Reintento {retry}/{RETRIES_POR_PARTIDO}")
        df_players = read_player_tables(driver)
        if df_players is not None and not df_players.empty:
            break
        time.sleep(SLEEP_ENTRE_REINTENTOS)

    if df_players is None or df_players.empty:
        print("   ❌ No hay datos")
        continue

    # Añadir match_url
    df_players["match_url"] = url

    # Asegurar columna team
    if "team" not in df_players.columns:
        df_players["team"] = pd.NA

    # Aplanar columnas
    df_players.columns = [str(c) for c in df_players.columns]

    # Reordenar
    cols = [c for c in df_players.columns if c not in ("team", "match_url")]
    cols += ["team", "match_url"]
    df_players = df_players[cols]

    print(f"   📝 {len(df_players)} filas × {len(df_players.columns)} cols")

    # Alinear al esquema si existe
    if schema_cols is not None:
        df_players = alinear_a_esquema(df_players, schema_cols)

    # Append
    schema_cols = append_al_csv(df_players, RAW_FILE, schema_cols)
    total_filas += len(df_players)

    print(f"   ✅ {len(df_players)} jugadores añadidos")

    processed_urls.add(url)
    time.sleep(SLEEP_ENTRE_PARTIDOS)

print(f"\n🎉 Terminado. Total añadido: {total_filas} filas")