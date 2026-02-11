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
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", " ", s)        # deja letras/numeros/_/espacio/-
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def generar_id(home_norm: str, away_norm: str, date_str: str) -> int | None:
    """ID numérica estable a partir de home+away+date (YYYY-MM-DD)."""
    if not isinstance(date_str, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return None
    base = f"{home_norm}_{away_norm}_{date_str}"
    h = hashlib.md5(base.encode()).hexdigest()
    return int(h[:12], 16)  # 12 hex ~ 48 bits -> entero estable

# Meses en inglés (fixtures vienen con Date->%B)
MONTHS = {"January","February","March","April","May","June",
          "July","August","September","October","November","December"}

# >>> Mapeo explícito de sufijos que pertenecen al LOCAL según su "raíz"
SUFFIX_BY_HOME_ROOT = {
    "athletic": {"club"},
    "real": {"madrid", "sociedad", "betis", "oviedo"},
    "celta": {"vigo"},
    "rayo": {"vallecano"},
    "atletico": {"madrid"},
    "atletico madrid": {"madrid"},  # por seguridad
    "atlético": {"madrid"},         # si viniera con tilde
}

def _clean_tokens(s: str) -> list[str]:
    """Limpia comas/espacios y devuelve tokens."""
    s = (s or "").replace(",", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s.split() if s else []

def fix_teams_and_month(home_raw: str, away_raw: str):
    """
    Repara equipos cuando el sufijo del local quedó al inicio del visitante.
    También quita el mes (si aparece al final del visitante).
    Devuelve: (home_fixed, away_fixed, month_txt)
    """
    # Limpieza inicial
    h_tokens = _clean_tokens(home_raw)
    a_tokens = _clean_tokens(away_raw)

    # Quitar mes (si el último token es un mes, o por si acaso repetido)
    month_txt = None
    while a_tokens and a_tokens[-1] in MONTHS:
        month_txt = a_tokens.pop()
        # si hubiese doble mes por cualquier motivo, seguimos sacándolo

    # Si no hay tokens, devolvemos tal cual
    if not h_tokens:
        return (home_raw or "").strip().replace(",", " "), " ".join(a_tokens).strip(), month_txt

    # Identificar raíz del local (primer token significativo)
    home_root = normalize_text(h_tokens[0])

    # >>> Normalizar la llave para buscar en el mapeo
    # Casos como "Atletico," y similares ya están limpios por _clean_tokens
    # pero igual hacemos robusto el acceso:
    key_candidates = {home_root}
    if len(h_tokens) >= 2:
        key_candidates.add(normalize_text(h_tokens[0] + " " + h_tokens[1]))

    # ¿Hay sufijos esperados para esta raíz?
    expected_suffixes = set()
    for k in key_candidates:
        if k in SUFFIX_BY_HOME_ROOT:
            expected_suffixes |= SUFFIX_BY_HOME_ROOT[k]

    # Si hay sufijos esperados y el primer token del visitante coincide, lo movemos al local
    if a_tokens and expected_suffixes:
        first_away_norm = normalize_text(a_tokens[0])
        if first_away_norm in expected_suffixes:
            # Mover el sufijo al final del nombre del local
            h_tokens.append(a_tokens.pop(0))

    # Reconstruir
    h_fixed = " ".join(h_tokens).strip()
    a_fixed = " ".join(a_tokens).strip()

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

    home_parts, away_parts = [], []
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

fixtures = fixtures[fixtures["Date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
fixtures = fixtures.dropna(subset=["Home", "Away"])
fixtures["home_norm"] = fixtures["Home"].apply(normalize_text)
fixtures["away_norm"] = fixtures["Away"].apply(normalize_text)
fixtures["month_txt"] = pd.to_datetime(fixtures["Date"]).dt.strftime("%B")

print(f"   ✅ {len(fixtures)} partidos procesados")

# =========================
# 2) Cargar y reparar STATS
# =========================

print("\n📂 [2/4] Procesando normalized_fbref.csv...")
stats = pd.read_csv("normalized_fbref.csv")
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
# 3) Emparejar stats -> fixtures
# =========================

join_cols_right = ["home_norm", "away_norm", "month_txt", "Date"]
stats_merged = stats.merge(fixtures[join_cols_right], on=["home_norm", "away_norm", "month_txt"], how="left")

# =========================
# 4) Generar ID para fixtures y stats
# =========================

print("\n🔢 [3/4] Generando IDs...")

fixtures["id"] = fixtures.apply(
    lambda r: generar_id(r["home_norm"], r["away_norm"], r["Date"]),
    axis=1
)

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
        jugadores = pd.read_csv(jugadores_file, header=[0, 1])
        jugadores = _flatten_columns(jugadores)
        print(f"   ✅ {len(jugadores)} jugadores leídos")
        
        if "match_url" in jugadores.columns:
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
            ids_ok = jugadores["id"].notna().sum()
            ids_fail = jugadores["id"].isna().sum()
            print(f"   ✅ IDs generadas: {ids_ok}")
            if ids_fail > 0:
                print(f"   ⚠️  IDs fallidas: {ids_fail}")
            
            cols = ["id"] + [c for c in jugadores.columns if c != "id"]
            jugadores = jugadores[cols]
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
# 6) Guardar CSVs de salida
# =========================

print("\n💾 Guardando archivos finales...")

# Fixtures: todas las columnas originales + id (sin columnas auxiliares de normalización)
fixtures_out = fixtures.drop(columns=["home_norm", "away_norm", "month_txt"])
fixtures_out.to_csv("laliga_partidos_with_id.csv", index=False)
print("   ✅ laliga_partidos_with_id.csv")

# >>> Stats: SOLO id + columnas originales PERO con equipos corregidos
#     Sobrescribimos las columnas originales home_team/away_team con las corregidas
stats_merged["home_team"] = stats_merged["home_fixed"]
stats_merged["away_team"] = stats_merged["away_fixed"]

original_cols_final = [
    "home_team", "away_team",
    "poss_home", "poss_away",
    "shots_ot_home", "shots_total_home",
    "shots_ot_away", "shots_total_away",
    "saves_home", "saves_away",
    "cards_home", "cards_away",
]

# Si alguna columna no existiera en tu CSV original, filtramos las que sí están
original_cols_final = [c for c in original_cols_final if c in stats_merged.columns]

stats_out = stats_merged[["id"] + original_cols_final]
stats_out.to_csv("normalized_estadisticas_equipos_with_id.csv", index=False, encoding="utf-8-sig")
print("   ✅ normalized_estadisticas_equipos_with_id.csv")

if jugadores_processed:
    print("   ✅ jugadores_raw_with_id.csv")

# =========================
# 7) Diagnóstico rápido
# =========================

print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)

no_fecha = stats_merged["Date"].isna().sum()
print(f"📊 Partidos con ID: {len(fixtures_out)}")
print(f"📊 Estadísticas con ID: {len(stats_out)}")
if jugadores_processed:
    print(f"📊 Jugadores con ID: {ids_ok} / {len(jugadores)} ({ids_ok/len(jugadores)*100:.1f}%)")

if no_fecha:
    print(f"\n⚠️  Filas de stats sin fecha: {no_fecha}")
    print("   Sugerencia: revisa filas tipo titulares ('El Clasico...', 'El Derbi...') y exclúyelas si se cuelan.")

print("\n✅ Proceso completado")