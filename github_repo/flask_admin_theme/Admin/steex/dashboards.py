from flask import Blueprint,render_template
from flask_login import login_required


dashboards = Blueprint('dashboards',__name__,template_folder='templates',
    static_folder='static',)
    

@dashboards.route('/')
@login_required
def index():
    return render_template('dashboards/index.html')

@dashboards.route('/dashboards/analytics')
@login_required
def analytics():
    return render_template('dashboards/dashboard-analytics.html')

@dashboards.route('/dashboards/crm')
@login_required
def crm():
    return render_template('dashboards/dashboard-crm.html')

@dashboards.route('/dashboards/learning')
@login_required
def learning():
    return render_template('dashboards/dashboard-learning.html')

@dashboards.route('/dashboards/real_estate')
@login_required
def real_estate():
    return render_template('dashboards/dashboard-real-estate.html')
