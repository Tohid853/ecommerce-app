from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, CartItem, Order,Category
from django.db.models import Sum


# Create your views here.
# --- USER AUTH ---
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        User.objects.create_user(username=username, password=password)
        return redirect('login')
    return render(request, 'store/signup.html')

def login_view(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'store/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# --- TEMPLATES ---
def home(request):
    category_slug=request.GET.get('category')
    categories=Category.objects.all()
    products = Product.objects.all()
    if category_slug:
        products=products.filter(category__slug=category_slug)
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)
     # --- PRICE FILTER YAHAN ADD KARO ---
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
        # --- SORTING ---
    sort = request.GET.get('sort')
    if sort == 'low_to_high':
        products = products.order_by('price')
    elif sort == 'high_to_low':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-id')
    return render(request, 'store/home.html', {'products': products,'categories':categories,'min_price':min_price,'max_price':max_price,'sort':sort})

def product_detail(request, pk):
    # Yahi wala tumhara wala fix - pk=None wala logic
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum([item.product.price * item.quantity for item in cart_items])
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum([item.product.price * item.quantity for item in cart_items])
    if request.method == 'POST':
        Order.objects.create(user=request.user, total_price=total, address=request.POST['address'])
        cart_items.delete() # cart khali
        return render(request, 'store/success.html')
    return render(request, 'store/checkout.html', {'total': total})

# --- ADMIN SALES REPORT ---
def sales_report(request):
    orders = Order.objects.all()
    total_sales = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders=orders.count()
    return render(request, 'store/admin_report.html', {'orders': orders, 'total_sales': total_sales,'total_orders':total_orders})
