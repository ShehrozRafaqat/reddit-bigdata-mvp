# reddit-bigdata-mvp

Below is a complete, end-to-end step-by-step guide to build the small MVP described (multi-user + posts with images/videos + comments) using PostgreSQL + MongoDB + object storage, and to implement it through OpenAI Codex (Cloud + CLI + IDE options).

This matches the design doc’s storage choices (PostgreSQL for users, MongoDB for posts/comments, and object storage for media with only “keys/paths” stored in DB).

## 0) MVP scope (keep it small)

### MVP features

- Multiple users
- Register + login (JWT)
- Posts
  - Create post (title/body) + attach image/video via object storage
  - List posts (latest)
- Comments
  - Add comment to a post
  - List comments for a post

### What we intentionally skip (for now)

- No dashboard, no moderation, no votes, no feeds, no search, no analytics pipelines.

## 1) Create the project folder on your laptop

Pick a workspace folder you always use (example):

- Windows: `D:\projects\`
- macOS/Linux: `~/projects/`

Create your project root:

```bash
mkdir reddit-bigdata-mvp
cd reddit-bigdata-mvp
```

Recommended repo layout (simple, clean):

```
reddit-bigdata-mvp/
  backend/                 # FastAPI app (one service MVP)
  infra/                   # docker-compose for Postgres/Mongo/MinIO
  docs/                    # your design doc + notes
  .env.example
  README.md
```

Now copy your design doc into `docs/` (commit it so Codex can read it):

```
docs/reddit_bigdata_design.docx
```

## 1.1) Start infrastructure locally (docker compose)

From repo root:

```bash
docker compose -f infra/docker-compose.yml up -d
docker ps
```

To stop and remove containers:

```bash
docker compose -f infra/docker-compose.yml down
```

### Create the MinIO bucket named `media`

Option A: via MinIO Console

1. Open `http://localhost:9001`
2. Log in with the credentials from `.env.example`
3. Create a bucket named `media`

Option B: via MinIO client (`mc`)

```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/media
```

## 1.2) Run the backend locally

From repo root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### Auth curl examples

Register:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ali","email":"ali@example.com","password":"123456"}'
```

Login:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"123456"}'
```

### Media presign curl example

Request a presigned URL:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"123456"}' | jq -r .access_token)

PRESIGN=$(curl -s -X POST http://localhost:8000/media/presign \
  -H "Authorization: Bearer $TOKEN")

MEDIA_KEY=$(echo $PRESIGN | jq -r .media_key)
UPLOAD_URL=$(echo $PRESIGN | jq -r .upload_url)
```

Upload a file directly to MinIO using the presigned URL:

```bash
curl -X PUT "$UPLOAD_URL" --upload-file ./myimage.jpg
echo $MEDIA_KEY
```

### Posts + comments curl examples

Create a post (store only `media_key` values):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"123456"}' | jq -r .access_token)

curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Hello\",\"body\":\"First post\",\"media_keys\":[\"$MEDIA_KEY\"]}"
```

List posts:

```bash
curl http://localhost:8000/posts
```

Get a post:

```bash
curl http://localhost:8000/posts/<POST_ID>
```

Create a comment:

```bash
curl -X POST http://localhost:8000/posts/<POST_ID>/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body":"Nice!"}'
```

List comments:

```bash
curl http://localhost:8000/posts/<POST_ID>/comments
```

## 2) Create the GitHub repository + push your local code

### A) Initialize git locally

```bash
git init
```

Create a `.gitignore` quickly:

```bash
cat > .gitignore <<'EOF'
.env
__pycache__/
*.pyc
.venv/
node_modules/
EOF
```

### B) Create a repo on GitHub

Create a new repo named: `reddit-bigdata-mvp` (public or private).

### C) Add remote + push

```bash
git add .
git commit -m "chore: initial structure"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## 3) Connect Codex to your GitHub repo (Cloud agent)

### A) Connect GitHub to ChatGPT

In ChatGPT:

`Settings → Connectors → GitHub → Connect and authorize repos.`

### B) Open Codex Cloud and create an Environment

Go to `chatgpt.com/codex`, connect your GitHub repo in an “environment”, and Codex will be able to open PRs with changes.

Codex Cloud runs tasks in an isolated sandbox and then proposes diffs / PRs you can review.

## 4) (Optional but recommended) Install Codex CLI for local development

If you want Codex to edit files and run commands on your machine, install the CLI:

```bash
npm i -g @openai/codex
codex
```

That install + launch flow is the official quickstart.

## 5) Boilerplate plan (what you ask Codex to build)

You’ll do this in 3 Codex tasks (Cloud) or as a single session (CLI/IDE). Copy-paste prompts are below.

### Task 1 — Infrastructure (Postgres + Mongo + MinIO)

Create:

- `infra/docker-compose.yml`
- `.env.example`
- `README.md` run steps

**Codex prompt (paste into Codex Cloud task):**

```
Build infra for MVP using docker compose:

Postgres (db: reddit, user: reddit, password: reddit)

