#!/bin/bash

# Production Deployment Script for RAG System
# This script prepares the application for deployment on Plesk or similar hosting

echo "==================================="
echo "RAG System Production Deployment"
echo "==================================="

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p tmp
mkdir -p static
mkdir -p uploads

# Set proper permissions
echo "Setting permissions..."
chmod 755 logs tmp static uploads
chmod 644 *.py
chmod 644 requirements*.txt
chmod 644 *.json

# Install production dependencies
echo "Installing production dependencies..."
pip install -r requirements-auth.txt

# Generate SECRET_KEY if not exists
if [ ! -f .env.production ]; then
    echo "Generating production environment file..."
    python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env.production
    python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env.production
fi

# Create production logging configuration
echo "Setting up logging..."
cat > logging_config.json << EOF
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        },
        "detailed": {
            "format": "%(asctime)s %(levelname)s %(name)s %(funcName)s():%(lineno)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/rag_system.log",
            "maxBytes": 10485760,
            "backupCount": 5
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/errors.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file", "error_file"]
    }
}
EOF

# Create systemd service file (optional)
cat > rag-system.service << EOF
[Unit]
Description=RAG Chat Assistant
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/rag-system
Environment=PATH=/path/to/rag-system/venv/bin
ExecStart=/path/to/rag-system/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:5000 app:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration (if using nginx)
cat > nginx_rag_system.conf << EOF
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Static files
    location /static/ {
        alias /path/to/rag-system/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
}
EOF

# Create Plesk-specific configuration
cat > .htaccess << EOF
# Plesk configuration for RAG System
RewriteEngine On

# Force HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# WSGI Application
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ app.py [L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

# Cache static files
<FilesMatch "\.(css|js|png|jpg|jpeg|gif|ico|svg)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 year"
</FilesMatch>
EOF

# Create backup script
cat > backup.sh << EOF
#!/bin/bash
# Backup script for RAG System

BACKUP_DIR="/path/to/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
APP_DIR="/path/to/rag-system"

echo "Creating backup..."

# Create backup directory
mkdir -p \$BACKUP_DIR

# Backup application files
tar -czf \$BACKUP_DIR/rag_system_\$DATE.tar.gz \\
    --exclude='__pycache__' \\
    --exclude='*.pyc' \\
    --exclude='logs/*.log' \\
    --exclude='tmp/*' \\
    \$APP_DIR

# Backup database
cp -r \$APP_DIR/chroma_db \$BACKUP_DIR/chroma_db_\$DATE

# Keep only last 7 backups
find \$BACKUP_DIR -name "rag_system_*.tar.gz" -mtime +7 -delete
find \$BACKUP_DIR -name "chroma_db_*" -mtime +7 -exec rm -rf {} +

echo "Backup completed: rag_system_\$DATE.tar.gz"
EOF

chmod +x backup.sh

echo ""
echo "==================================="
echo "Deployment preparation completed!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Update .env.production with your actual values"
echo "2. Set up Google OAuth credentials"
echo "3. Configure your domain in ALLOWED_DOMAINS"
echo "4. Upload files to your Plesk hosting"
echo "5. Set up SSL certificates"
echo "6. Configure cron job for backups"
echo ""
echo "Files created:"
echo "- app.py (WSGI entry point)"
echo "- .env.production (environment config)"
echo "- requirements-auth.txt (production deps)"
echo "- health_monitor.py (monitoring)"
echo "- nginx_rag_system.conf (nginx config)"
echo "- .htaccess (Plesk config)"
echo "- backup.sh (backup script)"
echo ""
echo "For Plesk deployment:"
echo "1. Upload all files to your domain directory"
echo "2. Point Python app to app.py"
echo "3. Install requirements-auth.txt"
echo "4. Set environment variables in Plesk panel"
echo ""