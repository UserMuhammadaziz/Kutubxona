from celery import shared_task


@shared_task
def sync_pending_payments():
    """Turn paid Taps checkouts into subscription time even if the payer never comes back."""
    from .services import sync_pending

    return sync_pending()
