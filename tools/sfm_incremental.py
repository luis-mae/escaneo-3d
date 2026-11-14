"""SfM incremental experimental desde tracks 2D con cámara intrínseca conocida.

Ancla las primeras dos vistas y añade cámaras con PnP; escala arbitraria.
No garantiza reconstrucción robusta ni aptitud dimensional.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .triangular_puntos import triangular_puntos
from .nube_dos_vistas import guardar_ply
from .auditar_sfm import auditar_sfm


def reconstruir_tracks(datos, focal_px, ancho, alto, min_inliers=12):
    if not np.isfinite(focal_px) or focal_px <= 0 or ancho <= 0 or alto <= 0:
        raise ValueError("Calibración inválida")
    if type(min_inliers) is not int or min_inliers < 8:
        raise ValueError("min_inliers inválido")
    imagenes = list(datos["puntos_por_imagen"])
    if len(imagenes) < 2:
        raise ValueError("Se requieren dos vistas")
    K = np.array([[focal_px, 0, ancho / 2], [0, focal_px, alto / 2], [0, 0, 1.]], dtype=float)
    tracks = datos["tracks"]
    observaciones = []
    for tr in tracks:
        obs = {}
        for nombre, indice in tr.items():
            if nombre not in datos["puntos_por_imagen"] or type(indice) is not int:
                raise ValueError("Track inválido")
            puntos = datos["puntos_por_imagen"][nombre]
            if not 0 <= indice < len(puntos):
                raise ValueError("Índice de track fuera de rango")
            uv = np.asarray(puntos[indice], dtype=float)
            if uv.shape != (2,) or not np.isfinite(uv).all():
                raise ValueError("Observación inválida")
            obs[nombre] = uv
        observaciones.append(obs)
    primero, segundo = imagenes[:2]
    indices = [i for i, tr in enumerate(observaciones) if primero in tr and segundo in tr]
    if len(indices) < min_inliers:
        raise ValueError("No hay tracks suficientes entre las primeras dos vistas")
    a = np.float64([observaciones[i][primero] for i in indices])
    b = np.float64([observaciones[i][segundo] for i in indices])
    E, mask = cv2.findEssentialMat(a, b, K, cv2.RANSAC, 0.999, 1.5)
    if E is None:
        raise ValueError("No se estimó geometría esencial")
    if E.shape != (3, 3):
        E = E[:3, :]
    cantidad, R, t, mascara = cv2.recoverPose(E, a, b, K, mask=mask)
    validos = np.flatnonzero(mascara.ravel() != 0)
    if cantidad < min_inliers:
        raise ValueError("No hay inliers suficientes para la pose inicial")
    triangulados = triangular_puntos(a[validos], b[validos], K, R, t)
    if triangulados["aceptados"] < min_inliers:
        raise ValueError("Triangulación inicial insuficiente")
    mapa = {indices[validos[j]]: xyz for j, xyz in
            zip(triangulados["indices_aceptados"], triangulados["puntos"])}
    camaras = {primero: (np.eye(3), np.zeros(3)), segundo: (R, t.ravel())}
    reportes = [{"vista": primero, "estado": "ancla"},
                {"vista": segundo, "estado": "pose_esencial", "inliers": int(cantidad)}]
    for nombre in imagenes[2:]:
        conocidos = [(i, tr[nombre], mapa[i]) for i, tr in enumerate(observaciones)
                     if nombre in tr and i in mapa]
        if len(conocidos) < max(6, min_inliers):
            reportes.append({"vista": nombre, "estado": "insuficiente_pnp",
                             "correspondencias": len(conocidos)})
            continue
        obj = np.float64([xyz for _, _, xyz in conocidos])
        uv = np.float64([pixel for _, pixel, _ in conocidos])
        ok, rv, tv, inliers = cv2.solvePnPRansac(
            obj, uv, K, None, iterationsCount=200, reprojectionError=4.,
            confidence=0.999, flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok or inliers is None or len(inliers) < max(6, min_inliers):
            reportes.append({"vista": nombre, "estado": "pnp_rechazado"})
            continue
        rot, _ = cv2.Rodrigues(rv)
        trans = tv.ravel()
        camaras[nombre] = (rot, trans)
        reportes.append({"vista": nombre, "estado": "pnp_aceptado",
                         "inliers": int(len(inliers))})
        # Triangular tracks nuevos usando cualquier vista ya registrada.
        for i, tr in enumerate(observaciones):
            if i in mapa or nombre not in tr:
                continue
            anteriores = [v for v in camaras if v != nombre and v in tr]
            if not anteriores:
                continue
            anterior = anteriores[0]
            Ra, ta = camaras[anterior]
            # Triangulación en coordenadas globales con proyecciones calibradas.
            P1 = K @ np.column_stack((Ra, ta))
            P2 = K @ np.column_stack((rot, trans))
            homog = cv2.triangulatePoints(P1, P2, tr[anterior].reshape(2, 1),
                                           tr[nombre].reshape(2, 1))
            if abs(homog[3, 0]) < 1e-10:
                continue
            X = homog[:3, 0] / homog[3, 0]
            if not np.isfinite(X).all():
                continue
            if (Ra @ X + ta)[2] <= 1e-6 or (rot @ X + trans)[2] <= 1e-6:
                continue
            def error(v, RR, tt):
                q = K @ (RR @ X + tt)
                return np.linalg.norm(q[:2] / q[2] - tr[v])
            if error(anterior, Ra, ta) <= 3 and error(nombre, rot, trans) <= 3:
                mapa[i] = X.tolist()
    indices_ordenados = sorted(mapa)
    auditoria = auditar_sfm([mapa[i] for i in indices_ordenados], indices_ordenados,
                           observaciones, camaras, K)
    return {"estado": "sfm_incremental_experimental", "escala": "arbitraria",
            "auditoria": auditoria, "indices_tracks_3d": indices_ordenados,
            "puntos": [mapa[i] for i in sorted(mapa)],
            "puntos_3d": len(mapa),
            "camaras": {k: {"R": v[0].tolist(), "t": v[1].tolist()} for k, v in camaras.items()},
            "vistas": reportes,
            "advertencia": "SfM disperso experimental, focal aproximada, sin ajuste global ni escala física; no es malla imprimible."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("tracks", type=Path)
    p.add_argument("--focal-px", type=float, required=True)
    p.add_argument("--ancho", type=int, required=True)
    p.add_argument("--alto", type=int, required=True)
    p.add_argument("--salida", type=Path, required=True)
    args = p.parse_args()
    datos = json.loads(args.tracks.read_text(encoding="utf-8"))
    resultado = reconstruir_tracks(datos, args.focal_px, args.ancho, args.alto)
    if args.salida.exists():
        raise FileExistsError("La carpeta de salida ya existe")
    args.salida.mkdir(parents=True)
    guardar_ply(resultado["puntos"], args.salida / "nube.ply")
    informe = {k: v for k, v in resultado.items() if k != "puntos"}
    (args.salida / "informe.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
