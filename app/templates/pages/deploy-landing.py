#!/usr/bin/env python3
# Run on VPS: python3 /root/deploy-landing.py
# Writes the complete new landing.html with holographic personas

import os
path = "/root/iffiu/app/templates/pages/landing.html"
os.makedirs(os.path.dirname(path), exist_ok=True)

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IFFIU — Predictive Marketing Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
<style>
:root {
  --bg: #eef0f7;
  --surface: #ffffff;
  --border: rgba(15,23,42,.09);
  --border-hover: rgba(99,102,241,.25);
  --text: #0f172a;
  --text-sub: #374151;
  --text-dim: #6b7280;
  --accent: #6366f1;
  --accent2: #8b5cf6;
  --accent3: #ec4899;
  --teal: #0d9488;
  --emerald: #059669;
  --font: 'Outfit', system-ui, -apple-system, sans-serif;
  --mono: 'JetBrains Mono', monospace;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; overflow-x: hidden; -webkit-font-smoothing: antialiased; }

.ambient {
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(ellipse 900px 700px at 15% 8%, rgba(99,102,241,.07), transparent 55%),
    radial-gradient(ellipse 800px 500px at 85% 15%, rgba(236,72,153,.05), transparent 50%),
    radial-gradient(ellipse 700px 400px at 50% 75%, rgba(13,148,136,.04), transparent 45%),
    linear-gradient(180deg, #eef0f7 0%, #e4e8f4 50%, #eef0f7 100%);
}

/* NAV */
nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  padding: 14px 48px; display: flex; align-items: center; justify-content: space-between;
  backdrop-filter: blur(24px) saturate(1.4);
  background: rgba(238,240,247,.88);
  border-bottom: 1px solid var(--border);
}
.logo { font-size: 26px; font-weight: 900; letter-spacing: -.04em; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.nav-links { display: flex; gap: 28px; align-items: center; }
.nav-links a { color: var(--text-sub); text-decoration: none; font-size: 14px; font-weight: 600; transition: color .2s; }
.nav-links a:hover { color: var(--accent); }

.btn-cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 11px 28px; border-radius: 12px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #ffffff; font-weight: 800; font-size: 14px;
  text-decoration: none; border: none; cursor: pointer;
  box-shadow: 0 4px 20px rgba(99,102,241,.3), 0 2px 6px rgba(99,102,241,.15);
  transition: transform .2s, box-shadow .2s;
}
.btn-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 36px rgba(99,102,241,.35); }

.btn-outline {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 11px 28px; border-radius: 12px;
  background: white; color: var(--text); font-weight: 700; font-size: 14px;
  text-decoration: none; border: 1.5px solid var(--border); cursor: pointer;
  transition: border-color .2s, box-shadow .2s;
}
.btn-outline:hover { border-color: var(--accent); box-shadow: 0 4px 20px rgba(99,102,241,.08); }

