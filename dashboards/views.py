from django.shortcuts import render, redirect
from django.http import JsonResponse 
from django.contrib import messages
from supabase_client import supabase, supabase_service
import pytz
from datetime import datetime
import uuid
from collections import defaultdict

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
    """
    Renders the main student dashboard with a welcome message and summaries
    of the most recent reservation and order.
    """
    raw_name = getattr(request.user, 'get_full_name', lambda: 'Wildcat')()
    display_name = raw_name.split()[0] if isinstance(raw_name, str) else "Wildcat"
    
    latest_reservation = None
    latest_order = None
    
    try:
        user_id = request.user.id
        
        # Fetch the most recent reservation
        res_response = supabase.rpc('get_my_detailed_reservations', {'p_user_id': user_id}).limit(1).execute()
        if res_response.data:
            latest_reservation = res_response.data[0]
            if latest_reservation.get('created_at'):
                latest_reservation['created_at'] = datetime.fromisoformat(latest_reservation['created_at'])
            if latest_reservation.get('expires_at'):
                latest_reservation['expires_at'] = datetime.fromisoformat(latest_reservation['expires_at'])

        # Fetch the most recent order
        order_response = supabase.rpc('get_my_orders', {'p_user_id': user_id}).limit(1).execute()
        if order_response.data:
            latest_order = order_response.data[0]
            if latest_order.get('created_at'):
                latest_order['created_at'] = datetime.fromisoformat(latest_order['created_at'])

    except Exception as e:
        messages.error(request, "Could not load dashboard summaries.")

    context = {
        'display_name': display_name,
        'greeting': get_greeting(),
        'latest_reservation': latest_reservation,
        'latest_order': latest_order,
        'active_page': 'dashboard',
        'page_title': 'Dashboard',
    }
    return render(request, 'dashboards/student_dashboard.html', context)

@student_required
def browse_products_view(request):
    """
    Renders the page for browsing products, categorized and searchable.
    """
    search_query = request.GET.get('search', '').strip()
    categorized_products = defaultdict(list)
    
    try:
        # Start the base query
        query = supabase.table('products').select('*').order('created_at', desc=True)

        # If there's a search query, add the filter to the query
        if search_query:
            query = query.ilike('name', f'%{search_query}%')
        
        # ✅ FIX: Execute the 'query' variable that you built.
        response = query.execute() 
        products = response.data

        if products:
            for product in products:
                # This correctly groups products with 'None' or no category
                category_name = product.get('category') or 'Uncategorized'
                categorized_products[category_name].append(product)
    
    except Exception as e:
        messages.error(request, f"Could not fetch products: {e}")

    context = {
        'categorized_products': dict(categorized_products), 
    'search_query': search_query,
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
                # ✅ THE FIX IS HERE:
                # Only process items that are explicitly in a 'pending' state.
                # This prevents already processed or cancelled items from appearing.
                if item.get('status') == 'pending':
                    if item.get('created_at'):
                        item['created_at'] = datetime.fromisoformat(item['created_at'])
                    if item.get('expires_at'):
                        item['expires_at'] = datetime.fromisoformat(item['expires_at'])
                    
                    if item['order_type'] == 'reservation':
                        reservations.append(item)
                    elif item['order_type'] == 'backorder':
                        backorders.append(item)
                            
    except Exception as e:
        messages.error(request, f"Could not fetch your reservations: {e}")
        
    context = {
        'reservations': reservations, 
        'backorders': backorders,
        'active_page': 'reservations', 
        'page_title': 'My Reservations',
    }
    return render(request, 'dashboards/my_reservations.html', context)

@student_required
def my_orders_view(request):
    # Initialize lists for each status category
    pending_orders, approved_orders, completed_orders, other_orders = [], [], [], []
    
    try:
        user_id = request.user.id
        # ✅ Call the new detailed function
        response = supabase.rpc('get_my_detailed_orders', {'p_user_id': user_id}).execute()
        
        if response.data:
            all_orders = response.data
            
            # Convert date strings to datetime objects
            for item in all_orders:
                if item.get('created_at'):
                    # Ensure timezone info is handled if present, else parse naive
                    created_at_str = item['created_at']
                    try:
                        # Attempt parsing with timezone
                        item['created_at'] = datetime.fromisoformat(created_at_str)
                    except ValueError:
                        # Fallback for naive datetime strings (adjust format if needed)
                        try:
                           item['created_at'] = datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%S.%f')
                        except ValueError:
                           # Handle potential other formats or log error
                           item['created_at'] = None # Or keep original string

            # Separate orders into lists based on status
            for item in all_orders:
                status = item.get('status', 'unknown') # Default if status is missing
                if status == 'pending': 
                    pending_orders.append(item)
                elif status == 'approved': 
                    approved_orders.append(item)
                elif status == 'completed': 
                    completed_orders.append(item)
                else: # Includes 'cancelled', 'rejected', etc.
                    other_orders.append(item)
                    
    except Exception as e:
        messages.error(request, f"Could not fetch your orders: {e}")
        # Ensure lists are empty on error
        pending_orders, approved_orders, completed_orders, other_orders = [], [], [], []

    context = {
        'pending_orders': pending_orders, 
        'approved_orders': approved_orders,
        'completed_orders': completed_orders, 
        'other_orders': other_orders,
        # Pass an empty search query for now, JS will handle filtering
        'search_query': '', 
        'active_page': 'orders', 
        'page_title': 'My Orders',
    }
    return render(request, 'dashboards/my_orders.html', context)

@student_required
def batch_delete_orders_view(request):
    """ Handles batch deletion of orders by the student who owns them. """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        order_ids_str = request.POST.get('order_ids')
        try:
            order_ids = [int(oid) for oid in order_ids_str.split(',') if oid.isdigit()]
            if not order_ids:
                raise ValueError("No valid order IDs provided.")

            user_id = request.user.id

            # Use service role but ensure the user owns the orders
            supabase_service.table('orders') \
                .delete() \
                .in_('id', order_ids) \
                .eq('user_id', user_id) \
                .execute()

            return JsonResponse({'success': True, 'message': f"✅ {len(order_ids)} order(s) have been deleted."})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f"An error occurred during batch deletion: {e}"}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

