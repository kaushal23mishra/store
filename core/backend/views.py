
import datetime

import json

import requests
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from backend.models import User, Otp, PasswordResetToken, Token, Category, Slide, PageItem, Product, ProductOption, \
    OrderedProduct, Order
from backend.serializers import UserSerializer, CategorySerializer, SlideSerializer, PageItemSerializer, \
    ProductSerializer, WishlistSerializer, CartSerializer, AddressSerializer, OrderItemSerializer, \
    OrderDetailsSerializer, NotificationSerializer
from backend.utils import send_otp, token_response, send_password_reset_email, IsAuthenticatedUser, cfSignature, \
    send_user_notification
from core.settings import TEMPLATES_BASE_URL, CF_ID, CF_KEY


@api_view(['POST'])
def request_otp(request):
    email = request.data.get('email')
    phone = request.data.get('phone')

    if email and phone:
        if User.objects.filter(email=email).exists():
            return Response('email already exists', status=400)
        if User.objects.filter(phone=phone).exists():
            return Response('phone already exists', status=400)
        return send_otp(phone)
    else:
        return Response('data_missing', status=400)


@api_view(['POST'])
def resend_otp(request):
    phone = request.data.get('phone')
    if not phone:
        return Response('data_missing', 400)
    return send_otp(phone)


@api_view(['POST'])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')

    otp_obj = get_object_or_404(Otp, phone=phone, verified=False)

    if otp_obj.validity.replace(tzinfo=None) > datetime.datetime.utcnow():
        if otp_obj.otp == int(otp):
            otp_obj.verified = True
            otp_obj.save()
            return Response('otp_verified_successfully')
        else:
            return Response('Incorrect otp', 400)
    else:
        return Response('otp expired', 400)


@api_view(['POST'])
def create_account(request):
    email = request.data.get('email')
    phone = request.data.get('phone')
    password = request.data.get('password')
    fullname = request.data.get('fullname')
    fcmtoken = request.data.get('fcmtoken')

    if email and phone and password and fullname:
        otp_obj = get_object_or_404(Otp, phone=phone, verified=True)
        otp_obj.delete()

        user = User()
        user.email = email
        user.phone = phone
        user.fullname = fullname
        user.password = make_password(password)
        user.save()
        return token_response(user, fcmtoken)

    else:
        return Response('data_missing', 400)


@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    phone = request.data.get('phone')
    password = request.data.get('password')
    fcmtoken = request.data.get('fcmtoken')
    print('jkjkkjkjjk')
    print(email)
    print(phone)
    print(password)
    print(fcmtoken)

    if email:
        user = get_object_or_404(User, email=email)
    elif phone:
        user = get_object_or_404(User, phone=phone)
    else:
        return Response('data_missing', 400)

    if check_password(password, user.password):
        return token_response(user, fcmtoken)
    else:
        return Response('incorrect password', 400)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def logout(request):
    token = request.headers.get('Authorization')
    logout_all = request.GET.get('logout_all')

    if logout_all:
        Token.objects.filter(user=request.user).delete()
    else:
        Token.objects.filter(token=token).delete()

    return Response('logged_out')


@api_view(['POST'])
def password_reset_email(request):
    email = request.data.get('email')
    if not email:
        return Response('params_missing', 400)

    user = get_object_or_404(User, email=email)
    return send_password_reset_email(user)


@api_view(['GET'])
def password_reset_form(request, email, token):
    token_instance = PasswordResetToken.objects.filter(user__email=email, token=token).first()
    link_expired = get_template('pages/link-expired.html').render()
    if token_instance:
        if datetime.datetime.utcnow() < token_instance.validity.replace(tzinfo=None):
            return render(request, 'pages/new-password-form.html', {
                'email': email,
                'token': token,
                'base_url': TEMPLATES_BASE_URL
            })
        else:
            token_instance.delete()
            return HttpResponse(link_expired)
    else:
        return HttpResponse(link_expired)


