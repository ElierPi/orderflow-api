# Guía para entender y presentar OrderFlow

## 1. Descripciones de productos y validación

**Problema:** Pydantic aceptaba `description`, pero las rutas no asignaban el valor
al modelo de SQLAlchemy. Validar una petición no significa persistirla.

**Archivos:** `app/routes/products.py`, `app/schemas/products.py`,
`tests/test_products_api.py`, `tests/test_commerce_api.py`.

Crear un producto construye `Product(description=product.description, ...)`;
actualizarlo asigna `product.description = data.description` antes del commit.
Pydantic valida longitud y tipos. SQLAlchemy transforma los cambios del objeto
en SQL. PostgreSQL conserva el resultado cuando se confirma la transacción.
`PUT` representa reemplazo completo: omitir la descripción la deja en `null`.

Los precios usan `Decimal` y `NUMERIC`, porque el punto flotante binario puede
representar de forma aproximada importes como `0.1`. Un precio del catálogo puede
cambiar; el precio vendido debe conservarse dentro del pedido.

**Cómo probar:** crear y consultar un producto con descripción; editarla;
enviar `null`; consultar de nuevo. Las pruebas verifican tanto la respuesta
inmediata como una lectura posterior, para comprobar persistencia.

**Entrevista:** ¿por qué aceptar un campo en el esquema no garantiza guardarlo?
¿Qué diferencia hay entre PUT y PATCH? ¿Por qué usar Decimal para dinero?

## 2. Aislamiento y seguridad de pruebas

**Problema:** el fixture original borraba y recreaba todas las tablas mapeadas
antes de cada prueba. Un error de configuración podía causar pérdida de datos.

**Archivos:** `tests/db_safety.py`, `tests/conftest.py`, `tests/test_db_safety.py`,
`tests/test_concurrency.py`, `tests/test_migrations.py`, `alembic/env.py`.

La configuración se lee directamente de `.env.test` con `dotenv_values`, sin
heredar campos de `.env` o del shell. Se exige el nombre exacto
`orderflow_test_db`. Antes de crear un esquema, se consulta `current_database()`.
Esto confirma la identidad de la conexión real, además de revisar su URL.

Cada prueba normal crea un esquema UUID en una transacción externa. Alembic
recibe esa misma conexión y aplica las migraciones allí. La sesión usa
`join_transaction_mode="create_savepoint"`: los commits de las rutas no confirman
la transacción externa. Al finalizar, un rollback elimina el esquema y sus datos.
Las tablas que ya estaban en `public` nunca forman parte de ese esquema.

Las pruebas concurrentes necesitan esquemas confirmados, visibles para dos
conexiones. Crean un esquema propio y eliminan únicamente ese esquema al terminar.
Un evento `after_begin` fija `search_path` en **cada** nueva transacción: un
`SET LOCAL` aislado deja de aplicarse después de un commit.

**Cómo probar:** ejecutar `python -m pytest -q tests/test_db_safety.py` sin tocar
ninguna base; después, con la base de testing verificada, ejecutar toda la suite.
`test_migrations.py` parte de un producto existente y verifica que la actualización
conserva sus datos y registra el saldo inicial de inventario.

**Entrevista:** ¿por qué comprobar solo el nombre de una variable no basta?
¿Qué es un savepoint? ¿Por qué dos conexiones no ven DDL sin confirmar?

## 3. Clientes y eliminación segura

**Problema:** los pedidos necesitan identificar a su cliente sin perder el
historial cuando esa persona deja de estar activa.

**Archivos:** `app/models/commerce.py`, `app/schemas/commerce.py`,
`app/routes/customers.py`, `alembic/versions/e1023a_customers_users.py`.

Pydantic valida el correo; el sistema normaliza a minúsculas y una restricción
UNIQUE garantiza que dos transacciones no registren el mismo correo. Una consulta
previa por sí sola no evita esa carrera. Se captura `IntegrityError`, se hace
rollback y se devuelve `409`.

Eliminar un cliente cambia `active=False`: deja de aparecer en el listado y no
puede recibir pedidos nuevos, pero sus pedidos anteriores siguen consultables.
El correo permanece reservado. Los productos se archivan por la misma razón:
conservar referencias y movimientos de inventario.

