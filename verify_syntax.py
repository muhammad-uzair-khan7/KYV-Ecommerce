#!/usr/bin/env python3
"""Quick syntax verification for all modules"""

import sys
import py_compile

files = [
    "orchestrator.py",
    "kyb_screening.py",
    "contract_analysis.py",
    "risk_scoring.py",
    "human_review.py",
    "state_container.py",
    "FRONTEND.py"
]

errors = []
for file in files:
    try:
        py_compile.compile(file, doraise=True)
        print(f"✅ {file}: OK")
    except Exception as e:
        print(f"❌ {file}: {e}")
        errors.append((file, str(e)))

if errors:
    print(f"\n{len(errors)} file(s) have syntax errors!")
    sys.exit(1)
else:
    print(f"\n✅ All {len(files)} files are syntactically correct!")
    sys.exit(0)
