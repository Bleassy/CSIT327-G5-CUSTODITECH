from django.shortcuts import render, redirect
from django.contrib import messages
from supabase_client import supabase, supabase_service
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

# Helper function to log admin activities
def log_activity(user, action, details=None):
    """ A simple helper to insert a new row into the activity_log table. """
    try:
        # ✅ THE FIX IS HERE: Use the powerful 'supabase_service' client for logging
        supabase_service.table('activity_log').insert({
            'user_id': user.id,
            'action': action,
            'details': details or {}
        }).execute()
    except Exception as e:
        print(f"--- FAILED TO LOG ACTIVITY: {e} ---")

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
    """
    Renders the page for browsing ALL products, including those that are out of stock.
    """
    try:
        # ✅ THE FIX IS HERE:
        # Removed the .eq('is_available', True) filter to fetch ALL products.
        # This allows the template to decide which buttons to show for each item.
        response = supabase.table('products').select('*').order('created_at', desc=True).execute()
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
    reservations, backorders = [], []
    try:
        user_id = request.user.id
        response = supabase.rpc('get_my_detailed_reservations', {'p_user_id': user_id}).execute()
        
        if response.data:
           for item in response.data:
                if item.get('created_at'):
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                if item.get('expires_at'):
                    item['expires_at'] = datetime.fromisoformat(item['expires_at'])
                if item['order_type'] == 'reservation':
                    reservations.append(item)
                else:
                    backorders.append(item)
    except Exception as e:
        messages.error(request, f"Could not fetch your reservations: {e}")
    context = {
        'reservations': reservations, 'backorders': backorders,
        'active_page': 'reservations', 'page_title': 'My Reservations',
    }
    return render(request, 'dashboards/my_reservations.html', context)

@student_required
def my_orders_view(request):
    pending_orders, approved_orders, completed_orders, other_orders = [], [], [], []
    try:
        user_id = request.user.id
        response = supabase.rpc('get_my_orders', {'p_user_id': user_id}).execute()
        if response.data:
            for item in response.data:
                if item.get('created_at'):
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                if item['status'] == 'pending': pending_orders.append(item)
                elif item['status'] == 'approved': approved_orders.append(item)
                elif item['status'] == 'completed': completed_orders.append(item)
                else: other_orders.append(item)
    except Exception as e:
        messages.error(request, f"Could not fetch your orders: {e}")
    context = {
        'pending_orders': pending_orders, 'approved_orders': approved_orders,
        'completed_orders': completed_orders, 'other_orders': other_orders,
        'active_page': 'orders', 'page_title': 'My Orders',
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
        except Exception as e:
            error_str = str(e)
            if "'success': True" in error_str:
                messages.success(request, "Your item has been reserved successfully!")
                return redirect('my_reservations')
            else:
                messages.error(request, f"Could not reserve item: {e}")
                return redirect('browse_products')
    return redirect('my_reservations')

@student_required
def create_order_view(request):
    if request.method == 'POST':
        try:
            params = {
                'p_product_id': int(request.POST.get('product_id')),
                'p_user_id': request.user.id,
                'p_quantity': int(request.POST.get('quantity')),
                'p_deal_method': request.POST.get('deal_method'),
                'p_payment_method': request.POST.get('payment_method'),
                'p_payment_transaction_id': request.POST.get('payment_transaction_id', None)
            }
            supabase.rpc('buy_product', params).execute()
        except Exception as e:
            error_str = str(e)
            if "'success': True" in error_str:
                messages.success(request, "Your order has been placed successfully!")
                return redirect('my_orders')
            else:
                messages.error(request, f"Could not place order: {e}")
                return redirect('browse_products')
    return redirect('my_orders')

@student_required
def checkout_reservation_view(request):
    if request.method == 'POST':
        try:
            reservation_id = int(request.POST.get('reservation_id'))
            user_id = request.user.id
            params = {'p_order_id': reservation_id, 'p_user_id': user_id}
            supabase.rpc('checkout_reservation', params).execute()
        except Exception as e:
            error_str = str(e)
            if "'success': True" in error_str:
                messages.success(request, "Checkout successful! Your reservation is now an order.")
                return redirect('my_orders')
            else:
                messages.error(request, f"Could not process checkout: {e}")
                return redirect('my_reservations')
    return redirect('my_orders')

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
        stats = {'total_products': 0, 'total_orders': 0, 'active_products': 0, 'pending_orders': 0}

    context = {
        'display_name': display_name, 'greeting': get_greeting(),
        'stats': stats, 'active_page': 'dashboard',
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@admin_required
def manage_products_view(request):
    search_query = request.GET.get('search', '').strip()
    try:
        query = supabase.table('products').select('*').order('created_at', desc=True)
        if search_query:
            query = query.or_(f'name.ilike.%{search_query}%,category.ilike.%{search_query}%')
        response = query.execute()
        products = response.data if response.data else []
    except Exception as e:
        messages.error(request, f"Error fetching products: {e}")
        products = []
    context = {
        'products': products, 'search_query': search_query,
        'active_page': 'manage_products',
    }
    return render(request, 'dashboards/manage_products.html', context)

@admin_required
def add_product(request):
    if request.method == 'POST':
        # ✅ THE FIX IS HERE: The entire 'try...except' block is now correctly indented.
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
                'category': request.POST.get('product-category'),
                'image_url': image_url,
                'is_available': 'is_available' in request.POST
            }
            response = supabase.table('products').insert(product_data).execute()
            messages.success(request, f"Product '{product_data['name']}' added successfully!")
            
            if response.data:
                log_activity(
                    request.user,
                    'PRODUCT_ADDED',
                    {'product_name': product_data['name'], 'product_id': response.data[0]['id']}
                )
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
                'category': request.POST.get('product-category'),
                'is_available': 'is_available' in request.POST
            }
            supabase.table('products').update(update_data).eq('id', product_id).execute()
            messages.success(request, "Product updated successfully!")
            
            log_activity(
                request.user,
                'PRODUCT_EDITED',
                {'product_name': update_data['name'], 'product_id': product_id}
            )
        except Exception as e:
            messages.error(request, f"Failed to update product: {e}")
    return redirect('manage_products')

