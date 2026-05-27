#!/usr/bin/env python3
"""
Test script to verify the vendor evaluation workflow
"""
import httpx
import json
import asyncio

async def test_vendor_evaluation():
    """Test the evaluate-vendor endpoint with your sample data"""
    
    # Your test payload
    test_payload = {
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
    }
    
    print("=" * 80)
    print("Testing Vendor Evaluation Workflow")
    print("=" * 80)
    print(f"\n📤 Sending Request:")
    print(json.dumps(test_payload, indent=2))
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/evaluate-vendor",
                json=test_payload
            )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nResponse Body:")
            print(json.dumps(result, indent=2, default=str))
            
            # Extract key info
            if "graph_output" in result:
                output = result["graph_output"]
                print(f"\n📊 Workflow Summary:")
                print(f"  - KYB Status: {output.get('kyb_status', 'N/A')}")
                print(f"  - Risk Vector: {output.get('computed_risk_vector', {})}")
                print(f"  - Parsed Contracts: {len(output.get('parsed_contracts', []))} contracts")
        else:
            print(f"\n❌ ERROR!")
            print(f"\nResponse Body:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Request Failed:")
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("Note: Make sure the FastAPI server is running on localhost:8000")
    print("Run: python orchestrator.py")
    print("")
    asyncio.run(test_vendor_evaluation())
