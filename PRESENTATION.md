# lotus

### A Clinical-Financial Digital Twin for Personalized Healthcare Cost Projection

---

## Slide 1: The Problem

**Healthcare costs are the #1 cause of bankruptcy in America — and patients have no way to see them coming.**

- Patients are blindsided by costs they could have predicted
- Chronic conditions cascade — one diagnosis leads to X more over X years
- Insurance plan selection is a guessing game with no personalized data
- Doctors treat conditions in isolation; no one models the full financial trajectory

> "What will my health cost me over the next 5 years?" — No tool answers this today.

---

## Slide 2: The Solution — lotus

**A digital twin of your health and finances.**

Describe your health in plain language. lotus builds a probabilistic care pathway across X chronic diseases, projects your out-of-pocket costs over X years, and lets you compare real marketplace insurance plans — all backed by federal data.

**Three inputs. One complete picture.**
1. Your conditions (voice or text — natural language)
2. Your demographics (age, sex)
3. Your insurance plan

**What you get:**
- A visual map of where your health is heading
- Dollar-precise cost projections grounded in real claims data
- Actionable intervention scenarios with projected savings
- Side-by-side marketplace plan comparison against your personal pathway

---

## Slide 3: How It Works — Architecture Overview

```
 [Patient]
    |
    |  "I'm 52 with diabetes and high blood pressure"
    v
 [Voice / Text Input]  ───>  [LLM Parser]  ───>  [Structured Profile]
                                                        |
                                                        v
                                              [Simulation Engine]
                                              /        |        \
                                             v         v         v
                                       [Comorbidity  [MEPS    [Drug Cost
                                        Network]     Claims]   Data]
                                             \         |        /
                                              v        v       v
                                          [Care Pathway Graph]
                                                   |
                                          +--------+--------+
                                          |                 |
                                    [Interactive      [Insurance Plan
                                     Visualization]    Comparison]
```

---

## Slide 4: Data Foundation

**Every number in lotus comes from federal health data — nothing is invented.**

| Data Source | What It Provides | Scale |
|---|---|---|
| **MEPS HC-233** | Real healthcare expenditures by condition, age, sex, insurance | X person-level records |
| **ICD-10 Comorbidity Network** | Disease-to-disease progression odds ratios | X ICD-10 codes mapped to X conditions |
| **MEPS H239 (Part D)** | Prescription drug costs per condition | X drug cost records |
| **CMS Marketplace PUF** | Real insurance plan details — premiums, deductibles, OOP max | Every marketplace plan in X states |

**Key design principle:** The LLM is never allowed to invent costs or probabilities. All numbers flow from the data.

---

## Slide 5: The Comorbidity Network

**Diseases don't exist in isolation. They cascade.**

- X chronic conditions connected through an epidemiological odds-ratio matrix
- Stratified by X age groups and X sexes (X total strata)
- Built from ICD-10 code co-occurrence in real patient populations
- Edges represent: "If you have condition A, your odds of developing condition B are X times higher"

**Example cascade:**
```
Obesity  ──(Xx odds)──>  Type 2 Diabetes
                              |
                    +---------+---------+
                    |                   |
              (Xx odds)           (Xx odds)
                    |                   |
                    v                   v
            Chronic Kidney       Heart Failure
              Disease                 |
                                (Xx odds)
                                      |
                                      v
                                   Stroke
```

Each edge is a real epidemiological odds ratio — not a guess.

---

## Slide 6: Condition Detection — Meeting Patients Where They Are

**Patients don't speak in ICD-10 codes. They say things like:**

- "My sugar's through the roof"
- "I can't breathe when I walk upstairs"
- "My knees are shot"
- "I've been peeing a lot and I'm always thirsty"

**Two-layer detection system:**

1. **Deterministic regex engine** — X+ keyword patterns across X conditions
   - Handles colloquial language, slang, and symptom descriptions
   - Same input always gives same output (reproducible)

2. **LLM fallback** (Groq Llama X-XB) — catches what regex misses
   - Maps unrecognized symptoms to the closest condition(s)
   - Distinguishes confirmed diagnoses from suspected symptoms
   - Returns relevance scores (X.0 – X.0) for symptom-derived conditions

**Result:** Patients describe their health however they want. The system understands.

---

## Slide 7: The Simulation Engine

**From conditions to a X-year financial projection in under X seconds.**