@admin_required
def delete_product(request, product_id):
    if request.method == 'POST':
        try:
            product_name = 'Unknown'
            response = supabase.table('products').select('name').eq('id', product_id).execute()
            if response.data:
                product_name = response.data[0]['name']
            supabase.table('products').delete().eq('id', product_id).execute()
            messages.success(request, "Product deleted successfully!")
            log_activity(request.user, 'PRODUCT_DELETED', {'product_id': product_id, 'product_name': product_name})
        except Exception as e:
            messages.error(request, f"Failed to delete product: {e}")
    return redirect('manage_products')

@admin_required
def order_management_view(request):
    search_query = request.GET.get('search', '').strip()
    pending_orders, approved_orders, other_orders = [], [], []
    try:
        params = {'p_search_term': search_query}
        response = supabase.rpc('get_all_orders_with_details', params).execute()
        
        if response.data:
            for item in response.data:
                if item.get('created_at'):
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                if item['status'] == 'pending':
                    pending_orders.append(item)
                elif item['status'] == 'approved':
                    approved_orders.append(item)
                else:
                    other_orders.append(item)
    except Exception as e:
        messages.error(request, f"An error occurred while fetching orders: {e}")
    context = {
        'pending_orders': pending_orders, 'approved_orders': approved_orders,
        'other_orders': other_orders, 'search_query': search_query,
        'active_page': 'order_management'
    }
    return render(request, 'dashboards/order_management.html', context)

@admin_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            try:
                if new_status in ['cancelled', 'rejected']:
                    supabase.rpc('cancel_or_reject_order', {'p_order_id': order_id, 'p_new_status': new_status}).execute()
                    messages.success(request, f"Order #{order_id} has been {new_status}.")
                else:
                    params = {'p_order_id': order_id, 'p_new_status': new_status}
                    supabase.rpc('update_order_status_by_admin', params).execute()
                    messages.success(request, f"Order status updated to '{new_status}'.")
                
                log_activity(
                    request.user, 'ORDER_STATUS_UPDATED',
                    {'order_id': order_id, 'new_status': new_status}
                )
            except Exception as e:
                messages.error(request, f"Failed to update order status: {e}")
    return redirect('order_management')

@admin_required
def delete_order_view(request, order_id):
    if request.method == 'POST':
        try:
            supabase.rpc('delete_order_by_admin', {'p_order_id': order_id}).execute()
            messages.success(request, f"Order #{order_id} has been permanently deleted.")
            log_activity(request.user, 'ORDER_DELETED', {'order_id': order_id})
        except Exception as e:
            messages.error(request, f"Failed to delete order: {e}")
    return redirect('order_management')

@admin_required
def reports_view(request):
    search_query = request.GET.get('search', '').strip()
    report_data = {}
    log_entries = []
    
    try:
        report_data = supabase.rpc('get_report_stats').execute().data
        log_response = supabase.rpc('get_activity_log', {'p_search_term': search_query}).execute()
        
        if log_response.data:
            for entry in log_response.data:
                if entry.get('created_at'):
                    entry['created_at'] = datetime.fromisoformat(entry['created_at'])
                if entry.get('action'):
                    entry['action_display'] = entry['action'].replace('_', ' ').title()
                log_entries.append(entry)
    except Exception as e:
        messages.error(request, f"Error fetching report data: {e}")
        report_data = {'total_products': 0, 'total_orders': 0, 'status_counts': {}}
    context = {
        'total_products': report_data.get('total_products', 0),
        'total_orders': report_data.get('total_orders', 0),
        'status_counts': report_data.get('status_counts', {}),
        'log_entries': log_entries,
        'search_query': search_query,
        'active_page': 'reports'
    }
    return render(request, 'dashboards/reports.html', context)