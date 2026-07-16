# =====================================================
# NEW: Order status emails — admin me status change karte hi
# customer ko branded email jata hai (Confirmed / Shipped /
# Delivered / Cancelled). Pending pe email nahi jata.
# =====================================================
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# Keys EXACTLY model ke STATUS_CHOICES jaisi (lowercase)
STATUS_EMAIL_CONTENT = {
    'confirmed': {
        'subject': 'Order Confirmed ✅ — Kasauti International',
        'heading': 'Your Order is Confirmed!',
        'message': ("Great news! We've confirmed your order and it's now "
                    "being prepared for dispatch."),
        'color': '#2e7d32',  # green
    },
    'shipped': {
        'subject': 'Your Order Has Been Shipped 📦 — Kasauti International',
        'heading': 'Your Order is On Its Way!',
        'message': ("Your order has been shipped and will reach you soon. "
                    "Get ready to create something amazing!"),
        'color': '#1565c0',  # blue
    },
    'delivered': {
        'subject': 'Order Delivered 🎉 — Kasauti International',
        'heading': 'Your Order Has Been Delivered!',
        'message': ("Your order has been delivered. We hope you love our "
                    "products! For any support, just reply to this email."),
        'color': '#b8860b',  # gold
    },
    'cancelled': {
        'subject': 'Order Cancelled — Kasauti International',
        'heading': 'Your Order Has Been Cancelled',
        'message': ("Your order has been cancelled. If this was a mistake or "
                    "you have any questions, please contact us immediately."),
        'color': '#c62828',  # red
    },
}

# Timeline ke liye normal flow (cancelled isme nahi aata)
STATUS_FLOW = ['pending', 'confirmed', 'shipped', 'delivered']


def send_order_status_email(order):
    """Order status ke hisaab se customer ko branded HTML email bhejta hai."""
    content = STATUS_EMAIL_CONTENT.get(order.status)
    if not content:
        return  # 'pending' ya unknown status — email nahi

    if not order.email:
        logger.warning("Order #%s: customer email missing, status email skip.", order.id)
        return

    # Timeline steps — current status tak green tick
    try:
        current_index = STATUS_FLOW.index(order.status)
    except ValueError:
        current_index = -1  # cancelled

    timeline = [
        {'label': s.capitalize(), 'done': i <= current_index}
        for i, s in enumerate(STATUS_FLOW)
    ]

    items = list(order.items.all())

    context = {
        'order': order,
        'items': items,
        'customer_name': order.name or 'Customer',
        'heading': content['heading'],
        'message': content['message'],
        'color': content['color'],
        'timeline': timeline,
        'is_cancelled': order.status == 'cancelled',
        'site_url': 'https://kasautiinternational.com',
    }

    html_content = render_to_string('emails/order_status.html', context)
    text_content = (
        f"{content['heading']}\n\n"
        f"Order #{order.id}\n"
        f"{content['message']}\n\n"
        f"Total: Rs.{order.total_amount}\n"
        "— Kasauti International"
    )

    try:
        msg = EmailMultiAlternatives(
            subject=content['subject'],
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)
        logger.info("Order #%s: status email '%s' sent to %s",
                    order.id, order.status, order.email)
    except Exception as e:
        # Email fail ho to bhi admin ka save kabhi nahi rukna chahiye
        logger.error("Order #%s: status email failed — %s", order.id, e)