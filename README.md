# 📋 Online Reservation and Ordering System / CustodiTech

<div align="center"\>
  <h3>An Online Reservation and Ordering System for School Supplies</h3>
  <p>Automating the request and distribution process at CIT-University</p>
</div>

-----

## 📖 Table of Contents

  - [Overview](https://www.google.com/search?q=%23-overview)
  - [Features](https://www.google.com/search?q=%23-features)
  - [Tech Stack](https://www.google.com/search?q=%23%EF%B8%8F-tech-stack)
  - [Prerequisites](https://www.google.com/search?q=%23-prerequisites)
  - [Setup & Installation](https://www.google.com/search?q=%23%EF%B8%8F-setup--installation)
  - [Project Structure](https://www.google.com/search?q=%23-project-structure)
  - [Usage Guide](https://www.google.com/search?q=%23-usage-guide)
  - [Team Members](https://www.google.com/search?q=%23-team-members)
  - [Deployment](https://www.google.com/search?q=%23-deployment)

-----

## 🌟 Overview

Welcome to the official repository for **CustoDiTech** (also known as the "WildShoppers Portal"), a web-based platform designed to automate the process of requesting and distributing school supplies for students and staff at the Cebu Institute of Technology - University.

### 🎯 Purpose

This system allows students to reserve unavailable items and order available items online, and it provides an administrative dashboard for custodial staff to manage inventory, approve requests, and track supplies efficiently. The goal is to provide:

  - **Faster** service for students and staff
  - **Improved** resource management and inventory tracking
  - **Modernization** of the school supply distribution process

## ✨ Features

### Core Features

  - 🔐 **Supabase Authentication**
      - Secure user sign-up and sign-in handled via API calls to Supabase.
      - Session management for authenticated users.
      - Protected routes for student and admin dashboards.

  - 🛒 **Student Portal**
      - Browse available school supplies from an item catalog.
      - Place orders/reserve for items online.
      - View order history and status.

  - 📊 **Administrative Dashboard**
      - A central hub for custodial staff to manage the system.
      - View and process incoming student requests.
      - Approve or decline orders.

  - 📦 **Inventory Management**
      - Add, update, and remove items from the supply catalog.
      - Track stock levels to prevent shortages.
      - Efficiently manage school resources.

-----

## 🛠️ Tech Stack

### **Backend Framework**

  - **Django** - High-level Python web framework
  - **Python** - Core programming language

### **Database & Authentication**

  - **Supabase**
      - PostgreSQL database for data storage.
      - Handles all user authentication (sign-up, sign-in, sessions).
      - Supabase Storage for image and file hosting.

### **Frontend Technologies**

  - **HTML**
  - **CSS**
  - **Django Template Engine**

### **Version Control**

  - **Git** - Distributed version control system
  - **GitHub** - Code hosting and collaboration platform

-----

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

  - **Python 3.8 or higher**
      - Download from [python.org](https://www.python.org/downloads/)
      - Verify installation: `python --version` or `python3 --version`

  - **Git**
      - Download from [git-scm.com](https://git-scm.com/downloads)
      - Verify installation: `git --version`

  - **IDE**
      - VS Code (Recommended)

-----

## ⚙️ Setup & Installation

### 📌 **Option 1: Fork the repo to make a contribute**

If you just want to contribute:
### 1. Fork the repo on GitHub
```bash
Open: https://github.com/theo2815/CSIT327-G5-CUSTODITECH
Click Fork (top-right). This creates your-username/CSIT327-G5-CUSTODITECH
```
----

### 2. Clone your fork locally
```bash
# replace <your-username> with your GitHub username
git clone https://github.com/<your-username>/CSIT327-G5-CUSTODITECH.git
cd CSIT327-G5-CUSTODITECH

```
----

### 3. Add the original repo as upstream (so you can sync later)
```bash
git remote add upstream https://github.com/theo2815/CSIT327-G5-CUSTODITECH.git
# verify remotes
git remote -v
```
----

### 4. Create a new branch for your changes (never work on main)
```bash
# use a descriptive branch name: feature/<what> or fix/<issue>
git checkout -b feature/add-new-page
```
----

### 5. Make changes & stage them
```bash
# edit files with your editor, then:
git add .
git commit -m "feat: add new page for X (short clear message)"

```
----

### 6. Keep your branch up-to-date with upstream (recommended before pushing)
```bash
# fetch upstream main and rebase (or merge) into your branch
git fetch upstream
git checkout main
git pull upstream main
git checkout feature/add-new-page
git rebase main
# if conflicts appear: resolve, then
git add <resolved-files>
git rebase --continue

```
----

### 7. Push your branch to your fork
```bash
git push origin feature/add-new-page

```
----

### 8. Open a Pull Request (PR)
```bash
- Go to your fork on GitHub → switch to feature/add-new-page branch → click Compare & pull request.
- Fill title and clear description (what you changed, why, how to test).
- Select base repo: theo2815/CSIT327-G5-CUSTODITECH main (or the repo's target branch).
```
----

### 9. Respond to reviews
   #### If reviewers request changes, update your branch locally, commit, and push again:
```bash
# make changes
git add .
git commit -m "fix: address review comment about X"
git push origin feature/add-new-page
```
  #### The PR will update automatically.
----

### 10. After PR is merged
```bash
# cleanup local branch
git checkout main
git fetch upstream
git pull upstream main
git branch -d feature/add-new-page
git push origin --delete feature/add-new-page   # optional: delete remote branch
```
-----

### 📌 **Option 2: Just Using the Project (Direct Clone)**

If you just want to use the application:

```bash
# Clone the repository directly
git clone https://github.com/theo2815/CSIT327-G5-CUSTODITECH.git

# Navigate to the project directory
cd CSIT327-G5-CUSTODITECH
```

-----

### 🔧 **Common Setup Steps (After Cloning)**

#### **Step 1: Create and Activate a Virtual Environment**

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Or activate it (macOS/Linux)
# source venv/bin/activate

# You should see (venv) in your terminal prompt
```

-----

#### **Step 2: Create Environment Variables File**

Create a `.env` file in the project root directory

Add the following configuration to `.env`:

```env
# Django Secret Key
SECRET_KEY=django-insecure-your-secret-key-here

# Supabase Configuration
SUPABASE_URL=https://lsumstfswtxqrieuibky.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzdW1zdGZzd3R4cXJpZXVpYmt5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MjQ3ODYsImV4cCI6MjA3NTUwMDc4Nn0.Ec1zIGJtibTLOaMLuRoecqhxVTWnYjAgzKnGVvq-xxY
SUPABASE_SERVICE_ROLE=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzdW1zdGZzd3R4cXJpZXVpYmt5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTkyNDc4NiwiZXhwIjoyMDc1NTAwNzg2fQ.iI0-luBMxXxUB1d3Xaq1MaVZqmJj5wv14X_ARR01Tfs

# Optional: If using Supabase as Django database
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.your-project-id.supabase.co:5432/postgres
```

**⚠️ Important Security Notes:**

  - You can find your Supabase URL and keys in your Supabase project dashboard under **Project Settings \> API**.
  - Never commit `.env` to version control.
      

-----

#### **Step 3: Install Project Dependencies**

```bash
# Make sure your virtual environment is activated (you should see (venv) in the prompt)

# Install all required packages from requirements.txt
pip install -r requirements.txt

# Wait for all packages to install
```

-----

#### **Step 4: Run Database Migrations**

This command sets up the necessary tables for Django's internal apps (like admin and sessions).

```bash
python manage.py migrate
```

-----

#### **Step 5: Run the Development Server**

```bash
# Start the Django development server
python manage.py runserver

# Server will start on http://127.0.0.1:8000/
```

-----

#### **Step 6: Access the Application**

Open your web browser and navigate to the application:

**Main Application Login:**

```
http://127.0.0.1:8000/accounts/login
```

**Available Pages:**

  - Login: `http://127.0.0.1:8000/accounts/login`
  - Register: `http://127.0.0.1:8000/accounts/register`
  - Student/Admin Dashboard: (Requires login)

-----

## 👥 Team Members

**Project Team**
| Name | Role | CIT-U Email |
|------|------|-------------|
| **Theo Cedric Chan** | Lead Developer full stack | theocedric.chan@cit.edu |
| **Bliss B. Chavez** | Frontend Developer | bliss.chavez@cit.edu |
| **Rusty Summer Daclan** | Backend Developer | rustysummer.daclan@cit.edu |

## **Academic Instructors** 
| Name | Role |
|------|------| 
| **Frederick Revilleza** | CSIT327 Instructor | 
| **Joemarie Amparo** | IT317 Instructor |

## 🌐 Deployment

### 🚧 **Status: In Development**

The application is currently being developed for local use. Deployment instructions will be added in the future.

---

<div align="center">
  <p>Made with ❤️ by the CustoDiTech Team</p>
  <p>© 2025 CustoDiTech. All rights reserved.</p>
  <br>
  <a href="\#-custoditech"\>Back to Top ⬆️</a>
</div>
