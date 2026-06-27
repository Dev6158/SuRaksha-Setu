# 🚀 SuRaksha-Setu Online Deployment Guide
This folder contains the complete, self-contained production deployment bundle for the **SuRaksha-Setu** document forensics and behavioral threat analytics platform. 

All algorithms (Error Level Analysis, FFT Moiré, QR Code Pre-Processing, and XML Signature Verification) run **100% locally and offline** without requiring external APIs or third-party web requests.

---

## 📋 System Requirements
Ensure the following are installed on your deployment server (e.g., Ubuntu VPS, EC2 instance, or Private server):
* **Docker** (version 20.10 or higher)
* **Docker Compose** (version 2.0 or higher)

---

## 🛠️ Step-by-Step Deployment Instructions

### 1. Copy the Deployment Folder
Copy this entire `deploy-online/` directory to your target deployment server using `scp`, `rsync`, or a zip file:
```bash
scp -r ./deploy-online user@your-server-ip:/home/user/
```

### 2. Configure Environment Variables
SSH into your server, navigate to the folder, and create the active environment file:
```bash
cd deploy-online/
cp .env.example .env
```
Open the `.env` file and configure secure production values:
* `POSTGRES_PASSWORD`: A secure database password.
* `JWT_SECRET`: A secure key for signing JSON Web Tokens.
* `SPRING_PORT`, `FASTAPI_PORT`, `NEXT_PORT`: Configure port bindings (defaults are `8080`, `8000`, and `3000`).

### 3. Deploy the Containers
Launch the stack in detached (background) mode:
```bash
docker compose up --build -d
```
*Docker will compile the Java Spring Boot source, Next.js frontend dashboard, and FastAPI ML engines. This may take 3-5 minutes on the first build.*

### 4. Verify Services Status
Verify that all 6 containers are running and healthy:
```bash
docker compose ps
```

---

## 🌐 Exposing the Web App (Optional: Reverse Proxy)
In a production web environment, it is best practice to expose the frontend and backend behind a reverse proxy like **Nginx** and secure it with SSL.

### Example Nginx Configuration (`/etc/nginx/sites-available/default`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Dashboard Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API Gateway Backend
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Secure the endpoints with SSL using **Certbot**:
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🔒 Security Best Practices
* Keep ports `5432` (PostgreSQL) and `6379` (Redis) blocked in your firewall (allow access only from internal containers).
* Update `POSTGRES_PASSWORD` and `JWT_SECRET` prior to building.
