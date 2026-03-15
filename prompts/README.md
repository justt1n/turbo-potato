# Prompts

Edit prompts here first.

Current prompt files:

- `chat_parser.default.txt`
- `daily_report.default.txt`
- `monthly_report.default.txt`

Prompt workflow:

- point config to a prompt file with `prompt_file`
- edit the `.txt` file directly when you want to change prompt behavior
- if both inline prompt text and a prompt file are set, the file wins

Recommended setup:

- keep prompt text out of `config/local.yaml`
- use:
  - `ai.prompt_file`
  - `ai.daily_report_prompt_file`
  - `ai.monthly_report_prompt_file`