/* HERO */
.hero { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 140px 48px 100px; position: relative; }
.hero-content { max-width: 820px; text-align: center; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 22px; border-radius: 999px;
  background: white; border: 1.5px solid rgba(99,102,241,.18);
  font-size: 13px; font-weight: 700; color: var(--accent);
  box-shadow: 0 4px 16px rgba(99,102,241,.08);
  margin-bottom: 32px; animation: fadeUp .8s ease both;
}
.hero-badge .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--emerald); animation: pulse 2s infinite; }
h1 { font-size: clamp(3.2rem,6vw,5.5rem); font-weight: 900; line-height: 1.02; letter-spacing: -.05em; margin-bottom: 24px; animation: fadeUp .8s .1s ease both; }
h1 .gradient { background: linear-gradient(135deg, var(--accent), var(--accent2), var(--accent3)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-sub { font-size: 19px; color: var(--text-sub); max-width: 600px; margin: 0 auto 44px; line-height: 1.7; font-weight: 400; animation: fadeUp .8s .2s ease both; }
.hero-actions { display: flex; gap: 16px; justify-content: center; animation: fadeUp .8s .3s ease both; }

/* SCORE FLOAT */
.score-float {
  position: absolute; right: 6%; top: 46%;
  width: 240px; padding: 28px; text-align: center;
  background: white; border: 1.5px solid var(--border); border-radius: 24px;
  box-shadow: 0 20px 60px rgba(15,23,42,.08), 0 4px 16px rgba(99,102,241,.06);
  animation: float 6s ease-in-out infinite, fadeUp 1s .6s ease both;
}
.score-ring { width: 100px; height: 100px; margin: 0 auto 12px; position: relative; }
.score-ring svg { transform: rotate(-90deg); }
.score-ring .value { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 30px; font-weight: 800; font-family: var(--mono); color: var(--accent); }
.score-label { font-size: 11px; color: var(--text-dim); font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 16px; }
.mini-bars { display: flex; flex-direction: column; gap: 8px; }
.mini-bar-row { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.mini-bar-label { width: 52px; color: var(--text-dim); font-weight: 600; }
.mini-bar-track { flex: 1; height: 5px; background: #e2e8f0; border-radius: 99px; overflow: hidden; }
.mini-bar-fill { height: 100%; border-radius: 99px; }
.mini-bar-val { width: 28px; text-align: right; font-family: var(--mono); font-weight: 700; font-size: 12px; }

/* FEATURES */
.features { padding: 120px 48px; max-width: 1200px; margin: 0 auto; }
.section-tag { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: .1em; margin-bottom: 16px; }
.section-title { font-size: clamp(2.2rem,4vw,3.2rem); font-weight: 900; line-height: 1.08; letter-spacing: -.04em; margin-bottom: 64px; max-width: 550px; }
.feature-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; }
.feature-card {
  padding: 36px; border-radius: 20px; background: white; border: 1.5px solid var(--border);
  transition: border-color .3s, transform .3s, box-shadow .3s;
}
.feature-card:hover { border-color: var(--border-hover); transform: translateY(-6px); box-shadow: 0 24px 64px rgba(15,23,42,.08); }
.feature-icon { width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-size: 26px; margin-bottom: 20px; }
.feature-card h3 { font-size: 18px; font-weight: 700; margin-bottom: 10px; letter-spacing: -.02em; }
.feature-card p { font-size: 14px; color: var(--text-sub); line-height: 1.7; }

/* ═══ HOLOGRAPHIC PERSONAS ═══════════════════════════════════ */
.personas { padding: 120px 48px; max-width: 1300px; margin: 0 auto; }
.holo-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 18px; }

.holo-card {
  position: relative; padding: 28px 20px; border-radius: 22px;
  text-align: center; cursor: default; overflow: hidden;
  transition: transform .4s cubic-bezier(.34,1.56,.64,1), box-shadow .4s;
  background: linear-gradient(160deg, rgba(255,255,255,.95) 0%, rgba(240,242,255,.85) 100%);
  border: 1.5px solid rgba(255,255,255,.7);
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 32px rgba(99,102,241,.07), 0 2px 8px rgba(0,0,0,.04), inset 0 1px 0 rgba(255,255,255,.9);
}
.holo-card:hover {
  transform: translateY(-12px) scale(1.04);
  box-shadow: 0 24px 72px rgba(99,102,241,.18), 0 8px 24px rgba(139,92,246,.1), inset 0 1px 0 rgba(255,255,255,1);
}
/* Holographic shimmer */
.holo-card::before {
  content: ''; position: absolute; inset: 0; border-radius: 22px;
  background: linear-gradient(135deg,
    rgba(99,102,241,.0) 0%, rgba(99,102,241,.08) 20%,
    rgba(236,72,153,.08) 40%, rgba(20,184,166,.08) 60%,
    rgba(251,191,36,.06) 80%, rgba(99,102,241,.0) 100%
  );
  background-size: 300% 300%;
  animation: holoShimmer 5s ease infinite;
  pointer-events: none; z-index: 1;
}
/* Rainbow edge glow */
.holo-card::after {
  content: ''; position: absolute; inset: -2px; border-radius: 24px;
  background: conic-gradient(from 0deg,
    rgba(99,102,241,.4), rgba(236,72,153,.4), rgba(20,184,166,.4),
    rgba(251,191,36,.4), rgba(99,102,241,.4)
  );
  z-index: -1; opacity: 0; transition: opacity .4s; filter: blur(12px);
}
.holo-card:hover::after { opacity: 1; }
.holo-card > * { position: relative; z-index: 2; }

/* Avatar with spinning light */
.holo-avatar {
  width: 68px; height: 68px; margin: 0 auto 14px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 32px;
  background: linear-gradient(135deg, rgba(99,102,241,.1), rgba(236,72,153,.08), rgba(20,184,166,.08));
  border: 2.5px solid rgba(255,255,255,.8);
  box-shadow: 0 6px 20px rgba(99,102,241,.12), inset 0 0 24px rgba(255,255,255,.4);
  position: relative; overflow: hidden;
}
.holo-avatar::after {
  content: ''; position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 0%, rgba(255,255,255,.5) 8%, transparent 16%);
  animation: holoSpin 3s linear infinite;
}

.holo-name { font-size: 14px; font-weight: 800; margin-bottom: 2px; letter-spacing: -.02em; color: var(--text); }
.holo-age { font-size: 11px; color: var(--text-dim); margin-bottom: 14px; font-weight: 500; }
.holo-score {
  font-family: var(--mono); font-size: 32px; font-weight: 800; margin-bottom: 4px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.holo-risk { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 14px; }
.holo-dims { display: flex; flex-direction: column; gap: 5px; }
.holo-dim { display: flex; align-items: center; gap: 6px; font-size: 10px; }
.holo-dim-label { width: 40px; color: var(--text-dim); font-weight: 600; }
.holo-dim-bar { flex: 1; height: 4px; background: #e2e8f0; border-radius: 99px; overflow: hidden; }
.holo-dim-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }
.holo-dim-val { width: 22px; text-align: right; font-family: var(--mono); font-weight: 700; font-size: 10px; }

/* PRICING */
.pricing { padding: 120px 48px; max-width: 1100px; margin: 0 auto; }
.price-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; }
.price-card {
  padding: 40px 32px; border-radius: 24px; background: white;
  border: 1.5px solid var(--border); position: relative;
  transition: border-color .3s, transform .3s, box-shadow .3s;
}
.price-card:hover { transform: translateY(-6px); box-shadow: 0 24px 64px rgba(15,23,42,.07); }
.price-card.featured { border-color: var(--accent); box-shadow: 0 8px 48px rgba(99,102,241,.12); }
.price-badge {
  position: absolute; top: -13px; left: 50%; transform: translateX(-50%);
  padding: 5px 20px; border-radius: 99px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #ffffff; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em;
}
.price-name { font-size: 15px; font-weight: 600; color: var(--text-sub); margin-bottom: 12px; }
.price-amount { font-size: 50px; font-weight: 900; letter-spacing: -.04em; margin-bottom: 4px; color: var(--text); }
.price-amount span { font-size: 16px; font-weight: 400; color: var(--text-dim); }
.price-period { font-size: 13px; color: var(--text-dim); margin-bottom: 28px; }
.price-features { list-style: none; margin-bottom: 32px; }
.price-features li { padding: 9px 0; font-size: 14px; color: var(--text-sub); display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #f1f5f9; }
.price-features li::before { content: '\2713'; color: var(--emerald); font-weight: 800; font-size: 15px; }

/* CTA */
.cta-section { padding: 120px 48px; text-align: center; }
.cta-box {
  max-width: 760px; margin: 0 auto; padding: 80px 48px; border-radius: 32px;
  background: white; border: 1.5px solid var(--border);
  box-shadow: 0 24px 80px rgba(99,102,241,.08);
  position: relative; overflow: hidden;
}
.cta-box::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, rgba(99,102,241,.04), rgba(236,72,153,.03), rgba(20,184,166,.03));
  pointer-events: none;
}
.cta-box h2 { font-size: clamp(2rem,3.5vw,3rem); font-weight: 900; margin-bottom: 16px; letter-spacing: -.04em; position: relative; }
.cta-box p { color: var(--text-sub); margin-bottom: 36px; font-size: 17px; position: relative; }

