# IFFIU — Predictive Marketing Intelligence

> AI-powered creative analysis. Know how every audience segment will react before you spend a single euro on media.

**Spin-off from KAMPA** | Powered by existing AWS Rekognition + Lambda infrastructure

---

## 🚀 Quick Start (Hostinger VPS)

### 1. SSH into your VPS
```bash
ssh root@your-vps-ip
```

### 2. Clone/Upload the project
```bash
cd /root
# Upload via SFTP or git clone
mkdir iffiu && cd iffiu
# Copy all project files here
```

### 3. Configure environment
```bash
cp .env.example .env
nano .env
```

**Required .env values:**
```
SECRET_KEY=<run: openssl rand -hex 32>
DB_PASSWORD=<strong password>
AWS_ACCESS_KEY_ID=<your KAMPA AWS key>
AWS_SECRET_ACCESS_KEY=<your KAMPA AWS secret>
```

### 4. Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

### 5. Point DNS
In Hostinger DNS settings, point `iffiu.com` → your VPS IP

### 6. SSL (after DNS propagation)
```bash
sudo certbot certonly --standalone -d iffiu.com -d www.iffiu.com
# Then uncomment HTTPS block in nginx/iffiu.conf
sudo docker compose restart nginx
```

---

## 📁 Project Structure

```
iffiu/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── core/
│   │   ├── config.py           # Environment settings
│   │   └── database.py         # PostgreSQL + SQLAlchemy
│   ├── api/
│   │   ├── auth.py             # Register, Login, Session
│   │   ├── analysis.py         # Upload, Analyze, Results API
│   │   ├── dashboard.py        # Protected dashboard pages
│   │   └── webhooks.py         # Lambda callback, Stripe
│   ├── models/
│   │   └── models.py           # User, Creative, Persona, Score models
│   ├── services/
│   │   ├── aws_service.py      # Rekognition + Lambda + S3 integration
│   │   └── scoring_engine.py   # Sinus-Milieu persona scoring (Python port)
│   ├── templates/pages/
│   │   ├── landing.html        # Public landing page
│   │   ├── demo.html           # Interactive demo (SALES TOOL!)
│   │   ├── login.html          # Auth
│   │   ├── register.html       # Auth
│   │   ├── dashboard_main.html # User dashboard
│   │   └── analysis_detail.html# Full analysis results
│   └── static/                 # CSS, JS, images
├── nginx/iffiu.conf            # Nginx reverse proxy
├── docker-compose.yml          # Full stack orchestration
├── Dockerfile                  # Python app container
├── requirements.txt            # Python dependencies
├── deploy.sh                   # One-click deployment
└── .env.example                # Environment template
```

---

## 🔗 AWS Integration (Existing KAMPA Infrastructure)

IFFIU connects to the **same AWS account** (754840114791, eu-central-1):

| Service | Usage | Existing? |
|---------|-------|-----------|
| Rekognition | Image/Video analysis (labels, faces, text, emotions) | ✅ Yes |
| Lambda | `kampa-predict-analyze` for async video analysis | ✅ Yes |
| S3 | `kampa-uploads` for file storage | ✅ Yes |
| IAM | Same credentials, scoped permissions | ✅ Yes |

**No new AWS infrastructure needed!**

---

## 📊 Key URLs

| URL | Purpose |
|-----|---------|
| `/` | Landing page |
| `/demo` | **Interactive demo (for sales meetings!)** |
| `/pricing` | Pricing page |
| `/login` | Login |
| `/register` | Registration (3 free analyses) |
| `/dashboard` | User dashboard |
| `/dashboard/analysis/{id}` | Full analysis results |
| `/api/docs` | API documentation (debug mode) |
| `/health` | Health check |

---

## 💰 Pricing Tiers

| Plan | Price | Analyses/mo |
|------|-------|-------------|
| Free Trial | €0 | 3 |
| Starter | €299/mo | 25 |
| Professional | €999/mo | 100 |
| Enterprise | €1.499/mo | Unlimited |

---

## 🎯 For Your Sales Meeting

1. Open `https://iffiu.com/demo` (or `http://your-vps-ip/demo`)
2. Click "Run Demo Analysis"
3. Watch the animated analysis process
4. Present the full dashboard with:
   - IFFIU Predictive Score (74)
   - Trust/Clarity/Emotion/Action dimensions
   - Sinus-Milieu persona cards (10 segments)
   - Sinus mapping visualization
   - Top/Bottom rankings
5. Explain: "Upload any creative → instant AI analysis → know before you spend"

---

## 🛠 Useful Commands

```bash
# View logs
sudo docker compose logs -f app

# Restart
sudo docker compose restart

# Rebuild after changes
sudo docker compose up -d --build

# Database access
sudo docker compose exec db psql -U iffiu

# Stop everything
sudo docker compose down
```
