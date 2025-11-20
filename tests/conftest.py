"""
Pytest configuration and fixtures for tests.
"""
import os
import sys
import pytest

# Add the src directory to Python path so imports work correctly
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Make api modules importable directly by aliasing them
import importlib.util
api_path = os.path.join(src_path, 'api')

# Import api modules and make them available for direct import
api_modules = ['util', 'search_index_manager', 'routes', 'main']
for module_name in api_modules:
    module_file = os.path.join(api_path, f'{module_name}.py')
    if os.path.exists(module_file):
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            # Load dependencies first
            if module_name != 'util':
                try:
                    spec.loader.exec_module(module)
                except ImportError:
                    pass  # Will be loaded later

# Now properly load util first
try:
    from api import util
    sys.modules['util'] = util
    from api import search_index_manager
    sys.modules['search_index_manager'] = search_index_manager
except Exception as e:
    print(f"Warning: Could not pre-load modules: {e}")

# Set environment variable for tests
os.environ.setdefault('SEARCH_ENDPOINT', 'https://test.search.windows.net')


@pytest.fixture(scope="session")
def mock_search_endpoint():
    """Provide a mock search endpoint for tests."""
    return os.environ['SEARCH_ENDPOINT']
