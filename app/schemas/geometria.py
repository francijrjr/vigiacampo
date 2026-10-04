"""Validação de um contorno simples GeoJSON em longitude/latitude (WGS84)."""
import math


def validar_poligono(valor):
    if valor is None:
        return None
    if valor.get('type') != 'Polygon':
        raise ValueError('A área deve ser um polígono GeoJSON.')
    aneis = valor.get('coordinates')
    if not isinstance(aneis, list) or len(aneis) != 1:
        raise ValueError('Desenhe um único contorno, sem buracos.')
    pontos = aneis[0]
    if not isinstance(pontos, list) or not 4 <= len(pontos) <= 301:
        raise ValueError('Use entre 3 e 300 pontos e feche o contorno.')
    for ponto in pontos:
        if (not isinstance(ponto, (list, tuple)) or len(ponto) != 2
                or any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in ponto)
                or not -180 <= ponto[0] <= 180 or not -90 <= ponto[1] <= 90):
            raise ValueError('Coordenadas inválidas; use longitude e latitude.')
    if pontos[0] != pontos[-1] or len(set(map(tuple, pontos[:-1]))) != len(pontos) - 1:
        raise ValueError('Feche o contorno e não repita seus vértices.')
    def orientacao(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def no_segmento(a, b, c):
        return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])
    segmentos = list(zip(pontos, pontos[1:]))
    for i, (a, b) in enumerate(segmentos):
        for j, (c, d) in enumerate(segmentos):
            if j <= i + 1 or (i == 0 and j == len(segmentos) - 1):
                continue
            x, y, z, w = orientacao(a, b, c), orientacao(a, b, d), orientacao(c, d, a), orientacao(c, d, b)
            if (x*y < 0 and z*w < 0) or any((
                x == 0 and no_segmento(a, b, c), y == 0 and no_segmento(a, b, d),
                z == 0 and no_segmento(c, d, a), w == 0 and no_segmento(c, d, b),
            )):
                raise ValueError('As linhas do contorno não podem se cruzar.')
    origem = pontos[0]
    area = sum(orientacao(origem, a, b) for a, b in segmentos)
    if abs(area) < 1e-12:
        raise ValueError('O contorno precisa delimitar uma área.')
    return {'type': 'Polygon', 'coordinates': [[list(p) for p in pontos]]}
