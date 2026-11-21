# Tasks: operación multiusuario

- [X] T001 Ampliar `Settings`: auth, secreto, usuarios, admins, cookie, límites.
- [X] T002 Implementar `assistant/auth.py` (PBKDF2, firma/verificación de sesión, middleware).
- [X] T003 Implementar `assistant/limits.py` (rate limit y cuota diaria).
- [X] T004 Crear `scripts/hash_password.py`.
- [X] T005 Añadir `/login`, `/logout` y plantilla `login.html`.
- [X] T006 Proteger rutas y permitir API 401 / HTML redirect.
- [X] T007 Aplicar límites a `/ask`, `/ask/stream`, `/quotes`, `/feedback`.
- [X] T008 Implementar `/admin/summary` con conteos y rol admin.
- [X] T009 Añadir métricas de auth/rate limit y logs sin secretos.
- [X] T010 Pruebas de auth, sesión inválida, límites y admin.
- [X] T011 Pruebas de compatibilidad con auth desactivada.
- [X] T012 Documentar variables y operación multiusuario.
- [X] T013 Actualizar README/AGENTS/constitución e índice.
- [X] T014 PR, CI y merge.
