# 🧙‍♂️ Ultimate Git Master Guide: Branching, Backups, Setups & Sanity Moves

---

## 🗂️ Section 1: Project Setup & First Commit

```bash
# Navigate to your project directory (change "your_project_directory" to your actual folder path)
cd "your_project_directory"

# Initialize Git (if not already initialized)
git init

# Assign the remote repository
git remote add origin https://github.com/victorliquiddata/jec_system.git
```

```bash
# Add all files to staging
git add .

# Commit the changes with a message
git commit -m "tests db,auth, main: ok >> proceed to implementation of next big mod "

# Ensure you're on the main branch
git branch -M main

# Push the code to the remote repository
git push -u origin main
```

> 🔁 *Note: `git init` is used twice (intentionally left in for completeness — can be deduplicated if needed)*

---

## 🌿 Section 2: Branching Away Safely (The Real Workhorse 🐎)

### 🎯 Goal:
Start a new idea or refactor without accidentally messing up `main`.

```bash
# Start from main branch
git checkout main
git pull origin main
git status
```

```bash
# Create and switch to a new branch
git checkout -b new-branch-name
```

```bash
# Make your changes, then stage and commit
git add .
git commit -m "starting something different, more robust and appealing from database and auth only"
```

```bash
# Triple check you're NOT on main
git branch --show-current  # → should say 'new-branch-name'
```

```bash
# Push your new branch and set it to track remote
git push -u origin $(git branch --show-current)

# From now on, just use:
git push
```

🧠 Pro Tips:
- Use descriptive branch names like `feature-auth-revamp`, `hotfix-login`, etc.
- Set up GitHub branch protection rules for `main`

---

## 🧯 Section 3: Hard Resets & Rollbacks

### 🧱 Reset to Current Branch HEAD
```bash
git reset --hard HEAD
```

### 🔙 Reset to Specific Commit Hash
```bash
git reset --hard <commit-hash>
```

### 📦 Reset to Remote Branch (like main)
```bash
git reset --hard origin/main
```

> ⚠️ Warning: This **erases local changes**, use with care.

---

## 💾 Section 4: Export Code From Specific Commits

Extracting specific versions of files:

```bash
git show d10078ddf2f0fb6f4ddad241c9bb8d0a5b3e139f:main.py > exported_code.py
git show d10078ddf2f0fb6f4ddad241c9bb8d0a5b3e139f:database.py >> exported_code.py
git show d10078ddf2f0fb6f4ddad241c9bb8d0a5b3e139f:config.py >> exported_code.py
git show d10078ddf2f0fb6f4ddad241c9bb8d0a5b3e139f:commands.py >> exported_code.py
git show d10078ddf2f0fb6f4ddad241c9bb8d0a5b3e139f:auth.py >> exported_code.py
```

> 🔁 *Note: This could also be added as a custom script if you're doing frequent snapshots.*

---

## 🧠 Bonus: Example Full Session (Recap Style)

```bash
cd path\to\your\repository
git checkout main
git pull
git checkout -b refactor-db
# Make changes
git add .
git commit -m "refactor: improve db structure"
git branch --show-current
git push -u origin $(git branch --show-current)
```

---

## 🏁 Final Thoughts

This guide is:
- Full stack safe (init, commit, push)
- Branching-proof (no more oops on `main`)
- Recovery-ready (resets + exports)
- Reusable for your future projects or teammates

---
