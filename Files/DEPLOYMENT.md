# Planora — Deployment Guide

## 1. Supabase Edge Function: Lemon Squeezy Webhook

### Prerequisites
- [Supabase CLI](https://supabase.com/docs/guides/cli) installed
- Your Supabase project linked

### Step 1: Install Supabase CLI
```bash
npm install -g supabase
```

### Step 2: Login & Link Project
```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
```
> Find your project ref in Supabase Dashboard → Settings → General

### Step 3: Set Environment Secrets
```bash
supabase secrets set LEMON_SQUEEZY_WEBHOOK_SECRET="your_lemon_squeezy_webhook_secret"
```
> `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are automatically available in Edge Functions.

### Step 4: Deploy the Edge Function
```bash
# From the project root (where /supabase folder is)
supabase functions deploy lemon-squeezy-webhook --no-verify-jwt
```
> `--no-verify-jwt` is required because Lemon Squeezy sends webhooks without a Supabase JWT.

### Step 5: Get Your Webhook URL
After deployment, your webhook URL will be:
```
https://YOUR_PROJECT_REF.supabase.co/functions/v1/lemon-squeezy-webhook
```

### Step 6: Configure in Lemon Squeezy
1. Go to [Lemon Squeezy Dashboard](https://app.lemonsqueezy.com) → Settings → Webhooks
2. Click **"+"** to add a new webhook
3. **Callback URL**: `https://YOUR_PROJECT_REF.supabase.co/functions/v1/lemon-squeezy-webhook`
4. **Signing Secret**: Generate one and save it (this is the `LEMON_SQUEEZY_WEBHOOK_SECRET`)
5. **Events to listen to**:
   - ✅ `order_created`
   - ✅ `subscription_created`
   - ✅ `subscription_payment_success`
   - ✅ `subscription_expired`
   - ✅ `subscription_cancelled`
6. Save the webhook

### How It Works
- When a customer pays → Lemon Squeezy sends a `order_created` or `subscription_created` event
- The Edge Function verifies the webhook signature for security
- It finds the user by their email in Supabase Auth
- It sets `is_pro = true` in the `profiles` table
- If the subscription is cancelled/expired → sets `is_pro = false`

---

## 2. Updated Wisdom Engine (app.py)

### What Changed
- Complete visual redesign with dark blue/navy premium theme
- Futuristic card-based layout with glowing purple accents
- AI-powered recommendations via Abacus.AI LLM API
- Task analysis with overdue detection
- Performance insights with focus score
- "Generate Insights" button for on-demand AI analysis
- Daily wisdom quotes (changes based on day of year)
- Locked state for non-Pro users with premium upgrade prompt

### Dependencies
The app uses `abacusai` Python SDK for AI insights. Add to `requirements.txt`:
```
abacusai
```

### Streamlit Secrets Required
In `.streamlit/secrets.toml` or Streamlit Cloud secrets:
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
TWILIO_SID = "your-twilio-sid"
TWILIO_TOKEN = "your-twilio-token"
TWILIO_FROM = "whatsapp:+14155238886"
```

### Deploying to Streamlit Cloud
1. Push updated `app.py` to your GitHub repo
2. Streamlit Cloud will auto-deploy on push
3. Ensure `abacusai` is in your `requirements.txt`

---

## 3. Testing the Webhook

### Test with cURL
```bash
curl -X POST https://YOUR_PROJECT_REF.supabase.co/functions/v1/lemon-squeezy-webhook \
  -H "Content-Type: application/json" \
  -H "x-signature: YOUR_COMPUTED_SIGNATURE" \
  -d '{
    "meta": {"event_name": "order_created"},
    "data": {"attributes": {"user_email": "test@example.com"}}
  }'
```

### Test in Lemon Squeezy
Use Lemon Squeezy's test mode to simulate a purchase and verify the webhook fires correctly.

### Verify in Supabase
Check the `profiles` table to confirm `is_pro` was updated to `true` for the test user.
