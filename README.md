CIT Shop: Online Reservation and Ordering System
Welcome to the official repository for the CIT Shop (also known as the "WildShoppers Portal"), a web-based platform designed to automate the process of requesting and distributing school supplies for students and staff at the Cebu Institute of Technology - University.

This system allows students to browse and order available items online, and it provides an administrative dashboard for custodial staff to manage inventory, approve requests, and track supplies efficiently. The goal is to provide faster service, improve resource management, and modernize the school supply distribution process.

🛠️ Tech Stack
This project is built with a modern and robust technology stack:

Backend: Django

Frontend: HTML & CSS (with Django Template Engine)

Database & Authentication: Supabase (PostgreSQL)

Image/File Storage: Supabase Storage

Crucially, this project does not use Django's built-in authentication system. All user sign-up, sign-in, and session management is handled via API calls to Supabase.

🚀 Setup and Run Instructions
Follow these steps to get a local copy of the project up and running on your machine.

Prerequisites
Python 3.8+ installed on your system.

Git installed on your system.

A Supabase account and a project created.

Step-by-Step Guide
Clone the Repository
Open your terminal or command prompt and clone the project to your local machine:

git clone [https://github.com/theo2815/CSIT327-G5-CUSTODITECH.git](https://github.com/theo2815/CSIT327-G5-CUSTODITECH.git)
cd CSIT327-G5-CUSTODITECH

Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies.

On macOS/Linux:

python3 -m venv venv
source venv/bin/activate

On Windows:

python -m venv venv
.\\venv\\Scripts\\activate

Your terminal prompt should now be prefixed with (venv).

Install Dependencies
With the virtual environment activated, install all the required Python packages:

pip install -r requirements.txt

Set Up Environment Variables
Create a new file named .env in the root directory of the project. Copy the contents of the .env.example file (if one exists) or use the template below and fill in your actual Supabase project credentials.

# Django Secret Key (you can generate one)
SECRET_KEY=django-insecure-your-secret-key-here

# Supabase Configuration
SUPABASE_URL=[https://your-project-url.supabase.co](https://your-project-url.supabase.co)
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE=your-supabase-service-role-key

You can find your Supabase URL and keys in your Supabase project dashboard under Project Settings > API.

Run Database Migrations
This command will set up the necessary tables for Django's internal apps (like the admin panel and sessions).

python manage.py migrate

Run the Development Server
You're all set! Start the Django development server with this command:

python manage.py runserver

The application will now be running at https://www.google.com/search?q=http://127.0.0.1:8000/. You can open this URL in your web browser to see the live application.

👥 Team Members
This project is developed and maintained by the following team members:

Name

Role

Email Address

Theo Cedric Chan

Lead Developer

theocedric.chan@cit.edu

Bliss B. Chavez

2nd Developer

bliss.chavez@cit.edu

Rusty Summer Daclan

3rd Developer

rustysummer.daclan@cit.edu

