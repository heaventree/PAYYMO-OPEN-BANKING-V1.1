from flask import Blueprint,render_template
from flask_login import login_required


components = Blueprint('components',__name__,template_folder='templates',
    static_folder='static',)
    
#  bootstrap-ui

@components.route('/components/bootstrap-ui/alerts')
@login_required
def alerts():
    return render_template('components/bootstrap-ui/ui-alerts.html')

@components.route('/components/bootstrap-ui/badges')
@login_required
def badges():
    return render_template('components/bootstrap-ui/ui-badges.html')

@components.route('/components/bootstrap-ui/buttons')
@login_required
def buttons():
    return render_template('components/bootstrap-ui/ui-buttons.html')

@components.route('/components/bootstrap-ui/colors')
@login_required
def colors():
    return render_template('components/bootstrap-ui/ui-colors.html')

@components.route('/components/bootstrap-ui/cards')
@login_required
def cards():
    return render_template('components/bootstrap-ui/ui-cards.html')

@components.route('/components/bootstrap-ui/carousel')
@login_required
def carousel():
    return render_template('components/bootstrap-ui/ui-carousel.html')

@components.route('/components/bootstrap-ui/dropdowns')
@login_required
def dropdowns():
    return render_template('components/bootstrap-ui/ui-dropdowns.html')

@components.route('/components/bootstrap-ui/grid')
@login_required
def grid():
    return render_template('components/bootstrap-ui/ui-grid.html')

@components.route('/components/bootstrap-ui/images')
@login_required
def images():
    return render_template('components/bootstrap-ui/ui-images.html')

@components.route('/components/bootstrap-ui/tabs')
@login_required
def tabs():
    return render_template('components/bootstrap-ui/ui-tabs.html')

@components.route('/components/bootstrap-ui/accordions')
@login_required
def accordions():
    return render_template('components/bootstrap-ui/ui-accordions.html')

@components.route('/components/bootstrap-ui/modals')
@login_required
def modals():
    return render_template('components/bootstrap-ui/ui-modals.html')

@components.route('/components/bootstrap-ui/offcanvas')
@login_required
def offcanvas():
    return render_template('components/bootstrap-ui/ui-offcanvas.html')

@components.route('/components/bootstrap-ui/placeholders')
@login_required
def placeholders():
    return render_template('components/bootstrap-ui/ui-placeholders.html')

@components.route('/components/bootstrap-ui/progress')
@login_required
def progress():
    return render_template('components/bootstrap-ui/ui-progress.html')

@components.route('/components/bootstrap-ui/notifications')
@login_required
def notifications():
    return render_template('components/bootstrap-ui/ui-notifications.html')

@components.route('/components/bootstrap-ui/media')
@login_required
def media():
    return render_template('components/bootstrap-ui/ui-media.html')

@components.route('/components/bootstrap-ui/embed_video')
@login_required
def embed_video():
    return render_template('components/bootstrap-ui/ui-embed-video.html')

@components.route('/components/bootstrap-ui/typography')
@login_required
def typography():
    return render_template('components/bootstrap-ui/ui-typography.html')

@components.route('/components/bootstrap-ui/lists')
@login_required
def lists():
    return render_template('components/bootstrap-ui/ui-lists.html')

@components.route('/components/bootstrap-ui/links')
@login_required
def links():
    return render_template('components/bootstrap-ui/ui-links.html')

@components.route('/components/bootstrap-ui/general')
@login_required
def general():
    return render_template('components/bootstrap-ui/ui-general.html')

@components.route('/components/bootstrap-ui/utilities')
@login_required
def utilities():
    return render_template('components/bootstrap-ui/ui-utilities.html')

# custom-ui

@components.route('/components/advance-ui/sweetalerts')
@login_required
def sweetalerts():
    return render_template('components/advance-ui/advance-ui-sweetalerts.html')

@components.route('/components/advance-ui/nestable')
@login_required
def nestable():
    return render_template('components/advance-ui/advance-ui-nestable.html')

@components.route('/components/advance-ui/scrollbar')
@login_required
def scrollbar():
    return render_template('components/advance-ui/advance-ui-scrollbar.html')

@components.route('/components/advance-ui/swiper')
@login_required
def swiper():
    return render_template('components/advance-ui/advance-ui-swiper.html')

@components.route('/components/advance-ui/ratings')
@login_required
def ratings():
    return render_template('components/advance-ui/advance-ui-ratings.html')

@components.route('/components/advance-ui/highlight')
@login_required
def highlight():
    return render_template('components/advance-ui/advance-ui-highlight.html')

@components.route('/components/advance-ui/scrollspy')
@login_required
def scrollspy():
    return render_template('components/advance-ui/advance-ui-scrollspy.html')


# custom-ui

@components.route('/components/custom-ui/ribbons')
@login_required
def ribbons():
    return render_template('components/custom-ui/ui-ribbons.html')

@components.route('/components/custom-ui/profile')
@login_required
def profile():
    return render_template('components/custom-ui/ui-profile.html')

@components.route('/components/custom-ui/counter')
@login_required
def counter():
    return render_template('components/custom-ui/ui-counter.html')

# widgets
@components.route('/components/widgets')
@login_required
def widgets():
    return render_template('components/widgets.html')

# forms

@components.route('/components/forms/advanced')
@login_required
def advanced():
    return render_template('components/forms/forms-advanced.html')

