from django.urls import path

from backend.views import request_otp, verify_otp, create_account, login, password_reset_email, password_reset_form, \
    password_reset_confirm, userdata, resend_otp, categories, slides, pageitems, product_details, \
    update_wishlist, update_cart, wishlist, cart, updateaddress, notify_url, initiate_payment, orders, orderdetails, \
    updaterating, search, updateinfo, update_phone_request_otp, change_password, logout, viewall, notifications

urlpatterns = [
    path('request_otp/', request_otp),
    path('resend_otp/', resend_otp),
    path('verify_otp/', verify_otp),
    path('create_account/', create_account),
    path('login/', login),
    path('logout/', logout),
    path('password_reset_email/', password_reset_email),
    path('password_reset_form/<email>/<token>/', password_reset_form,name="password_reset_form"),
    path('password_reset_confirm/', password_reset_confirm,name="password_reset_confirm"),
    path('userdata/', userdata,),
    path('categories/', categories,),
    path('slides/', slides,),
    path('pageitems/', pageitems,),
    path('productdetails/', product_details,),
    path('updatewishlist/', update_wishlist,),
    path('updatecart/', update_cart,),
    path('wishlist/', wishlist, ),
    path('cart/', cart, ),
    path('updateaddress/', updateaddress, ),
    path('initiate_payment/', initiate_payment, ),
    path('notify_url/', notify_url , ),
    path('orders/', orders, ),
    path('orderdetails/', orderdetails, ),
    path('updaterating/', updaterating, ),
    path('search/', search, ),
    path('updateinfo/', updateinfo, ),
    path('updatephone_otp/', update_phone_request_otp, ),
    path('changepassword/', change_password, ),
    path('viewall/', viewall, ),
    path('notifications/', notifications, ),
]