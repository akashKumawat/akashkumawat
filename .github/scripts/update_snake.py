#!/usr/bin/env python3
"""
Generate a simple contribution-snake SVG and write to assets/contribution-snake.svg

This script queries GitHub GraphQL for a user's contribution calendar and renders
a compact snake-style visualization. It's intentionally lightweight and dependency-free
except for `requests` which the workflow installs.

Usage:
  python .github/scripts/update_snake.py --username <github-username>
"""
import os
import sys
import json
import math
import argparse
from textwrap import dedent

try:
    import requests
except Exception:
    print("Please install requests: pip install requests")
    sys.exit(1)


def fetch_contributions(username, token):
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': f'Bearer {token}'}
    query = '''
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    '''
    variables = {"login": username}
    r = requests.post(url, json={'query': query, 'variables': variables}, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def parse_calendar(data):
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    days = []
    for w in weeks:
        for d in w['contributionDays']:
            days.append(d['contributionCount'])
    return days


def generate_svg(counts, out_path):
    # Render a compact 7xN grid (columns = weeks)
    cols = math.ceil(len(counts) / 7)
    cell = 12
    gap = 4
    width = cols * (cell + gap) + 24
    height = 7 * (cell + gap) + 24

    maxc = max(counts) if counts else 1

    def color(v):
        if v == 0:
            return '#0f172a'
        # gradient from teal to purple based on normalized value
        t = min(1.0, v / maxc)
        # linear interpolate
        r1, g1, b1 = (6, 182, 212)
        r2, g2, b2 = (124, 58, 237)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f'rgb({r},{g},{b})'

    cells = []
    for i, v in enumerate(counts):
        col = i // 7
        row = i % 7
        x = 12 + col * (cell + gap)
        y = 12 + row * (cell + gap)
        cells.append((x, y, color(v)))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append('<rect width="100%" height="100%" rx="8" fill="#071029"/>')
    for x, y, c in cells:
        svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{c}" />')
    svg.append('</svg>')

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--username', required=True)
    args = p.parse_args(argv)

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('GITHUB_TOKEN is required in environment')
        sys.exit(1)

    try:
        data = fetch_contributions(args.username, token)
        counts = parse_calendar(data)
        out = os.path.join(os.getcwd(), 'assets', 'contribution-snake.svg')
        generate_svg(counts, out)
        print('Wrote', out)
    except Exception as e:
        print('Error while generating snake:', str(e))
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
