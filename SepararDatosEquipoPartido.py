# -*- coding: utf-8 -*-
"""
Normaliza estadísticas de equipo por partido:
Entrada: TEAM_STATS_FINAL.csv
Salida: TEAM_MATCH_STATS_FINAL.csv (sin campo ID, BD lo generará)
"""

import pandas as pd
from pathlib import Path
import math

INPUT_FILE = "TEAM_STATS_FINAL.csv"
OUTFILE = "TEAM_MATCH_STATS_FINAL.csv"

def is_na(v):
    try:
        return v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v)
    except:
        return False

def safe_text(v):
    if is_na(v):
        return ""
    return str(v).strip()

def clean_match_id(raw):
    s = safe_text(raw)
    if "." in s:
        return s.split(".")[0]
    return s

def to_int(x):
    if is_na(x):
        return None
    s = safe_text(x)
    if s == "":
        return None
    try:
        return int(float(s))
    except:
        return None

def build_row(match_id, team_id, side, poss, shots_ot, shots_total, saves, cards):
    return {
        "match_id": clean_match_id(match_id),
        "team_id": safe_text(team_id),
        "side": side,
        "possession": to_int(poss),
        "shots_on_target": to_int(shots_ot),
        "shots_total": to_int(shots_total),
        "saves": to_int(saves),
        "cards": to_int(cards)
    }

def main():
    script_dir = Path(__file__).parent
    in_path = script_dir / INPUT_FILE
    out_path = script_dir / OUTFILE

    if not in_path.exists():
        print(f"❌ No se encontró {INPUT_FILE}.")
        return

    df = pd.read_csv(in_path, dtype=str, encoding="utf-8")

    required = [
        "id","home_team_id","away_team_id",
        "poss_home","poss_away",
        "shots_ot_home","shots_total_home",
        "shots_ot_away","shots_total_away",
        "saves_home","saves_away",
        "cards_home","cards_away"
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"❌ Faltan columnas: {missing}")
        return

    out_rows = []
    dropped_home = 0
    dropped_away = 0

    for _, row in df.iterrows():
        match_id = row["id"]

        home_id = safe_text(row["home_team_id"])
        if home_id:
            out_rows.append(build_row(
                match_id, home_id, "HOME",
                row["poss_home"],
                row["shots_ot_home"],
                row["shots_total_home"],
                row["saves_home"],
                row["cards_home"]
            ))
        else:
            dropped_home += 1

        away_id = safe_text(row["away_team_id"])
        if away_id:
            out_rows.append(build_row(
                match_id, away_id, "AWAY",
                row["poss_away"],
                row["shots_ot_away"],
                row["shots_total_away"],
                row["saves_away"],
                row["cards_away"]
            ))
        else:
            dropped_away += 1

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(out_path, index=False, encoding="utf-8")

    print("✅ Normalización completada.")
    print(f"   Filas entrada: {len(df)}")
    print(f"   Filas generadas: {len(out_df)}")
    print(f"   HOME omitidos: {dropped_home}, AWAY omitidos: {dropped_away}")
    print(f"📦 Archivo generado en: {out_path.resolve()}")

if __name__ == "__main__":
    main()