import json
import os
import random
from typing import List, Dict, Any

random.seed(42)

POLICIES = [
    "POL-HLT-001", # Silver Health
    "POL-HLT-002", # Gold Premier Health
    "POL-MOT-001", # Comprehensive Private Motor
    "POL-MOT-002", # Commercial Goods Vehicle
    "POL-HOM-001", # Homeowners Building
    "POL-HOM-002", # Household Contents & Renters
]

CLAIMS_TEMPLATES = [
    # --- HEALTH POL-HLT-001: Silver Care Health ---
    {
        "policy_id": "POL-HLT-001",
        "category": "Inpatient Hospitalization",
        "desc": "Claimant admitted to St. Jude Hospital for 3 days due to acute viral pneumonia. Underwent IV antibiotic therapy, chest X-rays, blood cultures, and 3 nights in standard single room. Total hospital bill $3,450.",
        "claimed_amount": 3450.00,
        "claimed_items": [{"item": "Room & Board 3 days", "amount": 900.00}, {"item": "Diagnostic X-rays & Blood Tests", "amount": 850.00}, {"item": "Physician & Specialist Fees", "amount": 700.00}, {"item": "Pharmacy & Medication", "amount": 1000.00}],
        "incident_date": "2026-03-12",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 1.1", "Clause 1.2", "Clause 1.3", "Clause 3.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Standard covered inpatient treatment minus $250 deductible."
    },
    {
        "policy_id": "POL-HLT-001",
        "category": "Ophthalmology / Day Care",
        "desc": "Patient underwent elective phacoemulsification cataract surgery for the right eye with monofocal intraocular lens insertion at City Eye Institute. Total procedure bill is $2,100.",
        "claimed_amount": 2100.00,
        "claimed_items": [{"item": "Cataract Surgery Theatre Charges", "amount": 1100.00}, {"item": "Intraocular Lens Implant", "amount": 700.00}, {"item": "Surgeon Consultation", "amount": 300.00}],
        "incident_date": "2026-04-05",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 3.2"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Approved but capped at the $1,200 sub-limit specified in Clause 3.2."
    },
    {
        "policy_id": "POL-HLT-001",
        "category": "Pre-Existing Exclusion",
        "desc": "Claimant hospitalized for acute ischemic stroke and secondary hypertension. Medical records reveal ongoing treatment for chronic hypertension diagnosed 18 months prior to policy inception. Current policy active for 8 months.",
        "claimed_amount": 7800.00,
        "claimed_items": [{"item": "ICU Care 2 days", "amount": 3200.00}, {"item": "Neurological Consultation & Medication", "amount": 4600.00}],
        "incident_date": "2026-05-10",
        "expected_decision": "REJECTED",
        "expected_cited_clauses": ["Clause 4.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Pre-existing condition within 36-month exclusion waiting period."
    },
    {
        "policy_id": "POL-HLT-001",
        "category": "Cosmetic Exclusion",
        "desc": "Patient underwent elective aesthetic rhinoplasty and septoplasty for facial aesthetic enhancement at Beverly Plastic Surgery Clinic. Total invoice $6,200.",
        "claimed_amount": 6200.00,
        "claimed_items": [{"item": "Rhinoplasty Surgical Fee", "amount": 4500.00}, {"item": "Anesthesia & Facility Fee", "amount": 1700.00}],
        "incident_date": "2026-06-15",
        "expected_decision": "REJECTED",
        "expected_cited_clauses": ["Clause 4.2"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Aesthetic and cosmetic surgeries are permanently excluded."
    },
    {
        "policy_id": "POL-HLT-001",
        "category": "High Value Orthopedic",
        "desc": "Total knee replacement surgery following severe osteoarthritic degradation. Implant surgery, 5 days hospital stay, physical therapy. Total claimed amount $14,500.",
        "claimed_amount": 14500.00,
        "claimed_items": [{"item": "Knee Prosthesis Implant", "amount": 5500.00}, {"item": "Surgical Theatre & Surgeon Fee", "amount": 5000.00}, {"item": "Room Rent & Nursing 5 days", "amount": 4000.00}],
        "incident_date": "2026-07-20",
        "expected_decision": "ESCALATED",
        "expected_cited_clauses": ["Clause 3.3"],
        "is_fraud": False,
        "requires_human_review": True,
        "notes": "High value claim exceeding $10,000 threshold and subject to Joint Replacement Sub-Limit."
    },

    # --- HEALTH POL-HLT-002: Gold Premier Health ---
    {
        "policy_id": "POL-HLT-002",
        "category": "Robotic Surgery",
        "desc": "Patient admitted for Da Vinci robotic-assisted laparoscopic radical prostatectomy at Metropolitan University Hospital. Incurred 2 nights in executive suite accommodation.",
        "claimed_amount": 9200.00,
        "claimed_items": [{"item": "Robotic Instrumentation Fee", "amount": 3500.00}, {"item": "Surgical Team Fee", "amount": 3700.00}, {"item": "Suite Room Stay", "amount": 2000.00}],
        "incident_date": "2026-03-28",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 1.1", "Clause 1.2", "Clause 3.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Fully covered under Gold Premier robotic surgery and suite accommodation."
    },
    {
        "policy_id": "POL-HLT-002",
        "category": "Mental Health",
        "desc": "Inpatient admission to Horizon Behavioral Health Centre for acute major depressive disorder and psychiatric crisis stabilization for 10 days.",
        "claimed_amount": 4200.00,
        "claimed_items": [{"item": "Inpatient Psychiatric Care & Therapy", "amount": 4200.00}],
        "incident_date": "2026-04-18",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 2.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Covered within the $5,000 mental health annual aggregate limit."
    },
    {
        "policy_id": "POL-HLT-002",
        "category": "Experimental Therapy Exclusion",
        "desc": "Claim for unapproved experimental peptide therapy and uncertified stem cell infusion administered at an offshore wellness retreat.",
        "claimed_amount": 8500.00,
        "claimed_items": [{"item": "Unapproved Experimental Stem Cell Injection", "amount": 8500.00}],
        "incident_date": "2026-05-22",
        "expected_decision": "REJECTED",
        "expected_cited_clauses": ["Clause 4.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Excluded under Clause 4.1: Unproven and experimental therapies."
    },

    # --- MOTOR POL-MOT-001: Private Comprehensive ---
    {
        "policy_id": "POL-MOT-001",
        "category": "Accidental Collision",
        "desc": "Insured vehicle collided with concrete guardrail during heavy rain. Front bumper shattered, radiator ruptured, hood crumpled. Vehicle towed to authorized repair centre.",
        "claimed_amount": 2800.00,
        "claimed_items": [{"item": "Front Bumper Replacement (Plastic)", "amount": 800.00}, {"item": "Radiator Replacement", "amount": 600.00}, {"item": "Hood Panel Beating & Paint", "amount": 1400.00}],
        "incident_date": "2026-02-14",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 1.1", "Clause 2.1", "Clause 2.2"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Standard collision covered minus $350 deductible and 50% depreciation on plastic bumper."
    },
    {
        "policy_id": "POL-MOT-001",
        "category": "Windshield Glass",
        "desc": "Gravel airborne from highway truck struck front windshield causing extensive spiderweb cracking. Replacement of original OEM laminated windshield.",
        "claimed_amount": 750.00,
        "claimed_items": [{"item": "OEM Front Glass Windshield", "amount": 600.00}, {"item": "Fitting & Sensor Calibration", "amount": 150.00}],
        "incident_date": "2026-03-04",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 1.1", "Clause 2.2"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Glass components carry 0% depreciation deduction under Clause 2.2."
    },
    {
        "policy_id": "POL-MOT-001",
        "category": "Drunk Driving Exclusion",
        "desc": "Vehicle swerved into ditch at 2 AM. Police report indicates driver breathalyzer registered Blood Alcohol Concentration (BAC) of 0.14%, well above statutory 0.05% threshold.",
        "claimed_amount": 5400.00,
        "claimed_items": [{"item": "Chassis & Suspension Repair", "amount": 5400.00}],
        "incident_date": "2026-04-11",
        "expected_decision": "REJECTED",
        "expected_cited_clauses": ["Clause 3.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Strictly excluded under Clause 3.1 for driving while intoxicated."
    },
    {
        "policy_id": "POL-MOT-001",
        "category": "Total Loss Burglary",
        "desc": "Vehicle stolen from residential driveway overnight. Police FIR lodged immediately; vehicle unrecovered after 30 days. Insured Declared Value (IDV) is $24,000.",
        "claimed_amount": 24000.00,
        "claimed_items": [{"item": "Total Loss Vehicle IDV", "amount": 24000.00}],
        "incident_date": "2026-05-01",
        "expected_decision": "ESCALATED",
        "expected_cited_clauses": ["Clause 1.4"],
        "is_fraud": False,
        "requires_human_review": True,
        "notes": "Valid total theft claim but exceeds $10k threshold, requiring senior adjuster sign-off."
    },

    # --- PROPERTY POL-HOM-001: Building Comprehensive ---
    {
        "policy_id": "POL-HOM-001",
        "category": "Sudden Pipe Burst",
        "desc": "Internal second-floor bathroom copper supply pipe burst suddenly due to freezing temperatures, causing ceiling collapse and structural drywall flooding into ground floor living room.",
        "claimed_amount": 4800.00,
        "claimed_items": [{"item": "Drywall and Ceiling Structural Restoration", "amount": 2800.00}, {"item": "Plumbing Pipe Replacement & Testing", "amount": 800.00}, {"item": "Hardwood Floor Drying & Remediation", "amount": 1200.00}],
        "incident_date": "2026-01-20",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 1.3", "Clause 2.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Sudden bursting covered minus $500 property deductible."
    },
    {
        "policy_id": "POL-HOM-001",
        "category": "Gradual Seepage Exclusion",
        "desc": "Homeowner reported mold growth and rotting baseboards in basement. Certified building inspector concluded damage resulted from continuous rainwater capillary seepage over 2 years.",
        "claimed_amount": 3900.00,
        "claimed_items": [{"item": "Basement Mold Removal & Foundation Sealing", "amount": 3900.00}],
        "incident_date": "2026-03-15",
        "expected_decision": "REJECTED",
        "expected_cited_clauses": ["Clause 3.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Gradual long-term seepage and maintenance failure excluded under Clause 3.1."
    },
    {
        "policy_id": "POL-HOM-001",
        "category": "Major Fire Damage",
        "desc": "Kitchen grease fire spread to roof rafters and attic structure. Fire service response extinguished flames but upper level sustained major structural charring. Claim includes temporary rental housing.",
        "claimed_amount": 28500.00,
        "claimed_items": [{"item": "Roof & Structural Timber Rebuilding", "amount": 22000.00}, {"item": "Temporary Accommodation 3 Months", "amount": 6500.00}],
        "incident_date": "2026-04-02",
        "expected_decision": "ESCALATED",
        "expected_cited_clauses": ["Clause 1.1", "Clause 2.2"],
        "is_fraud": False,
        "requires_human_review": True,
        "notes": "High value claim ($28.5k) routed to human adjuster for contractor quote validation."
    },

    # --- CONTENTS POL-HOM-002: Contents & Renters ---
    {
        "policy_id": "POL-HOM-002",
        "category": "Burglary Forced Entry",
        "desc": "Apartment rear patio door forced open with crowbar while tenant was at work. Burglar took 65-inch OLED television, gaming console, laptop, and leather jacket. Police evidence of jimmy marks attached.",
        "claimed_amount": 3100.00,
        "claimed_items": [{"item": "65-inch 4K OLED TV", "amount": 1600.00}, {"item": "Gaming Console & Controllers", "amount": 600.00}, {"item": "Laptop Computer", "amount": 900.00}],
        "incident_date": "2026-05-18",
        "expected_decision": "APPROVED",
        "expected_cited_clauses": ["Clause 1.1", "Clause 2.1", "Clause 2.2"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Forcible burglary covered minus $200 deductible; items within single-item limit."
    },
    {
        "policy_id": "POL-HOM-002",
        "category": "Mysterious Disappearance Exclusion",
        "desc": "Claimant states a gold diamond necklace disappeared from home during weekend party. No forced entry or damage to premises. Police report classifies as lost property.",
        "claimed_amount": 3200.00,
        "claimed_items": [{"item": "Gold Diamond Necklace", "amount": 3200.00}],
        "incident_date": "2026-06-08",
        "expected_decision": "REJECTED",
        "expected_cited_clauses": ["Clause 3.1"],
        "is_fraud": False,
        "requires_human_review": False,
        "notes": "Mysterious disappearance and unforced loss excluded under Clause 3.1."
    },

    # --- FRAUD / ANOMALY EXAMPLES ---
    {
        "policy_id": "POL-MOT-001",
        "category": "Duplicate Invoice Fraud",
        "desc": "Claim for bumper repair and paint respray following collision. Attached invoice receipt matches identical invoice number and transaction hash as claim CLM-2025-8812 submitted 3 months ago.",
        "claimed_amount": 1950.00,
        "claimed_items": [{"item": "Bumper Respray and Repair", "amount": 1950.00}],
        "incident_date": "2026-06-25",
        "expected_decision": "ESCALATED",
        "expected_cited_clauses": ["Clause 1.1"],
        "is_fraud": True,
        "fraud_reason": "Duplicate invoice hash detected across previous claims database.",
        "requires_human_review": True,
        "receipt_hash": "DUP-HASH-99812-REPAIR",
        "notes": "Flagged by fraud guard and escalated to SIU (Special Investigation Unit)."
    },
    {
        "policy_id": "POL-HLT-001",
        "category": "Inception Fraud",
        "desc": "Policy activated on May 10, 2026. Claim filed on May 12, 2026 for extensive multi-week lumbar spine treatment with doctor notes dating back to April 2026 prior to policy bound date.",
        "claimed_amount": 4300.00,
        "claimed_items": [{"item": "Spinal Therapy & Injections", "amount": 4300.00}],
        "incident_date": "2026-05-11",
        "expected_decision": "ESCALATED",
        "expected_cited_clauses": ["Clause 4.1"],
        "is_fraud": True,
        "fraud_reason": "Inception fraud: Incident occurred within 24 hours of policy inception with preexisting clinical records.",
        "requires_human_review": True,
        "notes": "Flagged for fraudulent inception timing."
    }
]

def generate_dataset(num_claims: int = 120) -> List[Dict[str, Any]]:
    claims = []
    base_templates = CLAIMS_TEMPLATES
    n_templates = len(base_templates)
    
    first_names = ["James", "Emma", "Michael", "Sophia", "David", "Olivia", "Daniel", "Ava", "Alexander", "Mia", "William", "Isabella", "Benjamin", "Charlotte", "Lucas", "Amelia", "Henry", "Harper", "Sebastian", "Evelyn"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

    for i in range(1, num_claims + 1):
        tmpl = base_templates[(i - 1) % n_templates]
        claim_id = f"CLM-2026-{i:04d}"
        claimant_id = f"CUST-{random.randint(1000, 9999)}"
        claimant_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Slight jitter in amounts to create distinct samples
        jitter = round(random.uniform(-0.08, 0.08), 2)
        adjusted_amount = round(tmpl["claimed_amount"] * (1.0 + jitter), 2)
        
        receipt_hash = tmpl.get("receipt_hash")
        if not receipt_hash and not tmpl["is_fraud"]:
            receipt_hash = f"HASH-{claim_id}-{random.randint(10000, 99999)}"
            
        claim_obj = {
            "claim_id": claim_id,
            "claimant_id": claimant_id,
            "claimant_name": claimant_name,
            "policy_id": tmpl["policy_id"],
            "category": tmpl["category"],
            "claim_text": tmpl["desc"],
            "claimed_amount": adjusted_amount,
            "claimed_items": tmpl["claimed_items"],
            "incident_date": tmpl["incident_date"],
            "receipt_hash": receipt_hash,
            "expected_decision": tmpl["expected_decision"],
            "expected_cited_clauses": tmpl["expected_cited_clauses"],
            "is_fraud": tmpl["is_fraud"],
            "fraud_reason": tmpl.get("fraud_reason"),
            "requires_human_review": tmpl["requires_human_review"],
            "evaluation_notes": tmpl["notes"]
        }
        claims.append(claim_obj)

    return claims

def main():
    output_dir = "data/synthetic_claims"
    os.makedirs(output_dir, exist_ok=True)
    
    claims = generate_dataset(120)
    
    # 1. Save individual claim files
    for claim in claims:
        filename = os.path.join(output_dir, f"{claim['claim_id']}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(claim, f, indent=2)
            
    # 2. Save ground truth evaluation dataset
    eval_file = "data/ground_truth_eval.json"
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump(claims, f, indent=2)
        
    print(f"Successfully generated {len(claims)} synthetic claims.")
    print(f"Individual files written to: {output_dir}/")
    print(f"Master evaluation dataset written to: {eval_file}")

    # Print summary statistics
    approved = sum(1 for c in claims if c["expected_decision"] == "APPROVED")
    rejected = sum(1 for c in claims if c["expected_decision"] == "REJECTED")
    escalated = sum(1 for c in claims if c["expected_decision"] == "ESCALATED")
    fraud = sum(1 for c in claims if c["is_fraud"])
    print(f"Summary: Approved={approved}, Rejected={rejected}, Escalated={escalated}, FraudFlags={fraud}")

if __name__ == "__main__":
    main()
