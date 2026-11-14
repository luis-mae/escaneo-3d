"""Verifica que las fotos de una sesión no cambiaron desde su preparación."""
import argparse
import hashlib
import json
from pathlib import Path


def verificar_manifiesto(manifiesto: Path, carpeta: Path) -> dict:
    data = json.loads(manifiesto.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('imagenes'), list):
        raise ValueError('Formato de manifiesto no compatible')
    carpeta = carpeta.resolve()
    resultados = []
    vistos = set()
    for item in data['imagenes']:
        nombre = item.get('archivo')
        if not isinstance(nombre, str) or not nombre or nombre in vistos:
            raise ValueError('Nombre de archivo inválido o duplicado')
        vistos.add(nombre)
        ruta = (carpeta / nombre).resolve()
        if ruta.parent != carpeta:
            raise ValueError('Ruta fuera de la carpeta permitida')
        if not ruta.is_file():
            resultados.append({'archivo': nombre, 'estado': 'faltante'})
            continue
        digest = hashlib.sha256(ruta.read_bytes()).hexdigest()
        correcto = digest == item.get('sha256') and ruta.stat().st_size == item.get('bytes')
        resultados.append({'archivo': nombre, 'estado': 'integro' if correcto else 'modificado'})
    return {'estado': 'integro' if resultados and all(x['estado'] == 'integro' for x in resultados) else 'requiere_revision',
            'total': len(resultados), 'archivos': resultados}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifiesto', type=Path)
    p.add_argument('carpeta', type=Path)
    args = p.parse_args()
    print(json.dumps(verificar_manifiesto(args.manifiesto, args.carpeta), ensure_ascii=False, indent=2))
