# 🔒 GitHub Security Setup Guide

## ⚠️ **NEVER COMMIT THESE TO GITHUB**

- AWS Access Keys (`AKIA...`)
- AWS Secret Access Keys  
- Database passwords
- API tokens
- Private keys (.pem, .key files)
- Environment files (.env)
- Terraform state files

## 🛡️ **How to Set Up GitHub Secrets**

### **Step 1: Go to Repository Settings**
1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**

### **Step 2: Add Required Secrets**
Click **New repository secret** for each:

```
Name: AWS_ACCESS_KEY_ID
Value: AKIA... (your AWS access key)

Name: AWS_SECRET_ACCESS_KEY  
Value: ... (your AWS secret key)

Name: AWS_REGION
Value: ap-south-1
```

### **Step 3: Verify Secrets Are Set**
✅ You should see 3 secrets listed (values are hidden)

## 🔍 **Security Checklist Before Push**

- [ ] No `.env` files committed
- [ ] No AWS credentials in code
- [ ] No hardcoded passwords
- [ ] No Terraform state files
- [ ] `.gitignore` includes security patterns
- [ ] GitHub secrets configured

## 🚨 **If You Accidentally Committed Secrets**

1. **Immediately rotate credentials** in AWS Console
2. Remove from git history:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch path/to/secret/file' --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push: `git push origin --force --all`

## ✅ **Safe to Commit**

- CloudFormation templates (no hardcoded secrets)
- Terraform files (using variables/references)
- Application code
- Documentation
- Docker files
- GitHub Actions workflows (using secrets references)

---

**Remember**: Once committed to GitHub, consider any secret compromised!
