# -*- coding: utf-8 -*-
"""
build_jugadores_with_id.py
==========================
Genera jugadores_raw_with_id.csv a partir de jugadores_raw.csv.

Fixes:
  1. Prefijos especiales de fbref eliminados antes de parsear
     (El Clasico, El Derbi Madrileno, etc.)
  2. Nombres de equipos con guiones resueltos con KNOWN_TEAMS
     (Rayo-Vallecano, Real-Madrid, Athletic-Club, etc.)
  3. Doble cabecera del CSV manejada correctamente.
  4. Eliminacion de filas tipo "16 Players ..."
  5. ID calculado con md5 identico al de generar_ids_para_todos.py
"""

import re
import hashlib
import unicodedata
from csv import reader as csv_reader

import pandas as pd

RAW = "jugadores_raw.csv"
OUT = "jugadores_raw_with_id.csv"

# ── Meses ─────────────────────────────────────────────────────────────────────
MONTHS = {
    "January":"01","February":"02","March":"03","April":"04",
    "May":"05","June":"06","July":"07","August":"08",
    "September":"09","October":"10","November":"11","December":"12",
}
MONTH_PAT = "|".join(MONTHS.keys())

# ── Equipos La Liga tal como aparecen en las URLs de fbref ────────────────────
# Amplia esta lista si hay equipos nuevos (ascensos, copas, etc.)
KNOWN_TEAMS = {
    "Alaves","Athletic-Club","Atletico-Madrid","Barcelona","Celta-Vigo",
    "Elche","Espanyol","Getafe","Girona","Levante","Mallorca","Osasuna",
    "Oviedo","Rayo-Vallecano","Real-Betis","Real-Madrid","Real-Sociedad",
    "Sevilla","Valencia","Villarreal",
}

# ── Prefijos especiales que fbref antepone a partidos destacados ──────────────
# fbref renombra ciertos partidos (El Clasico, El Derbi, etc.) en la URL,
# lo que rompe el parsing del equipo local. Se eliminan antes de parsear.
# Amplia esta lista si aparecen nuevos partidos con prefijo especial.
PREFIJOS_FBREF = [
    "El-Clasico-",
    "El-Derbi-Madrileno-",
    "El-Gran-Derbi-",
    "El-Derbi-",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def norm_team(s: str) -> str:
    if not isinstance(s, str): return ""
    return re.sub(r"\s+", " ", strip_accents(s).lower().replace("-", " ")).strip()


def generar_id(home_norm: str, away_norm: str, date_str: str):
    """
    Identico al algoritmo de generar_ids_para_todos.py:
      int(md5(f'{home_norm}_{away_norm}_{date_str}')[:12], 16)
    """
    if not home_norm or not away_norm or not date_str:
        return None
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date_str)):
        return None
    base = f"{home_norm}_{away_norm}_{date_str}"
    return int(hashlib.md5(base.encode()).hexdigest()[:12], 16)


