#!/usr/bin/env python3
"""
Test Phi-4 with detailed obstetric note
Verify no truncation and streaming functionality
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# The detailed obstetric note
OBSTETRIC_NOTE = """Patient Name: [Redacted]
MRN: [Redacted]
Date of Birth: [18 years old]
Gravida/Para: G2P0
Gestational Age: 35 weeks + 4 days
EDC: 21 January 2009
Consulting Physician: Dr. X
Referring Provider: [Redacted]

⸻

Chief Complaint:

Preterm contractions at 35 weeks and 4 days gestation with a history of prior complications during pregnancy.

⸻

History of Present Illness:

This is an 18-year-old multigravida (G2P0) with an estimated date of confinement (EDC) of 01/21/09, currently at 35+4 weeks gestation. She has been under Dr. X's antenatal care and is classified as high-risk due to the following risk factors:
    •    History of tobacco use (ceased in early second trimester per patient report).
    •    Chronic mild persistent asthma.
    •    Recurrent preterm contractions.
    •    Psychosocial stressors with limited family support.
    •    Previous spontaneous abortion at 8 weeks (G1 loss).

The patient presented with increased pelvic pressure, contractions, and vaginal discharge suggestive of possible rupture of membranes.

⸻

Prenatal Course Summary by Gestational Weeks:

Week 28 (First High-Risk OB Referral)
    •    Fundal height consistent with dates.
    •    Fetal movement noted.
    •    Ultrasound showed EFW (Estimated Fetal Weight) in the 35th percentile.
    •    Smoking cessation counseling reinforced.
    •    Received first dose of betamethasone for fetal lung maturity due to prior episode of uterine irritability.

Week 30
    •    Complained of intermittent dyspnea; PFTs stable, asthma controlled with salbutamol PRN.
    •    Fetal NST reactive.
    •    Cervical length by TVUS: 3.2 cm.
    •    Growth scan normal.
    •    Second dose of betamethasone administered as precaution.

Week 32
    •    Presented to triage with regular contractions every 10 minutes.
    •    Cervix 1 cm, 50% effaced.
    •    No ROM noted. Fetal fibronectin test: negative.
    •    Placed on bedrest at home.
    •    Fetal growth still in normal range.
    •    Continued weekly follow-ups initiated.

Week 34
    •    Contractions intensified; cervix 2 cm, 60% effaced.
    •    Bedrest continued.
    •    Discussion held about risks of preterm labor; patient counseled on signs of ROM and preterm labor.
    •    Group B Strep: Negative.

Week 35+4 (Delivery Admission)
    •    Patient arrived in active labor; contractions q4 minutes, moderate intensity.
    •    Confirmed rupture of membranes with positive pooling and nitrazine test.
    •    Cervix 5 cm, 70% effaced, -1 station.
    •    IUPC inserted, contractions confirmed.
    •    Epidural placed for pain relief.
    •    Pitocin initiated for labor augmentation.

⸻

Delivery Summary:
    •    Mode of Delivery: Spontaneous Vaginal Delivery
    •    Presentation: Occiput Anterior (OA)
    •    Duration of Second Stage: ~15 minutes
    •    Episiotomy: None
    •    Lacerations:
    •    Bilateral superficial labial lacerations (no repair needed).
    •    Hymenal remnant/skin tag excised per patient preference; single 3-0 Vicryl suture placed for hemostasis.
    •    Placenta: Delivered intact, three-vessel cord noted.
    •    Estimated Blood Loss: 300 mL
    •    Cord Gases: Sent due to prematurity.

⸻

Infant Details:
    •    Sex: Female
    •    Apgars: 8 and 9 at 1 and 5 minutes
    •    Initial Examination: Vigorous cry, bulb suctioned, warm and dry
    •    Transferred to: Neonatal care team for observation due to late-preterm delivery.

⸻

Postpartum Status:
    •    Mother: Alert, oriented, vitals stable. Uterus firm, fundus midline.
    •    Pain: Controlled post-epidural.
    •    Lochia: Moderate.
    •    Bladder/Bowel: Void spontaneous, no incontinence or retention.
    •    Mood: Tearful at times, possible early postpartum emotional lability noted. Will continue monitoring.

⸻

Assessment:
    1.    G2P0 at 35+4 weeks with spontaneous preterm labor – Delivered healthy female infant via uncomplicated vaginal delivery. No maternal or neonatal complications post-delivery.
    2.    Tobacco use in pregnancy (history) – Ceased use by 2nd trimester; no IUGR noted.
    3.    Chronic asthma – Mild, well-controlled; no exacerbation during labor.
    4.    History of spontaneous abortion (G1) – No impact on current outcome.
    5.    Psychosocial risk factors – Young maternal age, limited support; consider postpartum social work input.

