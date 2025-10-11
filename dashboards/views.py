from django.shortcuts import render, redirect
from django.contrib import messages
from supabase_client import supabase
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid
import os

logger = logging.getLogger(__name__)

def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user type"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    # Redirect based on user type from SupabaseUser object
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    return redirect('student_dashboard')

def get_greeting():
    """Returns a time-appropriate greeting for the Philippines timezone."""
    try:
        ph_tz = ZoneInfo("Asia/Manila")
        now = datetime.now(ph_tz)
        hour = now.hour

        if 5 <= hour < 12:
            return "Good Morning"
        elif 12 <= hour < 18:
            return "Good Afternoon"
        else:
            return "Good Evening"
    except Exception:
        return "Welcome" # Fallback greeting

def admin_dashboard(request):
    """
    Displays the admin dashboard with an overview and a list of all products.
    """
    # Ensure user is authenticated and is an admin
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        messages.error(request, "Access denied. You must be an admin to view this page.")
        return redirect('login')

    # Fetch all products from the 'products' table in Supabase
    try:
        products_response = supabase.table('products').select("*").order('created_at', desc=True).execute()
        products = products_response.data
        
        stats = {
            'total_products': len(products),
            'total_buyers': 120, # Placeholder
            'total_reservations': 85, # Placeholder
            'total_orders': 150, # Placeholder
        }

    except Exception as e:
        logger.error(f"Error fetching products from Supabase: {e}")
        messages.error(request, "Could not fetch product data. Please try again later.")
        products = []
        stats = {'total_products': 0, 'total_buyers': 0, 'total_reservations': 0, 'total_orders': 0}

    # Get user's display name for the greeting
    display_name = request.user.get_full_name().split()[0]

    context = {
        'greeting': get_greeting(),
        'display_name': display_name,
        'user_name': display_name,
        'products': products,
        'stats': stats,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


def add_product(request):
    """
    Handles form submission for adding a new product, including image upload.
    """
    if not request.user.is_authenticated or request.user.user_type != 'admin':
        messages.error(request, "You do not have permission to perform this action.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        try:
            image_url = None
            uploaded_file = request.FILES.get('product-image')

            if uploaded_file:
                # Generate a unique file name to prevent overwrites
                file_ext = os.path.splitext(uploaded_file.name)[1]
                file_name = f"{uuid.uuid4()}{file_ext}"
                
                # Upload the file to the 'product_images' bucket in Supabase Storage
                supabase.storage.from_('product_images').upload(
                    file=uploaded_file.read(),
                    path=file_name,
                    file_options={"content-type": uploaded_file.content_type}
                )
                
                # Get the public URL of the uploaded file
                image_url = supabase.storage.from_('product_images').get_public_url(file_name)

            # Extract other form data
            product_data = {
                'name': request.POST.get('product-name'),
                'description': request.POST.get('product-description'),
                'price': float(request.POST.get('product-price')),
                'stock_quantity': int(request.POST.get('product-stock')),
                'image_url': image_url, # Use the public URL from storage
                'is_available': 'is-available' in request.POST
            }

            # Insert product metadata into the 'products' table
            response = supabase.table('products').insert(product_data).execute()

            if response.data:
                messages.success(request, f"Successfully added '{product_data['name']}'.")
            else:
                messages.error(request, "Failed to add product. Please check data and permissions.")

        except Exception as e:
            logger.error(f"Error adding product: {e}")
            messages.error(request, f"An error occurred: {e}")

    return redirect('admin_dashboard')

def student_dashboard(request):
    """
    Displays the student dashboard with a list of available products.
    """
    if not request.user.is_authenticated or request.user.user_type != 'student':
        messages.error(request, "Access denied.")
        return redirect('login')
        
    try:
        # The RLS policy we created ensures this query only returns available products
        products_response = supabase.table('products').select("*").order('name').execute()
        products = products_response.data
    except Exception as e:
        logger.error(f"Error fetching products for student: {e}")
        products = []

    context = {
        'display_name': request.user.get_full_name().split()[0],
        'greeting': get_greeting(),
        'products': products
    }
    # NOTE: You will need to create/update a 'student_dashboard.html' template
    # to display the products fetched here.
    return render(request, 'dashboards/student_dashboard.html', context)


