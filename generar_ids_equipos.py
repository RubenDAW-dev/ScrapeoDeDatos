# -*- coding: utf-8 -*-
import pandas as pd
import hashlib

INPUT = "equipos_final.csv"
OUTPUT = "equipos_final_ids.csv"

def make_id(name):
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:8].upper()
    return f"TEAM-{h}"

df = pd.read_csv(INPUT)

df["team_id"] = df["equipo"].apply(make_id)

df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("✔ Generado:", OUTPUT)