⸻

Plan:

Maternal
    •    Monitor for postpartum hemorrhage, infection, and perineal healing.
    •    Continue vitals q4h.
    •    Provide lactation support.
    •    Consider psychosocial assessment prior to discharge.
    •    Pain management: NSAIDs and acetaminophen as needed.
    •    Iron and calcium supplementation to continue postpartum.

Infant
    •    NICU observation for 24–48 hours due to prematurity.
    •    Monitor blood glucose and temperature.
    •    Routine newborn screening and hearing test.

Follow-up
    •    OB follow-up in 1 week for suture check and emotional well-being.
    •    6-week postpartum check.
    •    Pediatric follow-up arranged.

⸻

Physician Signature:

Dr. X, MD
Department of Obstetrics and Gynecology"""

def test_obstetric_summary():
    """Test Phi-4 with detailed obstetric note"""
    
    print("🏥 Testing Phi-4 with Detailed Obstetric Note")
    print("=" * 80)
    print(f"Note length: {len(OBSTETRIC_NOTE)} characters")
    print(f"Estimated tokens: ~{len(OBSTETRIC_NOTE)//4} tokens")
    print("-" * 80)
    
    headers = {
        "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Custom prompt for pregnancy journey summary
    custom_prompt = """<|system|>
You are an expert obstetric documentation specialist. Create comprehensive summaries of pregnancy journeys.
<|end|>
<|user|>
Please create a comprehensive summary of this patient's entire pregnancy journey from the detailed obstetric note below. 

IMPORTANT REQUIREMENTS:
1. DO NOT truncate or skip any significant information
2. Include ALL key dates and gestational weeks
3. Cover the COMPLETE journey from initial risk factors through delivery and postpartum
4. Maintain medical accuracy while making it readable
5. Include all complications, interventions, and outcomes

Obstetric Note:

""" + OBSTETRIC_NOTE + """

Please provide a complete narrative summary that captures:
- Patient demographics and risk factors
- Complete prenatal course (all weeks mentioned)
- Labor and delivery details
- Maternal and neonatal outcomes
- Postpartum status and follow-up plans

Make this a flowing narrative that tells the complete story of this pregnancy.
<|end|>
<|assistant|>"""
    
    payload = {
        "input": {
            "text": custom_prompt,
            "max_tokens": 4096,  # Maximum tokens for complete summary
            "temperature": 0.7
        }
    }
    
    print("📤 Sending request to Phi-4 endpoint...")
    start_time = os.times()
    
    try:
        response = requests.post(
            f"https://api.runpod.ai/v2/{os.environ.get('PHI4_ENDPOINT_ID')}/runsync",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "COMPLETED":
                output = result["output"]
                
                print(f"\n✅ Summary generated successfully!")
                print(f"⏱️  Processing time: {output['processing_time']:.2f}s")
                print(f"📊 Tokens generated: {output['tokens_generated']}")
                print(f"⚡ Speed: {output['tokens_per_second']} tokens/s")
                print(f"💾 Model: {output['model']}")
                
                summary = output["insights"]
                
                print("\n" + "="*80)
                print("📄 PREGNANCY JOURNEY SUMMARY:")
                print("="*80)
                print(summary)
                print("="*80)
                
                # Verify no truncation
                print(f"\n✅ Summary length: {len(summary)} characters")
                
                # Check for key elements to ensure completeness
                key_elements = [
                    "18-year-old", "G2P0", "35+4 weeks", "high-risk",
                    "tobacco", "asthma", "preterm contractions",
                    "Week 28", "Week 30", "Week 32", "Week 34",
                    "betamethasone", "spontaneous vaginal delivery",
                    "female infant", "Apgars 8 and 9", "NICU",
                    "postpartum", "follow-up"
                ]
                
                missing_elements = []
                for element in key_elements:
                    if element.lower() not in summary.lower():
                        missing_elements.append(element)
                
                if missing_elements:
                    print(f"\n⚠️  Potentially missing elements: {', '.join(missing_elements)}")
                else:
                    print("\n✅ All key elements present in summary!")
                
                # Save full output for review
                with open("obstetric_summary_output.json", "w") as f:
                    json.dump({
                        "input_length": len(OBSTETRIC_NOTE),
                        "output_length": len(summary),
                        "metrics": output,
                        "summary": summary,
                        "key_elements_check": {
                            "checked": key_elements,
                            "missing": missing_elements
                        }
                    }, f, indent=2)
                print("\n💾 Full output saved to obstetric_summary_output.json")
                
            else:
                print(f"❌ Job failed: {result}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_obstetric_summary()