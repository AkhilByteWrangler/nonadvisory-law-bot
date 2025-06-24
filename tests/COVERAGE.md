# Coverage Suite Instructions

## Running Tests with Coverage

1. Install dependencies:

   ```bash
   pip install pytest pytest-cov fastapi
   ```
2. Run all tests with coverage:

   ```bash
   pytest --cov=../backend --cov-report=term --cov-report=html
   ```

   - To view the HTML report, open `coverage_html_report/index.html` in your browser.
