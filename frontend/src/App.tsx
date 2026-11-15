import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

type Profile = {
  personal_info?: { name?: string; email?: string; phone?: string };
  summary?: string;
  experience?: string[];
  education?: string[];
  skills?: string[];
  projects?: string[];
  certifications?: string[];
};
type Resume = {
  id: number;
  original_filename: string;
  status: "uploaded" | "parsed" | "needs_review" | "failed";
  parse_error: string;
  extracted_profile: Profile;
  extracted_text: string;
  created_at: string;
};
type AuthMode = "login" | "register";
const API_BASE = (import.meta as ImportMeta & { env: { VITE_API_BASE_URL?: string } }).env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

async function api<T>(path: string, token?: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Token ${token}`);
  if (!(options.body instanceof FormData) && options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof data === "object" ? Object.values(data).flat().join(" ") : "Request failed";
    throw new Error(String(message) || "Request failed");
  }
  return data as T;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("jobpilot_token") || "");
  const [mode, setMode] = useState<AuthMode>("register");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selected, setSelected] = useState<Resume | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileDraft, setProfileDraft] = useState("");

  const latestResume = useMemo(() => selected || resumes[0] || null, [selected, resumes]);

  async function loadResumes(activeToken: string) {
    const data = await api<Resume[]>("/resumes/", activeToken);
    setResumes(data);
    if (data.length) setSelected(data[0]);
  }

  useEffect(() => {
    if (!token) return;
    loadResumes(token).catch((err: Error) => {
      setError(err.message);
      setToken("");
      localStorage.removeItem("jobpilot_token");
    });
  }, [token]);

  async function handleAuth(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const endpoint = mode === "register" ? "/auth/register/" : "/auth/login/";
      const payload = mode === "register" ? { username, email, password } : { username, password };
      const result = await api<{ token: string }>(endpoint, undefined, { method: "POST", body: JSON.stringify(payload) });
      localStorage.setItem("jobpilot_token", result.token);
      setToken(result.token);
      setNotice("You're signed in. Upload your resume to create your candidate profile.");
    } catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  }

  function chooseFile(next: File | null) {
    setError(""); setNotice("");
    if (!next) return;
    const extension = next.name.toLowerCase().split(".").pop();
    if (!["pdf", "docx"].includes(extension || "")) { setError("Choose a PDF or Word DOCX file."); return; }
    if (next.size > 10 * 1024 * 1024) { setError("File size must be 10 MB or less."); return; }
    setFile(next);
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!file || !token) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const body = new FormData(); body.append("file", file);
      const result = await api<Resume>("/resumes/", token, { method: "POST", body });
      setResumes((current) => [result, ...current.filter((item) => item.id !== result.id)]);
      setSelected(result); setFile(null);
      setNotice(result.status === "failed" ? "The file was saved, but text extraction needs attention." : "Resume uploaded and parsed. Review the extracted profile below.");
    } catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  }

  async function saveProfile() {
    if (!latestResume) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const parsed = JSON.parse(profileDraft) as Profile;
      const updated = await api<{ id: number; extracted_profile: Profile }>(`/resumes/${latestResume.id}/profile/`, token, { method: "PATCH", body: JSON.stringify({ extracted_profile: parsed }) });
      const next = { ...latestResume, extracted_profile: updated.extracted_profile };
      setResumes((current) => current.map((item) => item.id === next.id ? next : item));
      setSelected(next); setEditingProfile(false); setNotice("Candidate profile saved.");
    } catch (err) {
      setError(err instanceof SyntaxError ? "Profile JSON is invalid. Please correct it before saving." : (err as Error).message);
    } finally { setBusy(false); }
  }

  function logout() {
    localStorage.removeItem("jobpilot_token"); setToken(""); setResumes([]); setSelected(null); setFile(null);
  }

  const profile = latestResume?.extracted_profile || {};
  const info = profile.personal_info || {};

  if (!token) return (
    <div className="auth-page">
      <div className="auth-brand"><span className="brand-mark">J</span><span>jobpilot<span className="brand-ai">.ai</span></span></div>
      <section className="auth-card">
        <div className="eyebrow">YOUR CAREER WORKSPACE</div>
        <h1>{mode === "register" ? "Build your next move." : "Welcome back."}</h1>
        <p className="muted">Your resume. Your experience. Tailored for every opportunity.</p>
        <form onSubmit={handleAuth} className="auth-form">
          <label>Username<input required value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" placeholder="Choose a username" /></label>
          {mode === "register" && <label>Email address<input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" /></label>}
          <label>Password<input required minLength={mode === "register" ? 10 : 1} type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "register" ? "new-password" : "current-password"} placeholder={mode === "register" ? "At least 10 characters" : "Your password"} /></label>
          {error && <div className="alert error">{error}</div>}
          <button className="primary-btn full" disabled={busy}>{busy ? "Please wait…" : mode === "register" ? "Create your workspace" : "Sign in"} <span>↗</span></button>
        </form>
        <div className="switch-auth">{mode === "register" ? "Already have an account?" : "New to JobPilot AI?"} <button className="text-btn" onClick={() => { setMode(mode === "register" ? "login" : "register"); setError(""); }}>{mode === "register" ? "Sign in" : "Create account"}</button></div>
      </section>
      <div className="auth-foot">Private by design · Your resumes are only visible to your account</div>
    </div>
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="side-brand"><span className="brand-mark">J</span><span>jobpilot<span className="brand-ai">.ai</span></span></div>
        <div className="workspace-label">WORKSPACE</div>
        <button className="nav-item active"><span>▤</span> Resume intelligence</button>
        <button className="nav-item" disabled><span>⌕</span> Job discovery <small>SOON</small></button>
        <button className="nav-item" disabled><span>◷</span> Applications <small>SOON</small></button>
        <div className="sidebar-bottom"><div className="user-avatar">{username.slice(0,1).toUpperCase()}</div><div className="user-meta"><strong>{username}</strong><span>Personal workspace</span></div><button className="logout-btn" onClick={logout} title="Sign out">↗</button></div>
      </aside>
      <main className="main-content">
        <header className="top-header"><div><span className="breadcrumb">Workspace</span><span className="crumb-sep">/</span><strong>Resume intelligence</strong></div><div className="header-right"><span className="secure-label"><i /> Private workspace</span><span className="header-avatar">{username.slice(0,1).toUpperCase()}</span></div></header>
        <div className="page-wrap">
          <section className="welcome-row"><div><div className="eyebrow">PHASE 01 · RESUME INTELLIGENCE</div><h1>Make every application <em>count.</em></h1><p>Start with your own resume. We'll turn it into a structured, reusable career profile.</p></div><div className="step-pill"><span>01</span> Your profile</div></section>
          {(error || notice) && <div className={`alert ${error ? "error" : "success"}`}>{error || notice}<button onClick={() => { setError(""); setNotice(""); }}>×</button></div>}
          <section className="content-grid">
            <div className="panel upload-panel">
              <div className="panel-top"><div><div className="section-kicker">01 / SOURCE DOCUMENT</div><h2>Upload your master resume</h2><p>Choose the latest version. You can replace it or add more versions anytime.</p></div><span className="panel-icon">↥</span></div>
              <form onSubmit={handleUpload}>
                <label className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(e) => { e.preventDefault(); setDragging(false); chooseFile(e.dataTransfer.files[0] || null); }}>
                  <input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(e: ChangeEvent<HTMLInputElement>) => chooseFile(e.target.files?.[0] || null)} />
                  <span className="upload-symbol">{file ? "✓" : "↑"}</span>
                  <strong>{file ? file.name : "Drop your resume here"}</strong>
                  <span className="drop-sub">{file ? "Ready to upload" : "or browse files from your device"}</span>
                  <span className="file-types"><b>PDF</b><b>DOCX</b><span>MAX 10 MB</span></span>
                </label>
                <div className="upload-actions"><span className="privacy-note">⌑ Encrypted in transit · Private to your account</span><button className="primary-btn" disabled={!file || busy}>{busy ? "Processing…" : "Upload & extract"} <span>→</span></button></div>
              </form>
              <div className="process-note"><span className="spark">✳</span><span><strong>Works with your format.</strong> No fixed resume template or predefined candidate data. Your document is the source of truth.</span></div>
            </div>
            <div className="panel history-panel">
              <div className="panel-top"><div><div className="section-kicker">YOUR LIBRARY</div><h2>Resume versions</h2><p>Your uploaded source documents.</p></div><span className="count-badge">{resumes.length.toString().padStart(2,"0")}</span></div>
              {resumes.length ? <div className="resume-list">{resumes.map((item) => <button className={`resume-row ${latestResume?.id === item.id ? "selected" : ""}`} key={item.id} onClick={() => setSelected(item)}><span className={`file-badge ${item.original_filename.toLowerCase().endsWith(".pdf") ? "pdf" : "word"}`}>{item.original_filename.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC"}</span><span className="resume-file"><strong>{item.original_filename}</strong><small>{new Date(item.created_at).toLocaleDateString()}</small></span><span className={`status-dot ${item.status}`} title={item.status} /></button>)}</div> : <div className="empty-library"><span>▤</span><strong>No resumes yet</strong><small>Your uploaded documents will appear here.</small></div>}
            </div>
          </section>
          {latestResume && <section className="panel profile-panel">
            <div className="profile-heading"><div><div className="section-kicker">02 / EXTRACTED INFORMATION</div><h2>Candidate profile</h2><p>Automatically extracted from <strong>{latestResume.original_filename}</strong>. Review everything before using it.</p></div><span className="review-tag">● {latestResume.status === "failed" ? "Needs attention" : "Review required"}</span></div>
            {latestResume.status === "failed" ? <div className="alert error">{latestResume.parse_error || "We couldn't extract text from this file."}</div> : <>
              <div className="profile-stats"><div><span>PERSONAL DETAILS</span><strong>{info.name || "Not detected"}</strong><small>{info.email || "Email not detected"}</small></div><div><span>EXPERIENCE</span><strong>{profile.experience?.length || 0} extracted lines</strong><small>Review roles and dates</small></div><div><span>SKILLS</span><strong>{profile.skills?.length || 0} extracted lines</strong><small>Confirm your skill set</small></div></div>
              {editingProfile ? <div className="profile-editor"><label>Edit candidate profile JSON<textarea className="profile-json-editor" value={profileDraft} onChange={(e) => setProfileDraft(e.target.value)} spellCheck={false} /></label><div className="editor-actions"><button className="secondary-btn" onClick={() => setEditingProfile(false)}>Cancel</button><button className="primary-btn" disabled={busy} onClick={saveProfile}>{busy ? "Saving…" : "Save profile"}</button></div></div> : <div className="profile-columns">{(["summary","experience","education","skills","projects","certifications"] as const).map((key) => <div className="profile-section" key={key}><h3>{key}</h3><p>{Array.isArray(profile[key]) ? (profile[key] as string[]).join(" · ") || "No section detected" : profile[key] || "No section detected"}</p></div>)}</div>}
              <details className="raw-text"><summary>View extracted source text</summary><pre>{latestResume.extracted_text}</pre></details>
              <div className="review-footer"><span>AI-generated structure is a starting point. Verify names, dates, skills and achievements.</span><button className="secondary-btn" onClick={() => { setProfileDraft(JSON.stringify(latestResume.extracted_profile, null, 2)); setEditingProfile(true); }}>Edit extracted profile</button></div>
            </>}
          </section>}
          <footer className="page-footer"><span>JOBPILOT AI</span><span>Built around evidence, never invented experience.</span></footer>
        </div>
      </main>
    </div>
  );
}
