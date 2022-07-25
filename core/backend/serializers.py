from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from backend.models import User, Category, Slide, Product, ProductOption, ProductImage, PageItem, OrderedProduct, \
    Notification


class UserSerializer(ModelSerializer):
    notifications = SerializerMethodField()
    class Meta:
        model = User
        fields = ['email','notifications', 'phone', 'fullname', 'wishlist', 'cart', 'name', 'address', 'contact_no', 'pincode', 'state',
                  'district']

    def get_notifications(self,obj):
        list = obj.notifications_set.filter(seen=False)
        return len(list)


class AddressSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'address', 'contact_no', 'pincode', 'state', 'district']


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'position', 'image']


class SlideSerializer(ModelSerializer):
    class Meta:
        model = Slide
        fields = ['position', 'image']


class ProductSerializer(ModelSerializer):
    options = SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'offer_price', 'delivery_charge', 'cod', 'star_5', 'star_4',
                  'star_3', 'star_2', 'star_1', 'options']

    def get_options(self, obj):
        options = obj.options_set.all()
        data = ProductOptionSerializer(options, many=True).data
        return data


class ProductOptionSerializer(ModelSerializer):
    images = SerializerMethodField()

    class Meta:
        model = ProductOption
        fields = ['id', 'option', 'quantity', 'images']

    def get_images(self, obj):
        images = obj.images_set.all()
        data = ProductImageSerializer(images, many=True).data
        return data


class ProductImageSerializer(ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['position', 'image', 'product_option']


class WishlistSerializer(ModelSerializer):
    id = SerializerMethodField()
    title = SerializerMethodField()
    price = SerializerMethodField()
    offer_price = SerializerMethodField()
    image = SerializerMethodField()

    def get_id(self, obj):
        return obj.product.id

    def get_title(self, obj):
        return obj.__str__()

    def get_price(self, obj):
        return obj.product.price

    def get_offer_price(self, obj):
        return obj.product.offer_price

    def get_image(self, obj):
        return ProductImageSerializer(obj.images_set.order_by('position').first(), many=False).data.get(
            'image')

    class Meta:
        model = ProductOption
        fields = ['id', 'title', 'image', 'price', 'offer_price']


class CartSerializer(WishlistSerializer):
    cod = SerializerMethodField()
    delivery_charge = SerializerMethodField()
    id = SerializerMethodField()

    def get_cod(self, obj):
        return obj.product.cod

    def get_delivery_charge(self, obj):
        return obj.product.delivery_charge

    def get_id(self, obj):
        return obj.id

    class Meta:
        model = ProductOption
        fields = ['id', 'title', 'image', 'price', 'offer_price', 'quantity', 'cod', 'delivery_charge']


class PageItemSerializer(ModelSerializer):
    product_options = SerializerMethodField()

    class Meta:
        model = PageItem
        fields = ['id', 'position', 'image', 'category', 'title', 'viewtype', 'product_options']

    def get_product_options(self, obj):
        options = obj.product_options.all()[:8]
        data = []
        for option in options:
            data.append({
                'id': option.product.id,
                'image': ProductImageSerializer(option.images_set.order_by('position').first(), many=False).data.get(
                    'image'),
                'title': option.__str__(),
                'price': option.product.price,
                'offer_price': option.product.offer_price,
            })

        return data


class OrderItemSerializer(ModelSerializer):
    title = SerializerMethodField()
    image = SerializerMethodField()
    created_at = SerializerMethodField()

    class Meta:
        model = OrderedProduct
        fields = ['id', 'title', 'image', 'created_at', 'quantity', 'status', 'rating']

    def get_title(self, obj):
        return obj.product_option.__str__()

    def get_image(self, obj):
        return ProductImageSerializer(obj.product_option.images_set.order_by('position').first(), many=False).data.get(
            'image')

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d %b %Y %H:%M %p")


class OrderDetailsSerializer(OrderItemSerializer):
    payment_mode = SerializerMethodField()
    address = SerializerMethodField()
    tx_id = SerializerMethodField()
    tx_status = SerializerMethodField()

    class Meta:
        model = OrderedProduct
        fields = ['id', 'title', 'image', 'created_at', 'quantity', 'status', 'rating'
                  ,'product_price','tx_price','delivery_price','payment_mode','address','tx_id','tx_status']

    def get_payment_mode(self,obj):
        return obj.order.payment_mode

    def get_address(self,obj):
        return obj.order.address

    def get_tx_id(self,obj):
        return obj.order.tx_id

    def get_tx_status(self,obj):
        return obj.order.tx_status


class NotificationSerializer(ModelSerializer):
    created_at = SerializerMethodField()
    class Meta:
        model = Notification
        fields = ['id','title','body','image','seen','created_at']


    def get_created_at(self, obj):
        return obj.created_at.strftime("%d %b %Y %H:%M %p")