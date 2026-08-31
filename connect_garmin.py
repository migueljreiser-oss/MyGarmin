#!/usr/bin/env python3
"""Conecta tu cuenta de Garmin Connect a esta computadora.

IMPORTANTE: ejecuta este script en TU terminal local, no lo pegues en
un chat. Pide el email y la contraseña de forma interactiva (la
contraseña con getpass, así que no se muestra en pantalla ni queda en
el historial de la shell) y los usa solo para autenticarte contra los
servidores de Garmin a través de la librería python-garminconnect.

Tras el primer login exitoso, la sesión (tokens OAuth) se guarda en
~/.garminconnect, así que las próximas veces no hará falta volver a
escribir la contraseña.
"""
import getpass
import os
import sys

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

TOKEN_STORE = os.path.expanduser("~/.garminconnect")


def prompt_mfa() -> str:
    return input("Código de verificación en 2 pasos (MFA), si tu cuenta lo pide: ").strip()


def main() -> None:
    email = os.getenv("GARMIN_EMAIL")
    if not email:
        email = input("Email de Garmin Connect: ").strip()

    password = os.getenv("GARMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Contraseña de Garmin Connect (no se mostrará): ")

    client = Garmin(email, password, prompt_mfa=prompt_mfa)

    try:
        client.login(TOKEN_STORE)
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as err:
        print(f"\nNo se pudo conectar con Garmin Connect: {err}", file=sys.stderr)
        sys.exit(1)

    print("\nConexión establecida con Garmin Connect.")
    print(f"  Sesión guardada en: {TOKEN_STORE} (para no pedir la contraseña la próxima vez)")

    try:
        print(f"  Cuenta: {client.get_full_name()}")
    except Exception:
        pass

    try:
        devices = client.get_devices()
    except Exception as err:
        print(f"\nNo se pudo obtener la lista de dispositivos: {err}", file=sys.stderr)
        return

    if devices:
        print("\nRelojes/dispositivos vinculados a tu cuenta de Garmin:")
        for d in devices:
            model = d.get("productDisplayName") or d.get("displayName") or "Dispositivo desconocido"
            device_id = d.get("deviceId", "?")
            print(f"  - {model} (id: {device_id})")
    else:
        print("\nNo se encontraron dispositivos vinculados a esta cuenta de Garmin Connect.")
        print("Verifica que tu reloj esté sincronizado con la app Garmin Connect al menos una vez.")


if __name__ == "__main__":
    main()