@student_required
def delete_single_order_view(request, order_id):
    """ Handles deletion of a single order by the student who owns it. """
    # Check for AJAX POST request
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            user_id = request.user.id

            # Use service role but ensure the user owns the order
            supabase_service.table('orders') \
                .delete() \
                .eq('id', order_id) \
                .eq('user_id', user_id) \
                .execute()

            # ✅ Return JSON success
            return JsonResponse({'success': True, 'message': f"🗑️ Order #{order_id} has been permanently deleted."})

        except Exception as e:
            # ✅ Return JSON error
            return JsonResponse({'success': False, 'error': f"Failed to delete order #{order_id}: {e}"}, status=400)

    # ✅ Return error for invalid requests
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

@student_required
def create_reservation_view(request):
    # We only expect AJAX (fetch) requests now
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            params = {
                'p_product_id': int(request.POST.get('product_id')),
                'p_user_id': request.user.id,
                'p_quantity': int(request.POST.get('quantity')),
                'p_deal_method': request.POST.get('deal_method', 'meet-up'),
                'p_is_urgent': 'is_urgent' in request.POST
            }
            
            # Execute the RPC
            response = supabase.rpc('create_reservation', params).execute()
            
            # Check for Supabase-level errors
            if hasattr(response, 'error') and response.error:
                 raise Exception(str(response.error))

            # Check for errors returned in the data (if your function does that)
            if isinstance(response.data, list) and len(response.data) > 0 and 'error' in response.data[0]:
                 raise Exception(response.data[0]['error'])

            # ✅ If no errors, send a JSON success response
            return JsonResponse({'success': True, 'message': '✅ Your item has been reserved successfully!'})

        except Exception as e:
            error_str = str(e)
            
            # ✅ THIS IS THE FIX: Check if the "error" is actually a success message
            if "'success': True" in error_str or "'message': 'Item reserved successfully!'" in error_str:
                return JsonResponse({'success': True, 'message': '✅ Your item has been reserved successfully!'})
            else:
                # This is a real error
                return JsonResponse({'success': False, 'error': f"Could not reserve item: {e}"}, status=400)
    
    # If it's not an AJAX POST request, return an error
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

