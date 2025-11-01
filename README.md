# 📋 Online Reservation and Ordering System / CustodiTech

<div align="center"\>
  <h3>An Online Reservation and Ordering System for School Supplies</h3>
  <p>Automating the request and distribution process at CIT-University</p>
</div>

-----

## 📖 Table of Contents

  - [Overview](#-overview)
  - [Features](#-features)
  - [Tech Stack](#-tech-stack)
  - [Prerequisites](#-prerequisites)
  - [Setup & Installation](#-setup--installation)
  - [Project Structure](#-project-structure)
  - [Usage Guide](#-usage-guide)
  - [Team Members](#-team-members)
  - [Deployment](#-deployment)

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

### 📌 **Option 1: How to Contribute to the CustodiTech Project**
#### This guide outlines the step-by-step process for contributing code to the project. We use a "Fork and Pull Request" model to maintain code quality and a clean history.

### Branch Naming Pattern
#### To keep our work organized, please follow this pattern for all new branches:
#### type/short-description
 - type: Describes the kind of change you are making.
 - feat: For a new feature (e.g., feat/student-profile-page).
 - fix: For a bug fix (e.g., fix/login-password-mismatch).
 - docs: For changes to documentation (e.g., docs/update-readme).
 - style: For code style changes that don't affect logic (e.g., style/reformat-css-files).
 - refactor: For code changes that neither fix a bug nor add a feature (e.g., refactor/simplify-view-logic).
 - short-description: A few words separated by hyphens that summarize the change.

----

## Part 1: One-Time Setup
#### You only need to do this once at the beginning.

#### Step 1: Fork the Repository
 - First, you need to create your own personal copy of the main project repository on GitHub.
 - Navigate to the main repository URL: https://github.com/theo2815/CSIT327-G5-CUSTODITECH
 - In the top-right corner of the page, click the Fork button.
 - This will create a new repository under your own GitHub account
   (e.g., your-username/CSIT327-G5-CUSTODITECH). This is your personal fork.

----

### Step 2: Clone Your Fork to Your Computer
#### Now, download the code from your personal fork to your local machine.
1. On your fork's GitHub page, click the green < > Code button.
2. Copy the HTTPS URL provided.
3. Open your terminal or Git Bash and run the following command, replacing the URL with the one you just copied:
```bash
git clone https://github.com/your-username/CSIT327-G5-CUSTODITECH.git
```
4. Navigate into the newly created project folder:
```bash
cd CSIT327-G5-CUSTODITECH
```
----

### Step 3: Configure Remotes
#### You need to tell your local repository about the original "upstream" project so you can keep your fork updated with the team's latest changes.
1. Your fork is already configured as the origin remote. You can verify this by running git remote -v.
2. Now, add the original project repository as a new remote called upstream
```bash
git remote add upstream https://github.com/theo2815/CSIT327-G5-CUSTODITECH.git
```
3. Verify that you now have two remotes (origin and upstream) by runnin
```bash
git remote -v
```
----

## Part 2: The Development Workflow
#### Follow these steps every time you want to start a new feature or bug fix.

### Step 1: Sync Your Fork
#### Before you start writing any new code, you must update your fork with the latest changes from the main project.
1. Make sure you are on your local main branch:
```bash
git checkout main
```
2. "Pull" the latest changes from the original (upstream) project into your local main branch:
```bash
git pull upstream main
```
3. Push these updates to your personal fork on GitHub (origin) to keep it in sync:
```bash
git push origin main
```
----

### Step 2: Create a New Branch
#### Never work directly on the main branch. Always create a new, descriptive branch for your task.
1. Create and switch to your new branch, following the naming pattern:
```bash
# Example for a new feature:
git checkout -b feat/add-shopping-cart
```
----

### Step 3: Write Your Code
#### This is where you do your work: add features, fix bugs, and make any other changes.

----

### Step 4: Commit Your Changes
#### Save your work to the branch's history.
1. Stage all your changed files:
```bash
git add .
```
2. Commit the changes with a clear, descriptive message:
```bash
git commit -m "Feat: Add shopping cart functionality to browse page"
```
----

### Step 5: Push Your Branch to Your Fork
#### Upload your new branch and its commits to your personal fork on GitHub.
```bash
git push -u origin feat/add-shopping-cart
```
----

### Step 6: Create a Pull Request (PR)
#### The final step is to propose your changes to the main project.
1. Go to your fork's page on GitHub (https://github.com/your-username/CSIT327-G5-CUSTODITECH).
2. GitHub will automatically detect your newly pushed branch and show a green button that says "Compare & pull request." Click it.
3. Give your pull request a clear title and a brief description of the changes you made.
4. Click the "Create pull request" button.
##### Your work is now submitted for review! The project lead can now review your code, suggest changes, and merge it into the main project.

----

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
http://127.0.0.1:8000/accounts/login/
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
