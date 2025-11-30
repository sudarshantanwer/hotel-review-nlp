# 🇮🇳 Deploy Hotel Review NLP to AWS (Mumbai Region)

## 🚀 **Quick Deploy from AWS Console**

### **Option 1: One-Click CloudFormation Deploy** ⭐ (Recommended)

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "feat: AWS infrastructure for Mumbai deployment"
   git push origin main
   ```

2. **Deploy via AWS CloudFormation Console**:
   - Go to [AWS CloudFormation Console (Mumbai)](https://ap-south-1.console.aws.amazon.com/cloudformation)
   - Click "Create Stack" > "With new resources"
   - Choose "Upload a template file"
   - Upload: `aws-infrastructure/cloudformation/main-stack.yaml`
   - Follow the wizard with these parameters:
     - **Region**: `ap-south-1` (Mumbai)
     - **Environment**: `prod`
     - **Project Name**: `hotel-review-nlp`
     - **Your Email**: (for alerts)

### **Option 2: AWS CodePipeline (CI/CD)**

1. **Create GitHub Connection**:
   - Go to [AWS CodeStar Connections](https://ap-south-1.console.aws.amazon.com/codesuite/settings/connections)
   - Create connection to GitHub
   - Authorize access to your repository

2. **Deploy Pipeline**:
   - Use the CloudFormation template: `aws-infrastructure/cloudformation/cicd-pipeline.yaml`
   - This creates automatic deployments on every GitHub push

### **Option 3: Manual Terraform from AWS CloudShell**

1. **Open AWS CloudShell** in Mumbai region
2. **Clone your repository**:
   ```bash
   git clone https://github.com/sudarshantanwer/hotel-review-nlp.git
   cd hotel-review-nlp
   ```
3. **Run deployment**:
   ```bash
   ./scripts/deploy.sh prod ap-south-1
   ```

## 📊 **Monitor Your Deployment**

Once deployed, monitor at:
- **CloudFormation**: https://ap-south-1.console.aws.amazon.com/cloudformation
- **ECS Services**: https://ap-south-1.console.aws.amazon.com/ecs/home?region=ap-south-1
- **RDS Database**: https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1
- **Application Load Balancer**: https://ap-south-1.console.aws.amazon.com/ec2/v2/home?region=ap-south-1#LoadBalancers

## 🌐 **Access Your Application**

After deployment (25-40 minutes), your app will be available at:
```
http://hotel-review-nlp-prod-alb-XXXXXXX.ap-south-1.elb.amazonaws.com
```

## 💰 **Cost Estimate (Mumbai Region)**

- **ECS Fargate**: ~₹1,500/month
- **RDS (db.t3.micro)**: ~₹1,200/month  
- **ALB**: ~₹600/month
- **Data Transfer**: ~₹300/month
- **CloudWatch**: ~₹200/month
- **Total**: ~₹3,800/month (~$45 USD)

## 🛠️ **Troubleshooting**

If deployment fails:
1. Check CloudFormation Events tab
2. Look at CloudWatch Logs
3. Verify IAM permissions
4. Ensure Mumbai region quotas

---

**Need help?** Check the detailed logs in CloudFormation or contact support.
