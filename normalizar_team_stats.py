# -*- coding: utf-8 -*-
import pandas as pd
import re
import unicodedata

# ========================================
# Helpers
# ========================================

MONTHS = {
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
}

# Palabras de prefijo que FBref mete en algunos slugs ("El Clasico", "El Derbi Madrileno", etc.)
PREFIXES = {"el", "clasico", "clásico", "derbi", "madrileno", "madrileño"}

def strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

def normalize_team(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = strip_accents(s).lower()
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def find_month_index(parts):
    for i, p in enumerate(parts):
        if p in MONTHS:
            return i
    return None

def extract_month_from_url(url: str):
    if not isinstance(url, str):
        return None
    for p in url.split("-"):
        if p in MONTHS:
            return p
    return None

def parse_stat_pair(cell: str):
    """
    Extrae (X, Y) de textos como:
      '2 of 7 — 29%'  -> (2, 7)
      '31% — 5 of 16' -> (5, 16)
    """
    if not isinstance(cell, str):
        return None, None
    m = re.search(r"(\d+)\s*of\s*(\d+)", cell, flags=re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

# ========================================
# 1) Cargar fixtures para lista real de equipos
# ========================================
fixtures = pd.read_csv("laliga_fixtures.csv")
fixtures = fixtures.dropna(subset=["Home", "Away"])

equipos_reales = set(fixtures["Home"].unique()).union(set(fixtures["Away"].unique()))
equipos_norm = {normalize_team(t): t for t in equipos_reales}

# ========================================
# 2) Extractor definitivo de equipos desde URL usando fixtures
# ========================================
def extract_teams(url: str):
    """
    Soporta slugs con prefijos (El-Clasico..., El-Derbi-Madrileno...),
    nombres de 1/2/3 palabras (Real Sociedad, Celta Vigo, Athletic Club, Rayo Vallecano...).
    """
    if not isinstance(url, str):
        return None, None

    slug = url.rsplit("/", 1)[-1]     # .../Girona-Rayo-Vallecano-August-15-2025-La-Liga
    parts = slug.split("-")

    # Encontrar índice del mes → todo lo anterior son las palabras de equipos (con o sin prefijos)
    m_idx = find_month_index(parts)
    team_words = parts[:m_idx] if m_idx is not None else parts[:]

    # Eliminar prefijos basura al inicio
    while team_words and normalize_team(team_words[0]) in PREFIXES:
        team_words.pop(0)

    # Probar todas las particiones posibles
    n = len(team_words)
    for i in range(1, n):
        left = " ".join(team_words[:i])
        right = " ".join(team_words[i:])
        ln = normalize_team(left)
        rn = normalize_team(right)
        if ln in equipos_norm and rn in equipos_norm:
            return equipos_norm[ln], equipos_norm[rn]

    # Intento "codicioso" por si el visitante es de 1 palabra y el local de varias (o viceversa)
    for i in range(n-1, 0, -1):
        left = " ".join(team_words[:i])
        right = " ".join(team_words[i:])
        ln = normalize_team(left)
        rn = normalize_team(right)
        if ln in equipos_norm and rn in equipos_norm:
            return equipos_norm[ln], equipos_norm[rn]

    return None, None

# ========================================
# 3) Procesar team_raw.csv → normalized_fbref.csv
# ========================================

df = pd.read_csv("team_raw.csv", header=None)
df.columns = ["home", "away", "url", "c4", "c5", "c6", "c7"]

partidos = []
current = {}
i = 0
N = len(df)

while i < N:
    row = df.iloc[i]

    # Inicio REAL de partido: línea de posesión válida + equipos detectables desde la URL
    if (
        isinstance(row["home"], str) and row["home"].endswith("%") and
        isinstance(row["away"], str) and row["away"].endswith("%")
    ):
        ht, at = extract_teams(row["url"])
        if ht is None or at is None:
            # Línea fantasma (suele haber una fila vacía con la URL tras 'Cards'): la saltamos
            i += 1
            continue

        # Guardar el partido anterior si lo hubiera
        if current:
            partidos.append(current)

        current = {
            "poss_home": int(row["home"].replace("%", "")),
            "poss_away": int(row["away"].replace("%", "")),
            "home_team": ht,
            "away_team": at,
            "month_txt": extract_month_from_url(row["url"]),
        }

        i += 1
        continue

    # Shots on Target
    if row["home"] == "Shots on Target" and i + 1 < N:
        nxt = df.iloc[i+1]
        h1, h2 = parse_stat_pair(nxt["home"])
        a1, a2 = parse_stat_pair(nxt["away"])
        current["shots_ot_home"] = h1
        current["shots_total_home"] = h2
        current["shots_ot_away"] = a1
        current["shots_total_away"] = a2

    # Saves
    if row["home"] == "Saves" and i + 1 < N:
        nxt = df.iloc[i+1]
        h1, _ = parse_stat_pair(nxt["home"])
        a1, _ = parse_stat_pair(nxt["away"])
        current["saves_home"] = h1
        current["saves_away"] = a1

    # Cards (en tu raw siempre 0/0)
    if row["home"] == "Cards":
        current["cards_home"] = 0
        current["cards_away"] = 0

    i += 1

# Volcar el último
if current:
    partidos.append(current)

out = pd.DataFrame(partidos)
out.to_csv("normalized_fbref.csv", index=False)

print("✔ NORMALIZADO COMPLETO → normalized_fbref.csv")
print(out.head(8))