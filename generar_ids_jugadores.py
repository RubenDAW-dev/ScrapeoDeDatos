# -*- coding: utf-8 -*-
import pandas as pd
import hashlib

INPUT = "jugadores_laliga.csv"
OUTPUT = "jugadores_laliga_ids.csv"

def make_id(name):
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:10].upper()
    return f"PLY-{h}"

df = pd.read_csv(INPUT)

df["player_id"] = df["Player"].apply(make_id)

df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

print("✔ Generado:", OUTPUT)