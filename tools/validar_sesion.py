"""Auditoría preliminar de sesiones fotográficas; no garantiza reconstrucción."""
import argparse
import hashlib
import json
from pathlib import Path

EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}


def _hash_archivo(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            digest.update(bloque)
    return digest.hexdigest()


def validar_sesion(carpeta: Path, min_fotos: int = 12) -> dict:
    if min_fotos < 2:
        raise ValueError('min_fotos debe ser >= 2')
    if not carpeta.is_dir():
        raise FileNotFoundError(f'No existe la carpeta: {carpeta}')
    archivos = sorted(p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONES)
    vacias = [p.name for p in archivos if p.stat().st_size == 0]
    validas = [p for p in archivos if p.stat().st_size > 0]
    por_hash = {}
    duplicadas = []
    for foto in validas:
        huella = _hash_archivo(foto)
        if huella in por_hash:
            duplicadas.append({'archivo': foto.name, 'igual_a': por_hash[huella]})
        else:
            por_hash[huella] = foto.name
    unicas = len(por_hash)
    avisos = []
    if unicas < min_fotos:
        avisos.append(f'Fotos únicas insuficientes: {unicas}/{min_fotos}')
    if vacias:
        avisos.append(f'Archivos vacíos: {len(vacias)}')
    if duplicadas:
        avisos.append(f'Fotografías idénticas detectadas: {len(duplicadas)}; no aportan nuevas vistas')
    tamanos = [p.stat().st_size for p in validas]
    if tamanos and min(tamanos) < 20_000:
        avisos.append('Algunas imágenes son muy pequeñas; revisar resolución y calidad')
    return {
        'estado': 'apta_para_intentar' if unicas >= min_fotos and not vacias else 'revisar',
        'total_imagenes': len(archivos),
        'imagenes_validas': len(validas),
        'imagenes_unicas': unicas,
        'imagenes_duplicadas': duplicadas,
        'imagenes_vacias': vacias,
        'bytes_totales': sum(tamanos),
        'avisos': avisos,
        'nota': 'No verifica cobertura angular, nitidez, validez de imagen ni calibración; solo detecta archivos idénticos.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carpeta', type=Path)
    parser.add_argument('--min-fotos', type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(validar_sesion(args.carpeta, args.min_fotos), indent=2, ensure_ascii=False))
