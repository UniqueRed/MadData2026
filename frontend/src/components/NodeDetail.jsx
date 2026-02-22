const NODE_TYPE_INFO = {
  current: { label: "Current Condition", color: "#e8548e" },
  future: { label: "Possible Future", color: "#eab308" },
  high_cost: { label: "High Cost Risk", color: "#9d174d" },
  intervention: { label: "Intervention", color: "#22c55e" },
};

const CONDITION_DESCRIPTIONS = {
  // Legacy conditions
  "Pre-Diabetes": "Blood sugar levels are higher than normal but not yet in the diabetes range. Lifestyle changes can prevent progression.",
  "Type 2 Diabetes": "A chronic condition where the body doesn't use insulin properly, leading to high blood sugar and potential complications.",
  "CKD Stage 2": "Mild kidney damage with slightly reduced kidney function. Early intervention can slow progression.",
  "CKD Stage 3": "Moderate kidney damage with noticeably reduced function. Requires active management to prevent dialysis.",
  "Retinopathy": "Damage to blood vessels in the retina caused by diabetes. Can lead to vision loss if untreated.",
  "Heart Attack": "A blockage of blood flow to the heart muscle. A life-threatening emergency requiring immediate care.",
  "Dialysis": "A treatment that filters blood when kidneys can no longer function. Requires multiple sessions per week.",
  "Diabetic Foot": "Foot complications from diabetes including ulcers, infections, and poor circulation.",
  "Angina": "Chest pain caused by reduced blood flow to the heart. Often a symptom of coronary artery disease.",
  // All 46 comorbidity network conditions
  "Hypertension": "Persistently elevated blood pressure that increases risk of heart disease, stroke, and kidney damage.",
  "High Cholesterol": "Elevated levels of cholesterol in the blood, increasing risk of heart disease and stroke.",
  "Chronic Low Back Pain": "Persistent pain in the lower back lasting 12 weeks or more. One of the most common causes of disability.",
  "Severe Vision Loss": "Significant reduction in visual acuity from conditions like macular degeneration, glaucoma, or diabetic eye disease.",
  "Joint Arthrosis": "Degenerative joint disease (osteoarthritis) where cartilage wears down, causing pain and stiffness.",
  "Diabetes Mellitus": "A chronic metabolic condition affecting how the body processes blood sugar, leading to complications across multiple organs.",
  "Coronary Artery Disease": "Narrowing of the coronary arteries reducing blood flow to the heart. Major cause of heart attacks.",
  "Thyroid Disease": "Disorders of the thyroid gland affecting metabolism. Includes hypothyroidism and hyperthyroidism.",
  "Cardiac Arrhythmia": "Irregular heart rhythm including atrial fibrillation. Can increase stroke risk and cause palpitations.",
  "Obesity": "Excess body fat (BMI 30+) that increases risk of diabetes, heart disease, and many other conditions.",
  "Gout": "A form of arthritis caused by uric acid crystal buildup in joints, causing sudden severe pain and swelling.",
  "Prostatic Hyperplasia": "Enlarged prostate gland common in older men. Causes difficulty urinating and frequent urination.",
  "Varicose Veins": "Enlarged, twisted veins usually in the legs. Caused by weakened valves allowing blood to pool.",
  "Liver Disease": "Damage to the liver from various causes including fatty liver, hepatitis, and alcohol use.",
  "Depression": "A mood disorder causing persistent feelings of sadness and loss of interest. Affects daily functioning.",
  "Asthma / COPD": "Chronic respiratory conditions causing airway inflammation, breathing difficulty, and reduced lung function.",
  "Gynecological Problems": "Conditions affecting the female reproductive system including menopause and endometriosis.",
  "Atherosclerosis / PAOD": "Hardening and narrowing of arteries, especially in the legs. Causes pain during walking.",
  "Osteoporosis": "Weakened bones that are more prone to fractures. Common in postmenopausal women and older adults.",
  "Chronic Kidney Disease": "Progressive loss of kidney function over time. Early detection and management can slow progression.",
  "Stroke": "A medical emergency where blood supply to the brain is interrupted, causing brain damage.",
  "Heart Failure": "The heart can't pump blood efficiently. Causes fatigue, shortness of breath, and fluid buildup.",
  "Hearing Loss": "Partial or complete inability to hear. Can be caused by aging, noise exposure, or disease.",
  "Gallstones": "Hardened deposits in the gallbladder that can cause pain, inflammation, and digestive issues.",
  "Somatoform Disorder": "Physical symptoms without a clear medical cause, often related to psychological stress.",
  "Hemorrhoids": "Swollen blood vessels in the rectum or anus causing discomfort, itching, and bleeding.",
  "Diverticulosis": "Small pouches that form in the walls of the colon. Can become inflamed (diverticulitis).",
  "Rheumatoid Arthritis": "An autoimmune condition causing chronic joint inflammation, pain, and progressive damage.",
  "Cardiac Valve Disorder": "Malfunction of one or more heart valves affecting blood flow through the heart.",
  "Neuropathy": "Nerve damage, often in hands and feet, causing numbness, tingling, and pain. Common in diabetes.",
  "Dizziness / Vertigo": "Sensation of spinning or unsteadiness. Can be caused by inner ear problems or other conditions.",
  "Dementia": "Progressive decline in cognitive function affecting memory, thinking, and daily activities. Includes Alzheimer's.",
  "Urinary Incontinence": "Involuntary leakage of urine. Common in older adults and can significantly impact quality of life.",
  "Kidney Stones": "Hard mineral deposits that form in the kidneys. Can cause severe pain when passing through the urinary tract.",
  "Anemia": "Low red blood cell count or hemoglobin, causing fatigue, weakness, and shortness of breath.",
  "Anxiety": "Persistent excessive worry and fear that interferes with daily activities. Includes generalized anxiety and panic disorder.",
  "Psoriasis": "A chronic autoimmune skin condition causing red, scaly patches. Can also affect joints.",
  "Migraine": "Recurring severe headaches often with nausea, light sensitivity, and visual disturbances.",
  "Parkinson's Disease": "A progressive neurological disorder affecting movement. Causes tremor, stiffness, and balance problems.",
  "Cancer": "A group of diseases involving abnormal cell growth with the potential to spread to other parts of the body.",
  "Allergy": "Immune system overreaction to substances like pollen, food, or medications. Ranges from mild to severe.",
  "GERD / Gastritis": "Chronic acid reflux or stomach lining inflammation causing heartburn, pain, and digestive discomfort.",
  "Sexual Dysfunction": "Difficulty with sexual response or satisfaction. Can have physical or psychological causes.",
  "Insomnia": "Chronic difficulty falling or staying asleep. Affects energy, mood, and overall health.",
  "Tobacco Use Disorder": "Dependence on tobacco/nicotine. Major risk factor for cancer, heart disease, and lung disease.",
  "Hypotension": "Abnormally low blood pressure that can cause dizziness, fainting, and fatigue.",
};

