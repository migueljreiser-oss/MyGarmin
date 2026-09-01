# MyGarmin

Conecta tu cuenta de Garmin Connect a tu computadora usando la librería
[`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect).

`python-garminconnect` habla con los servidores de Garmin Connect (los
mismos que usa la app oficial), así que tu reloj debe haberse
sincronizado al menos una vez con la app Garmin Connect (móvil o de
escritorio) para que aparezca vinculado a tu cuenta.

## Requisitos

- Python 3.12 o superior (es el mínimo que exige `python-garminconnect`)
- Una cuenta de Garmin Connect con el reloj ya vinculado

## Instalación

Ejecuta esto en tu terminal local, dentro de la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Conectar el reloj

```bash
python3 connect_garmin.py
```

El script te pedirá el email y, con `getpass`, la contraseña de forma
oculta (no se imprime en pantalla ni queda en el historial de la
shell). Las credenciales solo se usan para autenticarte contra los
servidores de Garmin; nunca se envían a ningún otro lugar.

Si tu cuenta tiene verificación en 2 pasos, el script te pedirá el
código.

Al terminar, verás la lista de dispositivos Garmin vinculados a tu
cuenta y la sesión quedará guardada en `~/.garminconnect`, para que la
próxima vez no tengas que volver a escribir la contraseña.

## Notas de seguridad

- El script nunca imprime tu contraseña ni la guarda en disco.
- Los tokens de sesión en `~/.garminconnect/garmin_tokens.json` sí
  quedan en tu disco (con permisos restringidos) para mantener la
  sesión iniciada; bórralos si quieres cerrar sesión.
- También puedes definir `GARMIN_EMAIL` y `GARMIN_PASSWORD` como
  variables de entorno antes de ejecutar el script si prefieres no
  escribirlas de forma interactiva.
