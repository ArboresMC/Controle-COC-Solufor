from django.urls import path
from .views import ClosingListView, SubmitCurrentClosingView, ManagerClosingListView, ManagerClosingApproveView, ManagerClosingRejectView

urlpatterns = [
    path('', ClosingListView.as_view(), name='closing_list'),
    path('submit-current/', SubmitCurrentClosingView.as_view(), name='submit_current_closing'),
    path('manager/', ManagerClosingListView.as_view(), name='manager_closing_list'),
    path('manager/<int:pk>/approve/', ManagerClosingApproveView.as_view(), name='manager_closing_approve'),
    path('manager/<int:pk>/reject/', ManagerClosingRejectView.as_view(), name='manager_closing_reject'),
]
