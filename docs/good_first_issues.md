# Good-first-issues — ready to paste into GitHub

No GitHub connector is available to me in this session, so I couldn't create these issues directly. Copy each block into **github.com/opens2p/OpenS2P → Issues → New issue**. Add labels `good first issue` + the extra label listed (GitHub creates `good first issue` and `documentation` by default; add `infra` once, first time you use it).

---

### 1. Add a CI workflow that runs on every PR
**Labels:** good first issue, infra
There's currently no `.github/workflows/` at the repo root — CI won't run. (Note: there's a stray `docs/.github/workflows/.gitkeep` that has no effect; GitHub only reads workflows from the top-level `.github/workflows/`.) Add `.github/workflows/ci.yml` that runs `make lint` and `make test` on every PR against `main`.

---

### 2. Add issue and PR templates
**Labels:** good first issue, documentation
Add `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, and `.github/PULL_REQUEST_TEMPLATE.md` so new issues/PRs come in with consistent structure (steps to reproduce, expected behavior, screenshots, etc.).

---

### 3. Add a `SECURITY.md`
**Labels:** good first issue, documentation
Create a `SECURITY.md` describing how to report a vulnerability (opens2p@gmail.com), supported versions, and response-time expectations. Link it from `CONTRIBUTING.md`.

---

### 4. Verify and document OAuth 2.0 / SSO plan
**Labels:** good first issue, documentation
The README roadmap lists "OAuth 2.0 / SSO" as not yet started. Write a short design note in `docs/` on the intended approach (which providers, where it plugs into the existing JWT/RBAC auth) so someone can pick up implementation later.

---

### 5. Add a supplier portal design note
**Labels:** good first issue, documentation
Same pattern as above for the "Supplier portal" roadmap item — a short scoping doc in `docs/` describing intended scope before code starts.

---

### 6. Improve error messages in the API layer
**Labels:** good first issue
Audit one API module (e.g. `app/api/v1/` suppliers or contracts) for generic/unhelpful error responses and replace them with clear, actionable messages. Good for someone getting familiar with the service → repository layering described in the README.

---

### 7. Add an architecture diagram to `docs/02_architecture/architecture.md`
**Labels:** good first issue, documentation
The README has an ASCII architecture diagram; expand on it with a proper diagram (Mermaid is fine) in `docs/02_architecture/architecture.md`, matching the layered design (FastAPI → Service → Repository → SQLAlchemy → PostgreSQL).

---

### 8. Add test coverage reporting
**Labels:** good first issue, infra
Wire up `pytest-cov` in the `test` Makefile target and report coverage in CI once issue #1 (CI workflow) lands.

---

**Tip:** you don't need all of these live on day one. 3–4 posted at launch is enough to give first-time contributors something to pick up — add more as needed.
