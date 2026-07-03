# Coding Standards

## General

- Follow PEP 8
- Write clean, readable code
- Prefer composition over inheritance
- Keep functions focused on a single responsibility

## Python

- Type hints required
- Docstrings for public methods
- Black formatting
- Ruff linting

## Git

Branch naming

```
feature/...
bugfix/...
hotfix/...
release/...
```

Commit messages

```
feat:
fix:
docs:
refactor:
test:
chore:
```

## API

- RESTful design
- Versioned APIs
- Consistent JSON responses
- Proper HTTP status codes

## Database

- UUID primary keys
- Foreign key constraints
- Soft deletes where appropriate
- Audit columns on all business tables

## Testing

- Unit tests for business logic
- Integration tests for APIs
- Minimum 80% code coverage
