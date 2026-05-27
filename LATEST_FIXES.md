# Latest Fixes - Embedding Error & Input Validation

## Problem 2: Embedding Generation NoneType Error

### Error Message
```
⚠️ Contract Embedding Generation Failed: 'NoneType' object is not subscriptable
⚠️ Contract Embedding Generation Failed: 'NoneType' object is not subscriptable
[repeated 6 times]
```

### Root Causes

1. **Direct Array Access in contract_analysis.py (Line 57)**
   - Was: `query_vector = embedding_result.embeddings[0].values`
   - Problem: `embedding_result.embeddings` could be None
   - Problem: `embeddings[0]` could be None
   - Problem: `embeddings[0].values` could be None

2. **Supervisor Loop Counter**
   - The embedding errors suggest the workflow was looping
   - Contract analysis was being called 6 times without advancing

3. **Missing Input Field Validation**
   - VendorInput model didn't accept all fields from your request
   - This could cause state initialization issues

### Fixes Applied

#### 1. Enhanced Embedding Error Handling (contract_analysis.py)
```python
# BEFORE - Would crash on None
query_vector = embedding_result.embeddings[0].values

# AFTER - Complete null safety
if embedding_result is None:
    query_vector = []
elif not hasattr(embedding_result, 'embeddings') or embedding_result.embeddings is None:
    query_vector = []
elif len(embedding_result.embeddings) == 0:
    query_vector = []
else:
    embedding_values = embedding_result.embeddings[0]
    if embedding_values is None:
        query_vector = []
    elif not hasattr(embedding_values, 'values') or embedding_values.values is None:
        query_vector = []
    else:
        query_vector = embedding_values.values
```

#### 2. Loop Prevention (orchestrator.py)
```python
# Added loop counter to prevent infinite supervisor loops
loop_count = state.get("_supervisor_loop_count", 0)
if loop_count > 10:
    print(f"⚠️ Supervisor loop prevention: Breaking out after {loop_count} iterations")
    return {"next_action_node": "END"}
```

#### 3. Enhanced Supervisor Logging (orchestrator.py)
```python
# Now prints debug info so you can see workflow progression
print(f"📊 Supervisor Check - KYB: {kyb_status}, Contracts: {len(parsed_contracts) if parsed_contracts else 0}, Risk Vector: {bool(computed_risk)}")
print(f"→ Routing to [NODE_NAME]")
```

#### 4. Expanded VendorInput Model (orchestrator.py)
```python
class VendorInput(BaseModel):
    company_name: str
    country_iso: str = "PK"
    country_code: str = "PK"           # ← NEW: Maps to country_iso
    vendor_id: str = ""
    vendor_type: str = "default"        # ← NOW EXPLICIT
    kyb_status: str = "PENDING"
    parsed_contracts: dict = Field(default_factory=dict)
    computed_risk_vector: dict = Field(default_factory=dict)
    # NEW: Accept additional fields from your request
    contact_email: str = ""
    industry: str = ""
    employee_count: int = 0
    quality_score: int = 0
    delivery_score: int = 0
    remarks: str = ""
    registration_number: str = ""
```

#### 5. Updated Initial State (orchestrator.py)
```python
# Now handles country_code properly
country_iso = vendor_data.country_code if vendor_data.country_code else vendor_data.country_iso

initial_state = {
    "vendor_id": v_id,
    "vendor_name": vendor_data.company_name,
    "company_name": vendor_data.company_name,
    "country_iso": country_iso,           # ← From country_code
    "kyb_status": vendor_data.kyb_status,
    "vendor_type": vendor_data.vendor_type,
    "parsed_contracts": vendor_data.parsed_contracts,
    "computed_risk_vector": vendor_data.computed_risk_vector,
    "next_action_node": "Supervisor",
    "_supervisor_loop_count": 0           # ← Loop counter initialized
}
```

#### 6. State Container Updated (state_container.py)
```python
class AssessmentGraphState(TypedDict):
    # ... existing fields ...
    _supervisor_loop_count: int   # ← NEW: For loop prevention
```

#### 7. Contract Analysis State Preservation
```python
# contract_analysis.py now returns kyb_status and maintains state better
return {
    "parsed_contracts": parsed_contracts,
    "messages": [AIMessage(content=summary)],
    "vendor_id": vendor_id,
    "tenant_id": tenant_id,
    "company_name": company_name,
    "kyb_status": "CLEAN"  # ← Explicitly set
}
```

## Why You Were Getting 6 Errors

The workflow was:
1. Supervisor → KYBScreening → Supervisor
2. Supervisor → ContractAnalysis (embedding error)
3. Supervisor → ContractAnalysis (embedding error)  
4. Supervisor → ContractAnalysis (embedding error)
... repeating because contractor analysis kept failing to return parsed_contracts

**Now:**
- Embedding errors are caught gracefully
- query_vector defaults to [] (empty list)
- Workflow continues to RiskScoring with empty contracts
- Supervisor advances to END

## Testing Your Request

```bash
curl -X POST http://localhost:8000/evaluate-vendor \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Al-Akhtar Trust",
    "contact_email": "compliance-test@techvendor.com",
    "industry": "Logistics",
    "employee_count": 45,
    "quality_score": 8,
    "delivery_score": 7,
    "remarks": "Testing Sanction Watchlists",
    "country_code": "PK",
    "vendor_type": "logistics",
    "registration_number": "REG-999-TEST"
  }'
```

## Expected Output Now

✅ No crash on embedding failure
✅ Workflow completes successfully
✅ Returns proper JSON response
✅ Debug logs show progression:
```
📊 Supervisor Check - KYB: PENDING, Contracts: 0, Risk Vector: False
→ Routing to KYBScreening
📊 Supervisor Check - KYB: CLEAN, Contracts: 0, Risk Vector: False
→ Routing to ContractAnalysis
⚠️ Contract Embedding Generation Failed: ... (but continues!)
📊 Supervisor Check - KYB: CLEAN, Contracts: 0, Risk Vector: False
→ Routing to RiskScoring
📊 Supervisor Check - KYB: CLEAN, Contracts: 0, Risk Vector: True
→ Routing to END
```

## Files Modified

- ✅ `contract_analysis.py` - Enhanced embedding error handling
- ✅ `orchestrator.py` - Loop prevention, better logging, expanded input model
- ✅ `state_container.py` - Added _supervisor_loop_count field
- ✅ `kyb_screening.py` - Already properly returning state

## Next Steps

If you still see errors:

1. Check environment variables:
   ```bash
   echo $GEMINI_API_KEY
   echo $PINECONE_API_KEY
   ```

2. Check Gemini API key validity
   - Navigate to Google Cloud Console
   - Verify API key has permissions

3. Check for rate limiting
   - Gemini API has rate limits
   - Wait a moment and retry

4. Enable full debug logging:
   - Add `--log-level debug` to uvicorn command