**Step 1: Build the graph**
- Start with confirmed conditions as root nodes
- Expand through comorbidity network using odds ratios
- Filter weak associations (below X threshold)
- Expand strong associations to depth X

**Step 2: Calculate probabilities**
- Convert odds ratios to annual transition probabilities using epidemiological formula
- Cap at X% annual transition to prevent unrealistic spikes
- For symptom-derived conditions: blend LLM confidence with comorbidity prior

**Step 3: Estimate costs**
- X-tier cost lookup: MEPS stratified -> MEPS summary -> Drug cost extrapolation -> Clinical fallback
- Out-of-pocket calculation respects deductible, coinsurance, and OOP max
- X-year expected value = annual cost x probability x years active

---

## Slide 8: The Visual — Interactive Care Pathway

**A living map of your health trajectory.**

- **Circular radial layout** — your profile at center, conditions radiating outward by risk depth
- **Color-coded nodes:**
  - Pink = current conditions you have today
  - Yellow = possible future conditions
  - Dark red = high-cost risks (>$X/year)
  - Green = interventions you've applied
- **Interactive:** tap any node to see its clinical description, likelihood, annual cost, and how it connects to your other conditions
- **Focus mode:** tap a condition to highlight its entire progression chain, dimming everything else

---

## Slide 9: Interventions — "What If I Start a Statin?"

**X evidence-based interventions with real risk reduction data.**

| Intervention | Example Effect |
|---|---|
| **Metformin** | X% reduction in diabetes progression from pre-diabetes |
| **SGLT2 Inhibitor** | X% reduction in CKD risk for diabetic patients |
| **Statin** | X% reduction in coronary artery disease from high cholesterol |
| **ACE Inhibitor** | X% reduction in stroke risk from hypertension |
| **Lifestyle Changes** | X% reduction in diabetes risk from obesity |

**How it works:**
1. User says "What if I start a statin?"
2. LLM parses intent and intervention
3. Engine re-runs pathway with risk multipliers applied
4. Graph updates in real-time
5. Cost savings displayed: "Estimated X-year savings: $X"

---

## Slide 10: Insurance Plan Comparison

**Stop guessing which insurance plan is right for you.**

**The problem:** Choosing a health plan means comparing premiums, deductibles, and OOP maximums — without knowing what your health will actually cost.

**lotus solves this:**
1. Search real CMS marketplace plans by state and metal level
2. Select up to X plans to compare
3. lotus simulates your personal care pathway against each plan's specific cost-sharing structure
4. See X-year total cost (premiums + out-of-pocket) side by side
5. System highlights the best value plan for your specific health profile

**Data:** Every plan in the CMS marketplace — real premiums, real deductibles, real OOP limits.

---

## Slide 11: Conversational AI — Ask Anything

**After building your pathway, ask any question.**

- "What's my biggest risk?" -> References your top risks with real probabilities
- "What should I do about my blood pressure?" -> Suggests specific interventions
- "How much would a statin save me?" -> Answers with projection data
- "Tell me more about heart failure" -> Explains in context of your profile
- "I live in poverty, what can I do?" -> Discusses accessible options and programs
- Follow-ups work: "Tell me more about that" -> Conversation history maintained

**Powered by:** LLM with full patient context (profile + graph + conversation history). Every response grounded in the simulation data.

---

## Slide 12: Voice-First Design

**Built for accessibility — speak your health, hear your future.**

- Voice input via browser speech recognition
- Natural language processing — no forms, no dropdowns, no medical jargon required
- Responses designed for voice output (X-X sentences, warm and direct)
- Entire flow works without typing a single character

**Why voice matters:**
- Health literacy is a barrier — X% of US adults have limited health literacy
- Elderly patients struggle with complex forms
- Voice is the most natural way to describe health

---

## Slide 13: Real-World Impact

**Who this helps:**

**Patients**
- See the financial trajectory of their conditions before costs arrive
- Make informed intervention decisions with real projected savings
- Choose the right insurance plan based on their personal health, not generic advice

**Healthcare navigators & social workers**
- Quickly model a patient's X-year outlook during intake
- Demonstrate cost impact of medication adherence
- Guide insurance enrollment with data-backed plan recommendations

**Policy researchers**
- Model population-level cost trajectories across demographics
- Quantify intervention cost-effectiveness at scale
- Identify high-cost risk pathways in specific populations

