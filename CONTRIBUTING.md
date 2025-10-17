# 🤝 Contributing to Agentic RAG

First off, thank you for considering contributing to Agentic RAG! 🎉

It's people like you that make Agentic RAG such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community](#community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

## 🎯 How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, etc.)

Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)

### ✨ Suggesting Features

Feature suggestions are welcome! Please:

- **Check existing feature requests** first
- **Provide clear use case** and benefits
- **Include mockups** if UI-related
- **Consider implementation complexity**

Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)

### 📝 Improving Documentation

Documentation improvements are always appreciated:

- Fix typos or unclear explanations
- Add examples and tutorials
- Translate documentation
- Improve API documentation

### 💻 Contributing Code

1. **Find an issue** to work on (or create one)
2. **Comment** on the issue to claim it
3. **Fork** the repository
4. **Create a branch** for your feature
5. **Make your changes**
6. **Test thoroughly**
7. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

```bash
# Required
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git

# Optional
- Ollama (for local LLM)
- PostgreSQL client
- Redis client
```

### Setup Steps

#### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/agenticrag.git
cd agenticrag

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/agenticrag.git
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Setup pre-commit hooks
pre-commit install

# Copy environment file
cp .env.example .env
# Edit .env with your settings
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local
# Edit .env.local with your settings
```

#### 4. Start Infrastructure

```bash
# From project root
docker-compose up -d postgres milvus redis

# Verify services
docker-compose ps
```

#### 5. Run Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

#### 6. Start Development Servers

```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit http://localhost:3000

## 📐 Coding Guidelines

### Python (Backend)

#### Style Guide

- Follow **PEP 8**
- Use **type hints**
- Maximum line length: **88 characters** (Black formatter)
- Use **docstrings** for all public functions/classes

```python
def process_document(
    file_content: bytes,
    filename: str,
    user_id: str
) -> tuple[Document, list[TextChunk]]:
    """
    Process a document and extract chunks.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        user_id: User identifier
        
    Returns:
        Tuple of (Document, list of TextChunks)
        
    Raises:
        DocumentProcessingError: If processing fails
    """
    # Implementation
```

#### Code Organization

```python
# Imports order
import standard_library
import third_party
import local_modules

# Class structure
class MyClass:
    """Class docstring."""
    
    # Class variables
    CLASS_VAR = "value"
    
    def __init__(self):
        """Initialize."""
        self.instance_var = None
    
    def public_method(self):
        """Public method."""
        pass
    
    def _private_method(self):
        """Private method."""
        pass
```

#### Testing

```python
# Use pytest
def test_process_document_success():
    """Test successful document processing."""
    # Arrange
    file_content = b"test content"
    filename = "test.txt"
    
    # Act
    result = process_document(file_content, filename)
    
    # Assert
    assert result is not None
    assert len(result.chunks) > 0
```

### TypeScript (Frontend)

#### Style Guide

- Follow **Airbnb Style Guide**
- Use **TypeScript** strictly
- Use **functional components** with hooks
- Maximum line length: **100 characters**

```typescript
// Component structure
interface MyComponentProps {
  title: string;
  onSubmit: (data: FormData) => void;
}

export function MyComponent({ title, onSubmit }: MyComponentProps) {
  const [state, setState] = useState<string>('');
  
  const handleSubmit = useCallback(() => {
    // Implementation
  }, [state]);
  
  return (
    <div className="my-component">
      {/* JSX */}
    </div>
  );
}
```

#### Testing

```typescript
// Use Jest + React Testing Library
describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" onSubmit={jest.fn()} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
  
  it('handles submit', async () => {
    const onSubmit = jest.fn();
    render(<MyComponent title="Test" onSubmit={onSubmit} />);
    
    await userEvent.click(screen.getByRole('button'));
    expect(onSubmit).toHaveBeenCalled();
  });
});
```

### General Guidelines

#### File Naming

```
Backend (Python):
- snake_case.py
- test_snake_case.py

Frontend (TypeScript):
- PascalCase.tsx (components)
- camelCase.ts (utilities)
- PascalCase.test.tsx (tests)
```

#### Comments

```python
# Good: Explain WHY, not WHAT
# Use cache to avoid expensive recomputation
result = cache.get(key) or compute_expensive()

# Bad: Obvious comment
# Get result from cache
result = cache.get(key)
```

#### Error Handling

```python
# Good: Specific exceptions with context
try:
    result = process_file(file)
except FileNotFoundError as e:
    logger.error(f"File not found: {file.name}")
    raise DocumentProcessingError(f"Cannot process {file.name}") from e

# Bad: Bare except
try:
    result = process_file(file)
except:
    pass
```

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

#### Examples

```bash
# Feature
feat(agents): add web search agent with DuckDuckGo integration

# Bug fix
fix(document): handle empty PDF files gracefully

# Documentation
docs(readme): add installation instructions for Windows

# Refactor
refactor(query): simplify adaptive routing logic

# Test
test(api): add integration tests for document upload
```

### Commit Best Practices

- **One logical change per commit**
- **Write clear, descriptive messages**
- **Reference issues** (#123)
- **Keep commits atomic**
- **Test before committing**

## 🔄 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages are clear

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Review Process

1. **Automated checks** run (tests, linting)
2. **Maintainer review** (1-2 business days)
3. **Address feedback** if needed
4. **Approval and merge**

### After Merge

- Delete your branch
- Update your fork
- Celebrate! 🎉

## 🏷️ Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `enhancement` | New feature or request |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `question` | Further information requested |
| `wontfix` | This will not be worked on |
| `duplicate` | This issue already exists |
| `priority: high` | High priority |
| `priority: low` | Low priority |

## 🌟 Recognition

Contributors will be:

- Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Mentioned in release notes
- Given credit in documentation
- Invited to contributor discussions

## 💬 Community

### Communication Channels

- **GitHub Discussions**: General questions and ideas
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time chat (coming soon)
- **Twitter**: [@AgenticRAG](https://twitter.com/agenticrag)

### Getting Help

- Check [Documentation](docs/)
- Search [existing issues](https://github.com/showjihyun/agentrag-v1/issues)
- Ask in [Discussions](https://github.com/showjihyun/agentrag-v1/discussions)
- Join our Discord (coming soon)

## 📚 Resources

### Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [Milvus Documentation](https://milvus.io/docs)

### Project Documentation

- [Architecture Overview](.kiro/steering/structure.md)
- [Tech Stack](.kiro/steering/tech.md)
- [API Documentation](backend/ADAPTIVE_ROUTING_API_DOCUMENTATION.md)
- [Feature Guide](docs/FEATURES.md)

## 🎯 Areas Needing Help

We especially welcome contributions in:

- 🌐 **Translations**: Help translate to more languages
- 📝 **Documentation**: Improve guides and examples
- 🧪 **Testing**: Add more test coverage
- 🎨 **UI/UX**: Design improvements
- ⚡ **Performance**: Optimization opportunities
- 🐛 **Bug Fixes**: Fix reported issues

## ❓ Questions?

Don't hesitate to ask! We're here to help:

- Open a [Discussion](https://github.com/showjihyun/agentrag-v1/discussions)
- Comment on an issue
- Reach out on Twitter

---

## 🙏 Thank You!

Your contributions make Agentic RAG better for everyone. We appreciate your time and effort!

**Happy Coding! 🚀**

---

**[← Back to README](README.md)**
