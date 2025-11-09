# File Naming Conventions

| Element | Convention | Example | Notes |
|---------|-----------|---------|-------|
| Python modules | snake_case | `motion_detector.py` | Lowercase with underscores |
| Python classes | PascalCase | `MotionDetector`, `DatabaseManager` | One class per file (generally) |
| Test files | `test_*.py` | `test_motion_detector.py` | Prefix with `test_` for pytest discovery |
| JavaScript files | PascalCase (components), camelCase (services) | `EventCard.js`, `apiClient.js` | Components capitalized, utilities/services camelCase |
| Configuration | lowercase | `config.yaml` | No underscores or capitals |
| SQL migrations | `NNN_description.sql` | `001_initial.sql` | Three-digit version prefix |
| Scripts | snake_case.sh | `download_models.sh` | Bash scripts with `.sh` extension |

---
