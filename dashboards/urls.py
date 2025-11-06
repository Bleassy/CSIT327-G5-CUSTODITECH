from django.urls import path
from . import views

urlpatterns = [
    # --- Student URLs ---
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/browse/', views.browse_products_view, name='browse_products'),
    path('student/my-reservations/', views.my_reservations_view, name='my_reservations'),
    path('student/my-orders/', views.my_orders_view, name='my_orders'),
    path('student/create-order/', views.create_order_view, name='create_order'),
    path('student/create-reservation/', views.create_reservation_view, name='create_reservation'),
    path('student/checkout-reservation/', views.checkout_reservation_view, name='checkout_reservation'),
    path('student/profile/', views.student_profile_view, name='student_profile'), 
    path('student/cancel-reservation/<int:reservation_id>/', views.cancel_reservation_view, name='cancel_reservation'),
    path('student/batch-delete-orders/', views.batch_delete_orders_view, name='batch_delete_orders'),
    path('student/delete-order/<int:order_id>/', views.delete_single_order_view, name='delete_single_order'),
    path('student/cancel-order/<int:order_id>/', views.cancel_order_view, name='cancel_order'),
    path('dashboard/student/notifications/mark-read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),
    path('dashboard/student/notifications/read/<int:notification_id>/', views.mark_notification_read_and_redirect, name='mark_notification_read_and_redirect'),
    path('dashboard/student/notifications/', views.all_notifications_view, name='all_notifications'),
    path('dashboard/student/notifications/batch-update/', views.batch_update_notifications, name='batch_update_notifications'),
    path('dashboard/student/notifications/batch-delete/', views.batch_delete_notifications, name='batch_delete_notifications'),
    path('notifications/mark-all-read/', views.mark_all_as_read_view, name='mark_all_as_read'),



    # --- Admin URLs ---
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('admin/manage-products/', views.manage_products_view, name='manage_products'),
    path('admin/batch-update-products/', views.batch_update_products, name='batch_update_products'),
    path('admin/profile/', views.admin_profile_view, name='admin_profile'), 
    path('admin/add_product/', views.add_product, name='add_product'),
    path('admin/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('admin/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('admin/order-management/', views.order_management_view, name='order_management'),
    path('admin/update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin/delete-order/<int:order_id>/', views.delete_order_view, name='delete_order'),
    path('admin/reports/', views.reports_view, name='reports'),
    path('dashboard/admin/batch-delete-logs/', views.batch_delete_logs_view, name='batch_delete_logs'),
    path('admin/batch-delete-orders/', views.admin_batch_delete_orders_view, name='admin_batch_delete_orders'),
    path('admin/manage-students/', views.manage_students_view, name='manage_students'),
    path('admin/block-student/<uuid:user_id>/', views.admin_block_student_view, name='admin_block_student'),
    path('admin/delete-student/<uuid:user_id>/', views.admin_delete_student_view, name='admin_delete_student'),
    path('admin/reports/clear-all-logs/', views.clear_all_logs_view, name='clear_all_logs'),
]

