# Videoflix Backend 🎬

The backend for the Videoflix platform, developed with Django and Django REST Framework. It provides APIs for user management, video handling, and authentication.

## 🚀 Features

- **User Management**: Registration, login, and token-based authentication.
- **Video Management**: Upload, retrieve, and categorize videos.
- **Token-Authentifizierung**: Secure access to protected endpoints.
- **Categorization**: Group and browse videos by category.
- **Google Cloud Storage**: Store and retrieve videos and thumbnails.

## 🛠️ Technologies Used

- **Python** – Core programming language
- **Django 5.2.1** – High-level web framework for rapid development
- **Django REST Framework 3.16.0** – Toolkit for building Web APIs
- **PostgreSQL** – Database for development
- **DRF Token Authentication** – Secure user authentication
- **AWS S3 / MinIO** – Storage solution for videos and media files
- **Gunicorn** – WSGI server for running the Django application
- **Nginx** – Reverse proxy and static file handling

## ⚙️ Installation & Setup with Dockers 🐳

1. Clone the repository:

   ```bash
    git clone https://github.com/LauraHexx/Videoflix_Backend
    cd Videoflix_Backend

   ```

2. Create and Fill the .env File

   ```bash
    cp .env.template .env

   ```

   [!IMPORTANT] Make sure to replace the placeholder values with actual values specific to your environment where necessary.

3. Clean Docker Containers:

   ```bash
    docker-compose down --volumes
    docker-compose build --no-cache

   ```

4. Start Docker Containers:

   ```bash
    docker-compose up --build

   ```

5. Open the App in Browser:

   http://localhost:8000/admin

6. Login Credentials:

   admin
   adminpassword

7. Upload a Video:

   Please note: It may take 5–10 seconds for the worker to convert the video

8. Start the Frontend:

   Refer to the README.md file in the frontend repository:
   https://github.com/LauraHexx/Videoflix_Frontend.git

## 📋 Testing

```bash
   coverage run -m pytest

```
