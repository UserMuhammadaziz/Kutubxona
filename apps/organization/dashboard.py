"""Dashboard widgets an organization can switch on, off and reorder.

The labels shown to librarians live in the frontend; the backend only owns the
keys, which organization types may use them, and the default selection.
"""

from .models import Organization

# key -> organization types that may show it (`None`: every type)
WIDGETS = {
    "overdue_loans": None,
    "active_reservations": None,
    "total_debt": None,
    "unpaid_fines": None,
    "total_books": None,
    "total_copies": None,
    "available_copies": None,
    "issued_copies": None,
    "students_count": (Organization.TYPE_SCHOOL,),
    "teachers_count": (Organization.TYPE_SCHOOL,),
    "members_count": None,
    "pending_applications": None,
    "approved_applications": None,
    "readers_by_class": (Organization.TYPE_SCHOOL,),
    "recent_activity": None,
    "top_books": None,
}


def available_widgets(org_type):
    """Widget keys the given organization type may show, in catalogue order."""
    return [key for key, types in WIDGETS.items() if types is None or org_type in types]


def dashboard_widgets(organization):
    """The ordered widget keys this organization's dashboard shows.

    Keys that do not fit the organization's (possibly changed) type are dropped
    here instead of being deleted, so switching the type back restores them.
    """
    allowed = available_widgets(organization.type)
    if organization.dashboard_widgets is None:
        return allowed
    return [key for key in organization.dashboard_widgets if key in allowed]
