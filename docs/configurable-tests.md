# Configurable browser tests

The config-driven runner keeps pytest and Selenium as the execution engine while moving site-specific URLs, locators, actions, and expected results into JSON files under `configs/`.

## Run tests

```powershell
python -m pytest tests/config_driven/test_configured.py --webtest-config configs/saucedemo.json
```

Add `--headless` to force headless Chrome, or use `--webtest-url https://your-site.example` to override the configured base URL. A report is written to `reports/results.json` by default. Override its location with `--results-file`.

Start the local dashboard and open `http://127.0.0.1:5000` to run the API suite, WCAG accessibility suite, or a configured browser-test suite and follow its output. API tests require an internet connection. The results area starts empty on each server start and shows only results from a test run in that server session.

```powershell
python dashboard/app.py
```

## Configuration format

Each file has a `base_url`, optional browser settings, and one or more named test cases. Each case runs independently from the base URL. Supported actions are `click`, `type`, `clear`, `wait_visible`, `assert_visible`, `assert_not_visible`, `assert_text_contains`, `assert_count`, `assert_url_contains`, `assert_title_contains`, and `accept_alert` (wait for and accept a JavaScript alert).

Locator actions accept `by` and `value`. Supported locator strategies are `id`, `name`, `class_name`, `css_selector`, `xpath`, `tag_name`, `link_text`, and `partial_link_text`.

```json
{
  "name": "Example site",
  "base_url": "https://example.test",
  "browser": {
    "headless": true,
    "timeout_seconds": 5
  },
  "tests": [
    {
      "name": "Search returns results",
      "steps": [
        { "action": "type", "by": "name", "value": "q", "text": "Selenium" },
        { "action": "click", "by": "css_selector", "value": "button[type='submit']" },
        { "action": "assert_text_contains", "by": "id", "value": "results", "text": "Selenium" }
      ]
    }
  ]
}
```

Use `${ENVIRONMENT_VARIABLE}` in a `type` step to supply sensitive values at runtime; a missing variable fails the test with an explicit error. Never commit real credentials into configuration files.

The dashboard has separate options for API and accessibility suites. The API suite reads its URL, endpoints, credentials, timeouts, and expected responses from [`configs/api.json`](../configs/api.json); run it directly with `python -m pytest tests/api --api-config configs/api.json`. You can put `${ENVIRONMENT_VARIABLE}` in a credential value to avoid keeping a password in the JSON file. The WCAG suite reads its target URL, Axe tags, pages, login selectors, and expected violations from [`configs/accessibility.json`](../configs/accessibility.json). The Sauce Demo login and cart scenarios are in [`configs/saucedemo.json`](../configs/saucedemo.json).
