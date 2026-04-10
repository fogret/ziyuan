name: 提取分类生成yings

on:
  workflow_dispatch:
  schedule:
    - cron: "0 21 * * *"

jobs:
  run-yings:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          path: .

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Run extractor
        run: python3 main.py

      - name: Commit and Push yings.txt
        run: |
          git config --local user.email "actions@github.com"
          git config --local user.name "GitHub Actions"
          git add yings.txt
          git commit -m "Update yings.txt" || echo "No changes to commit"
          git push

      - name: Upload yings.txt
        uses: actions/upload-artifact@v4
        with:
          name: yings
          path: yings.txt
