"""Provisionamiento local de planes ESCANEO 3D.

Ejecutar únicamente desde una consola administrativa segura. No existe endpoint
público para cambiar planes ni se aceptan identificadores de usuario desde el cliente.
"""
import argparse
import json

from tools.entitlements import configurar_cuenta, obtener_entitlements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_id", help="Subject exacto emitido por el proveedor de identidad")
    parser.add_argument("--plan", choices=["FREE", "PLUS", "PRO"], default="FREE")
    parser.add_argument("--inactivo", action="store_true")
    args = parser.parse_args()
    resultado = configurar_cuenta(args.user_id, args.plan, active=not args.inactivo)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
