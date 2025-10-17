"""Test script to verify Phase 1 setup is complete and working."""

import os
import sys
from pathlib import Path


def test_project_structure():
    """Verify project directory structure exists."""
    base_dir = Path(__file__).parent.parent
    
    required_dirs = [
        "src",
        "src/api",
        "src/api/routes",
        "src/api/middleware",
        "src/agents",
        "src/services",
        "src/models",
        "src/db",
        "src/db/repositories",
        "src/db/migrations",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "tests/fixtures",
        "docker",
        "docker/supabase",
        "scripts",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
    
    assert not missing_dirs, f"Missing directories: {missing_dirs}"
    print("✓ Project structure verified")


def test_config_files():
    """Verify essential configuration files exist."""
    base_dir = Path(__file__).parent.parent
    
    required_files = [
        ".gitignore",
        ".env.example",
        "pyproject.toml",
        "pytest.ini",
        "README.md",
        "IMPLEMENTATION_STATUS.md",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    assert not missing_files, f"Missing files: {missing_files}"
    print("✓ Configuration files verified")


def test_docker_files():
    """Verify Docker configuration files exist."""
    base_dir = Path(__file__).parent.parent
    
    docker_files = [
        "docker/Dockerfile",
        "docker/docker-compose.yml",
        "docker/supabase/docker-compose.yml",
        "docker/supabase/.env.example",
    ]
    
    missing_files = []
    for file_path in docker_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    assert not missing_files, f"Missing Docker files: {missing_files}"
    print("✓ Docker files verified")


def test_scripts():
    """Verify deployment scripts exist."""
    base_dir = Path(__file__).parent.parent
    
    scripts = [
        "scripts/deploy.sh",
        "scripts/setup_supabase.sh",
        "scripts/run_migrations.sh",
    ]
    
    missing_scripts = []
    for script_path in scripts:
        full_path = base_dir / script_path
        if not full_path.exists():
            missing_scripts.append(script_path)
    
    assert not missing_scripts, f"Missing scripts: {missing_scripts}"
    print("✓ Scripts verified")


def test_source_files():
    """Verify essential source files exist."""
    base_dir = Path(__file__).parent.parent
    
    source_files = [
        "src/__init__.py",
        "src/utils/config.py",
        "src/utils/logger.py",
    ]
    
    missing_files = []
    for file_path in source_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    assert not missing_files, f"Missing source files: {missing_files}"
    print("✓ Source files verified")


def test_test_files():
    """Verify test infrastructure exists."""
    base_dir = Path(__file__).parent.parent
    
    test_files = [
        "tests/conftest.py",
        "tests/unit/test_utils/test_config.py",
        "tests/unit/test_utils/test_logger.py",
    ]
    
    missing_files = []
    for file_path in test_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    assert not missing_files, f"Missing test files: {missing_files}"
    print("✓ Test files verified")


def test_imports():
    """Verify core modules can be imported."""
    try:
        from src.utils import config
        print("✓ config module imports successfully")
    except ImportError as e:
        assert False, f"Failed to import config: {e}"
    
    try:
        from src.utils import logger
        print("✓ logger module imports successfully")
    except ImportError as e:
        assert False, f"Failed to import logger: {e}"


def test_pyproject_toml():
    """Verify pyproject.toml has required dependencies."""
    base_dir = Path(__file__).parent.parent
    pyproject_path = base_dir / "pyproject.toml"
    
    with open(pyproject_path) as f:
        content = f.read()
    
    required_deps = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "crewai",
        "google-generativeai",
        "supabase",
        "crawl4ai",
        "pytest",
    ]
    
    missing_deps = []
    for dep in required_deps:
        if dep not in content:
            missing_deps.append(dep)
    
    assert not missing_deps, f"Missing dependencies: {missing_deps}"
    print("✓ Dependencies verified in pyproject.toml")


def test_env_example():
    """Verify .env.example has required variables."""
    base_dir = Path(__file__).parent.parent
    env_path = base_dir / ".env.example"
    
    with open(env_path) as f:
        content = f.read()
    
    required_vars = [
        "EVOLUTION_API_URL",
        "EVOLUTION_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_MODEL",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "MAX_FILE_SIZE_MB",
        "GEMINI_RATE_LIMIT_PER_MIN",
        "VECTOR_SIMILARITY_THRESHOLD",
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    assert not missing_vars, f"Missing environment variables: {missing_vars}"
    print("✓ Environment variables verified")


def run_all_tests():
    """Run all setup verification tests."""
    print("\n" + "="*60)
    print("NEO Chat MVP - Phase 1 Setup Verification")
    print("="*60 + "\n")
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Configuration Files", test_config_files),
        ("Docker Files", test_docker_files),
        ("Scripts", test_scripts),
        ("Source Files", test_source_files),
        ("Test Files", test_test_files),
        ("Module Imports", test_imports),
        ("Dependencies", test_pyproject_toml),
        ("Environment Variables", test_env_example),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            print("-" * 40)
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    if failed == 0:
        print("✅ All Phase 1 setup tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e \".[dev]\"")
        print("2. Run unit tests: pytest tests/unit/")
        print("3. Continue with Phase 2 implementation")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
