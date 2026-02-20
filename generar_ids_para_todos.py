# -*- coding: utf-8 -*-
import pandas as pd
import re
import hashlib
import unicodedata
from csv import reader as csv_reader

# =========================
# Helpers
# =========================

def strip_accents(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = strip_accents(s).lower()
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def generar_id(home_norm: str, away_norm: str, date_str: str):
    if not isinstance(date_str, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return None
    base = f"{home_norm}_{away_norm}_{date_str}"
    h = hashlib.md5(base.encode()).hexdigest()
    return int(h[:12], 16)  # 48 bits

MONTHS = {
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
}

EQUIPOS_TEAM_ID = {
    "Athletic Club":    "TEAM-0587F59E",
    "Mallorca":         "TEAM-0E077100",
    "Oviedo":           "TEAM-0FF29040",
    "Levante":          "TEAM-1C981597",
    "Villarreal":       "TEAM-27AC674B",
    "Alavés":           "TEAM-3E37DB98",
    "Girona":           "TEAM-51EA86E0",
    "Barcelona":        "TEAM-550D05AB",
    "Celta Vigo":       "TEAM-720795A0",
    "Getafe":           "TEAM-7273A887",
    "Real Sociedad":    "TEAM-782246EA",
    "Real Betis":       "TEAM-7C631724",
    "Osasuna":          "TEAM-839B22B8",
    "Real Madrid":      "TEAM-93330B41",
    "Rayo Vallecano":   "TEAM-A415D192",
    "Elche":            "TEAM-A4EC0F45",
    "Sevilla":          "TEAM-B2118D2C",
    "Valencia":         "TEAM-BDDFCDFA",
    "Espanyol":         "TEAM-D069E7F8",
    "Atlético Madrid":  "TEAM-F53424F0",
}

# =========================
# 1) Fixtures
# =========================
fixtures = pd.read_csv("laliga_fixtures.csv")

fixtures = fixtures[fixtures["Date"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
fixtures = fixtures.dropna(subset=["Home", "Away"])

fixtures["home_norm"] = fixtures["Home"].apply(normalize_text)
fixtures["away_norm"] = fixtures["Away"].apply(normalize_text)
fixtures["month_txt"] = pd.to_datetime(fixtures["Date"]).dt.strftime("%B")

# =========================
# 2) Stats
# =========================
stats = pd.read_csv("normalized_fbref.csv")

stats = stats.dropna(subset=["home_team", "away_team"])
stats["home_norm"] = stats["home_team"].apply(normalize_text)
stats["away_norm"] = stats["away_team"].apply(normalize_text)

fixtures["month_txt"] = fixtures["month_txt"].astype(str)
stats["month_txt"] = stats["month_txt"].astype(str)

stats_merged = stats.merge(
    fixtures[["home_norm", "away_norm", "month_txt", "Date"]],
    on=["home_norm", "away_norm", "month_txt"],
    how="left",
    validate="m:1"
)

# =========================
# 3) IDs
# =========================
fixtures["id"] = fixtures.apply(
    lambda r: generar_id(r["home_norm"], r["away_norm"], r["Date"]),
    axis=1
)

stats_merged["id"] = stats_merged.apply(
    lambda r: generar_id(r["home_norm"], r["away_norm"], r["Date"]),
    axis=1
)

# =========================
# 4) Jugadores con team_id
# =========================
# Leer con csv_reader para manejar correctamente campos con comas entre comillas
# (ej: "MF,FW" debe tratarse como un solo campo de posición)
jugadores_rows = []
with open("jugadores_laliga_ids.csv", encoding="utf-8-sig", newline="") as f:
    r = csv_reader(f)
    header = next(r)
    for row in r:
        jugadores_rows.append(row)

jug = pd.DataFrame(jugadores_rows, columns=header)

# Añadir team_id mapeando desde la columna Squad
jug["team_id"] = jug["Squad"].map(EQUIPOS_TEAM_ID)

sin_mapear = jug[jug["team_id"].isna()]["Squad"].unique()
if len(sin_mapear):
    print(f"⚠ Squads sin mapear a team_id: {sin_mapear}")

# Reordenar columnas: player_id y team_id al principio para mayor claridad
cols = ["player_id", "team_id"] + [c for c in jug.columns if c not in ("player_id", "team_id")]
jug = jug[cols]

jug.to_csv("jugadores_laliga_ids_FINAL.csv", index=False)
print(f"✔ Generado: jugadores_laliga_ids_FINAL.csv ({len(jug)} jugadores)")

# =========================
# 5) Guardar partidos y stats
# =========================
fixtures_out = fixtures.drop(columns=["home_norm", "away_norm", "month_txt"])
fixtures_out.to_csv("laliga_partidos_with_id.csv", index=False)

cols_stats = [
    "id",
    "home_team", "away_team",
    "poss_home", "poss_away",
    "shots_ot_home", "shots_total_home",
    "shots_ot_away", "shots_total_away",
    "saves_home", "saves_away",
    "cards_home", "cards_away",
]
cols_stats = [c for c in cols_stats if c in stats_merged.columns]

stats_out = stats_merged[cols_stats]
stats_out.to_csv("normalized_estadisticas_equipos_with_id.csv", index=False)

print("✔ Generado: laliga_partidos_with_id.csv")
print("✔ Generado: normalized_estadisticas_equipos_with_id.csv")