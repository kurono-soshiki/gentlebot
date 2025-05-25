# Testing Guide

This document explains how to run and write tests for the Discord TTS Bot.

## Running Tests

### Prerequisites

- Python 3.12 or later
- Poetry

### Running All Tests

To run all tests, execute:

```bash
poetry run python src/test_runner.py
```

### Environment Variables for Testing

Tests that interact with external services (like Google's Gemini API) require API keys. For CI environments, these are provided as GitHub Secrets. For local development, you can set them in a `.env` file or directly in your environment.

Required environment variables for tests:
- `DISCORD_TOKEN`: Discord bot token
- `GEMINI_API_KEY`: Google Gemini API key

If these environment variables are not available, tests that require them will be skipped with an appropriate message.

## Writing Tests

### Test Organization

Tests are organized alongside their respective modules:

- `umigame/umigame_test.py`: Tests for the umigame module
- `yomiage/voicebox_test.py`: Tests for the voicebox module
- `yomiage/yomiage_test.py`: Tests for the yomiage module

### Testing Patterns

1. **Mocking External Dependencies**
   
   For functions that rely on external services or APIs, use the `unittest.mock` module to mock responses:

   ```python
   @patch('google.genai.Client')
   @patch('config.GEMINI_API_KEY', 'mock_api_key')
   def test_gemini_generate_mock(self, mock_client):
       # Test implementation
   ```

2. **Testing Async Functions**
   
   For async functions, use a test loop to execute the coroutines:

   ```python
   def setUp(self):
       # Create a new event loop for each test
       self.loop = asyncio.new_event_loop()
       asyncio.set_event_loop(self.loop)

   def tearDown(self):
       # Close the event loop after each test
       self.loop.close()
       
   def test_async_function(self):
       result = self.loop.run_until_complete(some_async_function())
   ```

3. **Skipping Tests**
   
   If a test requires specific environment variables, use conditional skipping:

   ```python
   @unittest.skipIf(not getattr(config, 'GEMINI_API_KEY', None), "GEMINI_API_KEY is not set")
   def test_gemini_generate_real_api(self):
       # Test implementation for real API call
   ```

## Continuous Integration

This project uses GitHub Actions for CI. The workflow is defined in `.github/workflows/tests.yml` and runs automatically on pushes to the main branch and on pull requests.