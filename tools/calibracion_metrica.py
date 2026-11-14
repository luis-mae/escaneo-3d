"""Calibración de escala de una nube con varias distancias físicas conocidas.

No corrige deformaciones multivista: valida la consistencia antes de habilitar medidas.
"""
import numpy as np


def calibrar(puntos, referencias, tolerancia_relativa=0.05):
    """referencias: [{'a': índice, 'b': índice, 'mm': distancia real}, ...]."""
    pts = np.asarray(puntos, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 3 or len(pts) < 2 or not np.isfinite(pts).all():
        raise ValueError('Nube de puntos inválida')
    if not isinstance(referencias, (list, tuple)) or len(referencias) < 2:
        raise ValueError('Se necesitan al menos dos referencias físicas independientes')
    if not 0 < tolerancia_relativa < 1:
        raise ValueError('Tolerancia inválida')
    escalas = []
    pares = set()
    for r in referencias:
        a, b, mm = r['a'], r['b'], float(r['mm'])
        if not isinstance(a, int) or not isinstance(b, int) or a == b or min(a,b) < 0 or max(a,b) >= len(pts):
            raise ValueError('Índices de referencia inválidos')
        par = tuple(sorted((a,b)))
        if par in pares:
            raise ValueError('Referencia repetida')
        pares.add(par)
        d = float(np.linalg.norm(pts[a] - pts[b]))
        if not np.isfinite(mm) or mm <= 0 or d <= 1e-12:
            raise ValueError('Distancia física o geométrica inválida')
        escalas.append(mm/d)
    escala = float(np.median(escalas))
    errores = [abs(s / escala - 1) for s in escalas]
    max_error = float(max(errores))
    consistente = max_error <= tolerancia_relativa
    return {
        'estado': 'escala_consistente' if consistente else 'escala_inconsistente',
        'escala_mm_por_unidad': escala if consistente else None,
        'max_desviacion_relativa': max_error,
        'referencias': len(escalas),
        'apto_para_medicion': bool(consistente),
        'advertencia': ('La escala no garantiza exactitud geométrica; verificar con una pieza patrón.'
                        if consistente else 'Referencias incompatibles: no exportar medidas ni modelo métrico.')
    }


def puntos_en_mm(puntos, resultado):
    if not resultado.get('apto_para_medicion'):
        raise ValueError('Calibración no validada: exportación métrica bloqueada')
    return np.asarray(puntos, dtype=float) * resultado['escala_mm_por_unidad']
