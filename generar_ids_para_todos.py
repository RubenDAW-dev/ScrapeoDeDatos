# -*- coding: utf-8 -*-
import pandas as pd
import re
import hashlib
import unicodedata
from datetime import datetime
import os

# =========================
# Helpers de normalización
# =========================

def normalize_text(s: str) -> str:
    """Minúsculas, sin tildes, sin puntuación, espacios colapsados."""
    if not isinstance(s, str):
        return ""
    s = s.strip()
    # quitar tildes
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    # quitar signos (dejamos letras/números/espacios/guion bajo/guion)
    s = re.sub(r"[^\w\s-]", " ", s)
    # guiones a espacios y colapsar
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def generar_id(home_norm: str, away_norm: str, date_str: str) -> int | None:
    """ID numérica estable a partir de home+away+date (YYYY-MM-DD)."""
    if not isinstance(date_str, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return None
    base = f"{home_norm}_{away_norm}_{date_str}"
    h = hashlib.md5(base.encode()).hexdigest()
    return int(h[:12], 16)  # 12 hex ~ 48 bits -> int cabal

# Meses en inglés (fixtures vienen con Date->%B)
MONTHS = {"January","February","March","April","May","June",
          "July","August","September","October","November","December"}

# Palabras que "faltan" en home_team (se colaron al principio del away_team en tu stats)
SUFFIX_TO_PULL = {"club","madrid","vigo","sociedad","betis","vallecano"}

def fix_teams_and_month(home_raw: str, away_raw: str):
    """
    Repara equipos en stats cuando 'home' quedó cortado y la 1ª palabra del 'away'
    pertenece realmente al final del 'home' (Athletic [Club], Real [Madrid], etc).
    Además extrae el mes (última palabra con nombre de mes).
    """
    h = (home_raw or "").replace(",", " ").strip()
    a = (away_raw or "").replace(",", " ").strip()

    tokens = a.split()
    month_txt = None

    # Buscar el mes como última palabra que esté en MONTHS
    for idx in range(len(tokens)-1, -1, -1):
        if tokens[idx] in MONTHS:
            month_txt = tokens[idx]
            tokens.pop(idx)  # eliminar el mes del away
            break

    # Si la primera palabra del away está en el conjunto a recuperar -> súmala a home
    if tokens and tokens[0].lower() in SUFFIX_TO_PULL:
        h_fixed = (h + " " + tokens[0]).strip()
        a_fixed = " ".join(tokens[1:]).strip()
    else:
        h_fixed = h
        a_fixed = " ".join(tokens).strip()

    return h_fixed, a_fixed, month_txt

# =========================
# FUNCIONES PARA JUGADORES
# =========================

def parse_fbref_match_url(url: str) -> tuple[str, str, str] | None:
    """
    Parsea URL de FBref y extrae equipos + fecha.
    Returns: (home_team, away_team, date_YYYY-MM-DD) o None
    """
    if not isinstance(url, str):
        return None
    
    match = re.search(r'/matches/[a-f0-9]+/(.+?)-La-Liga', url)
    if not match:
        return None
    
    slug = match.group(1)
    parts = slug.split("-")
    
    if len(parts) < 4:
        return None
    
    year = parts[-1]
    day = parts[-2]
    month_name = parts[-3]
    team_slug = "-".join(parts[:-3])
    team_parts = team_slug.split("-")
    
    home_parts = []
    away_parts = []
    capitals_seen = 0
    found_second = False
    
    for part in team_parts:
        if part and part[0].isupper():
            capitals_seen += 1
            if capitals_seen >= 2:
                found_second = True
        
        if found_second:
            away_parts.append(part)
        else:
            home_parts.append(part)
    
    if not away_parts and len(home_parts) > 1:
        mid = len(home_parts) // 2
        away_parts = home_parts[mid:]
        home_parts = home_parts[:mid]
    
    home_team = " ".join(home_parts)
    away_team = " ".join(away_parts)
    
    try:
        date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
        date_str = date_obj.strftime("%Y-%m-%d")
    except:
        return None
    
    return home_team, away_team, date_str

def _flatten_columns(df):
    """Aplana columnas MultiIndex."""
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

# =========================
# 1) Cargar y limpiar FIXTURES
# =========================

print("=" * 70)
print("GENERACIÓN DE IDs PARA PARTIDOS, ESTADÍSTICAS Y JUGADORES")
print("=" * 70)

print("\n📂 [1/4] Procesando laliga_fixtures.csv...")
fixtures = pd.read_csv("laliga_fixtures.csv")

# Filtrar filas válidas de partido: Date con formato YYYY-MM-DD, Home/Away no nulos
fixtures = fixtures[fixtures["Date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
fixtures = fixtures.dropna(subset=["Home", "Away"])

# Normalizar equipos en fixtures
fixtures["home_norm"] = fixtures["Home"].apply(normalize_text)
fixtures["away_norm"] = fixtures["Away"].apply(normalize_text)

# Mes textual desde la fecha real
fixtures["month_txt"] = pd.to_datetime(fixtures["Date"]).dt.strftime("%B")

print(f"   ✅ {len(fixtures)} partidos procesados")

# =========================
# 2) Cargar y reparar STATS
# =========================

print("\n📂 [2/4] Procesando normalized_fbref.csv...")
stats = pd.read_csv("normalized_fbref.csv")

# Guardamos columnas originales para no romper tu pipeline
orig_cols = list(stats.columns)

# Repara equipos y saca el mes desde away_team
fixed = stats.apply(
    lambda r: pd.Series(fix_teams_and_month(r.get("home_team", ""), r.get("away_team", ""))),
    axis=1
)
fixed.columns = ["home_fixed", "away_fixed", "month_txt"]

stats = pd.concat([stats, fixed], axis=1)

# Normalizados para el emparejamiento
stats["home_norm"] = stats["home_fixed"].apply(normalize_text)
stats["away_norm"] = stats["away_fixed"].apply(normalize_text)

print(f"   ✅ {len(stats)} estadísticas procesadas")

# =========================
# 3) Emparejar stats -> fixtures por home_norm + away_norm + month_txt
#     (obtener la fecha real del partido para stats)
# =========================

join_cols_left  = ["home_norm", "away_norm", "month_txt"]
join_cols_right = ["home_norm", "away_norm", "month_txt", "Date"]

stats_merged = stats.merge(fixtures[join_cols_right], on=["home_norm", "away_norm", "month_txt"], how="left")

# =========================
# 4) Generar la MISMA ID para fixtures y stats
# =========================

print("\n🔢 [3/4] Generando IDs...")

# ID en fixtures
fixtures["id"] = fixtures.apply(
    lambda r: generar_id(r["home_norm"], r["away_norm"], r["Date"]),
    axis=1
)

# ID en stats (usando la Date encontrada del merge)
stats_merged["id"] = stats_merged.apply(
    lambda r: generar_id(r["home_norm"], r["away_norm"], r["Date"]),
    axis=1
)

# =========================
# 5) Procesar JUGADORES si existe el archivo
# =========================

jugadores_file = "jugadores_raw.csv"
jugadores_processed = False

if os.path.exists(jugadores_file):
    print(f"\n📂 [4/4] Procesando {jugadores_file}...")
    
    try:
        # Leer con MultiIndex header
        jugadores = pd.read_csv(jugadores_file, header=[0, 1])
        jugadores = _flatten_columns(jugadores)
        
        print(f"   ✅ {len(jugadores)} jugadores leídos")
        
        if "match_url" in jugadores.columns:
            # Parsear URLs y generar IDs
            print("   🔍 Parseando URLs y generando IDs...")
            
            parsed_data = []
            for idx, url in enumerate(jugadores["match_url"]):
                result = parse_fbref_match_url(url)
                if result:
                    home, away, date = result
                    home_norm = normalize_text(home)
                    away_norm = normalize_text(away)
                    id_val = generar_id(home_norm, away_norm, date)
                    parsed_data.append(id_val)
                else:
                    parsed_data.append(None)
                
                if (idx + 1) % 1000 == 0:
                    print(f"      Procesadas {idx + 1}/{len(jugadores)} URLs...")
            
            jugadores["id"] = parsed_data
            
            # Stats
            ids_ok = jugadores["id"].notna().sum()
            ids_fail = jugadores["id"].isna().sum()
            
            print(f"   ✅ IDs generadas: {ids_ok}")
            if ids_fail > 0:
                print(f"   ⚠️  IDs fallidas: {ids_fail}")
            
            # Reordenar: id primero
            cols = ["id"] + [c for c in jugadores.columns if c != "id"]
            jugadores = jugadores[cols]
            
            # Guardar
            jugadores.to_csv("jugadores_raw_with_id.csv", index=False, encoding='utf-8')
            jugadores_processed = True
            print(f"   💾 Guardado: jugadores_raw_with_id.csv")
        else:
            print(f"   ⚠️  No se encontró columna 'match_url' en {jugadores_file}")
    
    except Exception as e:
        print(f"   ❌ Error procesando jugadores: {e}")
else:
    print(f"\n⏭️  [4/4] No se encontró {jugadores_file}, saltando...")

# =========================
# 6) Guardar CSVs de salida (mismo formato + columna id)
# =========================

print("\n💾 Guardando archivos finales...")

# Para fixtures -> dejamos todas las columnas originales + id
fixtures_out = fixtures.drop(columns=["home_norm", "away_norm", "month_txt"])
fixtures_out.to_csv("laliga_partidos_with_id.csv", index=False)
print("   ✅ laliga_partidos_with_id.csv")

# Para stats -> mantenemos tus columnas + añadimos:
# id, home_fixed, away_fixed, Date (útil por si quieres auditar joins)
stats_out = stats_merged.copy()
# Reordenar: id primero
cols_stats_out = ["id"] + [c for c in stats_out.columns if c != "id"]
stats_out = stats_out[cols_stats_out]

stats_out.to_csv("normalized_estadisticas_equipos_with_id.csv", index=False)
print("   ✅ normalized_estadisticas_equipos_with_id.csv")

if jugadores_processed:
    print("   ✅ jugadores_raw_with_id.csv")

# =========================
# 7) Diagnóstico rápido en consola
# =========================

print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)

no_fecha = stats_out["Date"].isna().sum()
print(f"📊 Partidos con ID: {len(fixtures_out)}")
print(f"📊 Estadísticas con ID: {len(stats_out)}")
if jugadores_processed:
    print(f"📊 Jugadores con ID: {ids_ok} / {len(jugadores)} ({ids_ok/len(jugadores)*100:.1f}%)")

if no_fecha:
    print(f"\n⚠️  Filas de stats sin fecha: {no_fecha}")
    print("   Sugerencia: ampliar SUFFIX_TO_PULL o revisar nombres en esos casos.")

print("\n✅ Proceso completado")