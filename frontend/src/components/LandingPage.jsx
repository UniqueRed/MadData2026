import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

function LotusLogo({ size = 64 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
      <ellipse cx="50" cy="38" rx="10" ry="28" fill="#e8548e"/>
      <ellipse cx="50" cy="38" rx="10" ry="26" fill="#f472b6" transform="rotate(-25 50 55)"/>
      <ellipse cx="50" cy="38" rx="10" ry="26" fill="#f472b6" transform="rotate(25 50 55)"/>
      <ellipse cx="50" cy="40" rx="9" ry="24" fill="#f9a8c9" transform="rotate(-50 50 58)"/>
      <ellipse cx="50" cy="40" rx="9" ry="24" fill="#f9a8c9" transform="rotate(50 50 58)"/>
      <circle cx="50" cy="52" r="6" fill="#eab308"/>
      <circle cx="50" cy="52" r="3.5" fill="#fde68a"/>
    </svg>
  );
}

const FEATURES = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="5" r="3" /><line x1="12" y1="8" x2="12" y2="14" /><line x1="12" y1="14" x2="7" y2="20" /><line x1="12" y1="14" x2="17" y2="20" />
      </svg>
    ),
    color: "#e8548e",
    bg: "linear-gradient(135deg, #fdf2f8, #fce7f3)",
    title: "46 Conditions Mapped",
    desc: "Real ICD-10 comorbidity network with age and sex-stratified progression odds.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
    ),
    color: "#eab308",
    bg: "linear-gradient(135deg, #fffbeb, #fef3c7)",
    title: "5-Year Cost Forecast",
    desc: "Out-of-pocket and drug costs projected from federal MEPS survey data.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="20" height="18" rx="2" /><path d="M2 9h20" /><path d="M10 3v18" />
      </svg>
    ),
    color: "#e8548e",
    bg: "linear-gradient(135deg, #fdf2f8, #fce7f3)",
    title: "Plan Comparison",
    desc: "Compare real CMS marketplace plans against your specific care pathway.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    color: "#eab308",
    bg: "linear-gradient(135deg, #fffbeb, #fef3c7)",
    title: "FDA Drug Data",
    desc: "Treatments, warnings, and interactions from openFDA for every condition.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="23" />
      </svg>
    ),
    color: "#e8548e",
    bg: "linear-gradient(135deg, #fdf2f8, #fce7f3)",
    title: "Natural Language",
    desc: "Describe your health in plain English — AI builds the pathway instantly.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    color: "#eab308",
    bg: "linear-gradient(135deg, #fffbeb, #fef3c7)",
    title: "AI Health Chat",
    desc: "Ask follow-up questions and get contextual explanations about your pathway.",
  },
];

export default function LandingPage({ onGetStarted }) {
  const { user, loading, signInWithGoogle } = useAuth();
  const [step, setStep] = useState(user ? "login" : "splash");

  return (
    <div className="landing">
      {step === "splash" ? (
        <>
          <section className="landing-splash">
            <LotusLogo size={96} />
            <h1 className="landing-logo-text">lotus</h1>
            <p className="landing-tagline">Your health, projected, with voice.</p>
            <button
              className="landing-cta-pink"
              onClick={() => setStep("login")}
            >
              Get Started
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </button>

            <div className="landing-scroll-hint">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          </section>

          <section className="landing-features">
            <div className="landing-features-grid">
              {FEATURES.map((f, i) => (
                <div
                  key={i}
                  className="landing-feature"
                  style={{ "--accent": f.color, "--accent-bg": f.bg, animationDelay: `${i * 0.07}s` }}
                >
                  <div className="landing-feature-icon-wrap">
                    <div className="landing-feature-icon">{f.icon}</div>
                    <div className="landing-feature-number">{String(i + 1).padStart(2, "0")}</div>
                  </div>
                  <h3>{f.title}</h3>
                  <p>{f.desc}</p>
                  <div className="landing-feature-accent-line" />
                </div>
              ))}
            </div>

            <div className="landing-data-sources">
              <div className="landing-data-tags">
                <span>MEPS HC-233</span>
                <span>ICD-10 Matrices</span>
                <span>CMS PUF</span>
                <span>openFDA</span>
              </div>
            </div>
          </section>
        </>
      ) : (
        <section className="landing-login">
          <LotusLogo size={56} />
          <h2 className="landing-login-title">Welcome to lotus</h2>
          <p className="landing-login-desc">
            Sign in to simulate your care pathway and compare insurance plans.
          </p>

          {loading ? (
            <button className="landing-cta-pink" disabled>Loading...</button>
          ) : user ? (
            <button className="landing-cta-pink" onClick={onGetStarted}>
              Continue to App
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          ) : (
            <button className="google-btn" onClick={signInWithGoogle}>
              <svg width="18" height="18" viewBox="0 0 48 48">
                <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59a14.5 14.5 0 0 1 0-9.18l-7.98-6.19a24.01 24.01 0 0 0 0 21.56l7.98-6.19z"/>
                <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              </svg>
              Continue with Google
            </button>
          )}

          <button className="landing-back" onClick={() => setStep("splash")}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Back
          </button>
        </section>
      )}
    </div>
  );
}
