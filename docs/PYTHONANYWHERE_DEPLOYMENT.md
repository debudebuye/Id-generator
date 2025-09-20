# PythonAnywhere Deployment Guide

This guide will help you deploy your Flask application to PythonAnywhere with best practices.

## Prerequisites

1. A PythonAnywhere account (free or paid)
2. Your Flask application code ready for deployment
3. Basic knowledge of PythonAnywhere's interface

## Step 1: Upload Your Code

### Option A: Git Clone (Recommended)
1. Open a Bash console on PythonAnywhere
2. Navigate to your home directory: `cd ~`
3. Clone your repository:
   ```bash
   git clone <your-repository-url>
   cd <your-project-folder>
   ```

### Option B: Manual Upload
1. Use the Files tab to upload your project files
2. Or use the Upload a file feature for individual files

## Step 2: Set Up Virtual Environment

1. Create a virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.9 fyda_env
   ```

2. Activate the virtual environment:
   ```bash
   workon fyda_env
   ```

3. Install production requirements:
   ```bash
   pip install -r deployment/requirements-prod.txt
   ```

## Step 3: Configure Environment Variables

1. Create a `.env` file in your project root:
   ```bash
   cp deployment/env.example .env
   nano .env
   ```

2. Set your production values:
   ```env
   FLASK_ENV=production
   FLASK_APP=deployment/wsgi.py
   SECRET_KEY=your-super-secret-key-here
   CORS_ORIGINS=https://yourdomain.com
   ```

3. Generate a secure SECRET_KEY:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

## Step 4: Configure Web App

1. Go to the **Web** tab on PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Flask)
4. Select Python 3.9
5. Set the following:
   - **Source code**: `/home/yourusername/your-project-folder`
   - **Working directory**: `/home/yourusername/your-project-folder`
   - **WSGI configuration file**: Click on the file path and edit it

## Step 5: Configure WSGI File

Edit the WSGI file and replace the content with:

```python
import os
import sys

# Add your project directory to the Python path
path = '/home/yourusername/your-project-folder'
if path not in sys.path:
    sys.path.append(path)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import your Flask app
from app import app

# For PythonAnywhere
application = app

if __name__ == "__main__":
    app.run()
```

**Important**: Replace `yourusername` and `your-project-folder` with your actual values.

## Step 6: Set Up Static Files

1. In the **Web** tab, go to **Static files**
2. Add static file mappings:
   - **URL**: `/static/`
   - **Directory**: `/home/yourusername/your-project-folder/app/static/`

## Step 7: Configure Logs

1. In the **Web** tab, go to **Log files**
2. Set up log file paths:
   - **Error log**: `/home/yourusername/your-project-folder/logs/error.log`
   - **Access log**: `/home/yourusername/your-project-folder/logs/access.log`

## Step 8: Test Your Application

1. Click **Reload** in the **Web** tab
2. Visit your application URL
3. Check the error logs if something goes wrong

## Step 9: Set Up Custom Domain (Optional)

1. In the **Web** tab, go to **Domains**
2. Add your custom domain
3. Update your DNS settings to point to PythonAnywhere

## Troubleshooting

### Common Issues

1. **Import Errors**: Check that all dependencies are installed in your virtual environment
2. **Permission Errors**: Ensure file permissions are correct
3. **Path Issues**: Double-check all paths in your WSGI configuration
4. **Environment Variables**: Verify your `.env` file is in the correct location

### Debug Mode

For debugging, temporarily enable debug mode in your production config:
```python
DEBUG = True
```

### Check Logs

Always check the error logs first when troubleshooting:
```bash
tail -f ~/your-project-folder/logs/error.log
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong SECRET_KEY** values
3. **Enable HTTPS** for production
4. **Regularly update dependencies**
5. **Monitor error logs** for security issues

## Performance Optimization

1. **Enable static file caching** in your web server configuration
2. **Use CDN** for static assets if needed
3. **Optimize database queries** (when you add a database)
4. **Enable compression** for text-based responses

## Monitoring

1. **Set up log rotation** to prevent log files from growing too large
2. **Monitor disk space** usage
3. **Check application performance** regularly
4. **Set up alerts** for critical errors

## Backup Strategy

1. **Regular code backups** via Git
2. **Database backups** (when you add a database)
3. **Environment configuration** backups
4. **Static file backups**

## Maintenance

1. **Regular dependency updates**
2. **Security patches**
3. **Performance monitoring**
4. **Log file cleanup**

## Support

If you encounter issues:
1. Check PythonAnywhere's documentation
2. Review your application logs
3. Verify your configuration
4. Test locally before deploying

---

**Remember**: Always test your deployment in a staging environment first before going live with production.

## Updated File Structure

With the new organization, your deployment files are now in the `deployment/` folder:

```
your-project-folder/
├── deployment/
│   ├── wsgi.py              # WSGI entry point
│   ├── gunicorn.conf.py     # Gunicorn configuration
│   ├── requirements-prod.txt # Production dependencies
│   ├── env.example          # Production environment template
│   └── deploy.py            # Deployment script
├── docs/                     # Documentation
├── templates/                # ID card templates
├── app/                      # Flask application
└── ...                      # Other project files
```

**Important**: When configuring PythonAnywhere, use `deployment/wsgi.py` as your WSGI file path.
