# Elite Coach AI — API Changelog

**Date:** May 31, 2026

This changelog lists the concrete API changes made in this recent work. It highlights what was implemented in the backend edits I applied and which items were already present or not changed.

---

## Summary — What I changed (concrete)

- Implemented: Tutor role pairing on registration
  - When a user registers with `role: "tutor_author"` or `role: "tutor_responder"`, the backend now assigns both roles: `tutor_author` and `tutor_responder`.
  - Files changed: `app/services/auth.py`, `tests/test_auth.py`

- Implemented: Paystack callback URL + payload
  - The subscribe flow now reads `PAYSTACK_CALLBACK_URL` from settings and sends `callback_url` and `metadata` (and an optional `plan` code) to Paystack when initializing a transaction.
  - Files changed: `app/integrations/paystack.py`, `app/api/v1/payments.py`, `app/core/config.py`, `.env`

---

## What was already present (no changes needed)

- Login returns `user` object with `roles[]` (no change required).
- Register already returned tokens + `user` (no change required).
- Register already accepted a `role` field (no change required).
- Self-registration is already blocked for `platform_admin` (no change required).

These behaviors were present before this edit and thus were not modified by the recent commit.

---

## What I did NOT change here

- I did not add the four new endpoints listed in your draft changelog (Learning/AI/Escalations additions) — they remain outside this change set.
- I did not modify or patch the reported hashed_password column bug (login DB column mismatch) as part of this work.

---

## Frontend Handoff (what you need to do)

- Payment verify flow:

  1. Paystack redirects users to the frontend page configured as the callback, e.g.:

     `https://elitecoach-ai.vercel.app/payment/verify?reference=PAY_abc123xyz`

  2. On the `/payment/verify` page, extract either `reference` or `trxref` from the query string and call the backend verify endpoint:

  ```js
  const params = new URLSearchParams(window.location.search);
  const reference = params.get('reference') || params.get('trxref');

  if (!reference) {
    // show error
  } else {
    const { data } = await api.get(`/api/v1/payments/verify/${reference}`);
    // backend returns success message on success
    if (data?.message) {
      // show success and redirect
    } else {
      // show failure
    }
  }
  ```

  - Note: The verify endpoint requires authentication (Bearer token). Include the logged-in user's access token when calling `/api/v1/payments/verify/{reference}`.

- Tutor role UI:

  - Tutors will now always have both roles in `user.roles` if they register as either tutor type. Use `roles.includes('tutor_author')` and `roles.includes('tutor_responder')` as before — both checks will be true for tutors.

---

## Commit

- Commit hash: `5f08ed3`
- Message: `Fix tutor role pairing and Paystack callback payload`

---

If you want, I can also update your existing changelog draft to remove items I did not change and mark pre-existing items as "already present" — tell me which file to modify (I can patch `docs/API_CHANGELOG.md` or replace an existing changelog file).