@api_view(['POST'])
def password_reset_confirm(request):
    email = request.data.get('email')
    token = request.data.get('token')
    password1 = request.data.get('password1')
    password2 = request.data.get('password2')

    token_instance = PasswordResetToken.objects.filter(user__email=email, token=token).first()
    link_expired = get_template('pages/link-expired.html').render()

    if token_instance:
        if datetime.datetime.utcnow() < token_instance.validity.replace(tzinfo=None):
            if len(password1) < 8:
                return render(request, 'pages/new-password-form.html', {
                    'email': email,
                    'token': token,
                    'base_url': TEMPLATES_BASE_URL,
                    'error': 'Password length must be at least 8 characters!'
                })

            if password1 == password2:
                user = token_instance.user
                user.password = make_password(password1)
                user.save()
                token_instance.delete()
                Token.objects.filter(user=user).delete()
                return render(request, 'pages/password-updated.html')
            else:
                return render(request, 'pages/new-password-form.html', {
                    'email': email,
                    'token': token,
                    'base_url': TEMPLATES_BASE_URL,
                    'error': 'Password doesn\'t matched!'
                })
        else:
            token_instance.delete()
            return HttpResponse(link_expired)
    else:
        return HttpResponse(link_expired)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def userdata(request):
    user = request.user
    data = UserSerializer(user, many=False).data
    return Response(data)


@api_view(['GET'])
def categories(request):
    list = Category.objects.all().order_by('position')
    data = CategorySerializer(list, many=True).data
    return Response(data)


@api_view(['GET'])
def slides(request):
    list = Slide.objects.all().order_by('position')
    data = SlideSerializer(list, many=True).data
    return Response(data)


@api_view(['GET'])
def pageitems(request):
    category = request.GET.get('category')

    pagination = LimitOffsetPagination()

    page_items = PageItem.objects.filter(category=category)

    queryset = pagination.paginate_queryset(page_items, request)

    data = PageItemSerializer(queryset, many=True).data

    return pagination.get_paginated_response(data)


@api_view(['GET'])
def viewall(request):
    page_item_id = request.GET.get('id')

    pagination = LimitOffsetPagination()

    product_options = get_object_or_404(PageItem, id=page_item_id).product_options.all()

    queryset = pagination.paginate_queryset(product_options, request)

    data = WishlistSerializer(queryset, many=True).data
    return pagination.get_paginated_response(data)


@api_view(['GET'])
def product_details(request):
    productId = request.GET.get('productId')
    product = get_object_or_404(Product, id=productId)
    data = ProductSerializer(product, many=False).data
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def update_wishlist(request):
    id = request.GET.get('id')
    action = request.GET.get('action')
    user = request.user

    if action == 'ADD':
        user.wishlist.add(id)
        user.save()
    elif action == 'REMOVE':
        user.wishlist.remove(id)
        user.save()
    return Response('updated')


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def update_cart(request):
    id = request.GET.get('id')
    action = request.GET.get('action')
    user = request.user

    if action == 'ADD':
        user.cart.add(id)
        user.save()
    elif action == 'REMOVE':
        user.cart.remove(id)
        user.save()
    return Response('updated')


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def wishlist(request):
    _wishlist = request.user.wishlist.all()
    data = WishlistSerializer(_wishlist, many=True).data
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def cart(request):
    id = request.GET.get('id')
    if id:
        products = ProductOption.objects.filter(id=id)
        data = CartSerializer(products, many=True).data
    else:
        # load all cart items
        products = request.user.cart.all()
        data = CartSerializer(products, many=True).data
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticatedUser])
def updateaddress(request):
    name = request.data.get('name')
    address = request.data.get('address')
    pincode = request.data.get('pincode')
    contact_no = request.data.get('contact_no')

    if name and address and pincode and contact_no:
        pincode = int(pincode)
        try:
            pincode_response = requests.get("https://api.postalpincode.in/pincode/" + str(pincode)).json()
            if pincode_response[0]['Status'] == 'Success':
                district = pincode_response[0]['PostOffice'][0]['District']
                state = pincode_response[0]['PostOffice'][0]['State']
                user = request.user
                user.name = name
                user.address = address
                user.contact_no = contact_no
                user.pincode = pincode
                user.district = district
                user.state = state
                user.save()

                return Response(AddressSerializer(user, many=False).data)
            else:
                return Response('invalid_pincode', 400)
        except:
            return Response('failed to validate pincode', 400)
    else:
        return Response("data_missing", 400)


