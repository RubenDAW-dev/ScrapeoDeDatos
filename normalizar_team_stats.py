import pandas as pd
import re

df = pd.read_csv("team_raw.csv", header=None)
df.columns = ["home", "away", "url", "c4", "c5", "c6", "c7"]

partidos = []
current = {}

def extract_teams(url):
    if not isinstance(url, str):
        return None, None
    try:
        last = url.split("/")[-1]
        parts = last.split("-")
        teams = []
        for p in parts:
            if p.isdigit():  # año = fin
                break
            teams.append(p)
        name = " ".join(teams)
        if " " in name:
            h, a = name.split(" ", 1)
            return h.replace("-", " "), a.replace("-", " ")
    except:
        return None, None
    return None, None

def parse_values(s):
    if not isinstance(s, str):
        return []
    nums = re.findall(r"\d+", s)
    return list(map(int, nums))

i = 0
while i < len(df):

    row = df.iloc[i]

    # Detección de posesión (inicio de un partido)
    if isinstance(row["home"], str) and row["home"].endswith("%") and row["away"].endswith("%"):

        # Guardar partido anterior
        if current:
            partidos.append(current)

        current = {
            "poss_home": int(row["home"].replace("%", "")),
            "poss_away": int(row["away"].replace("%", "")),
        }

        # Extraer equipos desde URL
        ht, at = extract_teams(row["url"])
        current["home_team"] = ht
        current["away_team"] = at

        i += 1
        continue

    # Shots on Target
    if row["home"] == "Shots on Target":
        values = df.iloc[i+1]
        h = parse_values(values["home"])
        a = parse_values(values["away"])

        if len(h) >= 2:
            current["shots_ot_home"] = h[0]
            current["shots_total_home"] = h[1]
        if len(a) >= 2:
            current["shots_ot_away"] = a[0]
            current["shots_total_away"] = a[1]

    # Saves
    if row["home"] == "Saves":
        values = df.iloc[i+1]
        h = parse_values(values["home"])
        a = parse_values(values["away"])

        if len(h) >= 1:
            current["saves_home"] = h[0]
        if len(a) >= 1:
            current["saves_away"] = a[0]

    # Cards
    if row["home"] == "Cards":
        current["cards_home"] = 0
        current["cards_away"] = 0

    i += 1

# Guardar el último bloque
if current:
    partidos.append(current)

out = pd.DataFrame(partidos)

# 🔥 ELIMINAMOS match_url DEL CSV
# (Ya no existe en el diccionario, así que solo guardamos lo que hay)

out.to_csv("normalized_fbref.csv", index=False)

print(out.head())
print("✔ Archivo generado sin match_url → normalized_fbref.csv")