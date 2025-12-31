# Deploying Action Blocker to Vercel

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. The action-blocker code in a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### 1. Push to Git Repository

Make sure your `action-blocker` folder is in a Git repository and pushed to GitHub/GitLab/Bitbucket.

### 2. Import Project to Vercel

1. Go to https://vercel.com/new
2. Import your Git repository
3. Select the repository containing the action-blocker

### 3. Configure Vercel Settings

In the Vercel project settings:

- **Framework Preset**: Select `FastAPI` or `Other`
- **Root Directory**: Set to `./action-blocker` (if deploying from the transaction-blocker repo root) or `./` (if the repo is just action-blocker)
- **Build Command**: Leave empty or set to `None`
- **Output Directory**: Leave as `N/A`
- **Install Command**: Toggle ON and set to `pip install -r requirements.txt`

### 4. Environment Variables

Add these environment variables in Vercel (Settings → Environment Variables):

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key
- `ALLOWED_ORIGINS` - Comma-separated list of allowed origins (e.g., `https://your-frontend.vercel.app,http://localhost:3000`)

### 5. Deploy

Click "Deploy" and wait for the deployment to complete.

## API Endpoints

Once deployed, your API will be available at:
- `https://your-project.vercel.app/` - Root endpoint
- `https://your-project.vercel.app/health` - Health check
- `https://your-project.vercel.app/api/status` - Service status
- `https://your-project.vercel.app/api/check-transaction` - Check transaction (POST)

## Testing

After deployment, test the API:

```bash
# Health check
curl https://your-project.vercel.app/health

# Status
curl https://your-project.vercel.app/api/status

# Check transaction
curl -X POST https://your-project.vercel.app/api/check-transaction \
  -H "Content-Type: application/json" \
  -d '{
    "from_user_id": "user-id",
    "to_user_id": "recipient-id",
    "amount": 100.0,
    "sender_balance": 500.0
  }'
```

## Notes

- The action-blocker is now deployed as serverless functions on Vercel
- Each request will initialize the rules engine (stateless)
- For better performance, consider using Vercel's Edge Functions or caching
- Make sure your Supabase database has the required tables (run the SQL scripts)