---

## Slide 14: Technical Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, Vite, Cytoscape.js |
| **Backend** | FastAPI (Python, async) |
| **LLM** | Groq (Llama X-XB Versatile) |
| **Auth** | Supabase (Google OAuth) |
| **Data** | MEPS, CMS PUF, ICD-10 Comorbidity Networks |
| **Voice** | Web Speech API |

**Performance:**
- Lazy-loaded data with in-memory caching
- Async LLM calls (non-blocking)
- Pre-calculated graph layouts for instant rendering
- Full pathway generation in under X seconds

---

## Slide 15: What Makes This Different

| Existing Tools | lotus |
|---|---|
| Generic cost calculators | Personalized to your exact conditions, age, sex, insurance |
| Single-condition focus | Models X conditions and their cascading interactions |
| Static cost estimates | Dynamic X-year projections with probabilistic modeling |
| No intervention modeling | "What-if" scenarios with real risk reduction data |
| Separate from plan shopping | Simulates your pathway against real marketplace plans |
| Requires medical knowledge | Natural language — voice or text, plain English |

---

## Slide 16: The Data Pipeline

```
[Raw Federal Data]
       |
       v
[Processing Layer]
  - MEPS HC-233 -> Condition costs by demographic strata
  - ICD-10 GEXF files -> Comorbidity odds-ratio matrix (X strata)
  - H239 Part D -> Drug costs per condition
  - CMS PUF -> Marketplace plan attributes + premiums
       |
       v
[Runtime Data]
  - condition_costs.csv (stratified expenditures)
  - combined_adjacency_ICD.csv (X x X odds-ratio matrix)
  - drug_costs_by_condition.json
  - icd_mapping.json (X ICD codes -> X conditions)
  - plan_attributes_PUF.csv + Rate_PUF.csv
       |
       v
[Simulation Engine]
  - Probabilistic pathway expansion
  - Multi-tier cost estimation
  - Intervention effect modeling
  - Insurance OOP calculation
```

---

## Slide 17: Safety & Accuracy

**Built-in guardrails at every layer:**

- LLM is **never allowed to invent** costs or probabilities — all numbers from data
- Condition detection is **deterministic-first** (regex), LLM is only a fallback
- Transition probabilities **capped at X%** annual to prevent unrealistic projections
- MEPS stratification requires minimum X observations per cell — thin cells fall back to broader aggregates
- Symptom-derived conditions clearly marked as "AI estimates" with dashed borders
- System prompt enforces plain language — no internal code keys exposed to patients

---

## Slide 18: Demo Flow

```
1.  User: "I'm a 55-year-old man with diabetes and high blood pressure on a PPO"
         |
2.  System builds profile -> Generates pathway -> X health states mapped
         |
3.  Visual: Interactive graph showing current conditions,
            future risks (CKD, heart failure, stroke...),
            and projected X-year OOP cost
         |
4.  User: "What's my biggest risk?"
    Bot:  "Your top risk is [condition] at X% likelihood, ~$X/year..."
         |
5.  User: "What if I start a statin?"
    System: Recalculates pathway -> Shows X-year savings of $X
         |
6.  User switches to Compare Plans tab
    -> Searches marketplace plans in their state
    -> Selects 3 plans
    -> Sees total 5-year cost (premiums + OOP) for each
    -> Picks the best value plan for their specific health
```

---

## Slide 19: Future Directions

- **More interventions** — surgical options, specialist referrals, preventive screenings
- **Medication adherence modeling** — project cost impact of stopping/starting medications
- **Family history integration** — genetic risk factors in the comorbidity model
- **Employer/benefits integration** — model employer-sponsored plans, not just marketplace
- **Population health dashboard** — aggregate view for healthcare organizations
- **Mobile app** — voice-first experience optimized for phones
- **Multi-language support** — health literacy across language barriers

---

## Slide 20: Summary

**lotus turns health data into health decisions.**

- X chronic conditions modeled with real epidemiological data
- X-year cost projections personalized to your demographics and insurance
- Evidence-based intervention scenarios with projected savings
- Real marketplace plan comparison against your personal care pathway
- Voice-powered, natural language — no medical knowledge required
- Every number backed by federal MEPS and CMS data

> Your health has a financial future. lotus helps you see it — and change it.
