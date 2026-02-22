import { useAuth } from "../contexts/AuthContext";

export default function LandingPage({ onGetStarted }) {
  const { user, loading, signInWithGoogle } = useAuth();

  return (
    <div className="landing">
      <div className="landing-hero">
        <span className="landing-badge">Interactive Disease Progression & Insurance Cost Map</span>
        <h1 className="landing-headline">
          Know What Your Health <span className="text-purple">Will Cost</span>
        </h1>
        <p className="landing-subtitle">
          Describe your conditions in plain language. lotus builds a
          probabilistic care pathway across 46 chronic diseases, projects your
          out-of-pocket costs over 5 years, and lets you compare real
          marketplace insurance plans — all backed by federal MEPS and CMS data.
        </p>

        {loading ? (
          <button className="landing-cta auth-loading" disabled>
            Loading...
          </button>
        ) : user ? (
          <button className="landing-cta" onClick={onGetStarted}>
            Start Simulation
          </button>
        ) : (
          <button className="google-btn" onClick={signInWithGoogle}>
            <svg width="20" height="20" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59a14.5 14.5 0 0 1 0-9.18l-7.98-6.19a24.01 24.01 0 0 0 0 21.56l7.98-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            Sign in with Google
          </button>
        )}
      </div>

      <div className="landing-stats">
        {[
          { value: "45+", label: "Conditions" },
          { value: "1,080", label: "ICD-10 Codes" },
          { value: "28K+", label: "MEPS Records" },
          { value: "5-Year", label: "Projections" },
        ].map((s) => (
          <div key={s.label} className="stat-card">
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="landing-features">
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#e8548e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="5" r="3" /><line x1="12" y1="8" x2="12" y2="14" /><line x1="12" y1="14" x2="7" y2="20" /><line x1="12" y1="14" x2="17" y2="20" /><circle cx="7" cy="20" r="2" /><circle cx="17" cy="20" r="2" />
            </svg>
          </div>
          <h3>Comorbidity Network</h3>
          <p>
            Your conditions connect to future risks through a real
            epidemiological odds-ratio matrix — stratified by age, sex, and
            insurance type.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="18" rx="2" /><path d="M2 9h20" /><path d="M10 3v18" />
            </svg>
          </div>
          <h3>Marketplace Plan Comparison</h3>
          <p>
            Search real CMS marketplace plans by state and metal level, then
            simulate your exact pathway against each plan's deductible,
            coinsurance, and OOP max.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ea8c00" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" y1="19" x2="12" y2="23" /><line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </div>
          <h3>Voice-Powered Input</h3>
          <p>
            Speak or type naturally — &ldquo;I&rsquo;m a 52-year-old with
            diabetes and high blood pressure on a PPO.&rdquo; NLP parses your
            profile and builds the pathway instantly.
          </p>
        </div>
      </div>

      <p className="landing-attribution">
        Built on MEPS HC-233, ICD-10 comorbidity matrices, and CMS Plan &amp; Rate Public Use Files
      </p>
    </div>
  );
}
