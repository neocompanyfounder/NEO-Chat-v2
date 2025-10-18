<!--
Sync Impact Report:
- Version: 0.0.0 → 1.0.0
- New constitution created with 6 core principles
- Added principles:
  * I. Docker Build from Source (NON-NEGOTIABLE)
  * II. MCP Query First (NON-NEGOTIABLE)
  * III. Test-First Development
  * IV. Integration Testing
  * V. Observability & Logging
  * VI. Simplicity & YAGNI
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check section references this file
  ✅ spec-template.md - Requirements align with principles
  ✅ tasks-template.md - Task categorization reflects principles
- Follow-up TODOs: None
-->

# NEO Chat v2 Constitution

## Core Principles

### I. Docker Build from Source (NON-NEGOTIABLE)

**Rule**: NEVER use pre-built Docker images from registries. ALWAYS clone the source repository from GitHub and build Docker containers from source code.

**Requirements**:
- All Docker deployments MUST start with `git clone` of the source repository
- Dockerfiles MUST be built locally using `docker build` from the cloned source
- Pre-built images from Docker Hub, GHCR, or other registries are FORBIDDEN
- Build process MUST be documented in deployment scripts
- Source commit SHA MUST be tracked for reproducibility

**Rationale**: Building from source ensures transparency, security auditability, and full control over the build process. It prevents supply chain attacks and allows customization of build parameters.

### II. MCP Query First (NON-NEGOTIABLE)

**Rule**: ALWAYS use the crawl4ai-rag MCP server to run knowledge queries BEFORE executing plan, task, implementation, or analyze workflows.

**Requirements**:
- Before `/speckit.plan`: Query MCP for relevant technical patterns, architecture decisions, and implementation examples
- Before `/speckit.tasks`: Query MCP for task breakdown strategies, dependency patterns, and similar feature implementations
- Before `/speckit.implement`: Query MCP for code examples, API usage patterns, and implementation best practices
- Before `/speckit.analyze`: Query MCP for analysis frameworks, quality metrics, and validation approaches
- MCP queries MUST use `mcp0_get_available_sources` first to discover available knowledge sources
- Query results MUST inform design decisions and be referenced in documentation

**Rationale**: Leveraging existing knowledge prevents reinventing solutions, ensures consistency with proven patterns, and accelerates development by learning from prior implementations.

### III. Test-First Development

**Rule**: Tests MUST be written and approved BEFORE implementation begins.

**Requirements**:
- Write test cases that define expected behavior
- Ensure tests FAIL initially (red phase)
- Implement code to make tests pass (green phase)
- Refactor while keeping tests green
- Tests are OPTIONAL per feature specification - only include when explicitly requested

**Rationale**: Test-first development ensures clear requirements understanding, prevents scope creep, and provides immediate feedback on implementation correctness.

### IV. Integration Testing

**Rule**: Critical integration points MUST have dedicated integration tests.

**Focus Areas**:
- New library contract tests
- Contract changes between services
- Inter-service communication
- Shared schemas and data contracts
- External API integrations
- Database migrations and data access patterns

**Rationale**: Integration tests catch issues at system boundaries where unit tests cannot, ensuring components work together correctly.

### V. Observability & Logging

**Rule**: All components MUST provide comprehensive logging and observability.

**Requirements**:
- Structured logging for all critical operations
- Error states MUST be logged with context
- Performance metrics for key operations
- Trace IDs for request correlation
- Log levels: DEBUG, INFO, WARN, ERROR, CRITICAL

**Rationale**: Observability enables rapid debugging, performance optimization, and production issue resolution.

### VI. Simplicity & YAGNI

**Rule**: Start with the simplest solution. Add complexity only when justified by concrete requirements.

**Requirements**:
- Prefer simple, direct implementations over abstract frameworks
- Avoid premature optimization
- Complexity MUST be justified in plan.md Complexity Tracking section
- Refactor when patterns emerge, not before
- "You Aren't Gonna Need It" - don't build for hypothetical future needs

**Rationale**: Simple code is easier to understand, maintain, and debug. Complexity should be earned through demonstrated need, not assumed upfront.

## Infrastructure & Deployment

### Docker & Container Strategy

- All containerized services MUST follow Principle I (Docker Build from Source)
- Deployment scripts MUST include:
  * Repository URL and commit SHA
  * Build commands with explicit parameters
  * Build verification steps
  * Rollback procedures
- Container images MUST be tagged with source commit SHA
- Build logs MUST be preserved for audit

### Knowledge Management

- All design workflows MUST follow Principle II (MCP Query First)
- MCP query results MUST be documented in relevant artifacts:
  * `research.md` for plan phase queries
  * `tasks.md` for task generation queries
  * Implementation files for code example queries
  * Analysis reports for analyze phase queries
- Knowledge sources MUST be cited with source URLs

## Development Workflow

### Pre-Implementation Checklist

1. **Specification Phase** (`/speckit.specify`):
   - Define user stories with priorities
   - Document acceptance criteria
   - Identify edge cases

2. **Planning Phase** (`/speckit.plan`):
   - **GATE**: Query MCP for relevant patterns (Principle II)
   - Pass Constitution Check (all principles)
   - Document technical context
   - Define project structure
   - Justify any complexity violations

3. **Task Generation** (`/speckit.tasks`):
   - **GATE**: Query MCP for task patterns (Principle II)
   - Organize by user story priority
   - Mark parallel opportunities
   - Define clear dependencies

4. **Implementation** (`/speckit.implement`):
   - **GATE**: Query MCP for code examples (Principle II)
   - Write tests first if requested (Principle III)
   - Implement incrementally by user story
   - Verify each story independently

5. **Analysis** (`/speckit.analyze`):
   - **GATE**: Query MCP for analysis frameworks (Principle II)
   - Cross-artifact consistency check
   - Quality validation
   - Constitution compliance verification

### Docker Deployment Workflow

For any Docker-based deployment:

```bash
# 1. Clone source repository
git clone <repo-url> <target-dir>
cd <target-dir>
git checkout <commit-sha>

# 2. Build from source
docker build -t <image-name>:<commit-sha> .

# 3. Verify build
docker inspect <image-name>:<commit-sha>

# 4. Deploy
docker run <image-name>:<commit-sha>
```

## Governance

### Amendment Process

- Constitution amendments require:
  * Clear justification for change
  * Impact analysis on existing workflows
  * Update to all dependent templates
  * Version bump following semantic versioning
  * Sync Impact Report documenting changes

### Compliance Verification

- All feature implementations MUST pass Constitution Check in plan.md
- Violations MUST be justified in Complexity Tracking section
- Unjustified violations block implementation
- Regular audits of existing code for compliance

### Versioning Policy

- **MAJOR**: Backward incompatible principle changes or removals
- **MINOR**: New principles added or material expansions
- **PATCH**: Clarifications, wording improvements, non-semantic changes

**Version**: 1.0.0 | **Ratified**: 2025-01-16 | **Last Amended**: 2025-01-16
