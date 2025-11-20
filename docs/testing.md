# Testing Guide

Deze gids legt uit hoe je tests kunt uitvoeren voor het AI Chat project.

## Inhoudsopgave
- [Installatie](#installatie)
- [Tests Uitvoeren](#tests-uitvoeren)
- [Test Categorieën](#test-categorieën)
- [Code Coverage](#code-coverage)
- [Tests Schrijven](#tests-schrijven)

## Installatie

### 1. Python Virtual Environment

Maak eerst een Python virtual environment aan en activeer deze:

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/MacOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Installeer Test Dependencies

Installeer alle development dependencies inclusief pytest:

```bash
pip install -r requirements-dev.txt
```

Dit installeert:
- `pytest` - Test framework
- `pytest-asyncio` - Voor async/await test support
- `pytest-cov` - Voor code coverage rapportage
- `ddt` - Data-driven testing support

## Tests Uitvoeren

### Alle Tests Uitvoeren

Voer alle tests uit met coverage rapportage:

```bash
pytest
```

### Specifieke Test Bestanden

Voer een specifiek test bestand uit:

```bash
pytest tests/test_search_index_manager.py
```

### Specifieke Test Functies

Voer een specifieke test functie uit:

```bash
pytest tests/test_search_index_manager.py::TestSearchIndexManager::test_index_exist_mock
```

### Verbose Output

Voor meer gedetailleerde output:

```bash
pytest -v
```

### Alleen Unit Tests (zonder live Azure connecties)

```bash
pytest -m "not live"
```

## Test Categorieën

De tests zijn gecategoriseerd met markers:

### Unit Tests
Tests die geen externe dependencies vereisen (mocks gebruiken):
```bash
pytest -m unit
```

### Integration Tests
Tests die mogelijk Azure services vereisen:
```bash
pytest -m integration
```

### Live Tests
Tests die echte Azure connecties vereisen (standaard overgeslagen):
```bash
pytest -m live
```

**Let op:** Live tests vereisen geldige Azure credentials en environment variabelen.

### Slow Tests
Tests die lang duren om uit te voeren:
```bash
pytest -m "not slow"  # Skip slow tests
```

## Code Coverage

### Coverage Rapport Genereren

Coverage wordt automatisch gegenereerd bij het uitvoeren van tests:

```bash
pytest
```

Dit genereert:
- Terminal output met coverage percentage
- HTML rapport in `htmlcov/index.html`
- XML rapport in `coverage.xml`

### Coverage Rapport Bekijken

Open het HTML coverage rapport:

```bash
# Windows
start htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# MacOS
open htmlcov/index.html
```

### Minimum Coverage Threshold

Om te falen als coverage onder een bepaald percentage komt:

```bash
pytest --cov-fail-under=80
```

## Tests Schrijven

### Basis Test Structuur

```python
import unittest
from unittest.mock import AsyncMock, Mock, patch

class TestMyComponent(unittest.IsolatedAsyncioTestCase):
    """Tests voor MyComponent."""

    def setUp(self):
        """Setup die voor elke test wordt uitgevoerd."""
        self.test_data = "example"

    async def test_async_function(self):
        """Test een async functie."""
        result = await my_async_function()
        self.assertTrue(result)

    def test_sync_function(self):
        """Test een synchrone functie."""
        result = my_sync_function()
        self.assertEqual(result, "expected")
```

### Mock Azure Services

```python
async def test_with_mock_azure_client(self):
    """Test met gemockte Azure client."""
    mock_client = AsyncMock()
    mock_client.some_method.return_value = {"result": "success"}

    with patch('module.AzureClient', return_value=mock_client):
        result = await function_using_azure()
        self.assertEqual(result["result"], "success")
```

### Data-Driven Tests

```python
from ddt import ddt, data, unpack

@ddt
class TestWithMultipleInputs(unittest.TestCase):

    @data(
        (2, 4, 6),
        (3, 5, 8),
        (10, 20, 30)
    )
    @unpack
    def test_addition(self, a, b, expected):
        """Test met verschillende input waarden."""
        result = a + b
        self.assertEqual(result, expected)
```

### Test Markers Toevoegen

Voeg markers toe aan je tests in `pytest.ini`:

```python
import pytest

@pytest.mark.unit
def test_simple_unit():
    """Een simpele unit test."""
    pass

@pytest.mark.integration
@pytest.mark.slow
async def test_integration_with_azure():
    """Een langzame integration test."""
    pass

@pytest.mark.live
@pytest.skip("Only for live tests")
async def test_live_azure_connection():
    """Test met echte Azure connectie."""
    pass
```

## Environment Variabelen voor Tests

Sommige tests vereisen environment variabelen:

```bash
# Required voor search tests
export SEARCH_ENDPOINT="https://your-search-service.search.windows.net"

# Voor live tests (optional)
export AZURE_AIPROJECT_CONNECTION_STRING="your-connection-string"
export AZURE_AI_CHAT_DEPLOYMENT_NAME="gpt-4o-mini"
export AZURE_AI_EMBED_DEPLOYMENT_NAME="text-embedding-3-small"
```

Je kunt ook een `.env.test` bestand maken in de project root.

## Continuous Integration

### GitHub Actions

Om tests te laten draaien in GitHub Actions, voeg een test job toe aan je workflow:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest -m "not live"
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

## Troubleshooting

### Import Errors

Als je import errors krijgt, zorg dat je in de project root bent:
```bash
cd /path/to/get-started-with-ai-chat
pytest
```

### Async Test Errors

Zorg dat `pytest-asyncio` is geïnstalleerd en dat async tests `async def` gebruiken.

### Azure Credential Errors

Voor tests zonder live Azure connecties, gebruik de marker:
```bash
pytest -m "not live"
```

## Best Practices

1. **Schrijf tests voor nieuwe features** - Alle nieuwe functionaliteit moet tests hebben
2. **Gebruik mocks voor externe services** - Unit tests moeten geen echte Azure services gebruiken
3. **Test edge cases** - Test niet alleen de happy path
4. **Houd tests snel** - Unit tests moeten snel zijn (<1 seconde)
5. **Gebruik duidelijke test namen** - Test namen moeten beschrijven wat ze testen
6. **Isoleer tests** - Elke test moet onafhankelijk kunnen draaien

## Meer Informatie

- [pytest documentatie](https://docs.pytest.org/)
- [pytest-asyncio documentatie](https://pytest-asyncio.readthedocs.io/)
- [Azure AI Testing Best Practices](https://learn.microsoft.com/azure/ai-services/testing-best-practices)
