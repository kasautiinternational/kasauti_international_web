# =====================================================
# NEW: Owner alerts — naya order aate hi tumhe email milega.
# Signal-based hai, isliye order chahe checkout se bane ya
# Razorpay flow se — alert har jagah se fire hoga.
# =====================================================
import threading
import time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


def _send_order_alert(order_id):
    """Background thread me chalta hai:
    - Thoda wait karta hai taki OrderItems DB me save ho jayein
      (order pehle save hota hai, items uske baad)
    - Fir owner ko HTML email bhejta hai with full order details.
    Customer ke checkout page ko ye bilkul slow nahi karta."""
    time.sleep(8)  # items save hone ka time — mat hatana

    try:
        order = Order.objects.prefetch_related('items').get(id=order_id)
    except Order.DoesNotExist:
        return

    items = list(order.items.all())

    # ----- Items table (HTML) -----
    rows = ''
    for it in items:
        size = f' [{it.size} in]' if it.size else ''
        line_total = (it.unit_price or 0) * (it.quantity or 0)
        rows += (
            '<tr>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;">{it.product_title}{size}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:center;">{it.quantity}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;">&#8377;{it.unit_price:,.2f}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;">&#8377;{line_total:,.2f}</td>'
            '</tr>'
        )

    subtotal = (order.total_amount or 0) - (order.gst_amount or 0)

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:0 auto;
                border:1px solid #eee;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#c9973f,#f5d08a);padding:18px 24px;">
        <h2 style="margin:0;color:#0f172a;">&#128230; New Order #{order.id}</h2>
        <p style="margin:4px 0 0;color:#0f172a;font-size:13px;">Kasauti International — Order Alert</p>
      </div>
      <div style="padding:20px 24px;">
        <table style="width:100%;font-size:14px;color:#0f172a;">
          <tr><td style="padding:4px 0;color:#64748b;width:130px;">Customer</td><td><b>{order.name}</b></td></tr>
          <tr><td style="padding:4px 0;color:#64748b;">Phone</td>
              <td><a href="tel:{order.phone}">{order.phone}</a> &nbsp;|&nbsp;
                  <a href="https://wa.me/91{order.phone.lstrip('+').lstrip('91')}">WhatsApp karo</a></td></tr>
          <tr><td style="padding:4px 0;color:#64748b;">Email</td><td>{order.email}</td></tr>
          <tr><td style="padding:4px 0;color:#64748b;vertical-align:top;">Address</td><td>{order.address}</td></tr>
        </table>

        <table style="width:100%;border-collapse:collapse;margin-top:18px;font-size:14px;color:#0f172a;">
          <tr style="background:#f8fafc;">
            <th style="padding:8px 12px;text-align:left;">Product</th>
            <th style="padding:8px 12px;text-align:center;">Qty</th>
            <th style="padding:8px 12px;text-align:right;">Rate</th>
            <th style="padding:8px 12px;text-align:right;">Total</th>
          </tr>
          {rows}
        </table>

        <table style="width:100%;font-size:14px;color:#0f172a;margin-top:14px;">
          <tr><td style="text-align:right;color:#64748b;padding:2px 12px;">Subtotal:</td>
              <td style="text-align:right;width:120px;">&#8377;{subtotal:,.2f}</td></tr>
          <tr><td style="text-align:right;color:#64748b;padding:2px 12px;">GST (18%):</td>
              <td style="text-align:right;">&#8377;{order.gst_amount:,.2f}</td></tr>
          <tr><td style="text-align:right;padding:6px 12px;font-size:16px;"><b>Grand Total:</b></td>
              <td style="text-align:right;font-size:16px;"><b>&#8377;{order.total_amount:,.2f}</b></td></tr>
        </table>

        <a href="https://kasautiinternational.com/admin/core/order/{order.id}/change/"
           style="display:inline-block;margin-top:18px;background:#0f172a;color:#fff;
                  padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:bold;">
          Admin me Order dekho &#8594;
        </a>
      </div>
    </div>
    """

    # ----- Plain-text fallback -----
    text_lines = [
        f"NEW ORDER #{order.id} — Kasauti International",
        f"Customer: {order.name}",
        f"Phone: {order.phone}",
        f"Email: {order.email}",
        f"Address: {order.address}",
        "",
        "Items:",
    ]
    for it in items:
        size = f" [{it.size} in]" if it.size else ""
        text_lines.append(f"  - {it.product_title}{size} x{it.quantity} @ Rs.{it.unit_price}")
    text_lines.append("")
    text_lines.append(f"GST: Rs.{order.gst_amount}")
    text_lines.append(f"TOTAL: Rs.{order.total_amount}")
    text_lines.append(f"Admin: https://kasautiinternational.com/admin/core/order/{order.id}/change/")

    recipients = getattr(settings, 'ORDER_ALERT_EMAILS', [])
    if not recipients:
        return

    try:
        msg = EmailMultiAlternatives(
            subject=f"🛒 New Order #{order.id} — ₹{order.total_amount:,.0f} — {order.name}",
            body="\n".join(text_lines),
            from_email=settings.EMAIL_HOST_USER,
            to=recipients,
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=True)
    except Exception:
        # Email fail ho jaye to bhi customer ka order kabhi affect nahi hoga
        pass


@receiver(post_save, sender=Order, dispatch_uid="order_owner_alert")
def order_created_alert(sender, instance, created, **kwargs):
    """Naya Order create hote hi background thread me owner ko alert bhejo.
    Sirf CREATE pe chalta hai — status update (Shipped etc.) pe nahi."""
    if not created:
        return
    threading.Thread(
        target=_send_order_alert, args=(instance.id,), daemon=True
    ).start()