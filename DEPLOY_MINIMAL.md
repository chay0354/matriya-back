# Minimal Deployment Strategy

If Vercel still fails with large file errors, try this minimal deployment approach:

## Option 1: Deploy Only API Directory

1. Create a new branch for deployment:
```bash
git checkout -b vercel-deploy
```

2. Move only essential files to root:
```bash
# Keep only what's needed
mkdir deploy_temp
cp -r api/ deploy_temp/
cp *.py deploy_temp/
cp requirements.txt deploy_temp/
cp config.py deploy_temp/
cp vercel.json deploy_temp/
```

3. Update vercel.json to point to correct paths

4. Deploy from this minimal structure

## Option 2: Use Vercel CLI with Explicit Exclude

```bash
cd back
vercel --prod --force
```

## Option 3: Check What Vercel is Actually Uploading

The error suggests Vercel is trying to upload 4.3GB. This could be:

1. **Python dependencies** - Some packages download large models
2. **Cached files** - Vercel might have cached large files
3. **Git LFS** - If using Git LFS, large files might be included

## Option 4: Use Environment Variables to Prevent Model Downloads

Set these in Vercel:
```
TRANSFORMERS_OFFLINE=1
HF_HUB_OFFLINE=1
SENTENCE_TRANSFORMERS_HOME=/tmp
```

This prevents downloading models during installation.

## Option 5: Create a Separate Minimal Requirements File

Create `requirements-minimal.txt` with only essential packages:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-dotenv==1.0.0
pydantic>=2.6.3,<3.0.0
pydantic-settings==2.1.0
aiofiles==23.2.1
requests==2.31.0
sqlalchemy==1.4.46
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
bcrypt==4.0.1
psycopg2-binary==2.9.9
pgvector==0.2.3
```

Then use Supabase for embeddings (don't install sentence-transformers on Vercel).
