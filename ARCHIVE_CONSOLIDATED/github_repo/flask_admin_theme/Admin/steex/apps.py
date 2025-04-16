from flask import Blueprint,render_template
from flask_login import login_required


apps = Blueprint('apps',__name__,template_folder='templates',
    static_folder='static',)
    

@apps.route('/apps/calender')
@login_required
def calender():
    return render_template('apps/apps-calendar.html')

@apps.route('/apps/chat')
@login_required
def chat():
    return render_template('apps/apps-chat.html')

@apps.route('/apps/email')
@login_required
def email():
    return render_template('apps/apps-email.html')

# ecommerce

@apps.route('/apps/ecommerce/product')
@login_required
def ecommerce_product():
    return render_template('apps/ecommerce/apps-ecommerce-products.html')

@apps.route('/apps/ecommerce/product_grid')
@login_required
def ecommerce_product_grid():
    return render_template('apps/ecommerce/apps-ecommerce-products-grid.html')

@apps.route('/apps/ecommerce/product_details')
@login_required
def ecommerce_product_details():
    return render_template('apps/ecommerce/apps-ecommerce-product-details.html')

@apps.route('/apps/ecommerce/add_product')
@login_required
def ecommerce_add_product():
    return render_template('apps/ecommerce/apps-ecommerce-add-product.html')

@apps.route('/apps/ecommerce/orders')
@login_required
def ecommerce_orders():
    return render_template('apps/ecommerce/apps-ecommerce-orders.html')

@apps.route('/apps/ecommerce/order_overview')
@login_required
def ecommerce_order_overview():
    return render_template('apps/ecommerce/apps-ecommerce-order-overview.html')

@apps.route('/apps/ecommerce/customers')
@login_required
def ecommerce_customers():
    return render_template('apps/ecommerce/apps-ecommerce-customers.html')

@apps.route('/apps/ecommerce/cart')
@login_required
def ecommerce_cart():
    return render_template('apps/ecommerce/apps-ecommerce-cart.html')

@apps.route('/apps/ecommerce/checkout')
@login_required
def ecommerce_checkout():
    return render_template('apps/ecommerce/apps-ecommerce-checkout.html')

@apps.route('/apps/ecommerce/sellers')
@login_required
def ecommerce_sellers():
    return render_template('apps/ecommerce/apps-ecommerce-sellers.html')

@apps.route('/apps/ecommerce/seller_overview')
@login_required
def ecommerce_seller_overview():
    return render_template('apps/ecommerce/apps-ecommerce-seller-overview.html')

# file manager

@apps.route('/apps/file_manager')
@login_required
def file_manager():
    return render_template('apps/apps-file-manager.html')


# ========== start learning =============


# courses
@apps.route('/apps/learning/courses/list')
@login_required
def courses_list():
    return render_template('apps/learning/courses/apps-learning-list.html')

@apps.route('/apps/learning/courses/grid')
@login_required
def courses_grid():
    return render_template('apps/learning/courses/apps-learning-grid.html')

@apps.route('/apps/learning/courses/category')
@login_required
def courses_category():
    return render_template('apps/learning/courses/apps-learning-category.html')

@apps.route('/apps/learning/courses/overview')
@login_required
def courses_overview():
    return render_template('apps/learning/courses/apps-learning-overview.html')

@apps.route('/apps/learning/courses/create')
@login_required
def courses_create():
    return render_template('apps/learning/courses/apps-learning-create.html')

# students

@apps.route('/apps/learning/students/courses')
@login_required
def students_courses():
    return render_template('apps/learning/students/apps-student-courses.html')

@apps.route('/apps/learning/students/subscriptions')
@login_required
def students_subscriptions():
    return render_template('apps/learning/students/apps-student-subscriptions.html')

# instructors

@apps.route('/apps/learning/instructors/list')
@login_required
def instructors_list():
    return render_template('apps/learning/instructors/apps-instructors-list.html')

@apps.route('/apps/learning/instructors/grid')
@login_required
def instructors_grid():
    return render_template('apps/learning/instructors/apps-instructors-grid.html')

@apps.route('/apps/learning/instructors/overview')
@login_required
def instructors_overview():
    return render_template('apps/learning/instructors/apps-instructors-overview.html')

@apps.route('/apps/learning/instructors/create')
@login_required
def instructors_create():
    return render_template('apps/learning/instructors/apps-instructors-create.html')

# ========== end learning =============


# invoices

@apps.route('/apps/invoices/list')
@login_required
def invoices_list():
    return render_template('apps/invoices/apps-invoices-list.html')

@apps.route('/apps/invoices/overview')
@login_required
def invoices_overview():
    return render_template('apps/invoices/apps-invoices-overview.html')

@apps.route('/apps/invoices/create_invoice')
@login_required
def invoices_create():
    return render_template('apps/invoices/apps-invoices-create.html')

# support-tickets
@apps.route('/apps/support-tickets/list')
@login_required
def tickets_list():
    return render_template('apps/support-tickets/apps-tickets-list.html')

@apps.route('/apps/support-tickets/overview')
@login_required
def tickets_overview():
    return render_template('apps/support-tickets/apps-tickets-overview.html')

# real-estate

@apps.route('/apps/real-estate/grid')
@login_required
def real_estate_grid():
    return render_template('apps/real-estate/apps-real-estate-grid.html')

@apps.route('/apps/real-estate/list')
@login_required
def real_estate_list():
    return render_template('apps/real-estate/apps-real-estate-list.html')

@apps.route('/apps/real-estate/map')
@login_required
def real_estate_map():
    return render_template('apps/real-estate/apps-real-estate-map.html')

@apps.route('/apps/real-estate/property_overview')
@login_required
def real_estate_property_overview():
    return render_template('apps/real-estate/apps-real-estate-property-overview.html')

@apps.route('/apps/real-estate/add_property')
@login_required
def real_estate_add_property():
    return render_template('apps/real-estate/apps-real-estate-add-properties.html')

@apps.route('/apps/real-estate/earnings')
@login_required
def real_estate_earnings():
    return render_template('apps/real-estate/apps-real-estate-earnings.html')


# agent
@apps.route('/apps/real-estate/agent/list')
@login_required
def agent_list():
    return render_template('apps/real-estate/agent/apps-real-estate-agent-list.html')

@apps.route('/apps/real-estate/agent/grid')
@login_required
def agent_grid():
    return render_template('apps/real-estate/agent/apps-real-estate-agent-grid.html')

@apps.route('/apps/real-estate/agent/overview')
@login_required
def agent_overview():
    return render_template('apps/real-estate/agent/apps-real-estate-agent-overview.html')

# agencies
@apps.route('/apps/real-estate/agencies/list')
@login_required
def agencies_list():
    return render_template('apps/real-estate/agencies/apps-real-estate-agencies-list.html')

@apps.route('/apps/real-estate/agencies/overview')
@login_required
def agencies_overview():
    return render_template('apps/real-estate/agencies/apps-real-estate-agencies-overview.html')