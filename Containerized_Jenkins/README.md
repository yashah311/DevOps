# 🚀 Jenkins + Nginx (Docker Compose Setup)

A production-ready Jenkins setup using Docker Compose with:
- ✅ Custom Jenkins image
- ✅ Pre-installed plugins
- ✅ Default user provisioning
- ✅ Reverse proxy via Nginx
- ✅ Jenkins running on custom port (9090)
- ✅ Persistent storage
- ✅ Docker-in-Docker support for CI/CD

---

## 📁 Project Structure

devops-automation/
│
├── docker-compose.yml
├── build/
│   ├── Dockerfile
│   ├── plugins.txt
│   └── default-user.groovy
└── nginx/
    └── default.conf

---

## 🚀 Getting Started

```bash
docker compose up -d --build
```

Access:
http://<your-server-ip>

---

## 🔐 Default Credentials
Username: jenuser  
Password: myP@ss12

⚠️ Change after first login.

---

## 🐳 Docker Support

Jenkins can run Docker builds using mounted socket.

---

## 🌐 Nginx Proxy
Browser → Nginx → Jenkins (9090)

---

## 💻 Author
Yash Shah

