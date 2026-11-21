# Plan: operación multiusuario

- `assistant/auth.py`: PBKDF2, firma HMAC de sesión, middleware de autenticación.
- `assistant/limits.py`: ventanas deslizantes por usuario y cuota diaria en memoria.
- `assistant/config.py`: modo auth, secreto, usuarios, admins, cookie segura, límites.
- `assistant/web.py`: `/login`, `/logout`, `/admin/summary`, dependencias de permisos.
- `login.html`: formulario accesible y mínimo.
- `scripts/hash_password.py`: genera hashes para `AUTH_USERS`.
- Tests: auth on/off, sesión, límites, admin, config; docs de operación.

Sin dependencias nuevas. Sesión stateless firmada; límites en memoria (una instancia).
