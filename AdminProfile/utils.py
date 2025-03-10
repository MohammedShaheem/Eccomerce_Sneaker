from .models import Order

def get_allowed_statuses(order):
    """Helper function to determine which status options should be available"""
    status_dict = dict(Order.STATUS_CHOICES)
    allowed = {}
    
    if order.order_status == 'RETURNED':
        # No changes allowed if already returned
        allowed = {order.order_status: status_dict[order.order_status]}
    elif order.order_status == 'PENDING':
        # From PENDING can go to PROCESSING or DELIVERED
        allowed = {
            order.order_status: status_dict[order.order_status],
            'PROCESSING': status_dict['PROCESSING'],
            'DELIVERED': status_dict['DELIVERED']
        }
    elif order.order_status == 'DELIVERED':
        # From DELIVERED, can only go to CANCELED (RETURNED happens through return requests)
        allowed = {
            order.order_status: status_dict[order.order_status],
            'CANCELED': status_dict['CANCELED']  # Added CANCELED as per your comment
        }
    elif order.order_status == 'PROCESSING':
        # From PROCESSING can go to DELIVERED or CANCELED
        allowed = {
            order.order_status: status_dict[order.order_status],
            'DELIVERED': status_dict['DELIVERED'],
            'CANCELED': status_dict['CANCELED']
        }
    elif order.order_status == 'CANCELED':
        # No changes allowed if canceled
        allowed = {order.order_status: status_dict[order.order_status]}
    elif order.order_status == 'PARTIALLY_RETURNED':
        # From PARTIALLY_RETURNED, allow reverting to DELIVERED or keeping as is
        allowed = {
            order.order_status: status_dict[order.order_status],
            'DELIVERED': status_dict['DELIVERED'],  # Optional: allow reverting to DELIVERED
            'CANCELED': status_dict['CANCELED']    # Optional: allow cancellation
        }
    else:
        # Default fallback - only current status
        allowed = {order.order_status: status_dict[order.order_status]}
    
    return allowed