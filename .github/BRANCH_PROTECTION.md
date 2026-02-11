# GitHub Branch Protection Setup Guide

This document provides step-by-step instructions for configuring GitHub branch protection rules for the Boardroom project.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step-by-Step Setup](#step-by-step-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Emergency Hotfix Procedure](#emergency-hotfix-procedure)

---

## Overview

### Why Branch Protection?

Branch protection ensures code quality by enforcing a review-based workflow. It prevents accidental commits directly to `main` and ensures all changes go through pull requests with proper review and automated checks.

### Two-Layer Protection Strategy

**Layer 1 - Local Pre-Push Hook:**
- Blocks `git push origin main` locally
- Provides immediate feedback (<1 second)
- Can be bypassed with `--no-verify` (not recommended)

**Layer 2 - GitHub Branch Protection (This Guide):**
- Enforced on GitHub server (cannot be bypassed)
- Requires pull request to merge into main
- Requires code review approval
- Requires all CI checks to pass

### What Happens When Rules Are Violated?

**Local Attempt:**
```bash
$ git push origin main
╔═══════════════════════════════════════════════════════════╗
║  BLOCKED: Direct push to 'main' branch not allowed       ║
╠═══════════════════════════════════════════════════════════╣
║  Required workflow:                                        ║
║  1. Create feature branch: git checkout -b feat/my-feature║
║  2. Push to feature branch: git push origin feat/my-feature║
║  3. Open PR on GitHub                                      ║
╚═══════════════════════════════════════════════════════════╝
```

**GitHub Attempt (if local hook bypassed):**
```
remote: error: GH006: Protected branch update failed
remote: error: Required status checks must pass before merging
```

---

## Prerequisites

Before configuring branch protection, ensure:

- ✅ You have **Admin access** to the repository on GitHub
- ✅ The **PR Checks workflow** is active (`.github/workflows/pr-checks.yml`)
- ✅ At least one PR has been opened to verify workflow runs correctly
- ✅ **CODEOWNERS file** exists (`.github/CODEOWNERS`)

**To verify workflow is active:**
1. Go to repository on GitHub
2. Click "Actions" tab
3. Verify "PR Checks" workflow appears in the list
4. Optional: Open a test PR to see checks run

---

## Step-by-Step Setup

### Step 1: Navigate to Branch Protection Settings

1. Go to your repository on GitHub: https://github.com/ofircohen205/boardroom
2. Click **Settings** (tab at the top)
3. In the left sidebar, click **Branches** (under "Code and automation")

### Step 2: Add Branch Protection Rule

1. Click **Add rule** button (or **Add branch protection rule**)
2. In the "Branch name pattern" field, enter: `main`

### Step 3: Configure Protection Rules

Enable the following settings (in order):

#### Protect Matching Branches

- ✅ **Require a pull request before merging**
  - ✅ **Require approvals:** Set to `1`
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
  - ✅ **Require review from Code Owners**
  - ❌ Do not check "Require approval of the most recent reviewable push"
  - ❌ Do not check "Require conversation resolution before merging"

#### Status Checks

- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - In the search box, add these status checks:
    - `Backend Linting` (from pr-checks.yml)
    - `Backend Tests` (from pr-checks.yml)
    - `Frontend Linting` (from pr-checks.yml)
    - `Detect Secrets` (from pr-checks.yml)

  **Note:** Status checks only appear in the list after they've run at least once. If you don't see them:
  1. Open a test PR first
  2. Wait for checks to run
  3. Return to branch protection settings
  4. Search for the check names above

#### Additional Settings

- ✅ **Require linear history** (enforces squash or rebase merge)
- ✅ **Do not allow bypassing the above settings**
- ❌ **Do not** check "Allow force pushes"
- ❌ **Do not** check "Allow deletions"

#### Rules Applied to Administrators

- ❌ **Do not** check "Include administrators"
  - This allows admins to perform emergency hotfixes
  - Admins should still follow the PR workflow in normal circumstances

### Step 4: Save Changes

1. Scroll to the bottom
2. Click **Create** (or **Save changes** if editing existing rule)

---

## Verification

After configuring branch protection, verify it works correctly:

### Test 1: Direct Push Blocked (Local)

```bash
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "test: verify protection"
git push origin main
```

**Expected Result:**
```
╔═══════════════════════════════════════════════════════════╗
║  BLOCKED: Direct push to 'main' branch not allowed       ║
╚═══════════════════════════════════════════════════════════╝
```

Clean up:
```bash
git reset --hard HEAD~1
```

### Test 2: Direct Push Blocked (GitHub - if local hook bypassed)

```bash
git push --no-verify origin main
```

**Expected Result:**
```
remote: error: GH006: Protected branch update failed
remote: error: At least 1 approving review is required
```

Clean up:
```bash
git reset --hard HEAD~1
```

### Test 3: Feature Branch Allowed

```bash
git checkout -b feat/test-protection
echo "test" >> README.md
git add README.md
git commit -m "test: verify feature branch works"
git push origin feat/test-protection
```

**Expected Result:** Push succeeds

Clean up:
```bash
git push origin -d feat/test-protection
git checkout main
git branch -D feat/test-protection
```

### Test 4: PR Requires Approval

1. Create a test PR from a feature branch
2. Try to click "Merge pull request" button
3. **Expected Result:** Button is disabled with message:
   ```
   Merging is blocked
   Requires 1 approving review
   ```

### Test 5: PR Requires Passing Checks

1. Create a PR with intentionally failing tests
2. **Expected Result:** Merge button shows:
   ```
   Merging is blocked
   Required status checks must pass
   ```
3. Fix the tests, push again
4. **Expected Result:** Merge button becomes available after checks pass

### Test 6: Cannot Commit Directly via GitHub UI

1. Go to any file on GitHub (on main branch)
2. Click "Edit this file" (pencil icon)
3. **Expected Result:** You can edit but when you try to commit:
   - "Commit directly to the main branch" option is grayed out
   - "Create a new branch for this commit and start a pull request" is selected

---

## Troubleshooting

### Problem: Status checks don't appear in the list

**Cause:** Status checks only appear after they've run at least once.

**Solution:**
1. Create a test PR
2. Wait for the PR Checks workflow to run
3. Go back to branch protection settings
4. The checks should now appear in the search box

### Problem: Cannot find branch protection settings

**Cause:** You may not have admin access to the repository.

**Solution:**
1. Ask the repository owner (@ofircohen205) to grant you admin access
2. Or ask them to configure branch protection following this guide

### Problem: Merge button says "Review required" but no reviewers are available

**Cause:** CODEOWNERS requires approval from specific users.

**Solution:**
1. Add yourself to `.github/CODEOWNERS` if you're a maintainer
2. Or ask @ofircohen205 to review the PR

### Problem: Want to check if protection is active

**Check via GitHub UI:**
1. Go to Settings > Branches
2. Look for "Branch protection rules" section
3. You should see `main` listed with rules applied

**Check via API:**
```bash
gh api repos/ofircohen205/boardroom/branches/main/protection
```

### Problem: Status checks are failing but you want to merge anyway

**Wrong Solution:** Disable branch protection ❌

**Right Solution:**
1. Investigate why checks are failing
2. Fix the failing tests/lints
3. Push the fix
4. Wait for checks to pass
5. Then merge

**If checks are broken (not your code):**
1. Fix the CI/CD workflow
2. Or temporarily disable that specific check in branch protection
3. Merge your PR
4. Re-enable the check after fixing workflow

---

## Emergency Hotfix Procedure

### When to Use Emergency Procedures

Only in these scenarios:
- Production is down and you need to deploy a critical fix immediately
- Security vulnerability requires immediate patching
- Data loss is occurring and needs immediate intervention

**Do NOT use for:**
- "I don't want to wait for code review" ❌
- "The tests are failing but I think it's fine" ❌
- "I'm in a hurry" ❌

### Procedure 1: Hotfix Branch (Preferred)

This still follows the PR workflow but expedites it:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-<issue>

# 2. Make the fix
# ... edit files ...
git add .
git commit -m "hotfix: critical fix for <issue>"

# 3. Push to hotfix branch
git push origin hotfix/critical-<issue>

# 4. Open emergency PR
gh pr create \
  --title "HOTFIX: Critical fix for <issue>" \
  --body "Production emergency - requires immediate merge" \
  --label "hotfix" \
  --reviewer ofircohen205

# 5. Request immediate review (via Slack/email/phone)
# 6. Once approved and checks pass, merge via GitHub
# 7. Deploy to production
```

### Procedure 2: Bypass Local Hook (Still Subject to GitHub Protection)

```bash
git push --no-verify origin main
```

**Result:** Local hook is bypassed, but GitHub protection still blocks the push:
```
remote: error: GH006: Protected branch update failed
remote: error: At least 1 approving review is required
```

This only works if you're an admin with "Include administrators" disabled.

### Procedure 3: Temporarily Disable Protection (Admin Only - Last Resort)

⚠️ **Use only in extreme emergencies** ⚠️

**Steps:**
1. Go to Settings > Branches
2. Click "Edit" on the `main` branch rule
3. Scroll to bottom and click **"Delete rule"** or uncheck rules temporarily
4. Make your emergency push:
   ```bash
   git push --no-verify origin main
   ```
5. **Immediately re-enable protection** by following the setup steps again

**Better Alternative:** Use Procedure 1 (hotfix branch) instead.

### Post-Emergency Actions

After using emergency procedures:

1. **Create a post-mortem document** explaining:
   - What went wrong
   - Why emergency bypass was necessary
   - How to prevent it in the future

2. **Open a follow-up PR** if you disabled protection:
   - Re-enable branch protection
   - Explain what happened in PR description
   - Get retroactive code review

3. **Update runbooks** if this reveals a gap in deployment processes

---

## Summary

### What You Should See After Setup

✅ Main branch shows "Protected" badge on GitHub
✅ Direct pushes to main are blocked locally
✅ Direct pushes to main are blocked on GitHub
✅ PRs require 1 approval from CODEOWNERS
✅ PRs require all CI checks to pass
✅ Merge button enforces squash or rebase merge only

### Required Developer Workflow

```bash
# Create feature branch
git checkout -b feat/my-feature

# Make changes
git add .
git commit -m "feat: add new feature"

# Push to feature branch
git push origin feat/my-feature

# Open PR
gh pr create

# Wait for:
# 1. All CI checks to pass ✓
# 2. Code review approval ✓
# 3. Merge via GitHub UI
```

### Emergency Contact

If you have questions about branch protection or need help with an emergency situation:

- **Repository Owner:** @ofircohen205
- **GitHub Docs:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

---

**Last Updated:** 2026-02-11
**Maintained By:** @ofircohen205
