# Google Cloud Billing Alerts & Safety Setup

## 🚨 IMPORTANT: Protect Your $300 Credit

Follow these steps to ensure you never get charged beyond your free credits:

## Step 1: Set Up Budget Alerts

### Via Google Cloud Console (Recommended):

1. **Go to Billing**: https://console.cloud.google.com/billing/01E07D-1E1BB3-C7F2CB/budgets?project=rag-chatbot-475316

2. **Create Budget Alert #1 - $50 Alert**:
   - Click "CREATE BUDGET"
   - Name: `RAG System - $50 Spent Alert`
   - Select your billing account
   - Projects: Select "rag-chatbot-475316"
   - Budget type: "Specified amount"
   - Target amount: `$50`
   - Click "NEXT"
   - Set threshold rules:
     * At 100% of budget ($50) - Email alert
     * Optional: At 50% ($25), 75% ($37.50) for earlier warnings
   - Email recipients: Add your email
   - Click "FINISH"

3. **Create Budget Alert #2 - $200 Spent Alert ($100 Remaining)**:
   - Click "CREATE BUDGET" again
   - Name: `RAG System - $100 Remaining Alert`
   - Target amount: `$200` (this leaves $100 of your $300)
   - Set threshold rules:
     * At 100% of budget ($200) - Email alert
     * At 110% ($220) - Additional warning
   - Email recipients: Add your email
   - Click "FINISH"

4. **Create Budget Alert #3 - Critical $290 Alert**:
   - Click "CREATE BUDGET"
   - Name: `RAG System - CRITICAL NEAR LIMIT`
   - Target amount: `$290` (only $10 left!)
   - Set threshold rules:
     * At 100% of budget ($290) - Email alert
   - This gives you final warning before hitting $300
   - Click "FINISH"

### Via gcloud CLI (Alternative):

```bash
# Budget at $50
gcloud billing budgets create --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="RAG System - $50 Alert" \
  --budget-amount=50USD \
  --threshold-rule=percent=100

# Budget at $200 ($100 remaining)
gcloud billing budgets create --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="RAG System - $100 Remaining" \
  --budget-amount=200USD \
  --threshold-rule=percent=100

# Budget at $290 (critical)
gcloud billing budgets create --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="RAG System - CRITICAL" \
  --budget-amount=290USD \
  --threshold-rule=percent=100
```

## Step 2: Prevent Charges Beyond Free Credit

### ⚠️ CRITICAL: Remove Payment Method After Free Trial

**Option A: Keep Free Trial Only (SAFEST)**

1. Go to: https://console.cloud.google.com/billing
2. Click on your billing account
3. Click "Payment Method" on the left
4. **Remove or don't add a credit card**
5. Without a payment method, Google CANNOT charge you after credits run out
6. ✅ **System will simply stop working when credits are exhausted**

**Option B: Set Spending Limit with Payment Method**

If you added a credit card:

1. **Create Budget with Auto-Disable**:
   - Unfortunately, Google Cloud doesn't support automatic disabling at a budget threshold
   - You'll need to manually disable billing when alerted

2. **Set Up Pub/Sub Notifications** (Advanced):
   ```bash
   # Create Pub/Sub topic for budget alerts
   gcloud pubsub topics create billing-alerts
   
   # Add to your budget (replace BUDGET_ID)
   gcloud billing budgets update BUDGET_ID \
     --notifications-rule-pubsub-topic=projects/rag-chatbot-475316/topics/billing-alerts
   ```

3. **Create Cloud Function to Auto-Disable** (Advanced):
   - Create a Cloud Function that listens to Pub/Sub
   - When budget threshold is reached, function disables billing
   - See: https://cloud.google.com/billing/docs/how-to/notify#cap_disable_billing_to_stop_usage

### **Recommended: Manual Monitoring**

Since auto-disabling is complex, the safest approach:

