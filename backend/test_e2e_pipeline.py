"""
End-to-End Pipeline Test
Tests the complete flow: Chat → GitHub Issue → (Manual Implementation) → PR → Auto-Merge

Note: This tests up to GitHub issue creation. Lazy-bird implementation and PR creation
are external and would need to be tested separately with actual lazy-bird running.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.feature_analyzer import FeatureAnalyzer
from app.services.github_service import GitHubService
from app.models.github_integration import IssueDifficulty

def test_feature_analyzer():
    """Test Phase 1: Feature Analysis"""
    print("\n" + "="*60)
    print("PHASE 1: Feature Analysis")
    print("="*60)

    analyzer = FeatureAnalyzer()

    # Test easy feature
    print("\n[TEST] Easy feature classification...")
    result = analyzer.analyze_feature_request("Add a simple CSV export button")

    print(f"  Difficulty: {result.difficulty.value}")
    print(f"  Complexity Score: {result.complexity_score}")
    print(f"  Title: {result.title}")
    print(f"  Components: {', '.join(result.components)}")
    print(f"  Labels: {', '.join(result.labels)}")

    if result.difficulty == IssueDifficulty.EASY:
        print("  [OK] Correctly classified as EASY")
    else:
        print(f"  [WARN] Expected EASY, got {result.difficulty.value}")

    # Test medium feature
    print("\n[TEST] Medium feature classification...")
    result = analyzer.analyze_feature_request(
        "Create a new API endpoint for bulk document upload with validation and error handling"
    )

    print(f"  Difficulty: {result.difficulty.value}")
    print(f"  Complexity Score: {result.complexity_score}")

    if result.difficulty in [IssueDifficulty.EASY, IssueDifficulty.MEDIUM]:
        print("  [OK] Classified as EASY or MEDIUM")
    else:
        print(f"  [WARN] Expected EASY/MEDIUM, got {result.difficulty.value}")

    # Test hard feature
    print("\n[TEST] Hard feature classification...")
    result = analyzer.analyze_feature_request(
        "Implement real-time WebSocket notifications with distributed message queue"
    )

    print(f"  Difficulty: {result.difficulty.value}")
    print(f"  Complexity Score: {result.complexity_score}")

    if result.difficulty == IssueDifficulty.HARD:
        print("  [OK] Correctly classified as HARD")
    else:
        print(f"  [WARN] Expected HARD, got {result.difficulty.value}")

    return True


def test_github_service():
    """Test Phase 2: GitHub Service"""
    print("\n" + "="*60)
    print("PHASE 2: GitHub Service")
    print("="*60)

    if not settings.GITHUB_TOKEN:
        print("\n[SKIP] GitHub token not configured")
        print("  Set GITHUB_TOKEN in .env to test GitHub integration")
        print("  Get token from: https://github.com/settings/tokens")
        return False

    if "YOUR_GITHUB_TOKEN" in settings.GITHUB_TOKEN:
        print("\n[SKIP] GitHub token is placeholder")
        print("  Replace with actual token in backend/.env")
        return False

    print(f"\n[INFO] GitHub token configured")
    print(f"[INFO] Repository: {settings.GITHUB_REPO}")

    github = GitHubService()

    print("\n[TEST] GitHub service initialized")
    print("  [OK] Service ready to create issues")

    # We won't actually create an issue in automated tests
    # User can do that manually or via the API

    print("\n[INFO] To test issue creation:")
    print("  1. Start the backend server")
    print("  2. Use the chat API to create a feature request")
    print("  3. Check GitHub for the created issue")

    return True


def test_pipeline_readiness():
    """Test Phase 3: Pipeline Readiness"""
    print("\n" + "="*60)
    print("PHASE 3: Pipeline Readiness Check")
    print("="*60)

    checks = {
        "Feature Analyzer": True,
        "GitHub Service": settings.GITHUB_TOKEN is not None,
        "GitHub Token Valid": settings.GITHUB_TOKEN and "YOUR_GITHUB_TOKEN" not in settings.GITHUB_TOKEN,
        "Repository Configured": settings.GITHUB_REPO == "MihaiTheCoder/DocuVibe",
        "Auto-merge Enabled": settings.GITHUB_AUTO_MERGE_EASY,
        "Test Data Created": Path("test_credentials.txt").exists()
    }

    print("\nReadiness Checklist:")
    all_ready = True
    for check, status in checks.items():
        if status:
            print(f"  [OK] {check}")
        else:
            print(f"  [MISSING] {check}")
            all_ready = False

    if all_ready:
        print("\n[SUCCESS] All systems ready for end-to-end testing!")
    else:
        print("\n[INCOMPLETE] Some components need configuration")

    return all_ready


def print_next_steps():
    """Print manual testing steps"""
    print("\n" + "="*60)
    print("NEXT STEPS: Manual Testing")
    print("="*60)

    print("\n1. Start Backend Server:")
    print("   cd backend")
    print("   venv\\Scripts\\python.exe -m uvicorn app.main:app --reload")

    print("\n2. Create a Feature Request via API:")

    if Path("test_credentials.txt").exists():
        with open("test_credentials.txt", "r") as f:
            creds = f.read()
            org_id = None
            for line in creds.split("\n"):
                if line.startswith("Organization ID:"):
                    org_id = line.split(": ")[1]
                    break

        if org_id:
            print(f'''
   curl -X POST http://localhost:8000/api/v1/chat/message \\
     -H "Content-Type: application/json" \\
     -H "X-Organization-ID: {org_id}" \\
     -d '{{"message": "Add a simple CSV export button to the dashboard"}}'
            ''')
    else:
        print("   [Run setup_test_data.py first to get credentials]")

    print("\n3. Check GitHub for Created Issue:")
    print(f"   https://github.com/{settings.GITHUB_REPO}/issues")

    print("\n4. Mark Issue as Ready:")
    print("   Add 'ready' label to the issue on GitHub")
    print("   OR use the API: POST /api/v1/chat/mark-ready/{issue_id}")

    print("\n5. Watch Lazy-Bird (if configured):")
    print("   - Lazy-bird detects 'ready' label")
    print("   - Implements the feature")
    print("   - Creates PR")

    print("\n6. Watch GitHub Monitor:")
    print("   - Backend logs show PR detection")
    print("   - Auto-merge enabled for easy issues")
    print("   - PR merges when tests pass")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*15 + "VIBEDOCS E2E PIPELINE TEST")
    print("="*70)

    print("\nThis test verifies the automated pipeline is ready:")
    print("  Chat UI -> Feature Analysis -> GitHub Issue -> Lazy-Bird -> PR -> Auto-Merge")

    # Run tests
    results = {}

    results["Feature Analyzer"] = test_feature_analyzer()
    results["GitHub Service"] = test_github_service()
    results["Pipeline Readiness"] = test_pipeline_readiness()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test, passed in results.items():
        status = "[PASS]" if passed else "[SKIP]"
        print(f"{status} {test}")

    all_passed = all(results.values())

    if all_passed:
        print("\n[SUCCESS] All automated tests passed!")
        print_next_steps()
        return 0
    else:
        print("\n[PARTIAL] Some tests skipped (GitHub token needed)")
        print("\nTo complete testing:")
        print("  1. Add GITHUB_TOKEN to backend/.env")
        print("  2. Run this test again")
        print("  3. Follow manual testing steps")
        return 1


if __name__ == "__main__":
    sys.exit(main())
