export function groupRequest(body) {
  const clean = (key, max) => String(body[key] ?? '').trim().slice(0, max);
  const requestId = clean('requestId', 36);
  if (!/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(requestId)) throw Error('Please reload the form and try again.');
  if (clean('companyWebsite', 200)) throw Error('The request could not be accepted. Please call 910-395-5193.');
  if (!(Number(body.formElapsedMs) >= 1500)) throw Error('Please wait a moment and try again.');
  const name = clean('name', 120), email = clean('email', 254).toLowerCase(), program = clean('program', 200);
  if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !program) throw Error('Name, a valid email and a program are required.');
  const headcount = clean('headcount', 8);
  if (headcount && (!/^\d+$/.test(headcount) || Number(headcount) < 1 || Number(headcount) > 10000)) throw Error('Enter a valid estimated headcount.');
  const phone = clean('mobile', 40), organization = clean('organization', 200);
  const details = [
    `Program: ${program}`, `Name: ${name}`, `Organization: ${organization || 'Not supplied'}`,
    `Email: ${email}`, `Mobile: ${phone || 'Not supplied'}`, `Headcount: ${headcount || 'Not supplied'}`,
    `City: ${clean('city', 160)}`, `Address: ${clean('address', 400)}`,
    `Preferred times: ${clean('preferred_times', 500)}`, `Comments: ${clean('comments', 2500)}`
  ].join('\n');
  return {requestId, name, email, phone, program, organization, details};
}
