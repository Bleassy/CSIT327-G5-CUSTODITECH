from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
from django.http import JsonResponse 
from django.contrib import messages
from supabase_client import supabase, supabase_service
import pytz
from datetime import datetime
import uuid
from collections import defaultdict
import math
import requests
from .utils import log_activity
from supabase_client import supabase_service
from .decorators import admin_required
from django.views.decorators.http import require_POST

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
            'user_id': str(user.id),
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
    # ✅ CORRECTED INDENTATION FOR THIS ENTIRE BLOCK
    raw_name = getattr(request.user, 'get_full_name', lambda: 'Wildcat')()
    display_name = "Wildcat" # Default name

    if isinstance(raw_name, str) and raw_name: # Check if it's a non-empty string
        if ' ' in raw_name:
            # Case 1: It's a full name like "Jairus Dave"
            display_name = raw_name.split(' ')[0]
        elif '@' in raw_name:
            # Case 2: It's an email like "jairus.dave@cit.edu"
            name_part = raw_name.split('@')[0] # Gets "jairus.dave"
            if '.' in name_part:
                display_name = name_part.split('.')[0] # Gets "jairus"
            else:
                display_name = name_part # Gets "jairus" from "jairus@cit.edu"
        else:
            # Case 3: It's just a username like "jairus.dave"
            if '.' in raw_name:
                display_name = raw_name.split('.')[0] # Gets "jairus"
            else:
                display_name = raw_name # Use the name as-is

    # Finally, capitalize the result
    display_name = display_name.capitalize()
    
    # ✅ This is line 105 (in your file) - it is now correctly indented
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
        # if search_query:
            # query = query.ilike('name', f'%{search_query}%')
        
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

            return JsonResponse({'success': True, 'message': f"{len(order_ids)} order(s) have been deleted."})

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
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # --- Get product_id early ---
            product_id = int(request.POST.get('product_id'))
            quantity_reserved = int(request.POST.get('quantity')) # Needed if reservation affects stock

            params = {
                'p_product_id': product_id,
                'p_user_id': request.user.id,
                'p_quantity': quantity_reserved,
                'p_deal_method': request.POST.get('deal_method', 'meet-up'),
                'p_is_urgent': 'is_urgent' in request.POST
            }

            # --- Execute the RPC ---
            response = supabase.rpc('create_reservation', params).execute()

            # --- Check for errors ---
            if hasattr(response, 'error') and response.error:
                 raise Exception(str(response.error))
            if isinstance(response.data, list) and len(response.data) > 0 and 'error' in response.data[0]:
                 raise Exception(response.data[0]['error'])

            # --- ✅ Get New Stock Quantity (Important if reservation DECREASES stock) ---
            # If your 'create_reservation' RPC DOES NOT change stock_quantity,
            # you might fetch the *current* stock instead of assuming it changed.
            new_stock_quantity = None
            # OPTION A: If RPC returns new stock (less likely for reservation)
            if isinstance(response.data, list) and len(response.data) > 0 and 'new_stock_quantity' in response.data[0]:
                 new_stock_quantity = response.data[0]['new_stock_quantity']

            # OPTION B: Fetch current stock after RPC succeeds
            if new_stock_quantity is None:
                 print(f"--- Fetching stock after reservation for product {product_id} ---") # Debug
                 stock_response = supabase.table('products').select('stock_quantity').eq('id', product_id).single().execute()
                 if stock_response.data:
                      new_stock_quantity = stock_response.data.get('stock_quantity')
                      print(f"--- Fetched stock: {new_stock_quantity} ---") # Debug
                 else:
                      print(f"--- Failed to fetch stock for product {product_id} ---") # Debug

            # Handle case where stock couldn't be determined
            if new_stock_quantity is None:
                 print(f"--- WARNING: Could not determine stock for product {product_id} after reservation ---") # Debug
                 # Decide what to send back - current stock might be 0 if backordering
                 # Let's send 0 as a safe default if fetch failed after a supposed success
                 new_stock_quantity = 0

            # Determine appropriate success message
            success_message = '✅ Your reservation has been placed successfully!'
            # Add logic here if backorder message should be different based on RPC response

            # --- Return Success JSON ---
            return JsonResponse({
                'success': True,
                'message': success_message,
                # ✅ ADD these fields
                'product_id': product_id,
                'new_stock_quantity': new_stock_quantity
            })

        except Exception as e:
            error_str = str(e)
            # Handle potential success message disguised as error
            if "'success': True" in error_str or "'message': 'Item reserved successfully!'" in error_str:
                 print("--- WARNING: Caught potential success message in reservation error block ---") # Debug
                 _product_id = int(request.POST.get('product_id', 0))
                 _new_stock = 0 # Default if we hit this edge case
                 try: # Attempt to fetch current stock as fallback
                      stock_response = supabase.table('products').select('stock_quantity').eq('id', _product_id).single().execute()
                      if stock_response.data: _new_stock = stock_response.data.get('stock_quantity', 0)
                 except: pass
                 return JsonResponse({
                     'success': True,
                     'message': '✅ Your reservation has been placed successfully! (Stock may be outdated)',
                     'product_id': _product_id,
                     'new_stock_quantity': _new_stock
                 })
            else:
                # Genuine error
                print(f"--- ERROR in create_reservation_view: {e} ---") # Log real errors
                return JsonResponse({'success': False, 'error': f"Could not reserve item: {e}"}, status=400)

    # Not AJAX POST
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

