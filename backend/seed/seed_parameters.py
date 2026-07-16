"""
Seed script for Test Parameter Master (§4 of AKRITI_Report_Generation_Addendum.md).
Pre-populates reference ranges and parameter definitions for 65 standard diagnostic tests.
Can be run standalone via: python -m backend.seed.seed_parameters
"""
import sys
from pathlib import Path
from sqlalchemy.orm import Session

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.app.core.db import SessionLocal
from backend.app.models.test import Test
from backend.app.models.test_parameter import TestParameter


# Data structure:
# test_name -> list of dicts:
# [
#   {"name": str, "unit": str/None, "input_type": str, "low": float/None, "high": float/None,
#    "text": str/None, "gender": str, "options": list/None}
# ]
PARAMETERS_SEED_DATA = {
    "CBC 5 Part": [
        {"name": "Hemoglobin (Hb)", "unit": "g/dL", "input_type": "numeric", "low": 13.0, "high": 17.0, "text": "13.0 - 17.0", "gender": "male"},
        {"name": "Hemoglobin (Hb)", "unit": "g/dL", "input_type": "numeric", "low": 12.0, "high": 15.5, "text": "12.0 - 15.5", "gender": "female"},
        {"name": "Total RBC Count", "unit": "million/µL", "input_type": "numeric", "low": 4.5, "high": 5.5, "text": "4.5 - 5.5", "gender": "male"},
        {"name": "Total RBC Count", "unit": "million/µL", "input_type": "numeric", "low": 3.5, "high": 4.5, "text": "3.5 - 4.5", "gender": "female"},
        {"name": "Total WBC Count", "unit": "/µL", "input_type": "numeric", "low": 4000.0, "high": 11000.0, "text": "4,000 - 11,000", "gender": "all"},
        {"name": "Platelet Count", "unit": "/µL", "input_type": "numeric", "low": 150000.0, "high": 450000.0, "text": "150,000 - 450,000", "gender": "all"},
        {"name": "Hematocrit (PCV)", "unit": "%", "input_type": "numeric", "low": 40.0, "high": 52.0, "text": "40 - 52", "gender": "male"},
        {"name": "Hematocrit (PCV)", "unit": "%", "input_type": "numeric", "low": 36.0, "high": 48.0, "text": "36 - 48", "gender": "female"},
        {"name": "MCV", "unit": "fL", "input_type": "numeric", "low": 80.0, "high": 100.0, "text": "80 - 100", "gender": "all"},
        {"name": "MCH", "unit": "pg", "input_type": "numeric", "low": 27.0, "high": 33.0, "text": "27 - 33", "gender": "all"},
        {"name": "MCHC", "unit": "g/dL", "input_type": "numeric", "low": 32.0, "high": 36.0, "text": "32 - 36", "gender": "all"},
        {"name": "RDW", "unit": "%", "input_type": "numeric", "low": 11.5, "high": 14.5, "text": "11.5 - 14.5", "gender": "all"},
        {"name": "Neutrophils", "unit": "%", "input_type": "numeric", "low": 40.0, "high": 70.0, "text": "40 - 70", "gender": "all"},
        {"name": "Lymphocytes", "unit": "%", "input_type": "numeric", "low": 20.0, "high": 40.0, "text": "20 - 40", "gender": "all"},
        {"name": "Eosinophils", "unit": "%", "input_type": "numeric", "low": 1.0, "high": 6.0, "text": "1 - 6", "gender": "all"},
        {"name": "Monocytes", "unit": "%", "input_type": "numeric", "low": 2.0, "high": 8.0, "text": "2 - 8", "gender": "all"},
        {"name": "Basophils", "unit": "%", "input_type": "numeric", "low": 0.0, "high": 1.0, "text": "0 - 1", "gender": "all"},
    ],
    "TC DC OF WBC": [
        {"name": "Total WBC Count", "unit": "/µL", "input_type": "numeric", "low": 4000.0, "high": 11000.0, "text": "4,000 - 11,000", "gender": "all"},
        {"name": "Neutrophils", "unit": "%", "input_type": "numeric", "low": 40.0, "high": 70.0, "text": "40 - 70", "gender": "all"},
        {"name": "Lymphocytes", "unit": "%", "input_type": "numeric", "low": 20.0, "high": 40.0, "text": "20 - 40", "gender": "all"},
        {"name": "Eosinophils", "unit": "%", "input_type": "numeric", "low": 1.0, "high": 6.0, "text": "1 - 6", "gender": "all"},
        {"name": "Monocytes", "unit": "%", "input_type": "numeric", "low": 2.0, "high": 8.0, "text": "2 - 8", "gender": "all"},
        {"name": "Basophils", "unit": "%", "input_type": "numeric", "low": 0.0, "high": 1.0, "text": "0 - 1", "gender": "all"},
    ],
    "HB%": [
        {"name": "Hemoglobin (Hb)", "unit": "g/dL", "input_type": "numeric", "low": 13.0, "high": 17.0, "text": "13.0 - 17.0", "gender": "male"},
        {"name": "Hemoglobin (Hb)", "unit": "g/dL", "input_type": "numeric", "low": 12.0, "high": 15.5, "text": "12.0 - 15.5", "gender": "female"},
    ],
    "Blood Sugar(F)": [
        {"name": "Fasting Blood Sugar", "unit": "mg/dL", "input_type": "numeric", "low": 70.0, "high": 100.0, "text": "70 - 100", "gender": "all"},
    ],
    "Blood Sugar(R)": [
        {"name": "Random Blood Sugar", "unit": "mg/dL", "input_type": "numeric", "low": 70.0, "high": 140.0, "text": "70 - 140", "gender": "all"},
    ],
    "Blood Sugar Fasting/PP": [
        {"name": "Fasting Blood Sugar", "unit": "mg/dL", "input_type": "numeric", "low": 70.0, "high": 100.0, "text": "70 - 100", "gender": "all"},
        {"name": "Post-Prandial Blood Sugar (PP)", "unit": "mg/dL", "input_type": "numeric", "low": 70.0, "high": 140.0, "text": "70 - 140", "gender": "all"},
    ],
    "HbA1c": [
        {"name": "HbA1c", "unit": "%", "input_type": "numeric", "low": 4.0, "high": 5.6, "text": "Normal: <5.7 · Prediabetic: 5.7–6.4 · Diabetic: ≥6.5", "gender": "all"},
    ],
    "Lipid Profile": [
        {"name": "Total Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 100.0, "high": 200.0, "text": "< 200 desirable", "gender": "all"},
        {"name": "Triglycerides", "unit": "mg/dL", "input_type": "numeric", "low": 50.0, "high": 150.0, "text": "< 150 desirable", "gender": "all"},
        {"name": "HDL Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 40.0, "high": 100.0, "text": "> 40", "gender": "male"},
        {"name": "HDL Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 50.0, "high": 100.0, "text": "> 50", "gender": "female"},
        {"name": "LDL Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 50.0, "high": 100.0, "text": "< 100 desirable", "gender": "all"},
        {"name": "VLDL Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 5.0, "high": 40.0, "text": "5 - 40", "gender": "all"},
    ],
    "Cholesterol": [
        {"name": "Total Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 100.0, "high": 200.0, "text": "< 200 desirable", "gender": "all"},
    ],
    "Triglyceride": [
        {"name": "Triglycerides", "unit": "mg/dL", "input_type": "numeric", "low": 50.0, "high": 150.0, "text": "< 150 desirable", "gender": "all"},
    ],
    "LFT": [
        {"name": "SGPT (ALT)", "unit": "U/L", "input_type": "numeric", "low": 0.0, "high": 49.0, "text": "Up to 49", "gender": "all"},
        {"name": "SGOT (AST)", "unit": "U/L", "input_type": "numeric", "low": 5.0, "high": 40.0, "text": "5 - 40", "gender": "male"},
        {"name": "SGOT (AST)", "unit": "U/L", "input_type": "numeric", "low": 9.0, "high": 32.0, "text": "9 - 32", "gender": "female"},
        {"name": "Total Bilirubin", "unit": "mg/dL", "input_type": "numeric", "low": 0.2, "high": 1.2, "text": "0.2 - 1.2", "gender": "all"},
        {"name": "Direct Bilirubin", "unit": "mg/dL", "input_type": "numeric", "low": 0.0, "high": 0.3, "text": "0 - 0.3", "gender": "all"},
        {"name": "Indirect Bilirubin", "unit": "mg/dL", "input_type": "numeric", "low": 0.2, "high": 0.9, "text": "0.2 - 0.9", "gender": "all"},
        {"name": "Alkaline Phosphatase (ALP)", "unit": "U/L", "input_type": "numeric", "low": 44.0, "high": 147.0, "text": "44 - 147", "gender": "all"},
        {"name": "Total Protein", "unit": "g/dL", "input_type": "numeric", "low": 6.0, "high": 8.3, "text": "6.0 - 8.3", "gender": "all"},
        {"name": "Albumin", "unit": "g/dL", "input_type": "numeric", "low": 3.5, "high": 5.0, "text": "3.5 - 5.0", "gender": "all"},
        {"name": "A/G Ratio", "unit": "ratio", "input_type": "numeric", "low": 1.1, "high": 2.5, "text": "1.1 - 2.5", "gender": "all"},
    ],
    "SGPT": [
        {"name": "SGPT (ALT)", "unit": "U/L", "input_type": "numeric", "low": 0.0, "high": 49.0, "text": "Up to 49", "gender": "all"},
    ],
    "SGOT": [
        {"name": "SGOT (AST)", "unit": "U/L", "input_type": "numeric", "low": 5.0, "high": 40.0, "text": "5 - 40", "gender": "male"},
        {"name": "SGOT (AST)", "unit": "U/L", "input_type": "numeric", "low": 9.0, "high": 32.0, "text": "9 - 32", "gender": "female"},
    ],
    "Serum Bilirubin": [
        {"name": "Total Bilirubin", "unit": "mg/dL", "input_type": "numeric", "low": 0.2, "high": 1.2, "text": "0.2 - 1.2", "gender": "all"},
        {"name": "Direct Bilirubin", "unit": "mg/dL", "input_type": "numeric", "low": 0.0, "high": 0.3, "text": "0 - 0.3", "gender": "all"},
        {"name": "Indirect Bilirubin", "unit": "mg/dL", "input_type": "numeric", "low": 0.2, "high": 0.9, "text": "0.2 - 0.9", "gender": "all"},
    ],
    "Total Protein A/G Ratio": [
        {"name": "Total Protein", "unit": "g/dL", "input_type": "numeric", "low": 6.0, "high": 8.3, "text": "6.0 - 8.3", "gender": "all"},
        {"name": "Albumin", "unit": "g/dL", "input_type": "numeric", "low": 3.5, "high": 5.0, "text": "3.5 - 5.0", "gender": "all"},
        {"name": "A/G Ratio", "unit": "ratio", "input_type": "numeric", "low": 1.1, "high": 2.5, "text": "1.1 - 2.5", "gender": "all"},
    ],
    "KFT": [
        {"name": "Blood Urea", "unit": "mg/dL", "input_type": "numeric", "low": 15.0, "high": 45.0, "text": "15 - 45", "gender": "all"},
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.7, "high": 1.3, "text": "0.7 - 1.3", "gender": "male"},
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.6, "high": 1.1, "text": "0.6 - 1.1", "gender": "female"},
        {"name": "Uric Acid", "unit": "mg/dL", "input_type": "numeric", "low": 3.5, "high": 7.2, "text": "3.5 - 7.2", "gender": "male"},
        {"name": "Uric Acid", "unit": "mg/dL", "input_type": "numeric", "low": 2.6, "high": 6.0, "text": "2.6 - 6.0", "gender": "female"},
        {"name": "Serum Calcium", "unit": "mg/dL", "input_type": "numeric", "low": 8.5, "high": 10.5, "text": "8.5 - 10.5", "gender": "all"},
        {"name": "Sodium (Na+)", "unit": "mEq/L", "input_type": "numeric", "low": 135.0, "high": 145.0, "text": "135 - 145", "gender": "all"},
        {"name": "Potassium (K+)", "unit": "mEq/L", "input_type": "numeric", "low": 3.5, "high": 5.1, "text": "3.5 - 5.1", "gender": "all"},
        {"name": "Chloride (Cl-)", "unit": "mEq/L", "input_type": "numeric", "low": 96.0, "high": 106.0, "text": "96 - 106", "gender": "all"},
    ],
    "Blood Urea": [
        {"name": "Blood Urea", "unit": "mg/dL", "input_type": "numeric", "low": 15.0, "high": 45.0, "text": "15 - 45", "gender": "all"},
    ],
    "Serum Creatinine": [
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.7, "high": 1.3, "text": "0.7 - 1.3", "gender": "male"},
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.6, "high": 1.1, "text": "0.6 - 1.1", "gender": "female"},
    ],
    "Serum Uric Acid": [
        {"name": "Uric Acid", "unit": "mg/dL", "input_type": "numeric", "low": 3.5, "high": 7.2, "text": "3.5 - 7.2", "gender": "male"},
        {"name": "Uric Acid", "unit": "mg/dL", "input_type": "numeric", "low": 2.6, "high": 6.0, "text": "2.6 - 6.0", "gender": "female"},
    ],
    "Serum Calcium": [
        {"name": "Serum Calcium", "unit": "mg/dL", "input_type": "numeric", "low": 8.5, "high": 10.5, "text": "8.5 - 10.5", "gender": "all"},
    ],
    "Serum Electrolytes (Na,K,Cl)": [
        {"name": "Sodium (Na+)", "unit": "mEq/L", "input_type": "numeric", "low": 135.0, "high": 145.0, "text": "135 - 145", "gender": "all"},
        {"name": "Potassium (K+)", "unit": "mEq/L", "input_type": "numeric", "low": 3.5, "high": 5.1, "text": "3.5 - 5.1", "gender": "all"},
        {"name": "Chloride (Cl-)", "unit": "mEq/L", "input_type": "numeric", "low": 96.0, "high": 106.0, "text": "96 - 106", "gender": "all"},
    ],
    "Thyroid Profile (FT3,FT4,TSH)": [
        {"name": "TSH", "unit": "µIU/mL", "input_type": "numeric", "low": 0.4, "high": 4.0, "text": "0.4 - 4.0", "gender": "all"},
        {"name": "Free T3 (FT3)", "unit": "pg/mL", "input_type": "numeric", "low": 2.0, "high": 4.4, "text": "2.0 - 4.4", "gender": "all"},
        {"name": "Free T4 (FT4)", "unit": "ng/dL", "input_type": "numeric", "low": 0.9, "high": 1.7, "text": "0.9 - 1.7", "gender": "all"},
    ],
    "T3,T4,TSH": [
        {"name": "TSH", "unit": "µIU/mL", "input_type": "numeric", "low": 0.4, "high": 4.0, "text": "0.4 - 4.0", "gender": "all"},
        {"name": "T3 (Total)", "unit": "ng/dL", "input_type": "numeric", "low": 100.0, "high": 200.0, "text": "100 - 200", "gender": "all"},
        {"name": "T4 (Total)", "unit": "µg/dL", "input_type": "numeric", "low": 5.0, "high": 12.0, "text": "5 - 12", "gender": "all"},
    ],
    "Vitamin D": [
        {"name": "25-Hydroxy Vitamin D", "unit": "ng/mL", "input_type": "numeric", "low": 30.0, "high": 100.0, "text": "Deficient: <20 · Insufficient: 20–29 · Sufficient: 30–100", "gender": "all"},
    ],
    "Vitamin B12": [
        {"name": "Vitamin B12", "unit": "pg/mL", "input_type": "numeric", "low": 211.0, "high": 911.0, "text": "211 - 911", "gender": "all"},
    ],
    "CRP (Quantitative Test)": [
        {"name": "C-Reactive Protein (CRP)", "unit": "mg/L", "input_type": "numeric", "low": 0.0, "high": 6.0, "text": "< 6.0 (Normal)", "gender": "all"},
    ],
    "PSA": [
        {"name": "Prostate Specific Antigen (PSA)", "unit": "ng/mL", "input_type": "numeric", "low": 0.0, "high": 4.0, "text": "< 4.0", "gender": "male"},
    ],
    "Testosterone Total": [
        {"name": "Testosterone Total", "unit": "ng/dL", "input_type": "numeric", "low": 280.0, "high": 1100.0, "text": "280 - 1100", "gender": "male"},
        {"name": "Testosterone Total", "unit": "ng/dL", "input_type": "numeric", "low": 15.0, "high": 70.0, "text": "15 - 70", "gender": "female"},
    ],
    "PT/INR": [
        {"name": "Prothrombin Time (PT)", "unit": "sec", "input_type": "numeric", "low": 11.0, "high": 13.5, "text": "11.0 - 13.5", "gender": "all"},
        {"name": "INR", "unit": "", "input_type": "numeric", "low": 0.8, "high": 1.2, "text": "0.8 - 1.2 (Normal)", "gender": "all"},
    ],
    "ASO Titer": [
        {"name": "Anti-Streptolysin O (ASO)", "unit": "IU/mL", "input_type": "numeric", "low": 0.0, "high": 200.0, "text": "Up to 200", "gender": "all"},
    ],
    # Serology Qualitative Dropdowns
    "HIV 1&2 Test": [
        {"name": "HIV 1 & 2 Antibodies", "unit": "", "input_type": "dropdown", "options": ["Non-Reactive", "Reactive"], "text": "Non-Reactive", "gender": "all"},
    ],
    "TB Platinum Test": [
        {"name": "TB Platinum (IGRA)", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive", "Indeterminate"], "text": "Negative", "gender": "all"},
    ],
    "HBsAg": [
        {"name": "HBsAg (Hepatitis B)", "unit": "", "input_type": "dropdown", "options": ["Non-Reactive", "Reactive"], "text": "Non-Reactive", "gender": "all"},
    ],
    "HCV": [
        {"name": "HCV Antibodies (Hepatitis C)", "unit": "", "input_type": "dropdown", "options": ["Non-Reactive", "Reactive"], "text": "Non-Reactive", "gender": "all"},
    ],
    "VDRL": [
        {"name": "VDRL (Syphilis)", "unit": "", "input_type": "dropdown", "options": ["Non-Reactive", "Reactive"], "text": "Non-Reactive", "gender": "all"},
    ],
    "Trust Test": [
        {"name": "TRUST Test", "unit": "", "input_type": "dropdown", "options": ["Non-Reactive", "Reactive"], "text": "Non-Reactive", "gender": "all"},
    ],
    "Widal": [
        {"name": "Salmonella Typhi O", "unit": "", "input_type": "dropdown", "options": ["Negative (<1:80)", "1:80", "1:160 (Significant)", "1:320"], "text": "Negative (<1:80)", "gender": "all"},
        {"name": "Salmonella Typhi H", "unit": "", "input_type": "dropdown", "options": ["Negative (<1:80)", "1:80", "1:160 (Significant)", "1:320"], "text": "Negative (<1:80)", "gender": "all"},
        {"name": "Salmonella Paratyphi AH", "unit": "", "input_type": "dropdown", "options": ["Negative (<1:80)", "1:80", "1:160 (Significant)"], "text": "Negative (<1:80)", "gender": "all"},
        {"name": "Salmonella Paratyphi BH", "unit": "", "input_type": "dropdown", "options": ["Negative (<1:80)", "1:80", "1:160 (Significant)"], "text": "Negative (<1:80)", "gender": "all"},
    ],
    "Dengue (IgE/IgM)": [
        {"name": "Dengue IgM", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
        {"name": "Dengue IgG", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
        {"name": "Dengue NS1 Antigen", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
    ],
    "R.A. Test": [
        {"name": "Rheumatoid Factor (RA)", "unit": "", "input_type": "dropdown", "options": ["Negative (<18 IU/mL)", "Positive"], "text": "Negative (<18 IU/mL)", "gender": "all"},
    ],
    "Montox Test 5TU/10TU": [
        {"name": "Mantoux Tuberculin Skin Test", "unit": "mm", "input_type": "text", "text": "Induration <10mm (Negative)", "gender": "all"},
    ],
    "IgE": [
        {"name": "Total IgE", "unit": "IU/mL", "input_type": "numeric", "low": 0.0, "high": 150.0, "text": "< 150", "gender": "all"},
    ],
    "Aldehyde": [
        {"name": "Aldehyde Test (Kala-Azar)", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
    ],
    "Parahit Total": [
        {"name": "Parahit Total (Malaria Ag)", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive - P. falciparum", "Positive - P. vivax", "Positive - Mixed"], "text": "Negative", "gender": "all"},
    ],
    "Para Check of P.F": [
        {"name": "Malaria Antigen P.F", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
    ],
    "Para Check for (PV & PF)": [
        {"name": "Malaria Antigen PV & PF", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive - PV", "Positive - PF", "Positive - Both"], "text": "Negative", "gender": "all"},
    ],
    "Para Screen for P.F": [
        {"name": "Malaria Screen P.F", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
    ],
    "PBS for MP": [
        {"name": "Peripheral Blood Smear for MP", "unit": "", "input_type": "dropdown", "options": ["No Malarial Parasite seen", "P. vivax seen", "P. falciparum seen"], "text": "No Malarial Parasite seen", "gender": "all"},
    ],
    "RK 39": [
        {"name": "RK-39 (Kala-Azar Rapid)", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
    ],
    "Preg Colour": [
        {"name": "Urine Pregnancy Test", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "female"},
    ],
    # Descriptive / Imaging (§2.1)
    "USG Whole Abdomen": [
        {"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal study", "gender": "all"},
    ],
    "USG Upper Abdomen": [
        {"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal study", "gender": "all"},
    ],
    "USG Lower Abdomen": [
        {"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal study", "gender": "all"},
    ],
    "USG Uterus and Adnexa": [
        {"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal study", "gender": "female"},
    ],
    "USG Fetal Profile": [
        {"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal study", "gender": "female"},
    ],
    "ECG": [
        {"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal Sinus Rhythm", "gender": "all"},
    ],
    # Routine / Microscopy
    "R/E of Urine": [
        {"name": "Colour / Appearance", "unit": "", "input_type": "text", "text": "Pale Yellow / Clear", "gender": "all"},
        {"name": "Reaction (pH)", "unit": "", "input_type": "numeric", "low": 4.5, "high": 8.0, "text": "4.5 - 8.0", "gender": "all"},
        {"name": "Specific Gravity", "unit": "", "input_type": "numeric", "low": 1.005, "high": 1.030, "text": "1.005 - 1.030", "gender": "all"},
        {"name": "Protein / Albumin", "unit": "", "input_type": "dropdown", "options": ["Nil", "Trace", "1+", "2+", "3+"], "text": "Nil", "gender": "all"},
        {"name": "Sugar / Glucose", "unit": "", "input_type": "dropdown", "options": ["Nil", "Trace", "1+", "2+", "3+"], "text": "Nil", "gender": "all"},
        {"name": "Pus Cells", "unit": "/HPF", "input_type": "text", "text": "2 - 4 / HPF", "gender": "all"},
        {"name": "Epithelial Cells", "unit": "/HPF", "input_type": "text", "text": "2 - 3 / HPF", "gender": "all"},
        {"name": "RBCs", "unit": "/HPF", "input_type": "text", "text": "Nil", "gender": "all"},
    ],
    "Stool R/E": [
        {"name": "Colour / Consistency", "unit": "", "input_type": "text", "text": "Brown / Semi-formed", "gender": "all"},
        {"name": "Occult Blood", "unit": "", "input_type": "dropdown", "options": ["Negative", "Positive"], "text": "Negative", "gender": "all"},
        {"name": "Ova / Cysts", "unit": "", "input_type": "text", "text": "Not Seen", "gender": "all"},
    ],
    "Micral Test Albumin Urine": [
        {"name": "Microalbumin (Urine)", "unit": "mg/L", "input_type": "dropdown", "options": ["Negative (<20 mg/L)", "Positive (20-200 mg/L)", "High (>200 mg/L)"], "text": "Negative (<20 mg/L)", "gender": "all"},
    ],
    "Urine Culture": [
        {"name": "Culture & Sensitivity Report", "unit": "", "input_type": "text", "text": "No growth after 48 hours of incubation", "gender": "all"},
    ],
    "Blood Group and Rh Typing": [
        {"name": "ABO & Rh Blood Group", "unit": "", "input_type": "dropdown", "options": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], "text": "", "gender": "all"},
    ],
    # Profiles / Bundles (§4 note)
    "Hypertension Profile": [
        {"name": "Total Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 100.0, "high": 200.0, "text": "< 200 desirable", "gender": "all"},
        {"name": "Triglycerides", "unit": "mg/dL", "input_type": "numeric", "low": 50.0, "high": 150.0, "text": "< 150 desirable", "gender": "all"},
        {"name": "HDL Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 40.0, "high": 100.0, "text": "> 40", "gender": "all"},
        {"name": "LDL Cholesterol", "unit": "mg/dL", "input_type": "numeric", "low": 50.0, "high": 100.0, "text": "< 100 desirable", "gender": "all"},
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.6, "high": 1.3, "text": "0.6 - 1.3", "gender": "all"},
        {"name": "Sodium (Na+)", "unit": "mEq/L", "input_type": "numeric", "low": 135.0, "high": 145.0, "text": "135 - 145", "gender": "all"},
        {"name": "Potassium (K+)", "unit": "mEq/L", "input_type": "numeric", "low": 3.5, "high": 5.1, "text": "3.5 - 5.1", "gender": "all"},
    ],
    "Arthritis Profile": [
        {"name": "Rheumatoid Factor (RA)", "unit": "", "input_type": "dropdown", "options": ["Negative (<18 IU/mL)", "Positive"], "text": "Negative (<18 IU/mL)", "gender": "all"},
        {"name": "C-Reactive Protein (CRP)", "unit": "mg/L", "input_type": "numeric", "low": 0.0, "high": 6.0, "text": "< 6.0 (Normal)", "gender": "all"},
        {"name": "Uric Acid", "unit": "mg/dL", "input_type": "numeric", "low": 2.6, "high": 7.2, "text": "2.6 - 7.2", "gender": "all"},
        {"name": "Serum Calcium", "unit": "mg/dL", "input_type": "numeric", "low": 8.5, "high": 10.5, "text": "8.5 - 10.5", "gender": "all"},
    ],
    "Diabetic Profile": [
        {"name": "Fasting Blood Sugar", "unit": "mg/dL", "input_type": "numeric", "low": 70.0, "high": 100.0, "text": "70 - 100", "gender": "all"},
        {"name": "Post-Prandial Blood Sugar (PP)", "unit": "mg/dL", "input_type": "numeric", "low": 70.0, "high": 140.0, "text": "70 - 140", "gender": "all"},
        {"name": "HbA1c", "unit": "%", "input_type": "numeric", "low": 4.0, "high": 5.6, "text": "Normal: <5.7 · Prediabetic: 5.7–6.4 · Diabetic: ≥6.5", "gender": "all"},
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.6, "high": 1.3, "text": "0.6 - 1.3", "gender": "all"},
    ],
    "Kidney Profile": [
        {"name": "Blood Urea", "unit": "mg/dL", "input_type": "numeric", "low": 15.0, "high": 45.0, "text": "15 - 45", "gender": "all"},
        {"name": "Serum Creatinine", "unit": "mg/dL", "input_type": "numeric", "low": 0.6, "high": 1.3, "text": "0.6 - 1.3", "gender": "all"},
        {"name": "Uric Acid", "unit": "mg/dL", "input_type": "numeric", "low": 2.6, "high": 7.2, "text": "2.6 - 7.2", "gender": "all"},
        {"name": "Sodium (Na+)", "unit": "mEq/L", "input_type": "numeric", "low": 135.0, "high": 145.0, "text": "135 - 145", "gender": "all"},
        {"name": "Potassium (K+)", "unit": "mEq/L", "input_type": "numeric", "low": 3.5, "high": 5.1, "text": "3.5 - 5.1", "gender": "all"},
        {"name": "Chloride (Cl-)", "unit": "mEq/L", "input_type": "numeric", "low": 96.0, "high": 106.0, "text": "96 - 106", "gender": "all"},
    ],
    "Anemia Profile (HB%, CBC, Iron, TIBC, Ferritin)": [
        {"name": "Hemoglobin (Hb)", "unit": "g/dL", "input_type": "numeric", "low": 13.0, "high": 17.0, "text": "13.0 - 17.0", "gender": "male"},
        {"name": "Hemoglobin (Hb)", "unit": "g/dL", "input_type": "numeric", "low": 12.0, "high": 15.5, "text": "12.0 - 15.5", "gender": "female"},
        {"name": "Total RBC Count", "unit": "million/µL", "input_type": "numeric", "low": 4.5, "high": 5.5, "text": "4.5 - 5.5", "gender": "all"},
        {"name": "Total WBC Count", "unit": "/µL", "input_type": "numeric", "low": 4000.0, "high": 11000.0, "text": "4,000 - 11,000", "gender": "all"},
        {"name": "Platelet Count", "unit": "/µL", "input_type": "numeric", "low": 150000.0, "high": 450000.0, "text": "150,000 - 450,000", "gender": "all"},
        {"name": "Serum Iron", "unit": "µg/dL", "input_type": "numeric", "low": 60.0, "high": 170.0, "text": "60 - 170", "gender": "all"},
        {"name": "Total Iron Binding Capacity (TIBC)", "unit": "µg/dL", "input_type": "numeric", "low": 240.0, "high": 450.0, "text": "240 - 450", "gender": "all"},
        {"name": "Serum Ferritin", "unit": "ng/mL", "input_type": "numeric", "low": 12.0, "high": 300.0, "text": "12 - 300", "gender": "all"},
    ],
}


def seed_test_parameters(db: Session) -> int:
    """Idempotently seed parameters for any test currently lacking parameters."""
    tests = db.query(Test).all()
    existing_test_ids = {r[0] for r in db.query(TestParameter.test_id).distinct().all()}
    seeded_tests_count = 0

    for test in tests:
        # Check if test already has parameters
        if test.id in existing_test_ids:
            continue

        param_list = PARAMETERS_SEED_DATA.get(test.name)
        if not param_list:
            # Fallback: if it's a test not explicitly in dictionary, create a single standard finding text or numeric parameter
            if "USG" in test.name or "X-Ray" in test.name or "CT" in test.name or "ECG" in test.name:
                param_list = [{"name": "Findings / Impression", "unit": "", "input_type": "text", "text": "Normal study", "gender": "all"}]
            else:
                param_list = [{"name": test.name, "unit": "", "input_type": "text", "text": "Report findings", "gender": "all"}]

        for idx, item in enumerate(param_list, start=1):
            p = TestParameter(
                test_id=test.id,
                parameter_name=item["name"],
                unit=item.get("unit"),
                input_type=item.get("input_type", "numeric"),
                dropdown_options=item.get("options"),
                reference_low=item.get("low"),
                reference_high=item.get("high"),
                reference_text=item.get("text"),
                applicable_gender=item.get("gender", "all"),
                display_order=idx
            )
            db.add(p)
        seeded_tests_count += 1

    db.commit()
    return seeded_tests_count


if __name__ == "__main__":
    print("\nSeeding Test Parameters...")
    from backend.app.core.db import init_db
    init_db()
    db = SessionLocal()
    try:
        count = seed_test_parameters(db)
        print(f"  [OK] Seeded parameters for {count} tests!")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"  [ERROR] Seeding parameters failed: {e}")
    finally:
        db.close()
