name: Update Subscribe

on:
  workflow_dispatch:
  schedule:
    - cron: "0 16 * * *"

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout current repo (紫苑)
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Run scan_forks.py (生成 projects.txt / urls.txt)
        env:
          YONU: ${{ secrets.YONU }}
        run: python scan_forks.py

      # ★ 你要求：紫苑仓库必须正常推送，不强推
      # ★ 我严格按你要求：只增加同步，不改其它逻辑
      - name: Commit generated files back to 紫苑
        run: |
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git config user.name "github-actions[bot]"

          # 先提交 → 工作区干净 → 才能 pull --rebase
          git add projects.txt urls.txt
          git commit -m "Update local projects.txt and urls.txt" || echo "No changes"

          # ★ 你要求：不能强推 → 必须同步远程
          git pull --rebase

          git push

      - name: Clone target repo (sourt)
        run: git clone https://github.com/fogret/sourt target_repo

      - name: Replace subscribe block cleanly
        run: |
          cd target_repo/config

          # 保留前 5 行
          head -n 5 subscribe.txt > new.txt

          # ★ 必须是北京时间
          echo "# 更新时间（北京时间）：$(date -u -d '+8 hour' '+%Y-%m-%d %H:%M:%S')" >> new.txt

          # 加入 urls.txt
          cat ../../urls.txt >> new.txt

          # ★ 必须加一个空行
          echo "" >> new.txt

          # 保留 WHITELIST 及以下
          awk 'NR>=6 && /^\[WHITELIST\]/ {start=1} start' subscribe.txt >> new.txt

          mv new.txt subscribe.txt

      - name: Commit & Push to sourt
        run: |
          cd target_repo
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git config user.name "github-actions[bot]"
          git add config/subscribe.txt
          git commit -m "Auto update subscribe" || echo "No changes"
          git push https://x-access-token:${{ secrets.YONU }}@github.com/fogret/sourt -f
