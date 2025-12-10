# lighting.py
from typing import Tuple, Dict
import os

Vec3 = Tuple[float, float, float]

DEFAULT_LIGHTING = {
    "Iamb": (100.0, 100.0, 100.0),
    "Ka": 0.2,
    "Il": (127.0, 213.0, 254.0),
    "Pl": (60.0, 5.0, -10.0),
    "Kd": (0.5, 0.5, 0.5),
    "Od": (0.7, 0.7, 0.7),
    "Ks": 0.5,
    "eta": 1.0
}

def parse_floats_from_str(s: str):
    parts = s.strip().split()
    vals = []
    for p in parts:
        try:
            vals.append(float(p))
        except:
            pass
    return vals

def load_lighting(path: str = "lighting.txt") -> Dict[str, object]:
    light = DEFAULT_LIGHTING.copy()
    if not os.path.isfile(path):
        light["_from_file"] = False
        return light

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, rhs = line.split("=", 1)
                key = key.strip().lower()
                vals = parse_floats_from_str(rhs)
                if key == "iamb" and len(vals) >= 3:
                    light["Iamb"] = (vals[0], vals[1], vals[2])
                elif key == "ka" and len(vals) >= 1:
                    light["Ka"] = float(vals[0])
                elif key == "il" and len(vals) >= 3:
                    light["Il"] = (vals[0], vals[1], vals[2])
                elif key == "pl" and len(vals) >= 3:
                    light["Pl"] = (vals[0], vals[1], vals[2])
                elif key == "kd" and len(vals) >= 3:
                    light["Kd"] = (vals[0], vals[1], vals[2])
                elif key == "od" and len(vals) >= 3:
                    light["Od"] = (vals[0], vals[1], vals[2])
                elif key == "ks" and len(vals) >= 1:
                    light["Ks"] = float(vals[0])
                elif key in ("eta", "êta") and len(vals) >= 1:
                    light["eta"] = float(vals[0])
    light["_from_file"] = True
    return light

def pretty_print_lighting(L: Dict[str, object]):
    src = "arquivo" if L.get("_from_file", False) else "padrão (default)"
    print("=== Parâmetros de iluminação (fonte: {}) ===".format(src))
    print(f" Iamb = {L['Iamb']}")
    print(f" Ka   = {L['Ka']}")
    print(f" Il   = {L['Il']}")
    print(f" Pl   = {L['Pl']}")
    print(f" Kd   = {L['Kd']}")
    print(f" Od   = {L['Od']}")
    print(f" Ks   = {L['Ks']}")
    print(f" eta  = {L['eta']}")
    print("============================================")
