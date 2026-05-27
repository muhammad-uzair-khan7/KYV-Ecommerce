# Before & After Code Examples

## Problem 1: Direct Dictionary Access

### ❌ BEFORE (Would Crash)
```python
# risk_scoring.py line 103
def risk_scoring_node(state: AssessmentGraphState) -> dict:
    vendor_id = state["vendor_id"]  # ← KeyError if key missing!
    vendor_type = state.get("vendor_type", "default")
```

**Error Scenario:**
- If `vendor_id` not in state dict
- Raises: `KeyError: 'vendor_id'`
- Results in: 500 Internal Server Error

### ✅ AFTER (Safe)
```python
def risk_scoring_node(state: AssessmentGraphState) -> dict:
    vendor_id = state.get("vendor_id", "UNKNOWN")  # ← Safe with fallback
    vendor_type = state.get("vendor_type", "default")
```

**Why It Works:**
- Returns "UNKNOWN" if key missing
- No exception thrown
- Workflow continues with safe default

---

## Problem 2: Unsafe List Comprehension

### ❌ BEFORE (Would Crash)
```python
# risk_scoring.py line 48-51
flags = state.get("watchlist_flags", [])

if any(f.get("is_sanctioned") for f in flags):  # ← NoneType error!
    compliance = 100
elif any(f.get("is_pep") for f in flags):
    compliance = 65
```

**Error Scenario:**
- If flags list contains None: `[None, {...}]`
- Trying to call `.get()` on None
- Raises: `AttributeError: 'NoneType' object has no attribute 'get'`

### ✅ AFTER (Safe)
```python
flags = state.get("watchlist_flags", []) or []

if any(f.get("is_sanctioned") for f in flags if f is not None):  # ← Checks None
    compliance = 100
elif any(f.get("is_pep") for f in flags if f is not None):
    compliance = 65
```

**Why It Works:**
- `or []` ensures list, not None
- `if f is not None` filters out None items
- Only calls `.get()` on valid dicts

---

## Problem 3: Unvalidated Nested Access

### ❌ BEFORE (Would Crash)
```python
# risk_scoring.py line 59-66
if contracts:  # ← What if contracts = [None]?
    analysis = contracts[0].get("clause_analysis", {})  # ← Crashes!
    if not analysis.get("data_processing_agreement"):
        cyber += 30
```

**Error Scenario:**
- If `contracts = [None]` or `contracts = []`
- Accessing `contracts[0]` on empty list: `IndexError`
- Accessing `.get()` on None: `AttributeError`

### ✅ AFTER (Safe)
```python
if contracts and len(contracts) > 0:  # ← Validate length
    contract = contracts[0]            # ← Validate not None
    if contract is not None:            # ← Double check
        analysis = contract.get("clause_analysis", {}) or {}  # ← Fallback
        if not analysis.get("data_processing_agreement"):
            cyber += 30
```

**Why It Works:**
- `contracts` check ensures it's truthy
- `len(contracts) > 0` ensures it's not empty
- `contract is not None` ensures first element is valid
- `.get(...) or {}` ensures dict, not None

---

## Problem 4: Lost State in Return Values

### ❌ BEFORE (State Lost)
```python
# risk_scoring.py line 133-140 (OLD)
return {
    "computed_risk_vector": risk_vector,
    "messages": [AIMessage(content=f"Risk scoring complete...")]
    # ← vendor_id, tenant_id NOT forwarded!
}
```

**Error Scenario:**
- Next node tries to access `state["vendor_id"]`
- It was lost in previous node's return
- Causes: `KeyError: 'vendor_id'`

### ✅ AFTER (State Preserved)
```python
return {
    "computed_risk_vector": risk_vector,
    "messages": [AIMessage(content=f"Risk scoring complete...")],
    "vendor_id": vendor_id,           # ← Forwarded!
    "vendor_type": vendor_type        # ← Forwarded!
}
```

**Why It Works:**
- All nodes return required state properties
- LangGraph merges return dict into state
- Downstream nodes have complete context

---

## Problem 5: Dangerous Contract Access

### ❌ BEFORE (Would Crash)
```python
# human_review.py line 133 (OLD)
"contract_risk": contracts[0].get("clause_analysis", {}).get("overall_contract_risk") 
                 if contracts else None
# Problem: What if contracts = [None]?
```

**Error Scenario:**
- If `contracts = [None]`
- Condition passes: `if contracts` is True
- But `contracts[0]` is None
- Calling `.get()` on None crashes

### ✅ AFTER (Safe)
```python
# human_review.py line 133 (NEW)
"contract_risk": contracts[0].get("clause_analysis", {}).get("overall_contract_risk") 
                 if contracts and len(contracts) > 0 and contracts[0] is not None 
                 else None
```

**Why It Works:**
- `contracts` - checks it's truthy
- `len(contracts) > 0` - checks not empty list
- `contracts[0] is not None` - checks first item is valid
- Only then accesses the nested properties

---

## Problem 6: Unsafe State in Node Entry

### ❌ BEFORE (Would Crash)
```python
# kyb_screening.py line 9-11 (OLD)
async def kyb_sreening_node(state:AssessmentGraphState) -> dict:
    company_name = state["company_name"]   # ← Direct access
    country_iso = state["country_iso"]     # ← Direct access
    vendor_id = state["vendor_id"]         # ← Direct access
```

### ✅ AFTER (Safe)
```python
async def kyb_sreening_node(state:AssessmentGraphState) -> dict:
    if state is None:
        state = {}
    
    company_name = state.get("company_name", "Unknown Vendor")  # ← Safe
    country_iso = state.get("country_iso", "")                   # ← Safe
    vendor_id = state.get("vendor_id", "UNKNOWN")               # ← Safe
```

---

## Summary Pattern

### ❌ UNSAFE
```python
# Direct access
value = state["key"]
nested = dict[0]["property"]
item.method() if list
```

### ✅ SAFE
```python
# Safe access
value = state.get("key", default)
if dict and len(dict) > 0 and dict[0] is not None:
    nested = dict[0].get("property", {}) or {}
if list and len(list) > 0:
    for item in list:
        if item is not None:
            item.method()
```

---

## Testing These Fixes

```python
# Test Case: Minimal data
test_state = {
    "company_name": "Test Corp"
    # Missing: vendor_id, country_iso, etc.
}

# BEFORE: Would crash immediately
# AFTER: Uses fallback defaults, continues successfully

result = await kyb_sreening_node(test_state)
print(result)  # ✅ Works perfectly!
```

---

## Key Lessons

1. **Always validate before subscripting**: `if list and len(list) > 0 and list[0] is not None`
2. **Use .get() with defaults**: `state.get("key", default_value)`
3. **Check for None in loops**: `for item in list if item is not None`
4. **Forward state in returns**: Always include critical properties
5. **Add fallback operators**: `value or default` for additional safety
6. **Validate at entry points**: Check state immediately in each node
