# 🤝 Contributing to Workflow Platform

We love your input! We want to make contributing to the Workflow Platform as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## 🚀 Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Request Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## 🛠️ Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test categories
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/e2e/           # End-to-end tests

# Run performance tests
pytest tests/performance/
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run e2e

# Run E2E tests with UI
npm run e2e:ui

# Run tests in watch mode
npm run test:watch
```

## 📝 Code Style

### Python (Backend)

We use the following tools for code quality:

- **Black**: Code formatting (120 character line length)
- **isort**: Import sorting
- **mypy**: Type checking
- **flake8**: Linting
- **pre-commit**: Git hooks

```bash
# Format code
black .
isort .

# Type checking
mypy .

# Linting
flake8 .
```

**Style Guidelines**:
- Follow PEP 8
- Use type hints for all functions
- Write docstrings for public functions
- Maximum line length: 120 characters
- Use snake_case for variables and functions
- Use PascalCase for classes

### TypeScript (Frontend)

We use the following tools:

- **ESLint**: Linting with custom rules
- **Prettier**: Code formatting
- **TypeScript**: Type checking

```bash
# Linting
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run type-check
```

**Style Guidelines**:
- Use functional components with hooks
- Prefer TypeScript strict mode
- Maximum line length: 100 characters
- Use camelCase for variables and functions
- Use PascalCase for components
- Use kebab-case for file names

## 🏗️ Project Structure

### Backend Structure

```
backend/
├── api/                    # API endpoints
├── services/              # Business logic (DDD)
├── core/                  # Core infrastructure
├── db/                    # Database layer
├── models/                # Pydantic models
├── utils/                 # Utility functions
├── tests/                 # Test suite
└── alembic/               # Database migrations
```

### Frontend Structure

```
frontend/
├── app/                   # Next.js App Router
├── components/            # React components
├── lib/                   # Utilities and configs
├── hooks/                 # Custom hooks
├── styles/                # Global styles
├── public/                # Static assets
└── __tests__/             # Test files
```

## 🐛 Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/showjihyun/agentrag-v1/issues/new).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

### Bug Report Template

```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. iOS]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]

**Additional context**
Add any other context about the problem here.
```

## 💡 Feature Requests

We use GitHub issues to track feature requests. Request a feature by [opening a new issue](https://github.com/showjihyun/agentrag-v1/issues/new) with the "feature request" label.

### Feature Request Template

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Additional context**
Add any other context or screenshots about the feature request here.
```

## 🔄 Pull Request Guidelines

### Before Submitting

- [ ] Code follows the style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation made
- [ ] Tests added that prove the fix is effective or feature works
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots to help explain your changes

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass
```

## 🏷️ Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Examples

```
feat(workflow): add new condition node type
fix(api): resolve workflow execution timeout issue
docs(readme): update installation instructions
style(frontend): format code with prettier
refactor(backend): extract workflow validation logic
perf(cache): optimize Redis connection pooling
test(workflow): add unit tests for node execution
chore(deps): update dependencies to latest versions
```

## 🌟 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes for significant contributions
- Special mentions in project updates

## 📞 Getting Help

- 💬 **Discussions**: [GitHub Discussions](https://github.com/showjihyun/agentrag-v1/discussions)
- 🐛 **Issues**: [GitHub Issues](https://github.com/showjihyun/agentrag-v1/issues)
- 📧 **Email**: showjihyun@gmail.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Thank you for contributing to the Workflow Platform! Your efforts help make this project better for everyone.