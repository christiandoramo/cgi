# byu_loader.py
from typing import List, Tuple
import os

def parse_floats_from_tokens(tokens):
    return [float(t) for t in tokens]

def parse_ints_from_tokens(tokens):
    return [int(t) for t in tokens]

def load_byu(path: str) -> Tuple[List[Tuple[float,float,float]], List[Tuple[int,int,int]]]:
    """
    Lê um arquivo .byu simples:
      primeira linha: <n_vertices> <n_triangles>
      próximas n linhas: x y z (floats)
      próximas m linhas: i1 i2 i3 (1-based indices)
    Retorna (vertices, triangles) onde:
      vertices: list de (x,y,z) floats
      triangles: list de (i0, i1, i2) int (0-based)
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    vertices = []
    triangles = []
    tokens = []

    # leitura robusta: coletar todos os tokens (ignorando comentários e linhas vazias)
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            parts = line.split()
            tokens.extend(parts)

    if len(tokens) < 2:
        raise ValueError("Formato inválido: menos de 2 tokens no arquivo (esperado 'n m' na primeira linha).")

    # primeiro dois tokens: n_vertices, n_triangles
    try:
        n_vertices = int(tokens[0])
        n_triangles = int(tokens[1])
    except Exception as e:
        raise ValueError("Cabeçalho inválido. Esperado: <n_vertices> <n_triangles>") from e

    expected_tokens = 2 + 3 * n_vertices + 3 * n_triangles
    if len(tokens) < expected_tokens:
        # permitir se houver menos tokens, mas alertar
        # ainda assim tentaremos ler o máximo possível
        pass

    idx = 2
    # ler vértices
    for i in range(n_vertices):
        if idx + 2 >= len(tokens):
            raise ValueError(f"Arquivo incompleto ao ler vértice {i+1}.")
        x = float(tokens[idx]); y = float(tokens[idx+1]); z = float(tokens[idx+2])
        vertices.append((x,y,z))
        idx += 3

    # ler triângulos
    for j in range(n_triangles):
        if idx + 2 >= len(tokens):
            raise ValueError(f"Arquivo incompleto ao ler triângulo {j+1}.")
        i1 = int(tokens[idx]); i2 = int(tokens[idx+1]); i3 = int(tokens[idx+2])
        # lidar com formas de BYU que usam índice negativo para terminar uma face (remover sinal)
        i1 = abs(i1); i2 = abs(i2); i3 = abs(i3)
        # converter para 0-based
        triangles.append((i1-1, i2-1, i3-1))
        idx += 3

    return vertices, triangles

# função de teste simples (pode ser chamada diretamente)
def quick_test_load(filename: str):
    try:
        verts, tris = load_byu(filename)
    except Exception as e:
        print("Falha ao carregar .byu:", e)
        return
    print(f"Arquivo: {filename}")
    print(f"Vértices carregados: {len(verts)}")
    for i, v in enumerate(verts):
        print(f"  v[{i+1}] = {v}")
    print(f"Triângulos carregados: {len(tris)}")
    for j, t in enumerate(tris):
        print(f"  t[{j+1}] = ( {t[0]+1}, {t[1]+1}, {t[2]+1} )")  # Mostrando 1-based para leitura humana

# permite teste rápido quando executado diretamente
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python byu_loader.py arquivo.byu")
    else:
        quick_test_load(sys.argv[1])