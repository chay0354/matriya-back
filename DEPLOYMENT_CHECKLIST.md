# Vercel Deployment Checklist

## Pre-Deployment

- [ ] Ensure Supabase is set up and working
- [ ] All environment variables documented
- [ ] Database tables created in Supabase
- [ ] Test locally with Supabase mode

## Backend Deployment

- [ ] Deploy backend to Vercel
- [ ] Set all environment variables in Vercel Dashboard:
  - [ ] `DB_MODE=supabase`
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `SUPABASE_DB_URL`
  - [ ] `TOGETHER_API_KEY`
  - [ ] `TOGETHER_MODEL`
  - [ ] `SECRET_KEY` (generate random string)
  - [ ] `CORS_ORIGINS` (will set after frontend deployment)
  - [ ] `ENVIRONMENT=production`
- [ ] Note backend URL: `https://your-backend.vercel.app`
- [ ] Test backend health endpoint
- [ ] Test backend login endpoint

## Frontend Deployment

- [ ] Deploy frontend to Vercel
- [ ] Set environment variable: `REACT_APP_API_URL=https://your-backend.vercel.app`
- [ ] Note frontend URL: `https://your-frontend.vercel.app`
- [ ] Update backend `CORS_ORIGINS` to include frontend URL

## Post-Deployment Testing

- [ ] Test user signup
- [ ] Test user login
- [ ] Test file upload
- [ ] Test search functionality
- [ ] Test admin panel (if admin user exists)
- [ ] Test agent buttons (Contradiction/Risk)
- [ ] Check Vercel function logs for errors
- [ ] Check browser console for frontend errors

## Production Considerations

- [ ] Set up custom domain (optional)
- [ ] Enable Vercel Analytics
- [ ] Set up error monitoring
- [ ] Configure file size limits
- [ ] Review Supabase usage limits
- [ ] Set up backup strategy for database

## Troubleshooting

If issues occur:
1. Check Vercel function logs
2. Check Supabase logs
3. Check browser console
4. Verify environment variables are set correctly
5. Verify CORS_ORIGINS includes frontend URL
6. Test API endpoints directly with curl/Postman
