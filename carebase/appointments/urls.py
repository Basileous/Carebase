from django.urls import path
from . import views

urlpatterns = [
    path('',              views.home,                  name='home'),
    path('about/',        views.about,                 name='about'),
    path('patients/',     views.patients,              name='patients'),
    path('rates/',        views.rates,                 name='rates'),
    path('contact/',      views.contact,               name='contact'),
    path('ratings/',      views.ratings,               name='ratings'),
    path('book/',         views.book_appointment,      name='book_appointment'),
    path('book/success/', views.appointment_success,   name='appointment_success'),
    path('chatbot/',      views.chatbot_view,          name='chatbot'),
    path('profile/',      views.profile_view,          name='profile'),
    path('ajax/doctor-slots/', views.get_doctor_slots, name='get_doctor_slots'),
    path('ajax/ai-recommend/', views.ai_recommend_doctor, name='ai_recommend_doctor'),
    path('ajax/notifications/', views.get_notifications, name='get_notifications'),
    path('ajax/notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('admin-panel/',                             views.admin_dashboard,        name='admin_dashboard'),
    path('admin-panel/appointment/<int:pk>/action/', views.appointment_action,     name='appointment_action'),
    path('admin-panel/allot-slot/',                  views.allot_time_slot,        name='allot_time_slot'),
    path('admin-panel/delete-slot/<int:pk>/',        views.delete_time_slot,       name='delete_time_slot'),
    path('admin-panel/reschedule/<int:pk>/',         views.reschedule_appointment, name='reschedule_appointment'),
]