@student_required
def create_order_view(request):
    # We only expect AJAX (fetch) requests now
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            params = {
                'p_product_id': int(request.POST.get('product_id')),
                'p_user_id': request.user.id,
                'p_quantity': int(request.POST.get('quantity')),
                'p_deal_method': request.POST.get('deal_method'),
                'p_payment_method': request.POST.get('payment_method'),
                'p_payment_transaction_id': request.POST.get('payment_transaction_id', None)
            }
            
            # Execute the RPC
            response = supabase.rpc('buy_product', params).execute()

            # Check for Supabase-level errors
            if hasattr(response, 'error') and response.error:
                 raise Exception(str(response.error))

            # Check for errors returned in the data
            if isinstance(response.data, list) and len(response.data) > 0 and 'error' in response.data[0]:
                 raise Exception(response.data[0]['error'])

            # ✅ If no errors, send a JSON success response
            return JsonResponse({'success': True, 'message': '🎉 Your order has been placed successfully!'})

        except Exception as e:
            error_str = str(e)
            
            # ✅ THIS IS THE FIX: Check if the "error" is actually a success message
            if "'success': True" in error_str:
                return JsonResponse({'success': True, 'message': '🎉 Your order has been placed successfully!'})
            else:
                # This is a real error
                return JsonResponse({'success': False, 'error': f"Could not place order: {e}"}, status=400)
    
    # If it's not an AJAX POST request, return an error
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

@student_required
def checkout_reservation_view(request):
    if request.method == 'POST':
        try:
            print(f"--- CHECKOUT VIEW REACHED --- Received POST for reservation ID: {request.POST.get('reservation_id')}")
            reservation_id = int(request.POST.get('reservation_id'))
            user_id = request.user.id
            params = {'p_order_id': reservation_id, 'p_user_id': user_id}

            print(f"--- Calling Supabase RPC checkout_reservation with params: {params}")

            # ✅ CAPTURE and PRINT the response
            response = supabase.rpc('checkout_reservation', params).execute()
            print(f"--- Supabase RPC Response: {response}")

            return JsonResponse({'success': True, 'message': '✅ Checkout successful! Your reservation is now an order.'})

        except Exception as e:
            print(f"--- ERROR in checkout_reservation_view: {e}")
            return JsonResponse({'success': False, 'error': f"Could not process checkout: {e}"}, status=400)

    # If not POST, redirect (should ideally not happen with button clicks)
    print("--- CHECKOUT VIEW REACHED --- Not a POST request, redirecting.")
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

@student_required
def student_profile_view(request):
    user_id = request.user.id
    
    # Handle form submissions for updating profile or password
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # --- Handle Profile Details Update ---
        if form_type == 'details':
            try:
                params = {
                    'p_full_name': request.POST.get('full_name'),
                    'p_phone_number': request.POST.get('phone_number'),
                    'p_address': request.POST.get('address')
                }
                supabase.rpc('update_my_profile', params).execute()
                messages.success(request, 'Your profile has been updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {e}')
        
        # --- Handle Password Change ---
        elif form_type == 'password':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if new_password1 != new_password2:
                messages.error(request, 'Passwords do not match.')
            elif len(new_password1) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
            else:
                try:
                    # Use the Supabase Auth API to update the user's password
                    supabase.auth.update_user({'password': new_password1})
                    messages.success(request, 'Your password has been changed successfully!')
                except Exception as e:
                    messages.error(request, f'Error changing password: {e}')
        
        return redirect('student_profile')

    # --- Handle GET request to display the page ---
    profile_data = {}
    try:
        # Fetch the user's current profile to pre-fill the form
        response = supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
        profile_data = response.data
    except Exception as e:
        messages.error(request, f'Could not load your profile: {e}')
        
    context = {
        'profile': profile_data,
        'active_page': 'profile',
        'page_title': 'My Profile'
    }
    return render(request, 'dashboards/student_profile.html', context)


