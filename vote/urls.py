from django.conf.urls import url
import views


urlpatterns = [
    url(r'^user/register$', views.user_register),
    url(r'^user/logout$', views.user_logout),
    url(r'^user/login$', views.user_login),
    url(r'^user/vote$', views.user_vote),
    url(r'^vote/list$', views.vote_list),
]
