# MyGarmin

Vincula tu reloj Garmin con tu computadora usando la librería
[`python-garminconnect`](https://github.com/cyberjunky/python-garminconnect),
que habla con los servidores de Garmin Connect (los mismos que usa la
app oficial). Para que tu reloj aparezca, primero debe haberse
sincronizado al menos una vez con la app Garmin Connect (móvil o de
escritorio).

## Requisitos

- Python 3.9 o superior
- Una cuenta de Garmin Connect con el reloj ya vinculado

## 1. Instalar dependencias

Ejecuta esto **en tu terminal local**, dentro de la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate      # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Conectar el reloj

```bash
python3 connect_garmin.py
```

El script te pedirá el email y, con `getpass`, la contraseña de forma
oculta: no se muestra en pantalla, no queda en el historial de la
shell y solo se usa para autenticarte contra los servidores de Garmin.
**Tu contraseña nunca se te pide en este chat**, solo en tu propia
terminal.

Si tu cuenta tiene verificación en dos pasos, el script te pedirá el
código cuando corresponda.

Al terminar con éxito verás la lista de dispositivos Garmin vinculados
a tu cuenta, y la sesión quedará guardada en `~/.garminconnect` para
que la próxima vez no tengas que volver a escribir la contraseña.

## Notas de seguridad

- El script nunca imprime ni guarda tu contraseña en disco.
- Los tokens de sesión que sí quedan guardados en `~/.garminconnect`
  permiten mantener la sesión iniciada sin volver a autenticarte;
  borra esa carpeta si quieres cerrar sesión.
- Como alternativa a escribirlas de forma interactiva, puedes definir
  `GARMIN_EMAIL` y `GARMIN_PASSWORD` como variables de entorno antes
  de ejecutar el script.
