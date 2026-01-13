# 🤝 Contributing to AgenticRAG

Thank you for your interest in contributing to AgenticRAG! We welcome contributions from developers of all skill levels. This guide will help you get started with contributing to our visual AI workflow builder.

## 📋 Table of Contents

- [🎯 Ways to Contribute](#-ways-to-contribute)
- [🚀 Getting Started](#-getting-started)
- [🏗 Development Setup](#-development-setup)
- [📝 Code Contribution Guidelines](#-code-contribution-guidelines)
- [🧪 Testing Guidelines](#-testing-guidelines)
- [📖 Documentation Guidelines](#-documentation-guidelines)
- [🐛 Bug Reports](#-bug-reports)
- [💡 Feature Requests](#-feature-requests)
- [🔍 Code Review Process](#-code-review-process)
- [🏆 Recognition](#-recognition)

---

## 🎯 Ways to Contribute

### 🔧 **Code Contributions**
- **Bug fixes**: Help us squash bugs and improve stability
- **New features**: Implement new blocks, orchestration patterns, or integrations
- **Performance improvements**: Optimize existing code for better performance
- **Security enhancements**: Strengthen our security measures
- **Plugin development**: Create new agent plugins or workflow blocks

### 📚 **Documentation**
- **API documentation**: Improve our FastAPI auto-generated docs
- **Tutorials**: Create step-by-step guides for common use cases
- **Examples**: Build sample workflows and use case demonstrations
- **Translations**: Help us support more languages
- **Video content**: Create educational videos and demos

### 🎨 **Design & UX**
- **UI/UX improvements**: Enhance the visual workflow builder
- **Accessibility**: Make the platform more accessible to all users
- **Mobile responsiveness**: Improve mobile and tablet experience
- **Theme development**: Create new visual themes

### 🧪 **Testing & Quality Assurance**
- **Manual testing**: Test new features and report issues
- **Automated testing**: Write unit, integration, and E2E tests
- **Performance testing**: Help us benchmark and optimize performance
- **Security testing**: Identify potential security vulnerabilities

---

## 🚀 Getting Started

### Prerequisites

Before you start contributing, make sure you have:

- **Git**: Version control system
- **Docker & Docker Compose**: For running the full stack
- **Node.js 18+**: For frontend development
- **Python 3.10+**: For backend development
- **Code Editor**: VS Code recommended with our workspace settings

### 🍴 Fork and Clone

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/agenticrag.git
   cd agenticrag
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/agenticrag.git
   ```

---

## 🏗 Development Setup

### 🐳 **Quick Setup with Docker**

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your API keys
# At minimum, add one LLM provider API key

# Start all services
docker-compose up -d

# Check services are running
docker-compose ps
```

### 💻 **Local Development Setup**

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 🔧 **Development Tools**

#### Backend Tools
```bash
# Code formatting
black backend/
isort backend/

# Type checking
mypy backend/

# Linting
flake8 backend/

# Testing
pytest backend/tests/
```

#### Frontend Tools
```bash
# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Testing
npm run test
npm run test:watch

# E2E testing
npm run e2e
```

---

## 📝 Code Contribution Guidelines

### 🌿 **Branching Strategy**

We use **Git Flow** with the following branch types:

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/feature-name`**: New features
- **`bugfix/bug-description`**: Bug fixes
- **`hotfix/critical-fix`**: Critical production fixes
- **`docs/documentation-update`**: Documentation changes

#### Creating a Feature Branch
```bash
# Switch to develop branch
git checkout develop
git pull upstream develop

# Create feature branch
git checkout -b feature/amazing-new-feature

# Make your changes and commit
git add .
git commit -m "feat: add amazing new feature"

# Push to your fork
git push origin feature/amazing-new-feature
```

### 📏 **Code Style Guidelines**

#### **Python (Backend)**
- **PEP 8**: Follow Python style guidelines
- **Type hints**: Use type annotations for all functions
- **Docstrings**: Use Google-style docstrings
- **Line length**: Maximum 120 characters
- **Imports**: Use isort for import organization

```python
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

class WorkflowRequest(BaseModel):
    """Request model for workflow creation.
    
    Attributes:
        name: The workflow name
        description: Optional workflow description
        blocks: List of workflow blocks
    """
    name: str
    description: Optional[str] = None
    blocks: List[dict]

async def create_workflow(request: WorkflowRequest) -> dict:
    """Create a new workflow.
    
    Args:
        request: The workflow creation request
        
    Returns:
        The created workflow data
        
    Raises:
        HTTPException: If workflow creation fails
    """
    # Implementation here
    pass
```

#### **TypeScript (Frontend)**
- **ESLint**: Follow our ESLint configuration
- **Prettier**: Use for code formatting
- **Type safety**: Prefer explicit types over `any`
- **Component structure**: Use functional components with hooks
- **File naming**: Use kebab-case for files, PascalCase for components

```typescript
interface WorkflowBlockProps {
  id: string;
  type: string;
  data: BlockData;
  onUpdate: (id: string, data: BlockData) => void;
}

export const WorkflowBlock: React.FC<WorkflowBlockProps> = ({
  id,
  type,
  data,
  onUpdate
}) => {
  const [isEditing, setIsEditing] = useState(false);
  
  const handleUpdate = useCallback((newData: BlockData) => {
    onUpdate(id, newData);
  }, [id, onUpdate]);

  return (
    <div className="workflow-block">
      {/* Component implementation */}
    </div>
  );
};
```

### 📦 **Commit Message Convention**

We use **Conventional Commits** for clear commit history:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### **Types:**
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

#### **Examples:**
```bash
feat(workflow): add drag-and-drop block reordering
fix(api): resolve authentication token expiration issue
docs(readme): update installation instructions
style(frontend): apply consistent button styling
refactor(backend): simplify workflow execution logic
perf(database): optimize vector search queries
test(agents): add unit tests for agent orchestration
chore(deps): update dependencies to latest versions
```

---

## 🧪 Testing Guidelines

### 🎯 **Testing Strategy**

We maintain high code quality through comprehensive testing:

#### **Backend Testing**
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and database interactions
- **Performance Tests**: Benchmark critical operations
- **Security Tests**: Validate authentication and authorization

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_workflow_execution.py

# Run tests with specific marker
pytest -m "not slow"
```

#### **Frontend Testing**
- **Unit Tests**: Test individual components and utilities
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows
- **Accessibility Tests**: Ensure WCAG compliance

```bash
# Run unit tests
npm run test

# Run E2E tests
npm run e2e

# Run accessibility tests
npm run test:a11y
```

### ✅ **Test Requirements**

- **New features**: Must include comprehensive tests
- **Bug fixes**: Must include regression tests
- **Coverage**: Maintain >80% code coverage
- **Performance**: Include performance benchmarks for critical paths

---

## 📖 Documentation Guidelines

### 📚 **Documentation Types**

#### **Code Documentation**
- **Inline comments**: Explain complex logic
- **Function docstrings**: Document all public functions
- **Type annotations**: Use comprehensive type hints
- **README files**: Document each major module

#### **User Documentation**
- **API documentation**: Auto-generated from FastAPI
- **User guides**: Step-by-step tutorials
- **Examples**: Real-world use cases
- **Video tutorials**: Visual learning content

#### **Developer Documentation**
- **Architecture docs**: System design and patterns
- **Setup guides**: Development environment setup
- **Contributing guides**: This document!
- **Deployment docs**: Production deployment guides

### 📝 **Writing Guidelines**

- **Clear and concise**: Use simple, direct language
- **Examples**: Include code examples and screenshots
- **Structure**: Use consistent heading hierarchy
- **Links**: Cross-reference related documentation
- **Updates**: Keep documentation current with code changes

---

## 🐛 Bug Reports

### 📋 **Before Reporting**

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to ensure bug still exists
3. **Reproduce consistently** to provide clear steps
4. **Gather information** about your environment

### 🎯 **Bug Report Template**

```markdown
## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Screenshots
If applicable, add screenshots to help explain the problem.

## Environment
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Browser: [e.g. Chrome 96, Firefox 95, Safari 15]
- AgenticRAG Version: [e.g. 1.2.3]
- Docker Version: [if using Docker]

## Additional Context
Any other context about the problem.

## Possible Solution
If you have ideas for fixing the bug.
```

---

## 💡 Feature Requests

### 🎨 **Feature Request Template**

```markdown
## Feature Summary
A clear and concise description of the feature.

## Problem Statement
What problem does this feature solve?

## Proposed Solution
Describe your proposed solution in detail.

## Alternative Solutions
Describe any alternative solutions you've considered.

## Use Cases
Provide specific use cases where this feature would be valuable.

## Implementation Ideas
If you have technical implementation ideas, share them here.

## Additional Context
Any other context, mockups, or examples.
```

### 🚀 **Feature Development Process**

1. **Discussion**: Feature requests are discussed in GitHub Issues
2. **Design**: Create design documents for complex features
3. **Implementation**: Develop the feature following our guidelines
4. **Testing**: Comprehensive testing including edge cases
5. **Documentation**: Update relevant documentation
6. **Review**: Code review and feedback incorporation
7. **Merge**: Integration into the main codebase

---

## 🔍 Code Review Process

### 👥 **Review Requirements**

- **All PRs** require at least one review from a maintainer
- **Complex changes** may require multiple reviews
- **Breaking changes** require special attention and documentation
- **Security-related changes** require security team review

### ✅ **Review Checklist**

#### **Functionality**
- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Performance impact is acceptable

#### **Code Quality**
- [ ] Code follows style guidelines
- [ ] Code is well-documented
- [ ] No code duplication
- [ ] Appropriate abstractions

#### **Testing**
- [ ] Adequate test coverage
- [ ] Tests pass consistently
- [ ] Integration tests included
- [ ] Performance tests if needed

#### **Documentation**
- [ ] Code is self-documenting
- [ ] Public APIs are documented
- [ ] User-facing changes documented
- [ ] Breaking changes noted

### 🔄 **Review Process**

1. **Submit PR**: Create pull request with clear description
2. **Automated checks**: CI/CD pipeline runs tests and checks
3. **Review assignment**: Maintainers are automatically assigned
4. **Feedback**: Reviewers provide constructive feedback
5. **Iteration**: Address feedback and update PR
6. **Approval**: PR is approved by required reviewers
7. **Merge**: PR is merged into target branch

---

## 🏆 Recognition

### 🌟 **Contributor Recognition**

We value all contributions and recognize contributors in several ways:

#### **GitHub Recognition**
- **Contributors page**: All contributors listed on GitHub
- **Release notes**: Major contributors mentioned in releases
- **Issue/PR labels**: Special labels for different contribution types

#### **Community Recognition**
- **Discord roles**: Special roles for active contributors
- **Newsletter mentions**: Featured in our community newsletter
- **Conference opportunities**: Speaking opportunities at events

#### **Swag and Rewards**
- **Stickers and swag**: Physical rewards for significant contributions
- **Early access**: Beta access to new features
- **Mentorship**: Opportunities to mentor new contributors

### 📊 **Contribution Levels**

#### **🥉 Bronze Contributors**
- First-time contributors
- Bug reports and small fixes
- Documentation improvements

#### **🥈 Silver Contributors**
- Regular contributors
- Feature implementations
- Code reviews and mentoring

#### **🥇 Gold Contributors**
- Core team members
- Major feature development
- Project leadership and direction

---

## 📞 Getting Help

### 💬 **Community Support**

- **Discord**: Join our [Discord server](https://discord.gg/agenticrag) for real-time chat
- **GitHub Discussions**: Use for questions and feature discussions
- **Stack Overflow**: Tag questions with `agenticrag`

### 📧 **Direct Contact**

- **General questions**: community@agenticrag.com
- **Security issues**: security@agenticrag.com
- **Partnership inquiries**: partnerships@agenticrag.com

### 📚 **Resources**

- **Documentation**: [docs.agenticrag.com](https://docs.agenticrag.com)
- **API Reference**: [api.agenticrag.com](https://api.agenticrag.com)
- **Examples**: [examples.agenticrag.com](https://examples.agenticrag.com)
- **Blog**: [blog.agenticrag.com](https://blog.agenticrag.com)

---

## 📄 License

By contributing to AgenticRAG, you agree that your contributions will be licensed under the [MIT License](../LICENSE).

---

<div align="center">

### 🙏 Thank You!

**Your contributions make AgenticRAG better for everyone.**

**Happy coding! 🚀**

[⬆ Back to Top](#-contributing-to-agenticrag)

</div>