**Cómo probar:** crear un cliente, buscarlo por correo, editarlo, crear un pedido,
archivarlo y verificar que el pedido sigue disponible. Repetir un correo devuelve
`409`; un correo inválido devuelve `422`.

**Entrevista:** ¿qué resuelve una clave foránea? ¿Cuándo usar archivado en lugar
de DELETE físico? ¿Qué consecuencias tiene reservar el correo de un cliente archivado?

## 4. Inventario y pedidos transaccionales

**Problema:** si dos operadores venden la última unidad, una validación sin
bloqueo puede aceptar ambos pedidos. También puede guardarse medio pedido si se
confirman sus partes por separado.

**Archivos:** `app/services/inventory.py`, `app/routes/inventory.py`,
`app/routes/orders.py`, `app/models/commerce.py`,
`alembic/versions/e1023b_orders_inventory.py`, `tests/test_concurrency.py`.

`SELECT ... FOR UPDATE` bloquea las filas de los productos hasta el commit o
rollback. Los escritores adquieren los bloqueos en orden ascendente de ID para
reducir ciclos de espera. El siguiente vendedor espera y después ve el stock
actualizado. Además, `CHECK (stock >= 0)` protege el dato en PostgreSQL.

Crear un pedido:

1. Bloquea el cliente y valida que está activo.
2. Bloquea todos los productos en orden y verifica todas las cantidades.
3. Calcula subtotales y total con Decimal, usando el precio de la base.
4. Crea el pedido y sus líneas con nombre/precio históricos.
5. Descuenta existencias y crea movimientos dentro de la misma transacción.
6. Hace un único commit del cambio de negocio.

Si un monitor no tiene existencias, no se confirma ni la venta del teclado ni
ninguna línea del pedido. El cliente no decide el precio o el total.

`pending -> confirmed -> shipped` es la secuencia normal. Pending y confirmed
pueden pasar a cancelled. La cancelación bloquea primero el pedido y después
los productos; repone existencias y registra movimientos. Una segunda cancelación
ve el estado final y devuelve `409`, sin reponer otra vez.

Los ajustes de inventario son cantidades firmadas: `+5` significa entrada y
`-3` salida. Un PUT de producto con stock representa un recuento absoluto del
administrador, también auditado. Para operación diaria se prefieren los ajustes.

**Cómo probar:** crear un pedido con teclado y monitor; consultar sus totales y
stock; cambiar el precio del teclado y comprobar que el pedido conserva el precio
original; cancelar; intentar cancelar nuevamente. Ejecutar
`python -m pytest -q tests/test_concurrency.py` verifica carreras con conexiones reales.

**Entrevista:** ¿qué significa atomicidad? ¿Por qué una condición CHECK no sustituye
la lógica de negocio? ¿Cómo puede ocurrir un deadlock? ¿Qué diferencia hay entre
evitar sobreventa e impedir pedidos duplicados por reintentos HTTP?

## 5. Autenticación y permisos

**Problema:** el CRUD original era público. Ahora es necesario identificar quién
opera el sistema y quién puede administrar el catálogo.

**Archivos:** `app/security.py`, `app/routes/auth.py`, `app/cli.py`,
`tests/test_auth_api.py`, dependencias de las rutas.

Argon2id genera hashes con sal propia: la contraseña original no se guarda ni se
puede recuperar del hash. Verificar una contraseña ejecuta el algoritmo costoso.
La respuesta del login no distingue entre correo inexistente y contraseña errónea.

El JWT contiene el ID de usuario, emisor, audiencia, fecha de emisión y caducidad.
La API valida firma HS256, campos requeridos, destinatario y vigencia. Después
consulta el usuario para comprobar que sigue activo. Los roles se leen de la base,
por lo que la autorización no depende de un rol antiguo incluido en un token.

`Depends(current_user)` exige identidad; `Depends(administrator)` exige además
rol admin. Ocultar un botón en React mejora la interfaz, pero la protección real
está en el backend. El registro público ignora cualquier intento de escoger rol
admin. El comando local crea administradores y solicita la contraseña sin mostrarla.

