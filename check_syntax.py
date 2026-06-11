#!/usr/bin/env python3
import sys

files_to_check = [
    "orchestrator.py",
    "kyb_screening.py",
    "contract_analysis.py",
    "risk_scoring.py",
    "human_review.py",
    "state_container.py",
    "FRONTEND.py"
]

print("Checking Python syntax...")
errors = []

for fname in files_to_check:
    try:
        with open(fname) as f:
            compile(f.read(), fname, 'exec')
        print(f"✅ {fname}")
    except SyntaxError as e:
        print(f"❌ {fname}: {e}")
        errors.append((fname, str(e)))

if errors:
    print(f"\n❌ {len(errors)} file(s) with syntax errors!")
    sys.exit(1)
else:
    print(f"\n✅ All files are syntactically correct!")
    sys.exit(0)
