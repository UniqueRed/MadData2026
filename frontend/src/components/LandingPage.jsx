import { useAuth } from "../contexts/AuthContext";

export default function LandingPage({ onGetStarted }) {
  const { user, loading, signInWithGoogle } = useAuth();

  return (
    <div className="landing">
      <div className="landing-hero">
        <span className="landing-badge">Clinical-Financial Digital Twin</span>
        <h1 className="landing-headline">
          See Your Health Costs <span className="text-purple">Before They Happen</span>
        </h1>
        <p className="landing-subtitle">
          miff simulates your personal care pathway — mapping conditions,
          treatments, and out-of-pocket costs over the next 5 years so you can
          make smarter insurance and health decisions.
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
          { value: "5-Year", label: "Projections" },
          { value: "14+", label: "Conditions" },
          { value: "Voice", label: "Powered" },
          { value: "Federal", label: "Data" },
        ].map((s) => (
          <div key={s.label} className="stat-card">
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="landing-features">
        <div className="feature-card">
          <div className="feature-icon">&#x1f9ec;</div>
          <h3>Care Pathway Simulation</h3>
          <p>
            Describe your health profile and get a personalized graph of
            conditions, treatments, and projected costs.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">&#x1f4ca;</div>
          <h3>Insurance Plan Comparison</h3>
          <p>
            Compare PPO, HMO, and HDHP plans side-by-side to find the cheapest
            option for your specific situation.
          </p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">&#x1f52e;</div>
          <h3>What-If Scenarios</h3>
          <p>
            Ask &ldquo;What if I start Metformin?&rdquo; or &ldquo;What if I
            switch to an HMO?&rdquo; and see the financial impact instantly.
          </p>
        </div>
      </div>

      <p className="landing-attribution">
        Powered by MEPS (Medical Expenditure Panel Survey) &amp; CMS public data
      </p>
    </div>
  );
}
