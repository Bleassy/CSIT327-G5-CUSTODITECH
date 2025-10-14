from django.shortcuts import render, redirect
from django.contrib import messages
from supabase_client import supabase
import pytz
from datetime import datetime
import uuid

# --- Decorators for Access Control ---

def student_required(function):
    def wrap(request, *args, **kwargs):
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        
        user_type = getattr(request.user, 'user_type', 'student')
        if user_type != 'student':
            messages.warning(request, 'This page is for students only.')
            return redirect('admin_dashboard')
        
        return function(request, *args, **kwargs)
    return wrap

def admin_required(function):
    def wrap(request, *args, **kwargs):
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        
        user_type = getattr(request.user, 'user_type', 'student')
        if user_type != 'admin':
            messages.warning(request, 'You do not have permission to access this page.')
            return redirect('student_dashboard')
        
        return function(request, *args, **kwargs)
    return wrap

# --- Helper Function for Greeting ---
def get_greeting():
    ph_tz = pytz.timezone('Asia/Manila')
    current_hour = datetime.now(ph_tz).hour
    if 5 <= current_hour < 12: return "Good morning"
    if 12 <= current_hour < 18: return "Good afternoon"
    return "Good evening"

# --- Main Redirect View ---
def dashboard_redirect(request):
    if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    user_type = getattr(request.user, 'user_type', 'student')
    if user_type == 'admin':
        return redirect('admin_dashboard')
    return redirect('student_dashboard')

# --- Student Views ---

@student_required
def student_dashboard(request):
    raw_name = getattr(request.user, 'get_full_name', lambda: 'Wildcat')()
    display_name = raw_name.split()[0] if isinstance(raw_name, str) else "Wildcat"
    context = {
        'display_name': display_name,
        'greeting': get_greeting(),
        'active_page': 'dashboard',
        'page_title': 'Dashboard',
    }
    return render(request, 'dashboards/student_dashboard.html', context)

@student_required
def browse_products_view(request):
    try:
        response = supabase.table('products').select('*').eq('is_available', True).order('created_at', desc=True).execute()
        products = response.data
    except Exception as e:
        messages.error(request, f"Could not fetch products: {e}")
        products = []
    context = {
        'products': products,
        'active_page': 'browse',
        'page_title': 'Browse Products',
    }
    return render(request, 'dashboards/browse_products.html', context)

@student_required
def my_reservations_view(request):
    try:
        user_id = request.user.id
        response = supabase.rpc('get_my_reservations', {'p_user_id': user_id}).execute()
        reservations = response.data
    except Exception as e:
        messages.error(request, f"Could not fetch your reservations: {e}")
        reservations = []
        
    context = {
        'reservations': reservations,
        'active_page': 'reservations',
        'page_title': 'My Reservations',
    }
    return render(request, 'dashboards/my_reservations.html', context)

@student_required
def my_orders_view(request):
    try:
        user_id = request.user.id
        response = supabase.rpc('get_my_orders', {'p_user_id': user_id}).execute()
        orders = response.data
    except Exception as e:
        messages.error(request, f"Could not fetch your orders: {e}")
        orders = []

    context = {
        'orders': orders,
        'active_page': 'orders',
        'page_title': 'My Orders',
    }
    return render(request, 'dashboards/my_orders.html', context)

@student_required
def create_reservation_view(request):
    if request.method == 'POST':
        try:
            params = {
                'p_product_id': int(request.POST.get('product_id')),
                'p_user_id': request.user.id,
                'p_quantity': int(request.POST.get('quantity')),
                'p_deal_method': request.POST.get('deal_method', 'meet-up'),
                'p_is_urgent': 'is_urgent' in request.POST
            }
            supabase.rpc('create_reservation', params).execute()
            messages.success(request, "Your item has been reserved successfully!")
            return redirect('my_reservations')

        except Exception as e:
            error_str = str(e)
            if "'success': True" in error_str:
                messages.success(request, "Your item has been reserved successfully!")
                return redirect('my_reservations')
            else:
                messages.error(request, f"Could not reserve item: {e}")
                return redirect('browse_products')
    
    return redirect('browse_products')


@student_required
def create_reservation_view(request):
    """
    Handles the form submission for reserving a product.
    """
    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product_id'))
            quantity = int(request.POST.get('quantity'))
            deal_method = request.POST.get('deal_method')
            user_id = request.user.id

            params = {
                'p_product_id': product_id,
                'p_user_id': user_id,
                'p_quantity': quantity,
                'p_deal_method': deal_method
            }
            supabase.rpc('create_reservation', params).execute()
            
            messages.success(request, "Your item has been reserved successfully!")
            

        except Exception as e:
            error_str = str(e)
            if "'success': True" in error_str:
                messages.success(request, "Your item has been reserved successfully!")
                
            else:
                messages.error(request, f"Could not reserve item: {e}")
                return redirect('browse_products')
    
    return redirect('browse_products')

