🚀 Tutoring Platform – Django Web Application

A complete educational platform built with Django, featuring a blog system, courses, dashboard, authentication, and more.
This project is designed to be scalable, SEO-friendly, and ready for deployment on Railway / Render / VPS.

🧩 Features
🎓 Teaching Platform

User registration & login

Student dashboard

View and enroll in courses

Lesson pages with clean UI

Responsive front-end (mobile friendly)

📝 Blog System

Beautiful blog layout with:

Featured posts

Categories

Popular posts

Search

Sort by newest / popular / oldest

SEO-friendly URLs (slug system)

Auto reading-time calculation

View counter

Cloudinary image upload

🛠 Admin Features

Add / edit / delete posts

Add categories & icons

Manage courses & lessons

Manage users

Dashboard analytics

⚙️ Tech Stack
Component	Technology
Backend	Django (Python)
Database	SQLite (development) / PostgreSQL (production)
Frontend	HTML / CSS / JavaScript
Media Storage	Cloudinary
Deployment	Railway / Render
Version Control	Git + GitHub
📦 Installation

Clone the repository:

git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME


Create a virtual environment:

python -m venv venv
venv\Scripts\activate  # Windows


Install dependencies:

pip install -r requirements.txt


Run migrations:

python manage.py migrate


Start development server:

python manage.py runserver

🔧 Environment Variables

Create a .env file with:

SECRET_KEY=your_secret_key
DEBUG=True
CLOUDINARY_URL=your_cloudinary_url


(Required for image uploads)

📁 Project Structure
project/
│── blog/
│── accounts/
│── courses/
│── static/
│── templates/
│── media/ (ignored by Git)
│── manage.py
│── requirements.txt
│── README.md
└── ...

🚀 Deployment

Ready for:

Railway

Render

Docker

VPS (Ubuntu + Nginx + Gunicorn)

Make sure DEBUG=False and configure ALLOWED_HOSTS before deployment.


🤝 Contributing

Pull requests are welcome!
If you find any issue, open a GitHub issue.

📜 License

MIT License — Free to use and modify.

⭐ Support the Project

If this project helped you, please give it a ⭐ Star on GitHub!
