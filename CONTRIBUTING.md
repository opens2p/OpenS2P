# Contributing to OpenS2P

Thanks for your interest in contributing! We welcome contributions from everyone.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### 1. Find or Create an Issue

- Check existing [issues](https://github.com/OpenS2P/OpenS2P/issues)
- Open a new issue describing the feature or bug
- Wait for maintainer feedback before starting work

### 2. Set Up Development Environment

```bash
git clone https://github.com/OpenS2P/OpenS2P.git
cd OpenS2P
make install
```

### 3. Create a Branch

```bash
git checkout -b feat/your-feature-name
git checkout -b fix/your-bug-fix
```

### 4. Make Changes

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.x
- Frontend: React 19, TypeScript, Tailwind CSS
- Follow existing code style and patterns

### 5. Run Tests

```bash
make lint
make test
```

### 6. Submit a Pull Request

- Target the `develop` branch
- Include a clear description of changes
- Reference the related issue
- Keep PRs focused on a single concern

## Development Conventions

### Backend

- Use `async` for all endpoints and service methods
- Business logic belongs in services, not in endpoints
- Database queries belong in repositories, not in services
- Add audit events for all state-changing operations
- Include unit tests for new functionality

### Frontend

- One component per file
- Use TypeScript strict mode
- Use TanStack Query for server state
- Use Tailwind utility classes (no CSS modules)

## Pull Request Checklist

Before submitting:

- [ ] Code follows project style
- [ ] Tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] PR targets `develop` branch

## Questions?

Open a [discussion](https://github.com/OpenS2P/OpenS2P/discussions) or issue.