@student_required
def cancel_reservation_view(request, reservation_id):
    """
    Allows a student to cancel their own reservation.
    """
    if request.method == 'POST':
        try:
            # We will use the same RPC as the admin's 'cancel' function
            # It's efficient to reuse backend logic.
            supabase.rpc('cancel_or_reject_order', {
                'p_order_id': reservation_id, 
                'p_new_status': 'cancelled'
            }).execute()
            
            return JsonResponse({'success': True, 'message': '🗑️ Your reservation has been successfully cancelled.'})
            
            # Log this activity for the admin (optional but good practice)
            log_activity(
                request.user, 
                'RESERVATION_CANCELLED_BY_USER',
                {'order_id': reservation_id}
            )
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Could not cancel the reservation: {e}"}, status=400)
            
    # Redirect back to the reservations page regardless of method (POST or GET)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

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

        products = sorted(
            products, 
            key=lambda p: (
                p.get('is_available', True), # Sorts False (Unavailable) before True (Available)
                not (0 < p.get('stock_quantity', 0) < 10) # Sorts True (Low Stock) before False
            )
        )

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
        try:
            image_url = None
            image_file = request.FILES.get('product-image')
            
            if image_file:
                file_ext = image_file.name.split('.')[-1]
                file_name = f'product_{uuid.uuid4()}.{file_ext}'
                
                supabase_service.storage.from_('product_images').upload(
                    file=image_file.read(), 
                    path=file_name, 
                    file_options={"content-type": image_file.content_type}
                )
                image_url = supabase_service.storage.from_('product_images').get_public_url(file_name)
            
            stock = int(request.POST.get('stock-quantity', 0))

            product_data = {
                'name': request.POST.get('product-name'),
                'description': request.POST.get('product-description'),
                'price': float(request.POST.get('product-price')),
                'stock_quantity': int(request.POST.get('stock-quantity')),
                'category': request.POST.get('product-category'),
                'image_url': image_url,
                'is_available': stock > 0 and 'is_available' in request.POST
            }

            if request.POST.get('product-category') == 'Uniforms':
                product_data['size'] = request.POST.get('product-size')

            # ✅ CHANGED: We execute and get the data
            response = supabase_service.table('products').insert(product_data).execute()
            
            if not response.data or len(response.data) == 0:
                 raise Exception("Failed to create product, no data returned.")

            new_product = response.data[0]
            
            log_activity(
                request.user,
                'PRODUCT_ADDED',
                {'product_name': new_product['name'], 'product_id': new_product['id']}
            )
            
            # ✅ CHANGED: Return JSON instead of redirecting
            return JsonResponse({'success': True, 'message': 'Product added successfully!', 'product': new_product})

        except Exception as e:
            # ✅ CHANGED: Return JSON error
            return JsonResponse({'success': False, 'error': f"Failed to add product: {e}"}, status=400)
            
    # ✅ CHANGED: Handle non-POST requests (e.g., direct URL access)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@admin_required
def edit_product(request, product_id):
    if request.method == 'POST':
        try:
            category = request.POST.get('product-category')
            stock = int(request.POST.get('stock-quantity'))

            update_data = {
                'name': request.POST.get('product-name'),
                'description': request.POST.get('product-description'),
                'price': float(request.POST.get('product-price')),
                'stock_quantity': stock,
                'category': category, 
                'is_available': stock > 0 and 'is_available' in request.POST
            }

            if category == 'Uniforms':
                update_data['size'] = request.POST.get('product-size')
            else:
                update_data['size'] = None 
            
            new_image_file = request.FILES.get('product-image')
            if new_image_file:
                file_ext = new_image_file.name.split('.')[-1]
                file_name = f'product_{uuid.uuid4()}.{file_ext}'
                
                supabase_service.storage.from_('product_images').upload(
                    file=new_image_file.read(), 
                    path=file_name, 
                    file_options={"content-type": new_image_file.content_type}
                )
                
                new_image_url = supabase_service.storage.from_('product_images').get_public_url(file_name)
                update_data['image_url'] = new_image_url

                old_image_url = request.POST.get('current-image-url')
                if old_image_url and old_image_url.strip():
                    try:
                        old_file_name = old_image_url.split('/')[-1]
                        supabase_service.storage.from_('product_images').remove([old_file_name])
                    except Exception as e:
                        print(f"Could not remove old image '{old_file_name}': {e}")
            
            # ✅ CHANGED: Execute the update
            update_response = supabase_service.table('products').update(update_data).eq('id', product_id).execute()

            if not update_response.data or len(update_response.data) == 0:
                raise Exception("Failed to update product, no data returned from update.")
            
            updated_product = update_response.data[0]
            
            log_activity(
                request.user,
                'PRODUCT_EDITED',
                {'product_name': updated_product['name'], 'product_id': product_id}
            )
            
            # ✅ CHANGED: Return JSON with the updated product
            return JsonResponse({'success': True, 'message': 'Product updated successfully!', 'product': updated_product})

        except Exception as e:
            # ✅ CHANGED: Return JSON error
            return JsonResponse({'success': False, 'error': f"Failed to update product: {e}"}, status=400)
            
    # ✅ CHANGED: Handle non-POST requests
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

# [views.py]