def parse_from_match_url(url: str):
    """
    Extrae (home_norm, away_norm, date_iso) de una URL de fbref.

    Ejemplos de URL:
      .../matches/12c8079e/Girona-Rayo-Vallecano-August-15-2025-La-Liga
      .../matches/33523b09/El-Derbi-Madrileno-Atletico-Madrid-Real-Madrid-September-27-2025-La-Liga
      .../matches/9c9d1f09/El-Clasico-Real-Madrid-Barcelona-October-26-2025-La-Liga

    Estrategia:
      1. Aislar el segmento entre el hash y el sufijo de competicion.
      2. Eliminar prefijos especiales (El Clasico, El Derbi, etc.).
      3. Detectar Month-Day-Year al final.
      4. Probar todas las particiones del segmento de equipos usando
         KNOWN_TEAMS para resolver nombres con guiones.
    """
    if not isinstance(url, str):
        return None, None, None

    m = re.search(r"/matches/[a-f0-9]+/(.+?)(?:-La-Liga|-Copa|-Champions|$)", url)
    if not m:
        return None, None, None
    segment = m.group(1)

    # Eliminar prefijos especiales de fbref
    for prefijo in PREFIJOS_FBREF:
        if segment.startswith(prefijo):
            segment = segment[len(prefijo):]
            break

    dm = re.search(r"-(" + MONTH_PAT + r")-(\d{1,2})-(\d{4})$", segment)
    if not dm:
        return None, None, None

    date_iso   = f"{dm.group(3)}-{MONTHS[dm.group(1)]}-{int(dm.group(2)):02d}"
    teams_part = segment[:dm.start()]
    parts      = teams_part.split("-")

    # Intento 1: ambos equipos reconocidos -> split exacto
    for i in range(1, len(parts)):
        h = "-".join(parts[:i])
        a = "-".join(parts[i:])
        if h in KNOWN_TEAMS and a in KNOWN_TEAMS:
            return norm_team(h), norm_team(a), date_iso

    # Intento 2: al menos uno reconocido
    for i in range(1, len(parts)):
        h = "-".join(parts[:i])
        a = "-".join(parts[i:])
        if h in KNOWN_TEAMS or a in KNOWN_TEAMS:
            return norm_team(h), norm_team(a), date_iso

    # Fallback generico
    return norm_team(parts[0]), norm_team("-".join(parts[1:])), date_iso


# ── Carga ─────────────────────────────────────────────────────────────────────
print("Cargando jugadores_raw.csv ...")
rows = []
with open(RAW, encoding="utf-8-sig", newline="") as f:
    r = csv_reader(f)
    h0 = next(r)   # fila 0: cabeceras nivel-0 (Performance..., team, match_url)
    h1 = next(r)   # fila 1: Player, #, Nation, Pos, Age, Min, Gls...
    for row in r:
        rows.append(row)

# Fusionar cabeceras: usar h1 donde tenga valor, h0 donde h1 este vacio
combined = [(b.strip() if b.strip() else a.strip()) for a, b in zip(h0, h1)]

df = pd.DataFrame(rows, columns=combined)
df.columns = [c.strip() for c in df.columns]

if "match_url" not in df.columns:
    raise RuntimeError("No se encontro la columna match_url. Revisa el CSV.")

print(f"   Filas cargadas: {len(df)}")

# ── Eliminar filas tipo "16 Players ..." ──────────────────────────────────────
pat_players = re.compile(r"^\s*\d+\s+[Pp]layers", re.IGNORECASE)
player_col  = next((c for c in df.columns if "player" in c.lower()), None)

if player_col:
    antes = len(df)
    df    = df[~df[player_col].astype(str).str.match(pat_players)].reset_index(drop=True)
    print(f"Filas 'N Players' eliminadas: {antes - len(df)} -> {len(df)} filas restantes")
else:
    print("No se encontro columna Player; no se eliminaron filas de resumen.")

# ── Parsear URL y calcular id ─────────────────────────────────────────────────
print("Parseando URLs y calculando IDs ...")
parsed   = [parse_from_match_url(u) for u in df["match_url"]]
df["id"] = [generar_id(h, a, d) for h, a, d in parsed]

# ── Diagnostico ───────────────────────────────────────────────────────────────
total  = len(df)
con_id = df["id"].notna().sum()
sin_id = total - con_id

print(f"\nResultado:")
print(f"  Total filas : {total}")
print(f"  Con id      : {con_id}")
print(f"  Sin id      : {sin_id}")

if sin_id:
    urls_problema = df.loc[df["id"].isna(), "match_url"].dropna().unique()
    print(f"\nURLs sin id ({len(urls_problema)} partidos) -- amplia KNOWN_TEAMS o PREFIJOS_FBREF:")
    for u in urls_problema[:10]:
        print(f"  {u}")
    if len(urls_problema) > 10:
        print(f"  ... y {len(urls_problema) - 10} mas")

# ── Guardar ───────────────────────────────────────────────────────────────────
df.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"\nArchivo generado: {OUT}")