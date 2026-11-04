# Organization Onboarding Flow - Kutubxona SaaS

## Flow Overview

User visits public landing → Creates account → Submits organization registration → Organization becomes PENDING → Platform admin approves/rejects → Organization becomes ACTIVE → Owner enters workspace

## API Endpoints

### 1. User Registration (`POST /api/auth/register/`)

Creates:
- User account with `rol=administrator`
- Organization with `status=pending`, `turi=library`
- OrganizationSubscription with Free plan, 14-day trial

**Request:**
```json
{
  "kutubxona_nomi": "My Library",
  "full_name": "Owner Name",
  "username": "owner_name",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "turi": "library",
  "tavsif": "Public library serving community"
}
```

**Response includes:**
- JWT access/refresh tokens
- User details with `rol=administrator`
- Organization data with `status: pending`
- Subscription info: `{"plan": "free", "status": "trial", "trial_ends_at": "2026-11-13"}`

### 2. Approve Organization (`POST /api/saas/organizations/{pk}/approve/`)

**Permissions:** Platform admin (`is_superuser` or `is_staff`)

**Effect:**
- Organization status: `pending` → `active`
- `faol`: `False` → `True`
- `approved_at`: set to current timestamp
- `approved_by`: set to admin user
- Organization becomes accessible via all tenant API endpoints

**Response:** Full organization details + subscription info

### 3. Reject Organization (`POST /api/saas/organizations/{pk}/reject/`)

**Permissions:** Platform admin

**Effect:**
- Organization status: `pending` → `rejected`
- `faol`: `True` → `False`
- `status_reason`: "Ariza platforma administratori tomonidan rad etildi."
- `approved_at`: `None`
- Organization cannot access tenant API endpoints

### 4. Current Organization (`GET /api/auth/organization/`)

**Permissions:** Any authenticated user

**Effect:**
- Returns the user's current organization
- For pending organizations: returns the organization data (owner can see their pending request)
- For active organizations: returns normal data
- For rejected/suspended organizations: may return depending on context

## Workflow States

| Step | Status | Organization `status` | `faol` | Access |
|------|--------|----------------------|--------|--------|
| Registration | Initial | `pending` | `False` | No tenant API access |
| Admin reviews | Pending review | `pending` | `False` | No tenant API access |
| Admin approves | Approved | `active` | `True` | Full tenant API access |
| Admin rejects | Rejected | `rejected` | `False` | No tenant API access |
| Admin suspends | Suspended | `suspended` | `False` | No tenant API access |

## Frontend Integration

The frontend should:

1. **After registration:** Show organization creation form with fields for type, description, phone, address
2. **After registration response:** Display organization status as "Kutilmoqda" (Pending) 
3. **Show CTA:** "Tashkilot tasdiqlangandan keyin to'liq funksiya williaydi" 
4. **After admin approval:** Automatically redirect to dashboard or show notification
5. **Organization list:** Platform admins can see all organizations with their status badges

## Database Changes Tracked

- `Organization.status`: `pending` → `active`/`rejected`/`suspended`
- `Organization.faol`: Synchronized with `status` in `save()`
- `OrganizationSubscription.plan`: Free plan by default
- `OrganizationSubscription.status`: `trial` → `active` after approval
- `OrganizationSubscription.trial_ends_at`: 14 days from registration

## Testing

All onboarding flow endpoints tested and working:
- ✓ Registration creates PENDING organization with Free trial
- ✓ Admin can approve organization (status → active, faol → True)
- ✓ Admin can reject organization (status → rejected, faol → False)
- ✓ Organization status correctly blocks/allows tenant API access
- ✓ Audit log entries created for approval/rejection actions

## Next Steps (P2 Priority)

1. **Frontend organization creation form** - UI for type/description selection
2. **Organization dashboard** - Owner homepage after approval
3. **Staff management** - Invite staff, set roles per organization
4. **Plan upgrade** - Change from Free to Pro/Enterprise tariff
5. **Trial expiration** - Auto-notify before trial ends, handle upgrades