@components.route('/components/forms/checkboxs_radios')
@login_required
def checkboxs_radios():
    return render_template('components/forms/forms-checkboxs-radios.html')

@components.route('/components/forms/editors')
@login_required
def editors():
    return render_template('components/forms/forms-editors.html')

@components.route('/components/forms/elements')
@login_required
def elements():
    return render_template('components/forms/forms-elements.html')

@components.route('/components/forms/file_uploads')
@login_required
def file_uploads():
    return render_template('components/forms/forms-file-uploads.html')

@components.route('/components/forms/layouts')
@login_required
def layouts():
    return render_template('components/forms/forms-layouts.html')

@components.route('/components/forms/masks')
@login_required
def masks():
    return render_template('components/forms/forms-masks.html')

@components.route('/components/forms/pickers')
@login_required
def pickers():
    return render_template('components/forms/forms-pickers.html')

@components.route('/components/forms/range_sliders')
@login_required
def range_sliders():
    return render_template('components/forms/forms-range-sliders.html')

@components.route('/components/forms/select')
@login_required
def select():
    return render_template('components/forms/forms-select.html')

@components.route('/components/forms/validation')
@login_required
def validation():
    return render_template('components/forms/forms-validation.html')

@components.route('/components/forms/wizard')
@login_required
def wizard():
    return render_template('components/forms/forms-wizard.html')

# tables

@components.route('/components/tables/basic')
@login_required
def basic():
    return render_template('components/tables/tables-basic.html')

@components.route('/components/tables/datatables')
@login_required
def datatables():
    return render_template('components/tables/tables-datatables.html')

@components.route('/components/tables/gridjs')
@login_required
def gridjs():
    return render_template('components/tables/tables-gridjs.html')

@components.route('/components/tables/listjs')
@login_required
def listjs():
    return render_template('components/tables/tables-listjs.html')

# Apexcharts

@components.route('/components/apexcharts/area')
@login_required
def area():
    return render_template('components/apexcharts/charts-apex-area.html')

@components.route('/components/apexcharts/bar')
@login_required
def bar():
    return render_template('components/apexcharts/charts-apex-bar.html')

@components.route('/components/apexcharts/boxplot')
@login_required
def boxplot():
    return render_template('components/apexcharts/charts-apex-boxplot.html')

@components.route('/components/apexcharts/bubble')
@login_required
def bubble():
    return render_template('components/apexcharts/charts-apex-bubble.html')

@components.route('/components/apexcharts/candlestick')
@login_required
def candlestick():
    return render_template('components/apexcharts/charts-apex-candlestick.html')

@components.route('/components/apexcharts/column')
@login_required
def column():
    return render_template('components/apexcharts/charts-apex-column.html')

@components.route('/components/apexcharts/funnel')
@login_required
def funnel():
    return render_template('components/apexcharts/charts-apex-funnel.html')

@components.route('/components/apexcharts/heatmap')
@login_required
def heatmap():
    return render_template('components/apexcharts/charts-apex-heatmap.html')

@components.route('/components/apexcharts/line')
@login_required
def line():
    return render_template('components/apexcharts/charts-apex-line.html')

@components.route('/components/apexcharts/mixed')
@login_required
def mixed():
    return render_template('components/apexcharts/charts-apex-mixed.html')

@components.route('/components/apexcharts/pie')
@login_required
def pie():
    return render_template('components/apexcharts/charts-apex-pie.html')

@components.route('/components/apexcharts/polar')
@login_required
def polar():
    return render_template('components/apexcharts/charts-apex-polar.html')

@components.route('/components/apexcharts/radar')
@login_required
def radar():
    return render_template('components/apexcharts/charts-apex-radar.html')

@components.route('/components/apexcharts/radialbar')
@login_required
def radialbar():
    return render_template('components/apexcharts/charts-apex-radialbar.html')

@components.route('/components/apexcharts/range_area')
@login_required
def range_area():
    return render_template('components/apexcharts/charts-apex-range-area.html')

@components.route('/components/apexcharts/scatter')
@login_required
def scatter():
    return render_template('components/apexcharts/charts-apex-scatter.html')

@components.route('/components/apexcharts/timeline')
@login_required
def timeline():
    return render_template('components/apexcharts/charts-apex-timeline.html')

@components.route('/components/apexcharts/treemap')
@login_required
def treemap():
    return render_template('components/apexcharts/charts-apex-treemap.html')

# icons

@components.route('/components/icons/remix')
@login_required
def remix():
    return render_template('components/icons/icons-remix.html')

@components.route('/components/icons/boxicons')
@login_required
def boxicons():
    return render_template('components/icons/icons-boxicons.html')

@components.route('/components/icons/materialdesign')
@login_required
def materialdesign():
    return render_template('components/icons/icons-materialdesign.html')

@components.route('/components/icons/bootstrap')
@login_required
def bootstrap():
    return render_template('components/icons/icons-bootstrap.html')

@components.route('/components/icons/phosphor')
@login_required
def phosphor():
    return render_template('components/icons/icons-phosphor.html')


# maps
@components.route('/components/maps/google')
@login_required
def google():
    return render_template('components/maps/maps-google.html')

@components.route('/components/maps/leaflet')
@login_required
def leaflet():
    return render_template('components/maps/maps-leaflet.html')

@components.route('/components/maps/vector')
@login_required
def vector():
    return render_template('components/maps/maps-vector.html')
