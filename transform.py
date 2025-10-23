# transform.py
from typing import Tuple, List, Dict
import math

Vec3 = Tuple[float, float, float]
Camera = Dict[str, object]

EPS = 1e-9

def dot(a: Vec3, b: Vec3) -> float:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def length(v: Vec3) -> float:
    return math.sqrt(dot(v,v))

def normalize(v: Vec3) -> Vec3:
    L = length(v)
    if L < EPS:
        return (0.0, 0.0, 0.0)
    return (v[0]/L, v[1]/L, v[2]/L)

def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])

def scale(v: Vec3, s: float) -> Vec3:
    return (v[0]*s, v[1]*s, v[2]*s)

def cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def is_zero_vec(v: Vec3) -> bool:
    return length(v) < EPS

def compute_camera_basis(camera: Camera) -> Dict[str, Vec3]:
    """
    Recebe dict camera com chaves:
      - 'C': (x,y,z)
      - 'N': (x,y,z)  (direção de visão sugerida)
      - 'V': (x,y,z)  (up vector sugerido)
    Retorna dict com:
      - 'C': origem
      - 'u': eixo X da câmera (direita)
      - 'v': eixo Y da câmera (up)
      - 'n': eixo Z da câmera (forward)
    Procedimento (Gram-Schmidt-like):
      1) n = normalize(N)
      2) v' = V - (V·n) n
      3) u = normalize(n × v')
      4) v_final = u × n
    Isso produz uma base ortonormal (u, v_final, n).
    """
    C = tuple(camera.get("C", (0.0,0.0,0.0)))
    N = tuple(camera.get("N", (0.0,0.0,-1.0)))
    V = tuple(camera.get("V", (0.0,1.0,0.0)))

    # normaliza N
    n = normalize(N)
    if is_zero_vec(n):
        # fallback
        n = (0.0, 0.0, -1.0)

    # ortogonalizar V em relação a n: v' = V - proj_n(V)
    v_dot_n = dot(V, n)
    v_prime = sub(V, scale(n, v_dot_n))

    if is_zero_vec(v_prime):
        # V estava paralelo a N: escolher um up alternativo
        # preferir (0,1,0) se não paralelo; senão (1,0,0)
        alt_up = (0.0, 1.0, 0.0)
        if abs(dot(alt_up, n)) > 0.999:  # ainda quase paralelo
            alt_up = (1.0, 0.0, 0.0)
        v_prime = sub(alt_up, scale(n, dot(alt_up, n)))
        if is_zero_vec(v_prime):
            # último recurso
            v_prime = (0.0, 1.0, 0.0)

    # normalizar v'
    v_norm = normalize(v_prime)

    # u = normalize(n × v_norm)
    u_cross = cross(n, v_norm)
    if is_zero_vec(u_cross):
        # fallback: pick perpendicular to n
        if abs(n[0]) < 0.9:
            u_cross = cross(n, (1.0, 0.0, 0.0))
        else:
            u_cross = cross(n, (0.0, 1.0, 0.0))

    u = normalize(u_cross)

    # recomputar v_final = u × n (garante ortonormalidade)
    v_final = cross(u, n)
    v_final = normalize(v_final)

    return {"C": C, "u": u, "v": v_final, "n": n}

def world_to_view_point(P: Vec3, basis: Dict[str, Vec3]) -> Vec3:
    """
    Transforma ponto P (mundo) para coordenadas de vista:
      1) traslada por -C
      2) projeta nos eixos u, v, n por produto interno
    retorna (x_v, y_v, z_v)
    """
    C = basis["C"]
    u = basis["u"]
    v = basis["v"]
    n = basis["n"]
    Pv = sub(P, C)
    x_v = dot(Pv, u)
    y_v = dot(Pv, v)
    z_v = dot(Pv, n)
    return (x_v, y_v, z_v)

def world_to_view_vertices(vertices: List[Vec3], basis: Dict[str, Vec3]) -> List[Vec3]:
    return [world_to_view_point(p, basis) for p in vertices]


# função de teste rápido
def quick_test(camera: Camera, vertices: List[Vec3]):
    print("=== Teste: Cálculo da base da câmera e transformação mundo->vista ===")
    basis = compute_camera_basis(camera)
    print("Origem C:", basis["C"])
    print("u (direita):", basis["u"])
    print("v (up):", basis["v"])
    print("n (forward):", basis["n"])
    print("--- Transformando primeiros vértices ---")
    for i, p in enumerate(vertices[:10]):
        pv = world_to_view_point(p, basis)
        print(f"v[{i+1}] mundo = {p}  -> vista = {pv}")
    print("=== Fim do teste ===")
    return basis

if __name__ == "__main__":
    # exemplo rápido (quando executado isoladamente)
    cam = {
        "C": (0.0, 0.0, 5.0),
        "N": (0.0, 0.0, -1.0),
        "V": (0.0, 1.0, 0.0)
    }
    verts = [
        (50.0, 0.0, 0.0),
        (0.0, 50.0, 0.0),
        (0.0, 0.0, 50.0)
    ]
    quick_test(cam, verts)