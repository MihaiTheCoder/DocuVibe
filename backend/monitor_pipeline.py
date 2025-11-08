"""
Pipeline Monitoring Dashboard
Displays real-time status of GitHub issues and their lifecycle
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from sqlalchemy import create_engine, text
from app.models.github_integration import IssueStatus, IssueDifficulty


def clear_screen():
    """Clear terminal screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def get_issues_status():
    """Get current status of all GitHub issues"""
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    id,
                    issue_number,
                    issue_title,
                    difficulty,
                    status,
                    pr_number,
                    pr_url,
                    auto_merge_enabled,
                    created_at,
                    pr_created_at,
                    merged_at
                FROM github_issues
                ORDER BY created_at DESC
                LIMIT 20
            """))

            issues = []
            for row in result:
                issues.append({
                    'id': str(row[0]),
                    'issue_number': row[1],
                    'issue_title': row[2],
                    'difficulty': row[3],
                    'status': row[4],
                    'pr_number': row[5],
                    'pr_url': row[6],
                    'auto_merge_enabled': row[7],
                    'created_at': row[8],
                    'pr_created_at': row[9],
                    'merged_at': row[10]
                })

            return issues

    finally:
        engine.dispose()


def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "N/A"

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt

    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())}s ago"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)}m ago"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)}h ago"
    else:
        return f"{int(diff.total_seconds() / 86400)}d ago"


def get_status_emoji(status):
    """Get emoji for status"""
    status_map = {
        'created': '[NEW]',
        'ready': '[READY]',
        'in_progress': '[WORK]',
        'pr_created': '[PR]',
        'testing': '[TEST]',
        'merged': '[DONE]',
        'closed': '[CLOSED]'
    }
    return status_map.get(status, f'[{status}]')


def get_difficulty_color(difficulty):
    """Get difficulty indicator"""
    if difficulty == 'easy':
        return '[EASY]'
    elif difficulty == 'medium':
        return '[MED]'
    elif difficulty == 'hard':
        return '[HARD]'
    return f'[{difficulty}]'


def display_dashboard(issues, watch_mode=False):
    """Display issues dashboard"""

    if watch_mode:
        clear_screen()

    print("="*80)
    print(" "*20 + "VIBEDOCS PIPELINE MONITOR")
    print("="*80)
    print()

    if not issues:
        print("[INFO] No GitHub issues found in database")
        print()
        print("Create issues via:")
        print("  1. Chat UI API: POST /api/v1/chat/message")
        print("  2. Test script: python test_e2e_pipeline.py")
        return

    print(f"Monitoring {len(issues)} recent issues")
    print(f"Repository: {settings.GITHUB_REPO}")
    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Summary stats
    by_status = {}
    by_difficulty = {}

    for issue in issues:
        status = issue['status']
        difficulty = issue['difficulty']

        by_status[status] = by_status.get(status, 0) + 1
        by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1

    print("STATUS SUMMARY:")
    for status, count in sorted(by_status.items()):
        print(f"  {get_status_emoji(status)} {status}: {count}")

    print()
    print("DIFFICULTY BREAKDOWN:")
    for difficulty, count in sorted(by_difficulty.items()):
        print(f"  {get_difficulty_color(difficulty)} {difficulty}: {count}")

    print()
    print("-"*80)
    print()

    # Issue details
    for issue in issues:
        status_indicator = get_status_emoji(issue['status'])
        diff_indicator = get_difficulty_color(issue['difficulty'])

        print(f"{status_indicator} {diff_indicator} Issue #{issue['issue_number']}")
        print(f"  {issue['issue_title'][:70]}")
        print(f"  Created: {format_datetime(issue['created_at'])}")

        if issue['pr_number']:
            print(f"  PR: #{issue['pr_number']} (created {format_datetime(issue['pr_created_at'])})")

        if issue['auto_merge_enabled']:
            print(f"  Auto-merge: ENABLED")

        if issue['merged_at']:
            print(f"  Merged: {format_datetime(issue['merged_at'])}")

        print()

    print("-"*80)
    print()

    if watch_mode:
        print("Press Ctrl+C to exit watch mode")


def watch_mode(interval=10):
    """Watch mode - refresh every interval seconds"""
    print("Starting watch mode (refreshing every {} seconds)...".format(interval))
    print("Press Ctrl+C to exit")
    print()

    try:
        while True:
            issues = get_issues_status()
            display_dashboard(issues, watch_mode=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nExiting watch mode...")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor VibeDocs pipeline')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch mode (auto-refresh)')
    parser.add_argument('--interval', '-i', type=int, default=10, help='Refresh interval in seconds (default: 10)')

    args = parser.parse_args()

    if args.watch:
        watch_mode(args.interval)
    else:
        issues = get_issues_status()
        display_dashboard(issues)


if __name__ == "__main__":
    main()
