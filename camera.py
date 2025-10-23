# camera.py
from typing import Tuple, Dict, Optional
import os

# Tipos
Vec3 = Tuple[float, float, float]
Camera = Dict[str, object]

# Valores padrão (seguro para primeiros testes)
DEFAULT_CAMERA: Camera = {
    "C": (0.0, 0.0, 5.0),
    "N": (0.0, 0.0, -1.0),
    "V": (0.0, 1.0, 0.0),
    "d": 1.0,
    "hx": 1.0,
    "hy": 1.0
}

def parse_floats_from_str(s: str):
    parts = s.strip().split()
    return [float(p) for p in parts]

def load_camera(path: str = "camera.txt") -> Camera:
    """
    Carrega parâmetros da câmera de 'path'.
    Suporta:
      - Linhas no formato KEY = valores (onde KEY ∈ {C,N,V,d,hx,hy})
      - Ou um arquivo com 12 números: N(3) V(3) d hx hy C(3)
    Se algo estiver faltando, aplica valores padrão.
    """
    cam = DEFAULT_CAMERA.copy()

    if not os.path.isfile(path):
        # arquivo ausente: retorna defaults e avisa
        cam["_from_file"] = False
        return cam

    # ler linhas, ignorar comentários
    tokens = []
    has_key_value = False
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if "=" in line:
                has_key_value = True
                key, rhs = line.split("=", 1)
                key = key.strip().lower()
                vals = parse_floats_from_str(rhs)
                if key == "c":
                    if len(vals) >= 3:
                        cam["C"] = (vals[0], vals[1], vals[2])
                elif key == "n":
                    if len(vals) >= 3:
                        cam["N"] = (vals[0], vals[1], vals[2])
                elif key == "v":
                    if len(vals) >= 3:
                        cam["V"] = (vals[0], vals[1], vals[2])
                elif key == "d":
                    if len(vals) >= 1:
                        cam["d"] = float(vals[0])
                elif key == "hx":
                    if len(vals) >= 1:
                        cam["hx"] = float(vals[0])
                elif key == "hy":
                    if len(vals) >= 1:
                        cam["hy"] = float(vals[0])
                else:
                    # chave desconhecida -> ignorar
                    pass
            else:
                # sem '=', adicionar aos tokens para possível formato sem-chaves
                parts = line.split()
                for p in parts:
                    tokens.append(p)

    if not has_key_value:
        # tentar interpretar tokens como 12 números na ordem:
        # N(3) V(3) d hx hy C(3)
        try:
            nums = [float(t) for t in tokens]
            if len(nums) >= 12:
                cam["N"] = (nums[0], nums[1], nums[2])
                cam["V"] = (nums[3], nums[4], nums[5])
                cam["d"] = float(nums[6])
                cam["hx"] = float(nums[7])
                cam["hy"] = float(nums[8])
                cam["C"] = (nums[9], nums[10], nums[11])
        except Exception:
            # se falhar, manter defaults e prosseguir
            pass

    cam["_from_file"] = True
    # validações mínimas: se vetor n ou v for zero, usar default
    def is_zero_vec(v):
        return abs(v[0]) < 1e-9 and abs(v[1]) < 1e-9 and abs(v[2]) < 1e-9

    if is_zero_vec(cam["N"]):
        cam["N"] = DEFAULT_CAMERA["N"]
    if is_zero_vec(cam["V"]):
        cam["V"] = DEFAULT_CAMERA["V"]

    # garantias de float
    cam["d"] = float(cam.get("d", DEFAULT_CAMERA["d"]))
    cam["hx"] = float(cam.get("hx", DEFAULT_CAMERA["hx"]))
    cam["hy"] = float(cam.get("hy", DEFAULT_CAMERA["hy"]))

    return cam

def pretty_print_camera(cam: Camera):
    src = "arquivo" if cam.get("_from_file", False) else "padrão (default)"
    print("=== Parâmetros da câmera (fonte: {}) ===".format(src))
    print(f" C  = ({cam['C'][0]}, {cam['C'][1]}, {cam['C'][2]})")
    print(f" N  = ({cam['N'][0]}, {cam['N'][1]}, {cam['N'][2]})")
    print(f" V  = ({cam['V'][0]}, {cam['V'][1]}, {cam['V'][2]})")
    print(f" d  = {cam['d']}")
    print(f" hx = {cam['hx']}")
    print(f" hy = {cam['hy']}")
    print("==========================================")

# função de teste que pode ser chamada manualmente
def quick_test(path: str = "camera.txt"):
    cam = load_camera(path)
    pretty_print_camera(cam)
    return cam

if __name__ == "__main__":
    # teste rápido se executado diretamente
    quick_test()