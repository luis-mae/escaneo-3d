#!/usr/bin/env python3
"""Prepara en lote STL para revisión de impresión, sin sobrescribir originales.

Cada pieza produce un STL y un JSON; los fallos se registran y no interrumpen el lote.
"""
import argparse
import json
from pathlib import Path
from preparar_impresion import preparar


def ejecutar_lote(origen, destino, unidad='mm', orientar=False):
    origen, destino = Path(origen), Path(destino)
    if not origen.is_dir():
        raise ValueError('La carpeta de origen no existe')
    if origen.resolve() == destino.resolve() or origen.resolve() in destino.resolve().parents:
        raise ValueError('La salida debe estar fuera de la carpeta de origen')
    archivos = sorted(p for p in origen.iterdir() if p.is_file() and p.suffix.lower() == '.stl')
    if not archivos:
        raise ValueError('No se encontraron archivos STL')
    destino.mkdir(parents=True, exist_ok=True)
    resultados = []
    for archivo in archivos:
        salida = destino / (archivo.stem + '_preparado.stl')
        try:
            informe = preparar(archivo, salida, unidad, orientar)
            estado = 'ok'
            (destino / (archivo.stem + '_informe.json')).write_text(
                json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as exc:
            estado, informe = 'error', {'error': str(exc)}
        resultados.append({'archivo': archivo.name, 'estado': estado, 'detalle': informe})
    resumen = {'total': len(resultados), 'correctos': sum(x['estado'] == 'ok' for x in resultados),
               'errores': sum(x['estado'] == 'error' for x in resultados), 'resultados': resultados}
    (destino / 'resumen_lote.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
    return resumen


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('origen'); p.add_argument('destino')
    p.add_argument('--unidad', default='mm', choices=['mm', 'cm', 'm', 'in'])
    p.add_argument('--orientar', action='store_true')
    args = p.parse_args()
    resultado = ejecutar_lote(args.origen, args.destino, args.unidad, args.orientar)
    print(json.dumps({'total': resultado['total'], 'correctos': resultado['correctos'], 'errores': resultado['errores']}, ensure_ascii=False))
