name: Run scan_forks

on:
  workflow_dispatch:
  schedule:
    - cron: "0 */6 * * *"   # 每 6 小时运行一次，你可改成每天 4 点：0 20 * * *

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install requests

      - name: Run scan_forks.py
        run: |
          python scan_forks.py || true

      - name: Commit changes
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add .
          git commit -m "来自 scan_forks.py 的自动更新" || echo "No changes"

      - name: Force Push
        run: |
          git push -f
