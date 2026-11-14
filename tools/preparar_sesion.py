"""Genera manifiesto reproducible de una sesión fotográfica para motores 3D futuros."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from tools.validar_sesion import validar_sesion
from tools.seleccionar_fotografias import seleccionar


def preparar_sesion(carpeta: Path, destino: Path, maximo: int = 60, min_fotos: int = 12) -> dict:
    carpeta = carpeta.resolve()
    destino = destino.resolve()
    if maximo < 1 or min_fotos < 2:
        raise ValueError('Límites inválidos')
    if destino == carpeta or carpeta in destino.parents:
        raise ValueError('El destino debe estar fuera de la carpeta de imágenes')
    auditoria = validar_sesion(carpeta, min_fotos)
    seleccion = seleccionar(carpeta, maximo)
    entradas = []
    for nombre in seleccion['seleccionadas']:
        ruta = (carpeta / nombre).resolve()
        if ruta.parent != carpeta or not ruta.is_file():
            raise ValueError('Ruta de fotografía inválida')
        entradas.append({'archivo': nombre, 'sha256': hashlib.sha256(ruta.read_bytes()).hexdigest(),
                         'bytes': ruta.stat().st_size})
    estado = 'lista_para_intentar' if len(entradas) >= min_fotos and auditoria['estado'] == 'apta_para_intentar' else 'requiere_revision'
    resultado = {'schema_version': 1, 'creado_utc': datetime.now(timezone.utc).isoformat(),
                 'estado': estado, 'imagenes': entradas, 'auditoria': auditoria,
                 'descartadas': seleccion['descartadas'],
                 'advertencia': 'No se ha reconstruido geometría 3D ni verificado cobertura angular.'}
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return resultado


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('carpeta', type=Path)
    p.add_argument('destino', type=Path)
    p.add_argument('--maximo', type=int, default=60)
    p.add_argument('--min-fotos', type=int, default=12)
    a = p.parse_args()
    print(json.dumps(preparar_sesion(a.carpeta, a.destino, a.maximo, a.min_fotos), ensure_ascii=False, indent=2))