@student_required
def create_order_view(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # --- Get product_id and quantity early ---
            product_id = int(request.POST.get('product_id'))
            quantity_ordered = int(request.POST.get('quantity'))
            
            params = {
                'p_product_id': product_id,
                'p_user_id': request.user.id,
                'p_quantity': quantity_ordered,
                'p_deal_method': request.POST.get('deal_method'),
                'p_payment_method': request.POST.get('payment_method'),
                'p_payment_transaction_id': request.POST.get('payment_transaction_id', None)
            }

            # --- Execute the RPC ---
            response = supabase.rpc('buy_product', params).execute()

            # --- Check for errors ---
            if hasattr(response, 'error') and response.error:
                raise Exception(str(response.error))
            if isinstance(response.data, list) and len(response.data) > 0 and 'error' in response.data[0]:
                 raise Exception(response.data[0]['error'])

            # --- ✅ Get New Stock Quantity ---
            new_stock_quantity = None
            # OPTION A: If your 'buy_product' RPC returns the new stock directly (Ideal)
            # Example: Assuming RPC returns [{'new_stock_quantity': 5}]
            if isinstance(response.data, list) and len(response.data) > 0 and 'new_stock_quantity' in response.data[0]:
                 new_stock_quantity = response.data[0]['new_stock_quantity']

            # OPTION B: If RPC doesn't return stock, fetch it manually afterwards
            if new_stock_quantity is None:
                 print(f"--- Fetching stock manually for product {product_id} ---") # Debug log
                 stock_response = supabase.table('products').select('stock_quantity').eq('id', product_id).single().execute()
                 if stock_response.data:
                      new_stock_quantity = stock_response.data.get('stock_quantity')
                      print(f"--- Fetched new stock: {new_stock_quantity} ---") # Debug log
                 else:
                      print(f"--- Failed to fetch stock for product {product_id} ---") # Debug log


            # Handle case where stock couldn't be determined
            if new_stock_quantity is None:
                 print(f"--- WARNING: Could not determine new stock for product {product_id} ---") # Debug log
                 new_stock_quantity = 0 # Default to 0 if fetch failed

            # --- Return Success JSON with new data ---
            return JsonResponse({
                'success': True,
                'message': '🎉 Your order has been placed successfully!',
                # ✅ ADD these fields to the response
                'product_id': product_id,
                'new_stock_quantity': new_stock_quantity
            })

        except Exception as e:
            error_str = str(e)
            # Handle potential success message disguised as error
            # This part needs careful testing; ideally the RPC shouldn't error on success
            if "'success': True" in error_str:
                 print("--- WARNING: Caught potential success message in error block ---") # Debug log
                 # Try to get stock, but default to 0 as it's an edge case
                 _product_id = int(request.POST.get('product_id', 0)) # Get ID safely
                 _new_stock = 0
                 try:
                      stock_response = supabase.table('products').select('stock_quantity').eq('id', _product_id).single().execute()
                      if stock_response.data: _new_stock = stock_response.data.get('stock_quantity', 0)
                 except: pass # Ignore errors during this fallback
                 return JsonResponse({
                     'success': True,
                     'message': '🎉 Your order has been placed successfully! (Stock may be outdated)',
                     'product_id': _product_id,
                     'new_stock_quantity': _new_stock
                 })
            else:
                # Genuine error
                print(f"--- ERROR in create_order_view: {e} ---") # Log real errors
                return JsonResponse({'success': False, 'error': f"Could not place order: {e}"}, status=400)

    # Not an AJAX POST request
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
    
    # --- Handle AJAX POST request ---
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form_type = request.POST.get('form_type')

        # --- Handle Profile Details Update ---
        if form_type == 'details':
            # ✅ FIX: Indented this entire 'try...except' block
            try:
                # NEW: Handle file upload
                avatar_url = None
                avatar_file = request.FILES.get('avatar_image')

                if avatar_file:
                    # Create a unique file name
                    file_ext = avatar_file.name.split('.')[-1]
                    file_name = f'user_{user_id}_{uuid.uuid4()}.{file_ext}'

                    # Upload to Supabase Storage
                    supabase_service.storage.from_('avatars').upload(
                        file=avatar_file.read(),
                        path=file_name,
                        file_options={"content-type": avatar_file.content_type}
                    )

                    # Get the public URL
                    avatar_url = supabase_service.storage.from_('avatars').get_public_url(file_name)

                # Prepare parameters for the RPC function
                params = {
                    'p_full_name': request.POST.get('full_name'),
                    'p_phone_number': request.POST.get('phone_number'),
                    'p_address': request.POST.get('address')
                }

                # NEW: Add avatar_url to params ONLY if a new one was uploaded
                if avatar_url:
                    params['p_avatar_url'] = avatar_url

                # Call the RPC function
                supabase.rpc('update_my_profile', params).execute()

                # NEW: Send back the new avatar_url in the success message
                response_data = {
                    'success': True, 
                    'message': '✅ Your profile has been updated successfully!'
                }
                if avatar_url:
                    response_data['avatar_url'] = avatar_url

                return JsonResponse(response_data)

            except Exception as e:
                # (Error handling is the same)
                return JsonResponse({'success': False, 'error': f'Error updating profile: {e}'}, status=400)

        # --- Handle Password Change ---
        elif form_type == 'password':
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            # --- Frontend validation is repeated on backend for security ---
            if new_password1 != new_password2:
                return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)
            if len(new_password1) < 8: # Check for 8 characters, not 6
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long.'}, status=400)

            # ✅ 1. CHECK IF NEW PASSWORD IS SAME AS OLD
            if current_password == new_password1:
                return JsonResponse({'success': False, 'error': 'New password cannot be the same as the current password.'}, status=400)

            try:
                # ✅ 2. VALIDATE CURRENT PASSWORD
                # We do this by trying to sign in with it.
                user_email = request.user.email
                auth_response = supabase.auth.sign_in_with_password({
                    "email": user_email,
                    "password": current_password
                })

                # If we get here without error, the password was correct.
                # ✅ 3. UPDATE TO NEW PASSWORD
                supabase.auth.update_user({'password': new_password1})

                return JsonResponse({'success': True, 'message': '🔑 Your password has been changed successfully!'})

            except requests.exceptions.HTTPError as e:
                # ✅ 4. CATCH AUTHENTICATION ERROR
                if "Invalid login credentials" in str(e):
                    return JsonResponse({'success': False, 'error': 'Your current password was incorrect.'}, status=400)
                else:
                    return JsonResponse({'success': False, 'error': f'An error occurred: {e}'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error changing password: {e}'}, status=400)

        # Fallback for unknown form type
        return JsonResponse({'success': False, 'error': 'Invalid form submission.'}, status=400)

    # --- Handle GET request to display the page (this part is unchanged) ---
    profile_data = {}
    try:
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

@student_required
def cancel_order_view(request, order_id):
    """ Handles cancellation of an approved order by the student who owns it. """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            user_id = request.user.id
            # Ensure the order is approved, belongs to the user
            response = supabase.table('orders').select('id').eq('id', order_id).eq('user_id', user_id).eq('status', 'approved').single().execute()
            if not response.data:
                raise Exception("Order not found or cannot be cancelled.")
            # Call RPC to cancel and restore stock
            supabase.rpc('cancel_or_reject_order', {'p_order_id': order_id, 'p_new_status': 'cancelled'}).execute()
            return JsonResponse({'success': True, 'message': "🗑️ Your order has been successfully cancelled.", 'order_id': order_id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Could not cancel the order: {e}"}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    

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
    page_number = request.GET.get('page', 1) # Get page number, default to 1
    items_per_page = 15

    products = []
    total_products_count = 0
    pagination_context = {}
    
    try:
        query = supabase.table('products').select('*').order('created_at', desc=True)
        #if search_query:
            #query = query.or_(f'name.ilike.%{search_query}%,category.ilike.%{search_query}%')
        response = query.execute()
        products = response.data if response.data else []

        products = sorted(
            products, 
            key=lambda p: (
                p.get('is_available', True), # Sorts False (Unavailable) before True (Available)
                not (0 < p.get('stock_quantity', 0) < 10) # Sorts True (Low Stock) before False
            )
        )

        categories = sorted(list(set(p.get('category') for p in products if p.get('category'))))

    except Exception as e:
        messages.error(request, f"Error fetching products: {e}")
        products = []
    context = {
        'products': products, 
        'categories': categories,
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
                'is_available': stock > 0
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
                'is_available': stock > 0
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
                'message': 'Product deleted successfully!', 
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
    all_orders_empty = True
    
    try:
        params = {'p_search_term': search_query}
        response = supabase.rpc('get_all_orders_with_details', params).execute()
        
        if response.data:
            all_orders_empty = False
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
        all_orders_empty = True

    context = {
        'pending_orders': pending_orders, # ✅ ADDED: Pass the new list to the template
        'approved_orders': approved_orders,
        'completed_orders': completed_orders,
        'other_orders': other_orders,
        'search_query': search_query,
        'active_page': 'order_management',
        'page_title': 'Order Management',
        'all_orders_empty': all_orders_empty
    }
    return render(request, 'dashboards/order_management.html', context)

# [views.py]

@admin_required
def admin_batch_delete_orders_view(request):
    """ Handles batch deletion of orders by an admin. """
    if request.method == 'POST':
        order_ids_str = request.POST.get('order_ids')
        
        if not order_ids_str:
            # ✅ CHANGED: Return JSON error instead of redirect
            return JsonResponse({'success': False, 'error': "No orders selected for deletion."}, status=400)

        order_ids = [int(oid) for oid in order_ids_str.split(',') if oid.isdigit()]
        
        if not order_ids:
            # ✅ CHANGED: Return JSON error instead of redirect
            return JsonResponse({'success': False, 'error': "Invalid order IDs provided."}, status=400)

        try:
            # This part is correct
            supabase_service.table('orders').delete().in_('id', order_ids).execute()
            log_activity(
                request.user,
                'ORDER_BATCH_DELETED',
                {'count': len(order_ids), 'order_ids': order_ids}
            )
            
            # ✅ THE FIX: Add 'order_ids': order_ids to the response
            return JsonResponse({
                'success': True, 
                'message': f"🗑️ {len(order_ids)} has been permanently deleted.",
                'order_ids': order_ids  # This is the line your JavaScript needs
            })
            
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
                    'message': 'Product deleted successfully!',
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

# [views.py]

@admin_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        try:
            order_ids = []
            new_status = request.POST.get('status')

            if order_id == 0:
                order_ids_str = request.POST.get('order_ids')
                if not order_ids_str:
                    raise ValueError("No order IDs provided for batch update.")
                order_ids = [int(oid) for oid in order_ids_str.split(',') if oid.isdigit()]
            else:
                order_ids = [order_id]

            if not order_ids or not new_status:
                raise ValueError("Missing order IDs or new status.")

            # --- Start of the fix ---

            # 1. Run the correct update logic (RPC or simple update)
            if new_status in ['cancelled', 'rejected']:
                for oid in order_ids:
                    # Run the RPC, but we don't need its return value
                    supabase_service.rpc('cancel_or_reject_order', {
                        'p_order_id': oid,
                        'p_new_status': new_status
                    }).execute()
            else:
                # Run the simple status update
                supabase_service.table('orders').update({
                    'status': new_status
                }).in_('id', order_ids).execute()

            # 2. ✅ THE FIX: After updating, ALWAYS re-fetch the orders
            # to get their fresh, updated data.
            updated_orders_response = supabase_service.table('orders') \
                                            .select('*') \
                                            .in_('id', order_ids) \
                                            .execute()
            
            updated_orders_data = updated_orders_response.data if updated_orders_response.data else []
            
            # --- End of the fix ---

            # Log the activity
            log_activity(
                request.user,
                'ORDER_STATUS_BATCH_UPDATED' if order_id == 0 else 'ORDER_STATUS_UPDATED',
                {'order_ids': order_ids, 'new_status': new_status}
            )

            # 3. Return the fresh data
            return JsonResponse({
                'success': True,
                'message': f"{len(updated_orders_data)} order(s) updated to '{new_status}'.",
                'orders': updated_orders_data # This list will now be correct for all statuses
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Failed to update order status: {e}"}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@admin_required
def delete_order_view(request, order_id):
    if request.method == 'POST':
        try:
            # You can use the RPC or a direct delete with service_role
            # Using the RPC is safer if it has other logic (like stock restore)
            # supabase.rpc('delete_order_by_admin', {'p_order_id': order_id}).execute()
            
            # Using direct service_role delete (as seen in your other view)
            supabase_service.table('orders').delete().eq('id', order_id).execute()
            
            log_activity(request.user, 'ORDER_DELETED', {'order_id': order_id})
            
            # ✅ CHANGED: Return JSON instead of redirecting
            return JsonResponse({
                'success': True, 
                'message': f'🗑️ Order #{order_id} has been permanently deleted.',
                'order_id': order_id
            })
            
        except Exception as e:
            # ✅ CHANGED: Return JSON error
            return JsonResponse({'success': False, 'error': f"Failed to delete order: {e}"}, status=400)
            
    # ✅ CHANGED: Handle non-POST requests
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@admin_required
def reports_view(request):
    search_query = request.GET.get('search', '').strip()
    log_page_number = request.GET.get('log_page', 1) # Use 'log_page' to avoid conflict if other paginations exist
    logs_per_page = 10
    report_data = {}
    kpi_data = {}
    inventory_overview = {} # <-- New dict for inventory details
    reservation_stats = {}  # <-- New dict for reservation details
    sales_performance = {}  # <-- New dict for sales details
    log_entries = []
    low_stock_products = []
    unavailable_products = []
    status_counts_dict = {
        'pending': 0, 'approved': 0, 'completed': 0, 'rejected': 0, 'cancelled': 0
    }

    log_pagination_context = {} # Context specifically for log pagination
    total_log_count = 0

    try:
        # ✅ Call the NEW RPC function using service role
        report_data_response = supabase_service.rpc('get_advanced_report_stats').execute()
        print("--- DEBUG: Raw Advanced RPC Response Data:", report_data_response.data) # Keep for checking

        if report_data_response.data:
            # The RPC returns a single JSON object
            report_data = report_data_response.data

            # Extract status counts
            retrieved_status_counts = report_data.get('status_counts', {})
            status_counts_dict.update(retrieved_status_counts)

            # Extract KPIs
            kpi_data = report_data.get('kpi', {})

            # ✅ Extract NEW overview data (use .get() with default empty dicts)
            inventory_overview = report_data.get('inventory_overview', {})
            reservation_stats = report_data.get('reservation_stats', {})
            sales_performance = report_data.get('sales_performance', {})

        else:
            # Set defaults if RPC fails or returns no data
            report_data = {'total_products': 0, 'total_orders_reservations': 0}
            kpi_data = {'total_sales': 0, 'inventory_value': 0, 'orders_today': 0, 'pending_reservations': 0}
            # Keep overview dicts empty


        # --- Fetch Logs (Stock/Unavailable are now less critical as RPC provides totals) ---
        # You might still want these lists for the specific tables, so keep fetching them
        log_response = supabase_service.rpc('get_activity_log', {'p_search_term': search_query}).execute()
        low_stock_response = supabase_service.table('products').select('*').gt('stock_quantity', 0).lt('stock_quantity', 10).order('stock_quantity', desc=False).execute()
        if low_stock_response.data:
            low_stock_products = low_stock_response.data

        unavailable_response = supabase_service.table('products').select('*').eq('is_available', False).order('name').execute()
        if unavailable_response.data:
            unavailable_products = unavailable_response.data

        # --- Fetch Paginated Log Data (Corrected) ---
        try:
            log_page_number = int(log_page_number)
        except ValueError:
            log_page_number = 1

        log_start_index = (log_page_number - 1) * logs_per_page
        log_end_index = log_start_index + logs_per_page - 1

        # 1. Get the total count separately from the TABLE
        count_response = supabase_service.table('activity_log').select(
            '*', # Select something simple
            count='exact' # Get the count
        ).execute() # We don't actually need the data here, just the count

        total_log_count = count_response.count if count_response.count is not None else 0

        # 2. Fetch the paginated data using the RPC (WITHOUT count)
        log_query = supabase_service.rpc(
            'get_activity_log',
            {'p_search_term': ''} # Keep search term empty for client-side filtering
        ).order('created_at', desc=True).range(log_start_index, log_end_index) # Apply order and range

        log_response = log_query.execute()
        # --- End Correction ---

        # Process the fetched log entries (this part remains the same)
        if log_response.data:
            for entry in log_response.data:
                # ... (datetime conversion and action_display logic) ...
                if entry.get('created_at'):
                     entry['created_at'] = datetime.fromisoformat(entry['created_at'])
                if entry.get('action'):
                     entry['action_display'] = entry['action'].replace('_', ' ').title()
                log_entries.append(entry)

        # Calculate Log Pagination Details (this part remains the same)
        total_log_pages = math.ceil(total_log_count / logs_per_page)
        # ... (rest of log_pagination_context calculation) ...
        log_pagination_context = {
            'current_page': log_page_number,
            'total_pages': total_log_pages,
            'has_previous': log_page_number > 1,
            'has_next': log_page_number < total_log_pages,
            'previous_page_number': log_page_number - 1 if log_page_number > 1 else 1,
            'next_page_number': log_page_number + 1 if log_page_number < total_log_pages else total_log_pages,
            'page_range': range(max(1, log_page_number - 2), min(total_log_pages, log_page_number + 2) + 1),
            'param_name': 'log_page'
        }

    except Exception as e:
        messages.error(request, f"Error fetching report data: {e}")
        # Ensure defaults are set on error
        report_data = {'total_products': 0, 'total_orders_reservations': 0}
        kpi_data = {'total_sales': 0, 'inventory_value': 0, 'orders_today': 0, 'pending_reservations': 0}
        # Keep overview dicts empty on error
        log_entries = []
        total_log_count = 0

    print("--- DEBUG: Final status_counts_dict:", status_counts_dict)
    print("--- DEBUG: Final kpi_data:", kpi_data)
    # ✅ Add debug prints for new data
    print("--- DEBUG: Final inventory_overview:", inventory_overview)
    print("--- DEBUG: Final reservation_stats:", reservation_stats)
    print("--- DEBUG: Final sales_performance:", sales_performance)

    context = {
        'total_products': report_data.get('total_products', 0),
        'total_orders_reservations': report_data.get('total_orders_reservations', 0),
        'status_counts': status_counts_dict,
        'kpi': kpi_data,

        # ✅ Pass NEW overview data to the template
        'inventory_overview': inventory_overview,
        'reservation_stats': reservation_stats,
        'sales_performance': sales_performance,

        'log_entries': log_entries,
        'low_stock_products': low_stock_products,
        'unavailable_products': unavailable_products,
        'search_query': search_query,
        'log_pagination': log_pagination_context,
        'active_page': 'reports'
    }
    return render(request, 'dashboards/reports.html', context)

@admin_required
def batch_delete_logs_view(request):
    """
    Handles AJAX batch deletion of activity log entries.
    """
    if request.method == 'POST':
        log_ids_str = request.POST.get('log_ids')
        if not log_ids_str:
            return JsonResponse({'success': False, 'error': 'No log IDs provided.'}, status=400)
            
        try:
            log_ids = [int(lid) for lid in log_ids_str.split(',') if lid.isdigit()]
            if not log_ids:
                raise ValueError("No valid log IDs provided.")
            
            # Use service role to delete from the log table
            supabase_service.table('activity_log').delete().in_('id', log_ids).execute()
            
            # Return the IDs of the deleted logs
            return JsonResponse({
                'success': True,
                'message': f'{len(log_ids)} log entries have been deleted.',
                'deleted_ids': log_ids
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An error occurred: {e}'}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


@admin_required
def admin_profile_view(request):
    user_id = request.user.id

    # --- Handle AJAX POST request ---
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form_type = request.POST.get('form_type')

        # --- Handle Profile Details Update ---
        if form_type == 'details':
            try:
                # ✅ NEW: Handle file upload
                avatar_url = None
                avatar_file = request.FILES.get('avatar_image')

                if avatar_file:
                    # Create a unique file name
                    file_ext = avatar_file.name.split('.')[-1]
                    file_name = f'user_{user_id}_{uuid.uuid4()}.{file_ext}'

                    # Upload to Supabase Storage (using service client for admin)
                    supabase_service.storage.from_('avatars').upload(
                        file=avatar_file.read(),
                        path=file_name,
                        file_options={"content-type": avatar_file.content_type}
                    )

                    # Get the public URL
                    avatar_url = supabase_service.storage.from_('avatars').get_public_url(file_name)

                # Prepare parameters for the RPC function
                params = {
                    'p_full_name': request.POST.get('full_name'),
                    'p_phone_number': request.POST.get('phone_number'),
                    'p_address': request.POST.get('address')
                }

                # ✅ NEW: Add avatar_url to params ONLY if a new one was uploaded
                if avatar_url:
                    params['p_avatar_url'] = avatar_url

                # Call the RPC function (using user's auth)
                supabase.rpc('update_my_profile', params).execute()

                # ✅ NEW: Send back the new avatar_url in the success message
                response_data = {
                    'success': True, 
                    'message': '✅ Your profile has been updated successfully!'
                }
                if avatar_url:
                    response_data['avatar_url'] = avatar_url

                return JsonResponse(response_data)

            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error updating profile: {e}'}, status=400)

        # Handle Password Change
        elif form_type == 'password':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if new_password1 != new_password2:
                # ✅ Return JSON
                return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)
            elif len(new_password1) < 6:
                # ✅ Return JSON
                return JsonResponse({'success': False, 'error': 'Password must be at least 6 characters long.'}, status=400)
            else:
                try:
                    supabase.auth.update_user({'password': new_password1})
                    # ✅ Return JSON
                    return JsonResponse({'success': True, 'message': '🔑 Your password has been changed successfully!'})
                except Exception as e:
                    # ✅ Return JSON
                    return JsonResponse({'success': False, 'error': f'Error changing password: {e}'}, status=400)

        # Fallback for unknown form type
        return JsonResponse({'success': False, 'error': 'Invalid form submission.'}, status=400)

    # --- Handle GET request to display the page (this part is unchanged) ---
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


@admin_required
def manage_students_view(request):
    search_query = request.GET.get('search', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        current_page = int(request.GET.get('page', 1))
    except ValueError:
        current_page = 1
    
    page_size = 10 # Set how many students per page
    
    stats = {}
    students = []
    total_count = 0
    total_pages = 1
    
    try:
        # 1. Get the stat card data (only on the initial page load)
        if not is_ajax:
            stats_response = supabase_service.rpc('get_student_stats').execute()
            if stats_response.data:
                stats = stats_response.data[0]
            else:
                stats = {'total_students': 0, 'blocked_students': 0}

        # 2. Get student list
        params = {
            'p_search_term': search_query,
            'p_page_size': page_size,
            'p_page_number': current_page
        }
        students_response = supabase_service.rpc('get_paginated_student_profiles', params).execute()
        
        if students_response.data:
            students = students_response.data
            total_count = students[0].get('total_count', 0)
            total_pages = math.ceil(total_count / page_size)

            if not is_ajax:
                for student in students:
                    if student.get('created_at'):
                        student['created_at'] = datetime.fromisoformat(student['created_at'])
        
        if is_ajax:
            # If this is a background search, send all data as JSON
            return JsonResponse({
                'students': students,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': current_page,
                'page_range': list(range(1, total_pages + 1)) # Convert range to a list for JSON
            })

    except Exception as e:
        if is_ajax:
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, f"Error fetching student data: {e}")
        print(f"--- Manage Students Error: {e} ---")
        
    # This is for the normal, full-page load
    context = {
        'stats': stats,
        'students': students,
        'search_query': search_query,
        'total_count': total_count,
        'total_pages': total_pages,
        'current_page': current_page,
        'page_range': range(1, total_pages + 1),
        'active_page': 'manage_students',
        'page_title': 'Manage Student Accounts'
    }
    return render(request, 'dashboards/manage_students.html', context)


@admin_required
def admin_block_student_view(request, user_id):
    """
    Handles blocking or unblocking a student.
    This view expects an AJAX request.
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # The 'is_blocked' value from the form will be a string 'true' or 'false'
            is_blocked_str = request.POST.get('is_blocked', 'false')
            is_blocked = True if is_blocked_str == 'true' else False

            params = {
                'p_user_id': str(user_id),
                'p_is_blocked': is_blocked
            }
            supabase_service.rpc('admin_update_user_status', params).execute()

            action_text = "blocked" if is_blocked else "unblocked"
            log_activity(
                request.user, 
                'STUDENT_STATUS_UPDATED',
                {'student_user_id': str(user_id), 'action': action_text}
            )
            return JsonResponse({'success': True, 'message': f'✅ Student has been {action_text}.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@require_POST
@admin_required
def admin_delete_student_view(request, user_id):
    """
    Handles the permanent deletion of a student account.
    This view expects an AJAX request.
    """
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=400)

    try:
        # This will now work!
        params = {'p_user_id': str(user_id)}
        supabase_service.rpc('admin_delete_student', params).execute()

        # Log this admin action
        log_activity(
            request.user, 
            'STUDENT_DELETED',
            {'student_user_id': str(user_id)}
        )
        
        # Send a success response
        return JsonResponse({
            'success': True, 
            'message': '🗑️ Student account has been permanently deleted.',
            'user_id': str(user_id) # Send back the ID for the JS
        })

    except Exception as e:
        # Handle any errors
        print(f"--- Admin Delete Student Error: {e} ---")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)