@api_view(['POST'])
@permission_classes([IsAuthenticatedUser])
def initiate_payment(request):
    items = request.data.get('items')
    print(items)
    print("items")
    from_cart = request.data.get('from_cart')
    tx_amount = request.data.get('tx_amount')
    print(tx_amount)
    print("tx_amount1")
    payment_mode = request.data.get('payment_mode')

    query = Q(id=items[0]['id'])
    for item in items:
        query = query | Q(id=item['id'])

    product_options = ProductOption.objects.filter(query)

    ordered_products = []
    server_tx_amount = 0
    for option in product_options:
        for item in items:
            if str(option.id) == item['id']:
                option.quantity = option.quantity - item['quantity']
                order_tx_price = (option.product.offer_price * item['quantity']) + option.product.delivery_charge
                server_tx_amount = server_tx_amount + order_tx_price

                order_option = OrderedProduct()
                order_option.quantity = item['quantity']
                order_option.product_option = option
                order_option.product_price = option.product.offer_price
                order_option.delivery_price = option.product.delivery_charge
                order_option.tx_price = order_tx_price
                ordered_products.append(order_option)
                print("kaushal1")

    if server_tx_amount != tx_amount:
        print(server_tx_amount)
        print(tx_amount)
        print("kaushal")
        return Response("amount_mismatched", 400)

    order = Order()
    order.user = request.user
    order.from_cart = from_cart
    order.tx_amount = server_tx_amount
    order.address = request.user.name + "\n" \
                    + request.user.contact_no + "\n" \
                    + request.user.address + "\n" \
                    + str(request.user.pincode) \
                    + request.user.district + "\n" \
                    + request.user.state + "\n"
    order.payment_mode = payment_mode
    order.pending_orders = len(ordered_products)
    order.tx_status = 'INITIATED'
    order.save()

    for ordered_product in ordered_products:
        ordered_product.order = order
        ordered_product.save()

    for option in product_options:
        option.save()

    if payment_mode == 'COD':
        data = {
            "token": "",
            "orderId": order.id,
            "tx_amount": server_tx_amount,
            "appId": CF_ID,
            "orderCurrency": "INR",
        }
        return Response(data)

    headers = {
        'Content-Type': 'application/json',
        'x-client-id': CF_ID,
        'x-client-secret': CF_KEY,
    }

    data = {
        "orderId": str(order.id),
        "orderAmount": server_tx_amount,
        "orderCurrency": "INR",
    }

    response = requests.post("https://test.cashfree.com/api/v2/cftoken/order",
                             headers=headers, data=json.dumps(data))
    if response.json()['status'] == 'OK':
        data = {
            "token": response.json()['cftoken'],
            "orderId": order.id,
            "tx_amount": server_tx_amount,
            "appId": CF_ID,
            "orderCurrency": "INR",
        }
        return Response(data)
    else:
        print(response.json())
        order.tx_status = "FAILED"
        order.tx_msg = "MY_SMARTSTORE_SERVER_MSG: Failed to generate cftoken"
        order.save()
        return Response("Something went wrong", 400)


@api_view(['POST'])
def notify_url(request):
    try:
        order_id = request.form['orderId']
        order_amount = request.form['orderAmount']
        reference_id = request.form['referenceId']
        tx_status = request.form['txStatus']
        payment_mode = request.form['paymentMode']
        tx_msg = request.form['txMsg']
        tx_time = request.form['txTime']
        res_signature = request.form['signature']
    except:
        order_id = request.data['orderId']
        order_amount = request.data['orderAmount']
        reference_id = request.data['referenceId']
        tx_status = request.data['txStatus']
        payment_mode = request.data['paymentMode']
        tx_msg = request.data['txMsg']
        tx_time = request.data['txTime']
        res_signature = request.data['signature']

    if tx_status == 'SUCCESS' and payment_mode != 'COD':
        postData = {
            "orderId": order_id,
            "orderAmount": order_amount,
            "referenceId": reference_id,
            "txStatus": tx_status,
            "paymentMode": payment_mode,
            "txMsg": tx_msg,
            "txTime": tx_time,
        }
        signature = cfSignature(postData)

        if signature != bytes(res_signature, encoding='utf8'):
            return Response('tampered_request', 400)

    order = get_object_or_404(Order, id=order_id)
    if tx_status == 'CANCELLED':
        order.delete()
        return Response('updated')

    order.tx_id = reference_id
    order.tx_status = tx_status
    order.payment_mode = payment_mode
    order.tx_msg = tx_msg
    order.tx_time = tx_time
    order.save()

    if tx_status == 'SUCCESS' or payment_mode == 'COD':
        ordered_products = order.orders_set.all()
        for ordered_product in ordered_products:
            user = order.user
            title = "ORDER PLACED"
            body = "Your " + ordered_product.product_option.__str__() + " has been ordered."
            image = ordered_product.product_option.images_set.first().image
            send_user_notification(user, title, body, image)
            if order.from_cart:
                order.user.cart.remove(ordered_product.product_option)

    return Response('updated')


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def orders(request):
    orders = OrderedProduct.objects.filter(order__user=request.user).order_by('-created_at')
    pagination = LimitOffsetPagination()
    queryset = pagination.paginate_queryset(orders, request)
    data = OrderItemSerializer(queryset, many=True).data
    return pagination.get_paginated_response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def orderdetails(request):
    id = request.GET.get('id')
    order = get_object_or_404(OrderedProduct, id=id)
    data = OrderDetailsSerializer(order, many=False).data
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def updaterating(request):
    orderId = request.GET.get('id')
    new_rating = int(request.GET.get('rating'))

    order = get_object_or_404(OrderedProduct, id=orderId)
    initial_rating = order.rating
    order.rating = new_rating

    if initial_rating == 1:
        order.product_option.product.star_1 -= 1
    elif initial_rating == 2:
        order.product_option.product.star_2 -= 1
    elif initial_rating == 3:
        order.product_option.product.star_3 -= 1
    elif initial_rating == 4:
        order.product_option.product.star_4 -= 1
    elif initial_rating == 5:
        order.product_option.product.star_5 -= 1

    if new_rating == 1:
        order.product_option.product.star_1 += 1
    elif new_rating == 2:
        order.product_option.product.star_2 += 1
    elif new_rating == 3:
        order.product_option.product.star_3 += 1
    elif new_rating == 4:
        order.product_option.product.star_4 += 1
    elif new_rating == 5:
        order.product_option.product.star_5 += 1

    order.product_option.product.save()
    order.save()

    return Response('updated')


