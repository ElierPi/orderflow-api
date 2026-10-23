# OrderFlow delivery plan

## Baseline audit (2026-10-23)

- Existing: FastAPI product CRUD, SQLAlchemy/PostgreSQL, Decimal prices,
  three linear Alembic revisions, pytest schemas/API/health tests.
- Confirmed defect: product create/update silently ignore `description`.
- Risks: test fixtures drop all mapped tables; incomplete test configuration can
  inherit development settings; README contradicts the actual database guard.
- Missing: filtering/pagination, customers, inventory ledger, transactional orders,
  authentication/roles, React UI, Docker, CI.
- Existing migration `79e1982febfb` is a no-op. Preserve historical revisions.
- Working tree was clean. Existing code and local credential files are preserved.

## Phases and acceptance criteria

1. **Audit and fixes** — [complete]
   - [x] Inspect models, schemas, routes, migrations, dependencies and documentation.
   - [x] Persist product descriptions on create and update.
   - [x] Verify persistence and clearing through regression tests.
2. **Safe tests** — [complete]
   - [x] Load complete test settings without falling back to development credentials.
   - [x] Verify connected database identity before any DDL.
   - [x] Replace table deletion with a unique schema inside a rolled-back transaction.
   - [x] Exercise actual Alembic migrations and test safety failures without a database.
3. **Products, customers, inventory** — [complete]
   - [x] Bounded pagination/search/filters; customer validation and safe deletion.
   - [x] Audited inventory changes and nonnegative stock under concurrent requests.
4. **Orders** — [complete]
   - [x] Multiple lines, Decimal totals, stock validation, atomic creation/cancellation.
   - [x] History, state transitions, cancellation restores stock once, concurrency tests.
5. **Authentication and permissions** — [complete]
   - [x] Secure password hashes, expiring JWT, administrator/operator authorization.
   - [x] Private API, safe first-admin provisioning, auth/error tests.
6. **Frontend** — [complete]
   - [x] React/TypeScript/Vite login, dashboard, product/customer/order/inventory views.
   - [x] Real API calls, responsive layout, loading/errors/success, verified build.
7. **Reproducibility and portfolio** — [implemented; environment checks pending]
   - [x] Docker Compose, example settings, CI, professional English README.
   - [x] Real UI screenshots only after running the frontend.
   - [x] Record exact verification results and remaining limitations.
   - [ ] Run Compose on a Docker-enabled machine (Docker unavailable locally).
   - [ ] Run GitHub Actions after an explicitly authorized push (no push performed).

## Safety and delivery rules

- Never touch `orderflow_db` data in tests; no `drop_all`, resets, or automatic seeding.
- Keep `.env` and `.env.test` unchanged and never print their values.
- No push, merge, publication, or changes to other repositories.
- Use small conventional commits only for verified changes when filesystem permissions allow.
- Keep progress, commands and learning notes here or in `docs/` for the next session.

## Verification log

- Initial commands: repository and migration inspection completed; no tests executed.
- Local Python exists in `.venv`, but its base interpreter is outside the sandbox.
  Execution was approved. Read-only inspection confirmed `orderflow_test_db` exists
  and permits creation of isolated schemas before database tests were executed.
- Phase 1/2 checkpoint: `python -m pytest -q`: **30 passed**.
- Commerce/auth checkpoint: **64 passed** before dashboard/concurrency additions.
- Concurrency initially exposed a fixture isolation bug: `SET LOCAL search_path`
  resets at commit. Fixed by setting it on every `after_begin`; both real-connection
  race tests then passed (one reservation succeeds, one cancellation restores stock).
- Final backend run: `python -m pytest -q`: **69 passed**, one dependency deprecation
  warning from Starlette's HTTPX TestClient wrapper. No warnings were suppressed.
- Migration upgrade test preserves an existing product/description, records its
  opening inventory balance, and confirms no ORM/migration schema differences.
- `npm run build`: TypeScript and Vite production build passed.
- Final browser rerun after mobile/dialog adjustments: **1 E2E test passed**
  (desktop plus 390px mobile, real PostgreSQL-backed requests).
- Compose and GitHub Actions YAML syntax parsed successfully; `git diff --check`
  reported no whitespace errors. Runtime Docker/remote CI checks remain pending.
- Chromium E2E flow passed: login, description persistence/edit, customer creation,
  order reservation/cancellation, stock restoration, inventory adjustment, mobile
  layout with no page-width overflow, and sign-out. Test data is isolated PostgreSQL
  data, not mocks. Real screenshots are in `docs/screenshots/`.
- Browser tests initially failed on ambiguous accessible-name selectors; corrected
  to target the proper textboxes, comboboxes, and product text.
- Added an explicit Playwright global teardown because Windows can stop Python
  without running its finally block. Removed the exact generated schema from the
  first attempt after checking its fixture contents; a read-only audit confirmed
  no E2E schemas remain and the existing public test table is still present.
- Visually inspected desktop/mobile captures; improved the mobile navigation and
  compact money formatting so large totals remain legible on narrow cards.
- Node LTS was installed only under ignored `.tools/`; no system Node configuration
  was changed. Fonts are bundled locally. npm installation reported no vulnerabilities.

## Operational next steps

1. Review the English README and `docs/LEARNING.md` (Spanish feature walkthroughs,
   key files, testing steps, concepts, and interview questions).
2. To use the development workspace, privately configure JWT_SECRET, review the
   development connection, apply `alembic upgrade head`, and provision an admin with
   `python -m app.cli --email ...`. No development migrations or credential edits
   were performed during automated verification.
3. Start FastAPI and Vite as documented; all dashboard data comes from the API.
4. Verify Docker and remote CI in their target environments. No deployment performed.
5. Future enhancements: order idempotency keys, invitation/rate limits/password
   recovery, optimistic checks for absolute stock recounts, scalable pickers.

## Verification boundaries

- Backend/API/migration/concurrency tests and a Chromium desktop/mobile workflow
  were executed locally. Docker builds and GitHub Actions were not executed.
- Tests use only `orderflow_test_db`; development data and local credential files
  were not modified. No `drop_all`, database reset, downgrade, push, or merge ran.
- Forcefully terminating concurrent tests can leave their unique test schema behind;
  the E2E harness has explicit cleanup for its recorded generated schema.
- Dashboard value is non-cancelled order value, not collected revenue; dates in
  daily aggregates use UTC. The application assumes one workspace currency.
