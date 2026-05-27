# KYV Project - NoneType Error Fixes

## Problem Summary
The system was throwing **"500 Internal Server Error: NoneType not subscriptable"** when evaluating vendors. This occurred because:
1. Dictionary keys were being accessed directly without null/None checks
2. List items could be None but were accessed without validation
3. State properties could be missing, causing KeyError crashes
4. Return values from nodes weren't forwarding necessary state properties

## Root Causes Identified

### 1. **Direct Dictionary Access Without .get()**
- **File**: `risk_scoring.py` line 103
- **Issue**: `vendor_id = state["vendor_id"]` crashes if key missing
- **Fix**: Changed to `vendor_id = state.get("vendor_id", "UNKNOWN")`

### 2. **Unsafe List/Dictionary Comprehensions**
- **File**: `risk_scoring.py` lines 48-50
- **Issue**: `any(f.get("is_sanctioned") for f in flags)` crashes if `f` is None
- **Fix**: Added None check: `any(f.get("is_sanctioned") for f in flags if f is not None)`

### 3. **Missing Null Validation on Nested Structures**
- **File**: `risk_scoring.py` lines 59-66, 73-80
- **Issue**: `contracts[0].get("clause_analysis", {})` crashes if `contracts[0]` is None
- **Fix**: Added validation:
  ```python
  if contracts and len(contracts) > 0:
      contract = contracts[0]
      if contract is not None:
          analysis = contract.get("clause_analysis", {}) or {}
  ```

### 4. **Incomplete State Forwarding**
- **Files**: Multiple node functions
- **Issue**: Nodes weren't returning all required state properties, causing downstream failures
- **Fix**: Ensured all nodes return necessary state keys:
  - `vendor_id`, `tenant_id`, `company_name`, `country_iso`

### 5. **kyb_screening.py - Direct State Access**
- **Lines**: 9-11
- **Issue**: Direct access to state dictionary keys without fallback
- **Fix**: Changed all to use `.get()` with defaults:
  ```python
  company_name = state.get("company_name", "Unknown Vendor")
  country_iso = state.get("country_iso", "")
  vendor_id = state.get("vendor_id", "UNKNOWN")
  ```

### 6. **human_review.py - Unsafe Contract Access**
- **Line**: 133
- **Issue**: `contracts[0].get(...)` without validating contracts or contracts[0]
- **Fix**: Added full validation chain
  ```python
  contract_risk: contracts[0].get("clause_analysis", {}).get("overall_contract_risk") 
                 if contracts and len(contracts) > 0 and contracts[0] is not None else None
  ```

## Files Modified

1. **risk_scoring.py**
   - Added None checks in `_derive_domain_scores()`
   - Added None checks in `_derive_mitigations()`
   - Changed direct access to `.get()` in `risk_scoring_node()`
   - Ensured state forwarding in return value

2. **kyb_screening.py**
   - Changed all direct state access to `.get()` with defaults
   - Added None check when iterating over results
   - Ensure all state properties forwarded in return

3. **orchestrator.py**
   - Added None check in `orchestration_supervisor()`
   - Changed direct state access to `.get()` in `routing_logic()`

4. **human_review.py**
   - Added validation for contracts[0] before accessing
   - Ensured state properties forwarded in return value

## Testing Recommendations

Before deploying, test with:

```python
# Test Case 1: Clean vendor (no flags)
POST /evaluate-vendor
{
    "company_name": "Acme Corp",
    "country_iso": "US"
}

# Test Case 2: Flagged vendor
POST /evaluate-vendor
{
    "company_name": "Suspicious Corp",
    "country_iso": "PK"
}

# Test Case 3: Blocked vendor
POST /evaluate-vendor
{
    "company_name": "Blacklisted Exports LLC",
    "country_iso": "IR"
}

# Test Case 4: Missing optional fields
POST /evaluate-vendor
{
    "company_name": "Partial Data Corp"
}
```

## Expected Behavior After Fixes

✅ No more "NoneType not subscriptable" errors
✅ Proper error handling with fallback defaults
✅ Full state propagation through graph nodes
✅ Clean API responses even with missing data
✅ Graceful degradation instead of crashes

## Key Improvements

1. **Defensive Programming**: All state access now has safety guards
2. **State Continuity**: Each node properly forwards all state properties
3. **Null Safety**: Added checks before any subscript operations
4. **Error Handling**: Graceful fallbacks instead of exceptions
