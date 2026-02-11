# -*- coding: utf-8 -*-
"""
NORMALIZADOR FINAL DE jugadores_raw.csv
Elimina:
- match_url
- stat_type
- team (XXXXXX_summary)
- columnas *_summary
- columnas vacías
- filas vacías
"""

import pandas as pd

INPUT = "jugadores_raw_with_id.csv"
OUTPUT = "jugadores_estadisticas_normalizado.csv"

print("📂 Leyendo jugadores_raw_with_id.csv ...")
df = pd.read_csv(INPUT, dtype=str)

# Aplanar MultiIndex si lo hubiera
df.columns = [str(c) for c in df.columns]

print(f"✔ Columnas detectadas: {len(df.columns)}")

# -------------------------------
# 1) ELIMINAR URL
# -------------------------------
if "match_url" in df.columns:
    df = df.drop(columns=["match_url"])
    print("🗑 Eliminada columna match_url")

# -------------------------------
# 2) ELIMINAR stat_type
# -------------------------------
if "stat_type" in df.columns:
    df = df.drop(columns=["stat_type"])
    print("🗑 Eliminada columna stat_type")

# -------------------------------
# 3) ELIMINAR columna team (hash)
# -------------------------------
if "team" in df.columns:
    df = df.drop(columns=["team"])
    print("🗑 Eliminada columna team (hash)")

# -------------------------------
# 4) ELIMINAR columnas *_summary
# -------------------------------
summary_cols = [c for c in df.columns if c.endswith("_summary")]
if summary_cols:
    df = df.drop(columns=summary_cols)
    print(f"🗑 Eliminadas columnas resumen: {summary_cols}")

# -------------------------------
# 5) ELIMINAR columnas completamente vacías
# -------------------------------
empty_cols = [c for c in df.columns if df[c].isna().all() or (df[c] == "").all()]
if empty_cols:
    df = df.drop(columns=empty_cols)
    print(f"🗑 Eliminadas columnas vacías: {empty_cols}")

# -------------------------------
# 6) LIMPIEZA DE FILAS
# -------------------------------
df = df.dropna(how="all")
df = df[df.apply(lambda row: row.str.strip().astype(bool).any(), axis=1)]
df = df.reset_index(drop=True)

print(f"📦 Filas finales: {len(df)}")
print(f"📦 Columnas finales: {len(df.columns)}")

# -------------------------------
# 7) GUARDAR
# -------------------------------
df.to_csv(OUTPUT, index=False, encoding="utf-8")
print(f"\n🎉 Archivo normalizado generado: {OUTPUT}")