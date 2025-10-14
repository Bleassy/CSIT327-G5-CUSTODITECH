# 📋 CustoDiTech
<div align="center">
<h3>An Online Reservation and Ordering System for School Supplies</h3>
<p>Automating the request and distribution process at CIT-University</p>
</div>

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Setup & Installation](#️-setup--installation)
- [Team Members](#-team-members)
- [Deployment](#-deployment)

---

# 🌟 Overview
Welcome to the official repository for CustoDiTech (also known as the "WildShoppers Portal"), a web-based platform designed to automate the process of requesting and distributing school supplies for students and staff at the Cebu Institute of Technology - University.

# 🎯 Purpose
This system allows students to browse and order available items online, and it provides an administrative dashboard for custodial staff to manage inventory, approve requests, and track supplies efficiently. The goal is to provide:

Faster service for students and staff

Improved resource management and inventory tracking

Modernization of the school supply distribution process

# ✨ Features
Core Features
🔐 Supabase Authentication

Secure user sign-up and sign-in handled via API calls to Supabase.

Session management for authenticated users.

Protected routes for student and admin dashboards.

🛒 Student Portal

Browse available school supplies from an item catalog.

Place orders/requests for items online.

View order history and status.

📊 Administrative Dashboard

A central hub for custodial staff to manage the system.

View and process incoming student requests.

Approve or decline orders.

📦 Inventory Management

Add, update, and remove items from the supply catalog.

Track stock levels to prevent shortages.

Efficiently manage school resources.

# 🛠️ Tech Stack
Backend Framework
Django - High-level Python web framework

Database & Authentication
Supabase

PostgreSQL database for data storage.

Handles all user authentication (sign-up, sign-in, sessions).

Supabase Storage for image and file hosting.

Frontend Technologies
HTML

CSS

Django Template Engine

Version Control
Git - Distributed version control system

GitHub - Code hosting and collaboration platform

# 📋 Prerequisites
Before you begin, ensure you have the following installed on your system:

Python 3.8 or higher

Download from python.org

Verify installation: python --version or python3 --version

Git

Download from git-scm.com

Verify installation: git --version

Supabase Account

You will need a free Supabase account and a project created to get your API keys.

# ⚙️ Setup & Installation
Follow these steps to get a local copy of the project up and running.

Step 1: Clone the Repository
Bash

# Clone the repository
git clone https://github.com/theo2815/CSIT327-G5-CUSTODITECH.git

# Navigate to the project directory
cd CSIT327-G5-CUSTODITECH
Step 2: Create and Activate a Virtual Environment
It's highly recommended to use a virtual environment to manage project dependencies.

Bash

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Or activate it (macOS/Linux)
# source venv/bin/activate
Your terminal prompt should now be prefixed with (venv).
Step 3: Create Environment Variables File
Create a .env file in the project root directory (at the same level as manage.py). Add your credentials to this file:

Code snippet

# Django Secret Key (you can generate a new one)
SECRET_KEY=django-insecure-your-secret-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE=your-supabase-service-role-key
⚠️ Important Security Notes:

You can find your Supabase URL and keys in your Supabase project dashboard under Project Settings > API.

Never commit the .env file to version control.

Step 4: Install Project Dependencies
Bash

# Ensure your virtual environment is activated
pip install -r requirements.txt
Step 5: Run Database Migrations
This command sets up the necessary tables for Django's internal apps (like admin and sessions).

Bash

python manage.py migrate
Step 6: Run the Development Server
Bash

# Start the Django development server
python manage.py runserver
Step 7: Access the Application
Open your web browser and navigate to the application:

http://127.0.0.1:8000/accounts/login
👥 Team Members
Name	Role	CIT-U Email
Theo Cedric Chan	Lead Developer	theocedric.chan@cit.edu
Bliss B. Chavez	Frontend Developer	bliss.chavez@cit.edu
Rusty Summer Daclan	Backend Developer	rustysummer.daclan@cit.edu

Export to Sheets
🌐 Deployment
🚧 Status: In Development
The application is currently being developed for local use. Deployment instructions will be added in the future.

<div align="center">
<p>Made with ❤️ by the CustoDiTech Team</p>
<p>© 2025 CustoDiTech. All rights reserved.</p>



<a href="#-custoditech">Back to Top ⬆️</a>
</div>
