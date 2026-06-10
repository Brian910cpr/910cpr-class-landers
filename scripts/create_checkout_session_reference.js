// Reference backend contract for /api/create-checkout-session.
// Do not include Stripe secret keys in docs/pay/index.html.
// Implement this route in the server/runtime that will own Stripe credentials.

/*
POST /api/create-checkout-session

Request body from docs/pay/index.html:
{
  "source": "910cpr_pay_page",
  "student_name": "Jane Smith",
  "student_email": "jane@example.com",
  "student_phone": "910-395-5193",
  "course": "AHA BLS Provider",
  "class_date": "2026-06-10",
  "amount": "75.00",
  "payment_note": "910CPR - Jane Smith - AHA BLS Provider - 2026-06-10 - $75.00",
  "balance_lookup_used": "true",
  "balance_lookup_amount": "75.00",
  "notes": "Registration issue"
}

Backend behavior:
- Validate required fields server-side.
- Convert amount dollars to cents.
- Create one Stripe Checkout Session.
- Line item name: 910CPR - [Course] - [Class Date]
- mode: payment
- success_url: https://910cpr.com/pay/success/
- cancel_url: https://910cpr.com/pay/cancel/
- metadata:
  source
  student_name
  student_email
  student_phone
  course
  class_date
  amount
  payment_note
  balance_lookup_used
  balance_lookup_amount
  notes

Response:
{
  "url": "https://checkout.stripe.com/..."
}
*/