@admin_required
def delete_product(request, product_id):
    if request.method == 'POST':
        try:
            product_name = 'Unknown'
            # We must use the service client to delete
            response = supabase_service.table('products').select('name').eq('id', product_id).execute()
            if response.data:
                product_name = response.data[0]['name']
                
            # ✅ Use service client here
            supabase_service.table('products').delete().eq('id', product_id).execute()
            
            log_activity(request.user, 'PRODUCT_DELETED', {'product_id': product_id, 'product_name': product_name})
            
            # ✅ CHANGED: Return JSON
            return JsonResponse({
                'success': True, 
                'message': '🗑️ Product deleted successfully!', 
                'product_id': product_id # Send the ID back to the JS
            })
        except Exception as e:
            # ✅ CHANGED: Return JSON error
            return JsonResponse({'success': False, 'error': f"Failed to delete product: {e}"}, status=400)
            
    # ✅ CHANGED: Handle non-POST requests
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def order_management_view(request):
    search_query = request.GET.get('search', '').strip()
    
    # ✅ ADDED: Re-initialize the pending_orders list
    pending_orders = [] 
    approved_orders = []
    completed_orders = []
    other_orders = [] # This will hold cancelled/rejected
    
    try:
        params = {'p_search_term': search_query}
        response = supabase.rpc('get_all_orders_with_details', params).execute()
        
        if response.data:
            for item in response.data:
                if item.get('created_at'):
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                
                status = item.get('status')
                
                # ✅ ADDED: Logic to sort 'pending' orders into their own list
                if status == 'pending':
                    pending_orders.append(item)
                elif status == 'approved':
                    approved_orders.append(item)
                elif status == 'completed':
                    completed_orders.append(item)
                elif status in ['cancelled', 'rejected']:
                    other_orders.append(item)
                    
    except Exception as e:
        messages.error(request, f"An error occurred while fetching orders: {e}")

    context = {
        'pending_orders': pending_orders, # ✅ ADDED: Pass the new list to the template
        'approved_orders': approved_orders,
        'completed_orders': completed_orders,
        'other_orders': other_orders,
        'search_query': search_query,
        'active_page': 'order_management',
        'page_title': 'Order Management'
    }
    return render(request, 'dashboards/order_management.html', context)

@admin_required
def admin_batch_delete_orders_view(request):
    """ Handles batch deletion of orders by an admin. """
    if request.method == 'POST':
        order_ids_str = request.POST.get('order_ids')
        if not order_ids_str:
            messages.error(request, "No orders selected for deletion.")
            return redirect('order_management')

        order_ids = [int(oid) for oid in order_ids_str.split(',') if oid.isdigit()]
        if not order_ids:
            messages.error(request, "Invalid order IDs provided.")
            return redirect('order_management')

        try:
            # Use supabase_service to bypass RLS for admin actions
            supabase_service.table('orders').delete().in_('id', order_ids).execute()
            messages.success(request, f"{len(order_ids)} order(s) have been permanently deleted.")
            log_activity(
                request.user,
                'ORDER_BATCH_DELETED',
                {'count': len(order_ids), 'order_ids': order_ids}
            )
            return JsonResponse({'success': True, 'message': f"✅ {len(order_ids)} order(s) have been permanently deleted."})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"An error occurred during batch deletion: {e}"}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

