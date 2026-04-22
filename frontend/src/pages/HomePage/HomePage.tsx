import { observer } from "mobx-react-lite";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { signIn, signUp } from "@/services/auth.service";
import { useStores } from "@/stores/context";
import styles from "./HomePage.module.css";

type Tab = "signin" | "signup";

const BAR_HEIGHTS = [30, 55, 80, 45, 95, 60, 35, 75, 50, 88, 40, 65, 20, 70, 48, 90, 35, 60, 78, 42];
const BAR_DURATIONS = [1.1, 1.4, 0.9, 1.6, 1.2, 1.0, 1.5, 0.8, 1.3, 1.1, 1.7, 0.95, 1.4, 1.0, 1.25, 0.85, 1.3, 1.1, 0.9, 1.5];
const BAR_DELAYS = [0, 0.2, 0.4, 0.1, 0.3, 0.5, 0.15, 0.35, 0.25, 0.45, 0.05, 0.3, 0.4, 0.1, 0.2, 0.5, 0.35, 0.15, 0.4, 0.25];

export const HomePage = observer(() => {
  const { auth } = useStores();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("signin");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [signInForm, setSignInForm] = useState({ email: "", password: "" });
  const [signUpForm, setSignUpForm] = useState({ email: "", username: "", password: "" });

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signIn(auth, signInForm.email, signInForm.password);
      void navigate("/profile");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signUp(auth, signUpForm.email, signUpForm.username, signUpForm.password);
      void navigate("/profile");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign up failed");
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (next: Tab) => {
    setTab(next);
    setError(null);
  };

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.logo}>
          <svg className={styles.logoIcon} viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="rgba(124,92,252,0.15)" />
            {[4, 8, 12, 16, 20, 24, 28].map((x, i) => (
              <rect
                key={x}
                x={x - 1}
                y={32 - [16, 24, 12, 28, 10, 20, 14][i]!}
                width="2"
                height={[16, 24, 12, 28, 10, 20, 14][i]}
                rx="1"
                fill="currentColor"
              />
            ))}
          </svg>
          Music Genre Sommelier
        </div>

        <h1 className={styles.title}>
          AI That Hears<br />Your Genre
        </h1>

        <p className={styles.tagline}>
          Upload a track. Let the AI listen. Get a precise genre classification
          backed by mel-spectrogram analysis and computer vision.
        </p>

        <div className={styles.bars} aria-hidden="true">
          {BAR_HEIGHTS.map((h, i) => (
            <div
              key={i}
              className={styles.bar}
              style={{
                height: `${h}%`,
                "--dur": `${BAR_DURATIONS[i]}s`,
                "--delay": `${BAR_DELAYS[i]}s`,
              } as React.CSSProperties}
            />
          ))}
        </div>
      </section>

      <div className={styles.features}>
        {[
          { icon: "🎵", title: "Upload Audio", desc: "MP3, WAV, FLAC and more. Your files stay private." },
          { icon: "🧠", title: "AI Genre Detection", desc: "Spectrogram-based CV model classifies with high accuracy." },
          { icon: "⚡", title: "Pay Per Inference", desc: "Only pay when the prediction succeeds." },
        ].map((f) => (
          <div key={f.title} className={styles.featureCard}>
            <div className={styles.featureIcon}>{f.icon}</div>
            <div className={styles.featureTitle}>{f.title}</div>
            <div className={styles.featureDesc}>{f.desc}</div>
          </div>
        ))}
      </div>

      <div className={styles.authPanel}>
        <div className={styles.tabs} role="tablist">
          <button
            role="tab"
            aria-selected={tab === "signin"}
            className={`${styles.tab} ${tab === "signin" ? styles.tabActive : ""}`}
            onClick={() => handleTabChange("signin")}
          >
            Sign In
          </button>
          <button
            role="tab"
            aria-selected={tab === "signup"}
            className={`${styles.tab} ${tab === "signup" ? styles.tabActive : ""}`}
            onClick={() => handleTabChange("signup")}
          >
            Sign Up
          </button>
        </div>

        {tab === "signin" ? (
          <form className={styles.form} onSubmit={(e) => void handleSignIn(e)}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="signin-email">Email</label>
              <input
                id="signin-email"
                type="email"
                className={styles.input}
                placeholder="you@example.com"
                value={signInForm.email}
                onChange={(e) => setSignInForm({ ...signInForm, email: e.target.value })}
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="signin-password">Password</label>
              <input
                id="signin-password"
                type="password"
                className={styles.input}
                placeholder="••••••••"
                value={signInForm.password}
                onChange={(e) => setSignInForm({ ...signInForm, password: e.target.value })}
                required
                disabled={loading}
                autoComplete="current-password"
              />
            </div>
            {error !== null && <p className="error-message" role="alert">{error}</p>}
            <button type="submit" className={styles.submitBtn} disabled={loading}>
              {loading ? <span className="spinner" /> : null}
              {loading ? "Signing in…" : "Sign In"}
            </button>
          </form>
        ) : (
          <form className={styles.form} onSubmit={(e) => void handleSignUp(e)}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="signup-email">Email</label>
              <input
                id="signup-email"
                type="email"
                className={styles.input}
                placeholder="you@example.com"
                value={signUpForm.email}
                onChange={(e) => setSignUpForm({ ...signUpForm, email: e.target.value })}
                required
                disabled={loading}
                autoComplete="email"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="signup-username">Username</label>
              <input
                id="signup-username"
                type="text"
                className={styles.input}
                placeholder="soundhunter"
                value={signUpForm.username}
                onChange={(e) => setSignUpForm({ ...signUpForm, username: e.target.value })}
                required
                disabled={loading}
                autoComplete="username"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="signup-password">Password</label>
              <input
                id="signup-password"
                type="password"
                className={styles.input}
                placeholder="••••••••"
                value={signUpForm.password}
                onChange={(e) => setSignUpForm({ ...signUpForm, password: e.target.value })}
                required
                disabled={loading}
                autoComplete="new-password"
              />
            </div>
            {error !== null && <p className="error-message" role="alert">{error}</p>}
            <button type="submit" className={styles.submitBtn} disabled={loading}>
              {loading ? <span className="spinner" /> : null}
              {loading ? "Creating account…" : "Create Account"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
});