@student_required
def create_order_view(request):
    """
    Handles the form submission for buying a product with cash or GCash.
    """
    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product_id'))
            quantity = int(request.POST.get('quantity'))
            deal_method = request.POST.get('deal_method')
            payment_method = request.POST.get('payment_method')
            transaction_id = request.POST.get('payment_transaction_id', None)
            user_id = request.user.id

            params = {
                'p_product_id': product_id,
                'p_user_id': user_id,
                'p_quantity': quantity,
                'p_deal_method': deal_method,
                'p_payment_method': payment_method,
                'p_payment_transaction_id': transaction_id
            }
            supabase.rpc('buy_product', params).execute()
            
            messages.success(request, "Your order has been placed successfully!")
            

        except Exception as e:
            error_str = str(e)
            if "'success': True" in error_str:
                messages.success(request, "Your order has been placed successfully!")
                
            else:
                messages.error(request, f"Could not place order: {e}")
                return redirect('browse_products')
    
    return redirect('browse_products')


# --- Admin Views ---
@admin_required
def admin_dashboard(request):
    raw_name = getattr(request.user, 'get_full_name', lambda: 'Admin')()
    display_name = raw_name.split()[0] if isinstance(raw_name, str) else "Admin"
    
    stats = {}
    try:
        stats = supabase.rpc('get_dashboard_stats').execute().data
    except Exception as e:
        messages.error(request, f"Could not load dashboard stats: {e}")
        stats = {
            'total_products': 0, 'total_orders': 0,
            'active_products': 0, 'pending_orders': 0
        }

    context = {
        'display_name': display_name,
        'greeting': get_greeting(),
        'stats': stats,
        'active_page': 'dashboard',
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@admin_required
def manage_products_view(request):
    try:
        response = supabase.table('products').select('*').order('created_at', desc=True).execute()
        products = response.data if response.data else []
    except Exception as e:
        messages.error(request, f"Error fetching products: {e}")
        products = []

    context = {
        'products': products,
        'active_page': 'manage_products',
    }
    return render(request, 'dashboards/manage_products.html', context)

@admin_required
def add_product(request):
    if request.method == 'POST':
        try:
            image_url = None
            image_file = request.FILES.get('product-image')
            if image_file:
                file_ext = image_file.name.split('.')[-1]
                file_name = f'product_{uuid.uuid4()}.{file_ext}'
                supabase.storage.from_('product_images').upload(file=image_file.read(), path=file_name, file_options={"content-type": image_file.content_type})
                image_url = supabase.storage.from_('product_images').get_public_url(file_name)

            product_data = {
                'name': request.POST.get('product-name'),
                'description': request.POST.get('product-description'),
                'price': float(request.POST.get('product-price')),
                'stock_quantity': int(request.POST.get('stock-quantity')),
                'image_url': image_url,
                'is_available': 'is_available' in request.POST
            }
            supabase.table('products').insert(product_data).execute()
            messages.success(request, f"Product '{product_data['name']}' added successfully!")
        except Exception as e:
            messages.error(request, f"Failed to add product: {e}")
    return redirect('manage_products')

@admin_required
def edit_product(request, product_id):
    if request.method == 'POST':
        try:
            update_data = {
                'name': request.POST.get('product-name'),
                'description': request.POST.get('product-description'),
                'price': float(request.POST.get('product-price')),
                'stock_quantity': int(request.POST.get('stock-quantity')),
                'is_available': 'is_available' in request.POST
            }
            supabase.table('products').update(update_data).eq('id', product_id).execute()
            messages.success(request, "Product updated successfully!")
        except Exception as e:
            messages.error(request, f"Failed to update product: {e}")
    return redirect('manage_products')

@admin_required
def delete_product(request, product_id):
    if request.method == 'POST':
        try:
            supabase.table('products').delete().eq('id', product_id).execute()
            messages.success(request, "Product deleted successfully!")
        except Exception as e:
            messages.error(request, f"Failed to delete product: {e}")
    return redirect('manage_products')

@admin_required
def order_management_view(request):
    try:
        response = supabase.rpc('get_all_orders_with_details').execute()
        orders = response.data if response.data else []
    except Exception as e:
        messages.error(request, f"An error occurred while fetching orders: {e}")
        orders = []

    context = {
        'orders': orders,
        'active_page': 'order_management'
    }
    return render(request, 'dashboards/order_management.html', context)

@admin_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            try:
                supabase.table('orders').update({'status': new_status}).eq('id', order_id).execute()
                messages.success(request, f"Order status updated to '{new_status}'.")
            except Exception as e:
                messages.error(request, f"Failed to update order status: {e}")
    return redirect('order_management')

@admin_required
def reports_view(request):
    report_data = {}
    try:
        report_data = supabase.rpc('get_report_stats').execute().data
    except Exception as e:
        messages.error(request, f"Error fetching report data: {e}")
        report_data = {
            'total_products': 0, 'total_orders': 0,
            'active_products': 0, 'sold_out_products': 0,
            'status_counts': {}
        }

    context = {
        'total_products': report_data.get('total_products', 0),
        'total_orders': report_data.get('total_orders', 0),
        'active_products': report_data.get('active_products', 0),
        'sold_out_products': report_data.get('sold_out_products', 0),
        'status_counts': report_data.get('status_counts', {}),
        'active_page': 'reports'
    }
    return render(request, 'dashboards/reports.html', context)