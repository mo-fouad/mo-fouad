# Profile page builder

Every section of the profile README is an SVG in `../page/`, in a light and a dark version. This script draws them all.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# refresh the contribution data
gh api graphql -f query='{ viewer { contributionsCollection { contributionCalendar {
  totalContributions weeks { contributionDays { contributionCount date contributionLevel } } } } } }' \
  > contributions.json

.venv/bin/python build_page.py ../page contributions.json
```

The fonts in `fonts/` (Newsreader, Hanken Grotesk, JetBrains Mono) are under the SIL Open Font License. The script embeds subsets of them in each SVG so every visitor sees the same typefaces.
