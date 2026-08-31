#!/usr/bin/env python3
"""Vincula tu cuenta de Garmin Connect con esta computadora.

Ejecuta este script en tu propia terminal (no lo pegues en un chat).
Te pedirá tu email y, con `getpass`, tu contraseña de forma oculta:
nunca se imprime en pantalla, no queda en el historial de la shell y
no se envía a ningún sitio salvo a los servidores de Garmin, a través
de la librería `python-garminconnect`.

Si tu cuenta usa verificación en dos pasos (MFA), el script te pedirá
el código cuando Garmin lo solicite.

Una vez que el login funciona, la sesión (tokens OAuth, no tu
contraseña) se guarda en el directorio indicado por TOKEN_STORE para
que las próximas ejecuciones no vuelvan a pedirte la contraseña.
"""

from __future__ import annotations

import getpass
import os
import sys

try:
    from garminconnect import (
        Garmin,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )
except ImportError:
    sys.exit(
        "Falta instalar las dependencias. Ejecuta primero:\n"
        "  pip install -r requirements.txt"
    )

TOKEN_STORE = os.path.expanduser("~/.garminconnect")


def leer_codigo_mfa() -> str:
    return input("Código de verificación en dos pasos (MFA): ").strip()


def iniciar_sesion() -> Garmin:
    """Reutiliza la sesión guardada o pide credenciales por terminal."""
    client = Garmin()
    try:
        client.login(TOKEN_STORE)
        print(f"Sesión reutilizada desde {TOKEN_STORE}.\n")
        return client
    except Exception:
        pass  # No hay sesión guardada (o expiró); se pide login normal.

    email = os.environ.get("GARMIN_EMAIL") or input("Email de Garmin Connect: ").strip()
    password = os.environ.get("GARMIN_PASSWORD") or getpass.getpass(
        "Contraseña de Garmin Connect (no se mostrará): "
    )

    client = Garmin(email=email, password=password, prompt_mfa=leer_codigo_mfa)
    # login(TOKEN_STORE) hace el login con las credenciales y, si tiene
    # éxito, guarda los tokens de sesión (no la contraseña) en TOKEN_STORE.
    client.login(TOKEN_STORE)
    print(f"\nLogin correcto. Sesión guardada en {TOKEN_STORE}.")
    return client


def mostrar_dispositivos(client: Garmin) -> None:
    try:
        nombre = client.get_full_name()
        print(f"Cuenta conectada: {nombre}")
    except Exception:
        pass

    try:
        dispositivos = client.get_devices()
    except Exception as err:
        print(f"No se pudo obtener la lista de dispositivos: {err}", file=sys.stderr)
        return

    if not dispositivos:
        print(
            "\nNo hay dispositivos vinculados a esta cuenta todavía.\n"
            "Sincroniza tu reloj al menos una vez con la app Garmin Connect "
            "(móvil o de escritorio) y vuelve a ejecutar este script."
        )
        return

    print("\nRelojes/dispositivos vinculados a tu cuenta de Garmin:")
    for dispositivo in dispositivos:
        nombre = (
            dispositivo.get("productDisplayName")
            or dispositivo.get("displayName")
            or "Dispositivo desconocido"
        )
        device_id = dispositivo.get("deviceId", "?")
        print(f"  - {nombre} (id: {device_id})")


def main() -> None:
    try:
        client = iniciar_sesion()
    except (
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    ) as err:
        sys.exit(f"No se pudo conectar con Garmin Connect: {err}")

    mostrar_dispositivos(client)


if __name__ == "__main__":
    main()