1. ✅ **Don't add a credit card** (stops automatically at $300)
2. ✅ **Set up email alerts** at $50, $200, $290
3. ✅ **Check billing daily** during active development
4. ✅ **Manually disable APIs** if nearing limit

## Step 3: Set Up API Quotas (Additional Safety)

Limit how much the APIs can be used per day:

1. **Go to APIs**: https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=rag-chatbot-475316

2. **Set Quotas for Vertex AI**:
   - Find "Requests per day"
   - Click "EDIT QUOTAS"
   - Set reasonable limits:
     * Start with 1,000 requests/day (plenty for testing)
     * Increase if needed
   - This prevents runaway costs

## Step 4: Enable Billing Export (Track Spending)

See real-time costs:

1. Go to: https://console.cloud.google.com/billing/export
2. Enable "BigQuery Export"
3. View detailed spending data
4. Optional: Create dashboard to visualize costs

## Step 5: Monitor Spending

### Daily Monitoring:

**Check Current Spend**:
```bash
# View current month's costs
gcloud billing accounts list
gcloud billing accounts describe YOUR_BILLING_ACCOUNT_ID
```

**Via Console**:
- Visit: https://console.cloud.google.com/billing/reports?project=rag-chatbot-475316
- Set date range to "Month to date"
- View spending by service

### Expected Costs for Your RAG System:

**Vertex AI Gemini 1.5 Flash Pricing**:
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

**Typical Query Costs**:
- Multi-collection search with routing: ~500 input + 200 output tokens
- Cost per query: ~$0.0001 (0.01 cents)
- **1,000 queries = ~$0.10**
- **Your $300 = ~3 million queries!**

**Cost Breakdown**:
- AI Routing (if enabled): ~300 tokens input, 100 output = $0.00005 per query
- Main answer generation: ~8,000 tokens input, 500 output = $0.0008 per query
- **Total per query: ~$0.00085**

## What Happens When Credits Run Out?

**Without Credit Card**:
- ✅ APIs stop working
- ✅ You get email notification
- ✅ NO CHARGES - completely safe
- ✅ Can add payment method later if needed

**With Credit Card**:
- ⚠️ Billing continues automatically
- ⚠️ You get charged to your card
- ⚠️ Need to manually disable billing

## Emergency: Disable Billing Immediately

If you need to stop all charges right now:

### Option 1: Disable Billing on Project
```bash
gcloud billing projects unlink rag-chatbot-475316
```

### Option 2: Via Console
1. Go to: https://console.cloud.google.com/billing
2. Select your billing account
3. Find "rag-chatbot-475316" project
4. Click "..." menu → "Disable billing"
5. Confirm

### Option 3: Disable Vertex AI API
```bash
gcloud services disable aiplatform.googleapis.com --project=rag-chatbot-475316
```

## Recommended Safety Configuration

For maximum safety, use this setup:

1. ✅ **NO credit card** on billing account
2. ✅ **Email alerts** at $50, $200, $290
3. ✅ **Daily quota limit** of 1,000 requests on Vertex AI
4. ✅ **Manual monitoring** of billing dashboard weekly
5. ✅ **Disable AI routing** when not testing (saves 40% of API calls)

With these settings:
- You'll get 3 email alerts as you approach your limit
- System will automatically stop when $300 is exhausted
- NO RISK of unexpected charges

## Quick Links

- **Billing Dashboard**: https://console.cloud.google.com/billing/01E07D-1E1BB3-C7F2CB?project=rag-chatbot-475316
- **Budget Alerts**: https://console.cloud.google.com/billing/01E07D-1E1BB3-C7F2CB/budgets?project=rag-chatbot-475316
- **API Quotas**: https://console.cloud.google.com/apis/dashboard?project=rag-chatbot-475316
- **Billing Reports**: https://console.cloud.google.com/billing/reports?project=rag-chatbot-475316

## Contact Support

If you get charged unexpectedly:
- Contact Google Cloud Support
- Explain it was during free trial
- Request refund (often granted for first-time issues)
- Support: https://console.cloud.google.com/support