export default function NodeDetail({ node, onClose }) {
  if (!node) return null;

  const name = node.label?.split("\n")[0] || node.id;
  const typeInfo = NODE_TYPE_INFO[node.nodeType] || { label: "Unknown", color: "#94a3b8" };
  const description = CONDITION_DESCRIPTIONS[name];
  const likelihood = node.probability != null ? node.probability * 100 : null;

  return (
    <div className="node-overlay">
      <div className="node-overlay-header">
        <div className="node-overlay-badge" style={{ background: typeInfo.color }}>
          {typeInfo.label}
        </div>
        <button className="node-overlay-close" onClick={onClose} title="Close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <h3 className="node-overlay-title">{name}</h3>

      {description && (
        <p className="node-overlay-desc">{description}</p>
      )}

      {likelihood !== null && (
        <div className="node-overlay-likelihood">
          <div className="likelihood-bar-track">
            <div
              className="likelihood-bar-fill"
              style={{ width: `${Math.min(likelihood, 100)}%` }}
            />
          </div>
          <div className="likelihood-text">
            <span className="likelihood-value">{likelihood.toFixed(1)}%</span>
            <span className="likelihood-label">associated risk probability</span>
          </div>
        </div>
      )}

      <div className="node-overlay-stats">
        <div className="node-stat">
          <span className="node-stat-value">${Math.round(node.annualCost).toLocaleString()}</span>
          <span className="node-stat-label">Annual Cost</span>
        </div>
        <div className="node-stat">
          <span className="node-stat-value oop">${Math.round(node.oopEstimate).toLocaleString()}</span>
          <span className="node-stat-label">Out-of-Pocket</span>
        </div>
        {node.year > 0 && (
          <div className="node-stat">
            <span className="node-stat-value">Year {node.year}</span>
            <span className="node-stat-label">Onset</span>
          </div>
        )}
      </div>
    </div>
  );
}