El secreto JWT se configura de forma privada; el login devuelve `503` cuando
falta una configuración válida. Los errores de validación no devuelven los valores
originales de entrada, para no exponer contraseñas en respuestas `422`.

**Cómo probar:** registrar un operador, iniciar sesión, consultar `/auth/me`,
crear un cliente, intentar crear un producto y obtener `403`. Probar un token
vencido o alterado produce `401`.

**Entrevista:** ¿hashing y cifrado son lo mismo? ¿La firma de un JWT oculta su
contenido? ¿Autenticación y autorización resuelven el mismo problema?

## 6. React, TypeScript y la conexión real

**Problema:** una API sin una interfaz obliga a operar mediante Swagger y no
demuestra un flujo de usuario completo.

**Archivos:** `frontend/src/api.ts`, `App.tsx`, `components.tsx`, `pages/*`,
`styles.css`, `vite.config.ts`, `frontend/e2e/workspace.spec.ts`.

El cliente tipado centraliza fetch, errores y Authorization. El token vive en
memoria: cerrar sesión o recargar elimina la sesión local. Un `401` durante una
sesión devuelve al login. Vite envía `/api` al backend sin exponer secretos en
variables del navegador. Solo opciones públicas deben usar el prefijo `VITE_`.

`useApi` vuelve a consultar cuando cambia la ruta o una revisión después de guardar;
usa AbortController al desmontar. `useSearch` retrasa 250 ms la consulta para no
enviar una petición por cada tecla. Los listados solicitan 21 registros, muestran
20 y usan el sobrante para saber si existe otra página.

Los formularios envían datos reales y muestran validación, errores y confirmación.
El dashboard recibe agregados SQL; no inventa ventas ni tendencias. Los pedidos
estiman importes en el navegador, pero aceptan como definitivo el total que calcula
FastAPI. Los diálogos nativos ofrecen foco y navegación por teclado.

**Cómo probar:** `npm run build` comprueba tipos y empaqueta la aplicación;
`npm run test:e2e` opera Chromium contra FastAPI/PostgreSQL reales. El flujo crea
producto y cliente, reserva stock, cancela, verifica la reposición y ajusta el
inventario. Las capturas muestran esos datos desechables, identificados como pruebas.

**Entrevista:** ¿un tipo TypeScript valida datos en ejecución? ¿Por qué no guardar
secretos en `VITE_`? ¿Qué diferencia hay entre un estado vacío y un error de carga?

## 7. Docker, CI y presentación profesional

**Archivos:** `Dockerfile`, `frontend/Dockerfile`, `compose.yaml`,
`.github/workflows/ci.yml`, archivos de ejemplo, `.gitignore`, `README.md`, `PLAN.md`.

Compose describe servicios reproducibles y dependencias: PostgreSQL sano antes
de las migraciones del API; Vite conecta con el hostname interno `api`.
El volumen de Compose está separado de PostgreSQL local y usa el puerto 5433
para no ocupar su puerto habitual. Los secretos reales no entran en Git ni en
la imagen. Las fuentes del frontend se distribuyen localmente con sus dependencias.

GitHub Actions define una base efímera y ejecuta las verificaciones. Tener un YAML
no equivale a haber ejecutado CI. Docker y el workflow remoto deben verificarse
en sus entornos correspondientes; no se ha publicado nada ni se ha hecho push.

**Cómo probar:** seguir el README en una máquina con Docker; comprobar login,
crear un pedido y reiniciar sin perder datos del volumen. Ejecutar CI después de
un push autorizado. No usar `down -v` con datos que se quieran conservar.

**Entrevista:** ¿qué diferencia hay entre una imagen, un contenedor y un volumen?
¿Por qué un healthcheck no garantiza que las migraciones estén aplicadas? ¿Qué
valor demuestra una prueba de navegador frente a una prueba unitaria?

## Ejercicio breve para practicar

Dos operadores intentan comprar una unidad de un teclado cuyo stock es uno.
Explica el recorrido de ambas peticiones y señala el instante en que PostgreSQL
impide que ambas se acepten. Después explica por qué esto **no** evita que un
reintento HTTP cree dos pedidos cuando hay stock suficiente: esa garantía requiere
una clave de idempotencia, que queda como mejora futura explícita.