MongoDB (db: reddit)

MinIO (S3 compatible) with console enabled

Add volumes for persistence

Expose ports (Postgres 5432, Mongo 27017, MinIO 9000 and console 9001)

Add an init step or instructions to create a bucket named media

Create .env.example with all required env vars for backend

Update README with exact commands to start/stop infra and verify containers
Keep it minimal and dev-friendly.
```

After Codex creates the PR, merge it (or pull branch locally and test).

### Task 2 — Backend API skeleton (FastAPI) + DB connections

Backend choices that match the design doc:

- PostgreSQL: users
- MongoDB: posts/comments
- MinIO: media objects (store only keys in DB)

**Codex prompt:**

```
Create a FastAPI backend under backend/:

Python 3.11

requirements.txt (fastapi, uvicorn, sqlalchemy, psycopg2-binary, pymongo, python-jose[cryptography], passlib[bcrypt], boto3, pydantic)

Config via environment variables from .env

Postgres: users table (id uuid, username unique, email unique, password_hash, created_at)

Mongo collections: posts, comments

MinIO S3 client via boto3 using endpoint_url + access keys

Add routers: /auth, /posts, /comments, /media

Add health endpoint /health

Add README instructions to run backend locally (venv + uvicorn)
Keep it MVP only, no extra features.
```

### Task 3 — Implement the MVP endpoints

**Codex prompt:**

```
Implement MVP endpoints:

Auth (Postgres)

POST /auth/register {username,email,password}

POST /auth/login {email,password} -> {access_token}
Use bcrypt hashing + JWT.

Media (MinIO)

POST /media/presign (auth required) -> returns {media_key, upload_url}
Use a presigned PUT URL so client can upload image/video directly.

Posts (Mongo)

POST /posts (auth) {title, body, media_keys: []}

GET /posts list latest

GET /posts/{post_id}

Comments (Mongo)

POST /posts/{post_id}/comments (auth) {body, parent_comment_id?}

GET /posts/{post_id}/comments

Store author_id as the Postgres user UUID string in Mongo documents.
Add basic validation + error handling.
Add minimal curl examples in README.
```

## 6) What files you should expect after Codex finishes (reference structure)

Your repo will look like this:

```
reddit-bigdata-mvp/
  infra/
    docker-compose.yml
  backend/
    app/
      main.py
      core/
        config.py
        security.py
      db/
        postgres.py
        mongo.py
        s3.py
      routers/
        auth.py
        media.py
        posts.py
        comments.py
      schemas/
        auth.py
        posts.py
        comments.py
    requirements.txt
  docs/
    reddit_bigdata_design.docx
  .env.example
  README.md
```

## 7) Run it locally (exact steps)

### A) Start databases + MinIO

From repo root:

```bash
docker compose -f infra/docker-compose.yml up -d
docker ps
```

### B) Create backend venv + install deps

```bash
cd backend
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows powershell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```bash
cp ../.env.example .env
```

### C) Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Test health:

```bash
curl http://localhost:8000/health
```

## 8) Quick manual test flow (curl)

Register + login:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ali","email":"ali@example.com","password":"123456"}'

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"123456"}' | jq -r .access_token)
echo $TOKEN
```

Get a presigned URL + upload a file:

```bash
PRESIGN=$(curl -s -X POST http://localhost:8000/media/presign \
  -H "Authorization: Bearer $TOKEN")

MEDIA_KEY=$(echo $PRESIGN | jq -r .media_key)
UPLOAD_URL=$(echo $PRESIGN | jq -r .upload_url)

curl -X PUT "$UPLOAD_URL" --upload-file ./myimage.jpg
echo $MEDIA_KEY
```

Create post with that `media_key`:

```bash
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Hello\",\"body\":\"First post\",\"media_keys\":[\"$MEDIA_KEY\"]}"
```

Comment on post:

```bash
curl http://localhost:8000/posts | jq
# copy a post_id from response

curl -X POST http://localhost:8000/posts/<POST_ID>/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body":"Nice!"}'
```

## 9) How to “use Codex correctly” while building (workflow that won’t get messy)

### Keep changes reviewable

Do it like:

- One Codex task = one PR
- You pull and run locally
- Merge only when it runs

Codex Cloud is designed around generating diffs and PRs you review.

### Recommended PR sequence

- infra: docker compose for postgres/mongo/minio
- backend: scaffold + health + configs
- auth: postgres users + jwt
- media: presigned upload
- posts/comments: mongo collections + endpoints
- docs: README + curl examples

## 10) What to tell your lead (short status you can send)

- “MVP uses Postgres for users, Mongo for posts/comments, MinIO as object store for images/videos. Posts store only media keys.”
- “Endpoints: register/login, presign upload, create/list posts, add/list comments.”
- “Infra via docker-compose; backend via FastAPI.”

If you want, I can also paste a ready-to-run `docker-compose.yml` + `.env.example` + FastAPI skeleton directly here so you can start even before running Codex tasks—but the prompts above are already structured so Codex will generate the boilerplate cleanly and in PRs.
