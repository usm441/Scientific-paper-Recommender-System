from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^login/$', views.login_request, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'GUIManager/logout.html'}, name='logout'),
    url(r'^$', views.index, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^add_user/$', views.add_user, name='add_user'),
    url(r'^add_algorithm/$', views.add_algorithm, name='add_algorithm'),
    url(r'^register/$', views.register, name='register'),
    url(r'^show_catalog/$', views.show_catalog, name='show_catalog'),
    url(r'^show_rated/$', views.show_ratedpapers, name='show_rated_papers'),
    url(r'^algorithms_table/$', views.algorithms, name='algorithms_table'),
    url(r'^modify_algorithm/(?P<algorithm_id>[0-9]+)/$', views.update_algorithm, name='update_algorithm'),
    url(r'^delete_algorithm/(?P<algorithm_id>[0-9]+)/$', views.delete_algorithm, name='delete_algorithm'),
    url(r'^search/$', views.search, name='search'),
    url(r'^add_feedback/$', views.process_feedback, name='process_feedback'),
    url(r'^register/$', views.register, name='register'),
    url(r'^displayrecommendation/$', views.getrecommendation, name='display_recommendation'),
    url(r'^externalurl/$', views.add_ctr, name='external_url'),
    url(r'^external_search/$', views.external_search, name='external_search'),
    url(r'^eval_results/$', views.eval_results, name='evaluation_results'),
    url(r'^add_to_catalog/$', views.add_to_catalog, name='add_to_catalog'),
    url(r'^eval_manager/$', views.show_feedback_rating, name='feedback_ratings'),
    url(r'^convert_feedback/$', views.convert_feedback_rating, name='convert_feedback'),
    url(r'^update_system_rec/$', views.update_system_recommendation, name='update_system_rec')

]