@admin_required
def batch_update_products(request):
    """
    Handles batch actions for products (e.g., mark as available, delete).
    NOW HANDLES AJAX REQUESTS for 'delete-selected'.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        product_ids_str = request.POST.get('product_ids')
        
        if not all([action, product_ids_str]):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid batch action request.'}, status=400)
            messages.error(request, "Invalid batch action request.")
            return redirect('manage_products')

        try:
            product_ids = [int(pid) for pid in product_ids_str.split(',') if pid.isdigit()]
            if not product_ids:
                raise ValueError("No valid product IDs provided.")
            count = len(product_ids)

        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': f"Invalid product IDs: {e}"}, status=400)
            messages.error(request, f"Invalid product IDs: {e}")
            return redirect('manage_products')

        try:
            if action == 'mark-available':
                # This action still uses the redirect, which is fine for now
                supabase_service.table('products').update({'is_available': True}).in_('id', product_ids).execute()
                messages.success(request, f"{count} product(s) marked as available.")
                log_activity(
                    request.user, 
                    f'PRODUCT_BATCH_{action.upper().replace("-", "_")}',
                    {'count': count, 'product_ids': product_ids}
                )
                return redirect('manage_products')

            elif action == 'delete-selected':
                # ✅ AJAX ACTION: This will now return JSON
                supabase_service.table('products').delete().in_('id', product_ids).execute()
                
                log_activity(
                    request.user, 
                    'PRODUCT_BATCH_DELETE',
                    {'count': count, 'product_ids': product_ids}
                )
                
                # ✅ Return JSON success
                return JsonResponse({
                    'success': True, 
                    'message': '🗑️ Product deleted successfully!',
                    'product_ids': product_ids # Send back the IDs
                })
                
            else:
                messages.warning(request, f"The batch action '{action}' is not supported.")

        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                 return JsonResponse({'success': False, 'error': f"An error occurred: {e}"}, status=400)
            messages.error(request, f"An error occurred during the batch {action}: {e}")
    
    # Fallback for non-POST or other issues
    return redirect('manage_products')

@admin_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        try:
            # For batch updates, the order IDs come from a hidden input and order_id is 0
            if order_id == 0:
                order_ids_str = request.POST.get('order_ids')
                order_ids = [int(oid) for oid in order_ids_str.split(',') if oid.isdigit()]
                new_status = request.POST.get('status')
                count = len(order_ids)
                success_message = f"{count} order(s) updated to '{new_status}'."

            # For single updates, the ID comes from the URL
            else:
                order_ids = [order_id]
                new_status = request.POST.get('status')
                success_message = f"Order #{order_id} updated to '{new_status}'."

            if not order_ids or not new_status:
                raise ValueError("Missing order IDs or new status.")

            # If the status is cancelled or rejected, it's good practice to call
            # the function that also handles stock restoration for reservations.
            if new_status in ['cancelled', 'rejected']:
                for oid in order_ids:
                    # Using supabase_service to ensure permissions
                    supabase_service.rpc('cancel_or_reject_order', {
                        'p_order_id': oid,
                        'p_new_status': new_status
                    }).execute()
            
            # For other status updates (like to 'completed' or 'approved'), just update the status field
            else:
                # Use supabase_service for all admin database modifications
                supabase_service.table('orders').update({'status': new_status}).in_('id', order_ids).execute()

            messages.success(request, success_message)
            log_activity(
                request.user,
                'ORDER_STATUS_BATCH_UPDATED' if order_id == 0 else 'ORDER_STATUS_UPDATED',
                {'order_ids': order_ids, 'new_status': new_status}
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
    low_stock_products = []
    unavailable_products = []
    
    try:
        report_data = supabase.rpc('get_report_stats').execute().data
        log_response = supabase.rpc('get_activity_log', {'p_search_term': search_query}).execute()
        low_stock_response = supabase.table('products').select('*').gt('stock_quantity', 0).lt('stock_quantity', 10).order('stock_quantity', desc=False).execute()
        if low_stock_response.data:
            low_stock_products = low_stock_response.data
        
        unavailable_response = supabase.table('products').select('*').eq('is_available', False).order('name').execute()
        if unavailable_response.data:
            unavailable_products = unavailable_response.data
        
        
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
        'low_stock_products': low_stock_products,
        'unavailable_products': unavailable_products,
        'search_query': search_query,
        'active_page': 'reports'
    }
    return render(request, 'dashboards/reports.html', context)


@admin_required
def admin_profile_view(request):
    user_id = request.user.id
    
    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # Handle Profile Details Update
        if form_type == 'details':
            try:
                params = {
                    'p_full_name': request.POST.get('full_name'),
                    'p_phone_number': request.POST.get('phone_number'),
                    'p_address': request.POST.get('address')
                }
                supabase.rpc('update_my_profile', params).execute()
                messages.success(request, 'Your profile has been updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {e}')
        
        # Handle Password Change
        elif form_type == 'password':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if new_password1 != new_password2:
                messages.error(request, 'Passwords do not match.')
            elif len(new_password1) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
            else:
                try:
                    supabase.auth.update_user({'password': new_password1})
                    messages.success(request, 'Your password has been changed successfully!')
                except Exception as e:
                    messages.error(request, f'Error changing password: {e}')
        
        return redirect('admin_profile')

    # Handle GET request to display the page
    profile_data = {}
    try:
        response = supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
        profile_data = response.data
    except Exception as e:
        messages.error(request, f'Could not load your profile: {e}')
        
    context = {
        'profile': profile_data,
        'active_page': 'profile',
        'page_title': 'Admin Profile'
    }
    return render(request, 'dashboards/admin_profile.html', context)