@api_view(['GET'])
def search(request):
    query = request.GET.get('query', "")

    pagination = LimitOffsetPagination()
    keywords = query.split(' ')

    datalist_container = []
    result = []

    if len(keywords) > 0:
        query = Q(product__title__icontains=keywords[0]) | Q(option__icontains=keywords[0])
        for keyword in keywords:
            datalist_container.append([])
            query = query | Q(product__title__icontains=keyword) | Q(option__icontains=keywords[0])

        products = ProductOption.objects.filter(query)

        for product in products:
            index = len(keywords)
            for keyword in keywords:
                if keyword.lower() in product.product.title.lower() or keyword.lower() in product.option.lower():
                    index = index - 1

            datalist_container[index].append(product)

        for sublist in datalist_container:
            result.extend(sublist)

    result_page = pagination.paginate_queryset(result, request)
    data = WishlistSerializer(result_page, many=True).data
    return pagination.get_paginated_response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticatedUser])
def updateinfo(request):
    phone = request.data.get('phone')
    email = request.data.get('email')
    name = request.data.get('fullname')
    password = request.data.get('password')

    if not email or not phone or not name or not password:
        return Response('params_missing', 400)

    if check_password(password, request.user.password):
        if phone != request.user.phone:
            if User.objects.filter(phone=phone).exists():
                return Response('phone already exists', 400)
            otp_obj = get_object_or_404(Otp, phone=phone, verified=True)
            otp_obj.delete()

        if email != request.user.email:
            if User.objects.filter(email=email).exists():
                return Response('email already exists', 400)

        user = request.user
        user.phone = phone
        user.email = email
        user.fullname = name
        user.save()
        return Response('updated_successfully')
    else:
        return Response('incorrect_password', 401)


@api_view(['POST'])
@permission_classes([IsAuthenticatedUser])
def update_phone_request_otp(request):
    phone = request.data.get('phone')
    password = request.data.get('password')

    if check_password(password, request.user.password):
        if not phone:
            return Response('params_missing', 400)

        if User.objects.filter(phone=phone).exists():
            return Response('phone already exists', 400)
        else:
            return send_otp(phone)
    else:
        return Response('incorrect_password', 401)


@api_view(['POST'])
@permission_classes([IsAuthenticatedUser])
def change_password(request):
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if check_password(old_password, request.user.password):
        request.user.password = make_password(new_password)
        request.user.save()
        Token.objects.filter(user=request.user).delete()
        return Response('password_updated')
    else:
        return Response('incorrect_password', 401)


@api_view(['GET'])
@permission_classes([IsAuthenticatedUser])
def notifications(request):
    pagination = LimitOffsetPagination()

    request.user.notifications_set.filter(seen=False).update(seen=True)

    notifications_set = request.user.notifications_set.all().order_by('-created_at')

    queryset = pagination.paginate_queryset(notifications_set, request)

    data = NotificationSerializer(queryset, many=True).data
    return pagination.get_paginated_response(data)