footer { padding: 48px; text-align: center; border-top: 1px solid var(--border); font-size: 13px; color: var(--text-dim); }
footer a { color: var(--accent); text-decoration: none; font-weight: 600; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .3; } }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }
@keyframes holoShimmer { 0% { background-position: 200% 200%; } 50% { background-position: 0% 0%; } 100% { background-position: 200% 200%; } }
@keyframes holoSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width:1100px) { .holo-grid { grid-template-columns: repeat(3,1fr); } }
@media (max-width:900px) {
  nav { padding: 14px 20px; } .nav-links { display: none; }
  .hero { padding: 120px 24px 80px; } .score-float { display: none; }
  .feature-grid, .price-grid { grid-template-columns: 1fr; }
  .holo-grid { grid-template-columns: repeat(2,1fr); }
  .features, .personas, .pricing, .cta-section { padding: 80px 24px; }
}
@media (max-width:500px) { .holo-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="ambient"></div>

<nav>
  <div class="logo">IFFIU</div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#personas">Personas</a>
    <a href="#pricing">Pricing</a>
    <a href="/demo" class="btn-outline"><i class="fas fa-play"></i> Live Demo</a>
    <a href="/register" class="btn-cta">Start Free <i class="fas fa-arrow-right"></i></a>
  </div>
</nav>

<section class="hero">
  <div class="hero-content">
    <div class="hero-badge"><span class="dot"></span> Predictive Marketing Intelligence</div>
    <h1>Know your audience<br><span class="gradient">before you spend.</span></h1>
    <p class="hero-sub">Upload any creative and instantly see how 10 distinct audience segments will react. AI-powered persona simulation backed by real computer vision.</p>
    <div class="hero-actions">
      <a href="/demo" class="btn-cta"><i class="fas fa-play"></i> Try Live Demo</a>
      <a href="#features" class="btn-outline">Learn More</a>
    </div>
  </div>
  <div class="score-float">
    <div class="score-ring">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" stroke-width="6"/>
        <circle cx="50" cy="50" r="42" fill="none" stroke="url(#sg)" stroke-width="6" stroke-dasharray="264" stroke-dashoffset="66" stroke-linecap="round"/>
        <defs><linearGradient id="sg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
      </svg>
      <div class="value">74</div>
    </div>
    <div class="score-label">IFFIU Predictive Score</div>
    <div class="mini-bars">
      <div class="mini-bar-row"><div class="mini-bar-label">Trust</div><div class="mini-bar-track"><div class="mini-bar-fill" style="width:72%;background:var(--accent);"></div></div><div class="mini-bar-val" style="color:var(--accent);">72</div></div>
      <div class="mini-bar-row"><div class="mini-bar-label">Clarity</div><div class="mini-bar-track"><div class="mini-bar-fill" style="width:68%;background:var(--accent2);"></div></div><div class="mini-bar-val" style="color:var(--accent2);">68</div></div>
      <div class="mini-bar-row"><div class="mini-bar-label">Emotion</div><div class="mini-bar-track"><div class="mini-bar-fill" style="width:81%;background:var(--accent3);"></div></div><div class="mini-bar-val" style="color:var(--accent3);">81</div></div>
      <div class="mini-bar-row"><div class="mini-bar-label">Action</div><div class="mini-bar-track"><div class="mini-bar-fill" style="width:63%;background:var(--teal);"></div></div><div class="mini-bar-val" style="color:var(--teal);">63</div></div>
    </div>
  </div>
</section>

<section id="features" class="features">
  <div class="section-tag"><i class="fas fa-bolt"></i> What makes IFFIU different</div>
  <h2 class="section-title">Predictive intelligence, not just analytics.</h2>
  <div class="feature-grid">
    <div class="feature-card"><div class="feature-icon" style="background:rgba(99,102,241,.1);color:var(--accent);">&#129504;</div><h3>Sinus-Milieu AI Simulation</h3><p>10 scientifically-modeled German audience segments. Each with unique reaction profiles for Trust, Clarity, Emotion, and Action.</p></div>
    <div class="feature-card"><div class="feature-icon" style="background:rgba(139,92,246,.1);color:var(--accent2);">&#128300;</div><h3>Computer Vision Analysis</h3><p>Our AI engine scans every frame — detecting faces, emotions, text, objects, and brand elements.</p></div>
    <div class="feature-card"><div class="feature-icon" style="background:rgba(236,72,153,.1);color:var(--accent3);">&#128202;</div><h3>IFFIU Predictive Score</h3><p>One number that predicts creative effectiveness. Broken down by dimension, persona, and risk level.</p></div>
    <div class="feature-card"><div class="feature-icon" style="background:rgba(13,148,136,.1);color:var(--teal);">&#127919;</div><h3>Custom Persona Import</h3><p>Bring your own audience segments from market research, CRM data, or industry studies.</p></div>
    <div class="feature-card"><div class="feature-icon" style="background:rgba(99,102,241,.1);color:var(--accent);">&#9889;</div><h3>Instant Results</h3><p>Upload, analyze, results in under 30 seconds. Full dashboard with score rings and persona mapping.</p></div>
    <div class="feature-card"><div class="feature-icon" style="background:rgba(5,150,105,.1);color:var(--emerald);">&#128274;</div><h3>Enterprise Security</h3><p>All data encrypted. GDPR compliant. European cloud infrastructure only.</p></div>
  </div>
</section>

<section id="personas" class="personas">
  <div style="text-align:center; margin-bottom:64px;">
    <div class="section-tag"><i class="fas fa-users"></i> Sinus-Milieu Personas</div>
    <h2 class="section-title" style="margin:16px auto;text-align:center;">10 audience segments.<br>10 unique reactions.</h2>
    <p style="color:var(--text-sub);max-width:560px;margin:0 auto;font-size:16px;">Each persona simulates how a real audience segment reacts to your creative across four dimensions.</p>
  </div>
  <div class="holo-grid" id="holoGrid"></div>
</section>

<section id="pricing" class="pricing">
  <div style="text-align:center;margin-bottom:64px;">
    <div class="section-tag"><i class="fas fa-tag"></i> Simple Pricing</div>
    <h2 class="section-title" style="margin:16px auto;text-align:center;">Start free. Scale when ready.</h2>
  </div>
  <div class="price-grid">
    <div class="price-card">
      <div class="price-name">Starter</div>
      <div class="price-amount">&euro;299<span>/mo</span></div>
      <div class="price-period">Up to 25 analyses/month</div>
      <ul class="price-features"><li>25 AI Analyses</li><li>10 Sinus-Milieu Personas</li><li>Score Dashboard</li><li>Video + Image Support</li><li>CSV Export</li></ul>
      <a href="/register" class="btn-outline" style="width:100%;justify-content:center;">Get Started</a>
    </div>
    <div class="price-card featured">
      <div class="price-badge">Most Popular</div>
      <div class="price-name">Professional</div>
      <div class="price-amount">&euro;999<span>/mo</span></div>
      <div class="price-period">Up to 100 analyses/month</div>
      <ul class="price-features"><li>100 AI Analyses</li><li>Custom Personas</li><li>API Access</li><li>Team Collaboration</li><li>Priority Support</li></ul>
      <a href="/register" class="btn-cta" style="width:100%;justify-content:center;">Start Free Trial</a>
    </div>
    <div class="price-card">
      <div class="price-name">Enterprise</div>
      <div class="price-amount">&euro;1.499<span>/mo</span></div>
      <div class="price-period">Unlimited analyses</div>
      <ul class="price-features"><li>Unlimited Analyses</li><li>White-Label Option</li><li>Dedicated Support</li><li>Custom Integrations</li><li>SLA Guarantee</li></ul>
      <a href="mailto:hello@iffiu.com" class="btn-outline" style="width:100%;justify-content:center;">Contact Sales</a>
    </div>
  </div>
</section>

<section class="cta-section">
  <div class="cta-box">
    <h2>Ready to predict creative success?</h2>
    <p>Start with 3 free analyses. No credit card required.</p>
    <div style="display:flex;gap:16px;justify-content:center;position:relative;">
      <a href="/demo" class="btn-cta"><i class="fas fa-play"></i> Try Live Demo</a>
      <a href="/register" class="btn-outline">Create Account</a>
    </div>
  </div>
</section>

<footer><p>&copy; 2026 IFFIU &middot; Predictive Marketing Intelligence &middot; <a href="mailto:hello@iffiu.com">hello@iffiu.com</a></p></footer>

<script>
const personas = [
  { emoji:'\U0001f3db\ufe0f', name:'Konservativ-Etablierte', age:'40\u201370 \u00b7 High Income', score:68, risk:'medium', t:72, c:68, e:34, a:42 },
  { emoji:'\U0001f4da', name:'Liberal-Intellektuelle', age:'30\u201370 \u00b7 High Income', score:72, risk:'low', t:58, c:76, e:52, a:35 },
  { emoji:'\U0001f680', name:'Performer', age:'25\u201355 \u00b7 High Income', score:81, risk:'low', t:45, c:52, e:68, a:85 },
  { emoji:'\u2728', name:'Expeditive', age:'18\u201335 \u00b7 Medium', score:85, risk:'low', t:30, c:42, e:86, a:72 },
  { emoji:'\U0001f3af', name:'Adaptiv-Pragmatische', age:'20\u201345 \u00b7 Medium', score:74, risk:'low', t:68, c:78, e:52, a:65 },
  { emoji:'\U0001f33f', name:'Sozial\u00f6kologische', age:'30\u201360 \u00b7 Medium', score:62, risk:'medium', t:78, c:62, e:68, a:28 },
  { emoji:'\U0001f3e0', name:'B\u00fcrgerliche Mitte', age:'30\u201365 \u00b7 Medium', score:58, risk:'medium', t:76, c:82, e:38, a:55 },
  { emoji:'\U0001f3e1', name:'Traditionelle', age:'55\u201380 \u00b7 Low', score:38, risk:'high', t:85, c:80, e:18, a:22 },
  { emoji:'\U0001f527', name:'Prek\u00e4re', age:'35\u201365 \u00b7 Low', score:44, risk:'medium', t:65, c:82, e:42, a:55 },
  { emoji:'\U0001f3ae', name:'Konsum-Hedonisten', age:'18\u201340 \u00b7 Low', score:76, risk:'low', t:28, c:42, e:82, a:68 },
];

function sc(v) { return v >= 70 ? '#059669' : v >= 45 ? '#d97706' : '#dc2626'; }
function rl(r) { return r === 'low' ? 'Low Risk' : r === 'medium' ? 'Medium Risk' : 'High Risk'; }

const grid = document.getElementById('holoGrid');
personas.forEach((p, i) => {
  const dims = [['Trust',p.t],['Clarity',p.c],['Emotion',p.e],['Action',p.a]];
  const dh = dims.map(([l,v]) =>
    '<div class="holo-dim"><div class="holo-dim-label">'+l+'</div><div class="holo-dim-bar"><div class="holo-dim-fill" style="width:'+v+'%"></div></div><div class="holo-dim-val" style="color:'+sc(v)+'">'+v+'</div></div>'
  ).join('');
  grid.innerHTML +=
    '<div class="holo-card" style="animation:fadeUp .6s '+(i*.08)+'s ease both">' +
    '<div class="holo-avatar">'+p.emoji+'</div>' +
    '<div class="holo-name">'+p.name+'</div>' +
    '<div class="holo-age">'+p.age+'</div>' +
    '<div class="holo-score">'+p.score+'</div>' +
    '<div class="holo-risk" style="color:'+sc(p.score)+'">'+rl(p.risk)+'</div>' +
    '<div class="holo-dims">'+dh+'</div></div>';
});
</script>
</body>
</html>'''

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Done! Written {len(html):,} bytes to {path}")
print("Now run: cd /root/iffiu && docker compose up -d --build")
