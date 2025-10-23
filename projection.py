# projection.py
from typing import Tuple, List, Dict, Optional
import math

Vec3 = Tuple[float, float, float]
ScreenPt = Tuple[Optional[float], Optional[float], Optional[int]]  # (x_s, y_s, valid_flag)

def project_perspective(point_view: Vec3, d: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Projeta um ponto em coordenadas de vista (Xv, Yv, Zv) para (x_s, y_s) no plano de projeção
    a distância d da origem da câmera. Se Zv <= 0, retorna (None, None).
    """
    Xv, Yv, Zv = point_view
    if Zv is None:
        return (None, None)
    if Zv <= 0.0:
        return (None, None)
    x_s = d * (Xv / Zv)
    y_s = d * (Yv / Zv)
    return (x_s, y_s)

def to_ndc(x_s: Optional[float], y_s: Optional[float], hx: float, hy: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Converte (x_s, y_s) para coordenadas normalizadas (x_ndc, y_ndc).
    Se x_s ou y_s for None, retorna (None, None).
    """
    if x_s is None or y_s is None:
        return (None, None)
    if hx == 0 or hy == 0:
        raise ValueError("hx e hy devem ser diferentes de 0")
    x_ndc = x_s / hx
    y_ndc = y_s / hy
    return (x_ndc, y_ndc)

def ndc_to_screen(x_ndc: Optional[float], y_ndc: Optional[float], width: int, height: int) -> Tuple[Optional[int], Optional[int]]:
    """
    Mapeia NDC (-1..1) para coordenadas de tela (i,j) em pixels.
    Retorna inteiros (i,j). Se x_ndc/y_ndc for None, retorna (None, None).
    Observação: j é contado de cima para baixo (0 = topo).
    """
    if x_ndc is None or y_ndc is None:
        return (None, None)
    # clamp opcional em [-1,1] (evita valores fora do viewport extremos)
    if x_ndc < -1.0: x_ndc = -1.0
    if x_ndc > 1.0: x_ndc = 1.0
    if y_ndc < -1.0: y_ndc = -1.0
    if y_ndc > 1.0: y_ndc = 1.0

    i = (x_ndc + 1.0) / 2.0 * width
    j = (1.0 - y_ndc) / 2.0 * height
    # converter para inteiros de pixel
    return (int(round(i)), int(round(j)))

def world_view_to_screen_list(view_vertices: List[Vec3], camera_params: Dict[str, float], width: int, height: int):
    """
    Pipeline que recebe uma lista de vértices já em coordenadas de vista (Xv,Yv,Zv),
    parâmetros da câmera (d,hx,hy) e resolução (width,height).
    Retorna lista de dicionários por vértice com:
      { 'view': (Xv,Yv,Zv), 'x_s':..., 'y_s':..., 'x_ndc':..., 'y_ndc':..., 'pixel': (i,j), 'visible':bool }
    """
    d = float(camera_params.get("d", 1.0))
    hx = float(camera_params.get("hx", 1.0))
    hy = float(camera_params.get("hy", 1.0))

    results = []
    for P in view_vertices:
        Xv, Yv, Zv = P
        item = {"view": P, "x_s": None, "y_s": None, "x_ndc": None, "y_ndc": None, "pixel": (None, None), "visible": False}
        if Zv is None or Zv <= 0.0:
            # não projetável
            results.append(item)
            continue
        # projeção perspectiva
        x_s, y_s = project_perspective(P, d)
        item["x_s"] = x_s
        item["y_s"] = y_s
        # ndc
        x_ndc, y_ndc = to_ndc(x_s, y_s, hx, hy)
        item["x_ndc"] = x_ndc
        item["y_ndc"] = y_ndc
        # dentro do frustum (checar -1..1)
        visible = (x_ndc is not None and y_ndc is not None and -1.0 <= x_ndc <= 1.0 and -1.0 <= y_ndc <= 1.0)
        item["visible"] = visible
        # screen coords
        px, py = ndc_to_screen(x_ndc, y_ndc, width, height)
        item["pixel"] = (px, py)
        results.append(item)
    return results