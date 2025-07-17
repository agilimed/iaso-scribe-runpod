#!/usr/bin/env python3
"""
Test Phi-4 with Cardiology Consultation Note
Verify universal template works across specialties
"""

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Cardiology consultation note
CARDIOLOGY_NOTE = """Cardiology Consultation Note
Date of Consultation: July 17, 2025
Patient Name: [Redacted], John
MRN: [Redacted]
Age/Sex: 72-year-old male
Consulting Physician: Dr. A. Sharma (Cardiology)
Referring Team: Dr. L. Chen (Internal Medicine)

Reason for Consultation:
New-onset atrial fibrillation with rapid ventricular response (RVR) and hypotension.

History of Present Illness:
Mr. [Redacted] is a 72-year-old male with a significant past medical history (see below) who was admitted to the Internal Medicine service 24 hours ago for community-acquired pneumonia. He was started on IV Ceftriaxone and Azithromycin and was clinically stable until this evening.

At approximately 7:00 PM, the patient activated the nurse call light complaining of sudden-onset palpitations, severe lightheadedness, and worsening shortness of breath. He denied any chest pain, pressure, or diaphoresis. He did not lose consciousness.

On initial evaluation by the primary team, he was found to be tachycardic with a heart rate in the 140s-150s, and his blood pressure, which was previously stable at 130/80 mmHg, had dropped to 95/60 mmHg. An urgent EKG was performed which revealed atrial fibrillation with a rapid ventricular response. He received a 500 mL bolus of normal saline with transient improvement in his blood pressure to 105/65 mmHg. Cardiology was consulted for management recommendations.

Past Medical History:
• Hypertension (HTN)
• Hyperlipidemia (HLD)
• Type 2 Diabetes Mellitus (T2DM) – on oral agents
• Obstructive Sleep Apnea (OSA) – uses CPAP at home, but not yet set up in hospital
• Chronic Kidney Disease (CKD) Stage III (Baseline Creatinine ~1.6 mg/dL)
• Former smoker, 30-pack-year history, quit 10 years ago.

Home Medications:
• Lisinopril 20 mg daily
• Atorvastatin 40 mg nightly
• Metformin 1000 mg twice daily
• Aspirin 81 mg daily

Allergies: No Known Drug Allergies

Physical Examination:
General: Alert and oriented x3, appears anxious and in mild respiratory distress.
Vitals: Temp 38.5°C, HR 138 bpm, BP 98/62 mmHg, RR 22/min, SpO2 93% on 2L nasal cannula.
Cardiovascular: Tachycardic, irregularly irregular rhythm. Normal S1/S2. A grade 2/6 systolic ejection murmur is noted at the left upper sternal border. Jugular venous pressure is estimated at 8 cm H2O. 1+ pitting edema in bilateral lower extremities.
Pulmonary: Crackles noted at the right lung base. Otherwise, clear to auscultation bilaterally.
Extremities: Warm with brisk capillary refill.

Data & Investigations:
Labs (from this evening):
• CBC: WBC 14.5 K/uL (high), Hgb 12.8 g/dL, Platelets 220 K/uL
• BMP: Na 137 mmol/L, K 3.6 mmol/L, Cl 101 mmol/L, CO2 22 mmol/L, BUN 35 mg/dL, Creatinine 1.7 mg/dL (up from baseline 1.6), Glucose 188 mg/dL
• Cardiac Enzymes: High-Sensitivity Troponin I: 0.08 ng/mL (Reference: <0.04 ng/mL). A repeat troponin was ordered.
• BNP: 850 pg/mL (elevated)
• TSH: 1.8 mIU/L (normal)

EKG (19:15): Atrial fibrillation, ventricular rate 145 bpm. No acute ST-segment elevation or depression. Meets voltage criteria for Left Ventricular Hypertrophy (LVH). QTc is normal.

Chest X-Ray (on admission): Confirmed right lower lobe infiltrate consistent with pneumonia. No overt pulmonary edema.

Bedside Transthoracic Echocardiogram (TTE) - Limited Study:
• Left Ventricular Ejection Fraction (LVEF) is estimated at 45-50% (mildly reduced).
• Left atrium appears moderately dilated.
• No significant valvular stenosis. Mild mitral regurgitation.
• No pericardial effusion.

Assessment & Impression:
This is a 72-year-old male with multiple cardiovascular risk factors presenting with:

1. New-Onset Atrial Fibrillation with RVR, likely secondary to Sepsis: The patient's acute decompensation is most likely precipitated by the systemic inflammatory response and metabolic stress from his pneumonia. His hypotension is likely rate-related.

2. Demand Ischemia (Type 2 Myocardial Infarction): The low-level positive troponin in the setting of extreme tachycardia, fever, and hypoxemia is most consistent with myocardial supply-demand mismatch, not an acute coronary syndrome (ACS) from plaque rupture.

3. Acute on Chronic Heart Failure Exacerbation: The patient has evidence of previously undiagnosed heart failure with mildly reduced ejection fraction (HFrEF) and likely diastolic dysfunction given his history of HTN. The new-onset A-fib with RVR has precipitated an acute exacerbation, evidenced by his dyspnea, elevated JVP, and high BNP.

4. Community-Acquired Pneumonia / Sepsis: The underlying driver of the current cardiac instability.

Plan & Recommendations:

1. Rate Control: The immediate priority is to control the ventricular rate to improve hemodynamic stability.
   • Given borderline hypotension, recommend cautious use of IV beta-blockers.
   • Start IV Metoprolol 5 mg slow push, may repeat x2 every 10 minutes as tolerated, monitoring blood pressure closely.
   • Goal heart rate < 110 bpm initially for symptomatic and hemodynamic improvement.
   • Avoid calcium channel blockers (e.g., Diltiazem) at this time due to their more potent negative inotropic effects in a patient with reduced LVEF and borderline BP.

2. Anticoagulation: Patient's stroke risk requires assessment.
   • CHA₂DS₂-VASc Score = 4 (Age >65, HTN, DM, CHF). This confers a high risk of thromboembolism.
   • HAS-BLED Score = 2 (HTN, abnormal renal function).
   • The benefit of anticoagulation strongly outweighs the bleeding risk. Recommend starting therapeutic anticoagulation.
   • Given CKD Stage III, initiate Apixaban (Eliquis) 5 mg twice daily. Can be started immediately.

3. Heart Failure Management:
   • The metoprolol used for rate control will also serve as initial guideline-directed medical therapy (GDMT).
   • Recommend gentle diuresis once blood pressure is more stable. Lasix 20 mg IV x1 now, and monitor urine output and renal function.
   • Strict intake and output monitoring. Daily weights.

4. Ischemia Management:
   • At present, there is no indication for urgent coronary angiography as the picture is not consistent with ACS.
   • Continue to trend troponins q6h x2 to ensure they are not dynamically rising.
   • Optimize oxygenation and continue treatment for underlying pneumonia.

5. Follow-up:
   • Please replete electrolytes: target Potassium > 4.0 mEq/L and Magnesium > 2.0 mg/dL.
   • Will require transition to oral rate control agents once stable.
   • Recommend a formal, comprehensive TTE once the acute infectious process has resolved.

Thank you for this interesting and challenging consultation. We will continue to follow the patient with you.

Dr. A. Sharma, MD
Cardiology Fellow
Pager: [Redacted]"""

def wait_for_job_completion(job_id, endpoint_id, headers, max_wait=300):
    """Poll job status until completion"""
    print(f"\n⏳ Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n❌ Timeout after {max_wait}s")
            return None
            
        response = requests.get(
            f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            
            if status == 'COMPLETED':
                print(f"\n✅ Job completed in {elapsed:.1f}s")
                return result
            elif status == 'FAILED':
                print(f"\n❌ Job failed")
                return result
            else:
                print(f"Status: {status} ({elapsed:.0f}s elapsed)", end='\r')
                time.sleep(2)
        else:
            print(f"\n❌ Error checking status: {response.status_code}")
            return None

def test_cardiology_summary():
    """Test Phi-4 with cardiology consultation note"""
    
    print("🫀 Testing Phi-4 with Cardiology Consultation Note")
    print("=" * 80)
    print(f"Note length: {len(CARDIOLOGY_NOTE)} characters")
    print(f"Estimated tokens: ~{len(CARDIOLOGY_NOTE)//4} tokens")
    print("-" * 80)
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    endpoint_id = os.environ.get('PHI4_ENDPOINT_ID')
    
    # Use summary prompt type with the universal template
    payload = {
        "input": {
            "text": CARDIOLOGY_NOTE,
            "prompt_type": "summary",
            "max_tokens": 4096,
            "temperature": 0.7
        }
    }
    
    print("📤 Sending request to Phi-4 endpoint...")
    
    try:
        # Submit job
        response = requests.post(
            f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            initial_result = response.json()
            
            # Check if job is queued or in progress
            if initial_result.get("status") in ["IN_QUEUE", "IN_PROGRESS"]:
                job_id = initial_result.get("id")
                print(f"Job ID: {job_id}")
                
                # Wait for completion
                result = wait_for_job_completion(job_id, endpoint_id, headers)
                if not result:
                    return
            else:
                result = initial_result
            
            if result.get("status") == "COMPLETED":
                output = result["output"]
                
                print(f"\n✅ Summary generated successfully!")
                print(f"⏱️  Processing time: {output.get('processing_time', 'N/A')}")
                print(f"📊 Tokens generated: {output.get('tokens_generated', 'N/A')}")
                print(f"⚡ Speed: {output.get('tokens_per_second', 'N/A')} tokens/s")
                print(f"💾 Model: {output.get('model', 'N/A')}")
                
                summary = output.get("insights", "")
                
                print("\n" + "="*80)
                print("📄 CARDIOLOGY CONSULTATION SUMMARY:")
                print("="*80)
                print(summary)
                print("="*80)
                
                # Verify no truncation
                print(f"\n📏 Summary length: {len(summary)} characters")
                
                # Check for key cardiology elements
                key_elements = [
                    "72-year-old", "atrial fibrillation", "RVR", "hypotension",
                    "pneumonia", "troponin", "BNP", "EKG", "echo",
                    "metoprolol", "apixaban", "CHA2DS2-VASc",
                    "heart failure", "rate control", "anticoagulation"
                ]
                
                missing_elements = []
                for element in key_elements:
                    if element.lower() not in summary.lower():
                        missing_elements.append(element)
                
                if missing_elements:
                    print(f"\n⚠️  Potentially missing elements: {', '.join(missing_elements)}")
                else:
                    print("\n✅ All key cardiology elements present in summary!")
                
                # Save full output
                with open("cardiology_summary_output.json", "w") as f:
                    json.dump({
                        "input_length": len(CARDIOLOGY_NOTE),
                        "output_length": len(summary),
                        "metrics": output,
                        "summary": summary,
                        "key_elements_check": {
                            "checked": key_elements,
                            "missing": missing_elements
                        }
                    }, f, indent=2)
                print("\n💾 Full output saved to cardiology_summary_output.json")
                
                # Save clean summary
                with open("cardiology_summary_clean.txt", "w") as f:
                    f.write("CARDIOLOGY CONSULTATION SUMMARY\n")
                    f.write("="*80 + "\n\n")
                    f.write(summary)
                    f.write("\n\n" + "="*80 + "\n")
                    f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Tokens: {output.get('tokens_generated', 'N/A')}\n")
                    f.write(f"Processing time: {output.get('processing_time', 'N/A')}s\n")
                print("💾 Clean summary saved to cardiology_summary_clean.txt")
                
            else:
                print(f"❌ Job failed:")
                print(json.dumps(result, indent=2))
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cardiology_summary()