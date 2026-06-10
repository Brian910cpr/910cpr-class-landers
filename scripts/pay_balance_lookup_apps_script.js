// Google Apps Script web app for /pay/ optional Balance Due lookup.
// Deploy from script.google.com as a web app with access limited as appropriate.
// Public response must stay narrow: no full rows, addresses, comments, phone numbers,
// student lists, or private registration notes.

const SPREADSHEET_ID = "1lnjU7qrDfVUhgguNqCX50YhlX6qJEggWJyO3RDfbCM0";
const SHEET_NAME = "Sheet1";
const TEXT_910CPR = "sms:+19103955193";

function doPost(e) {
  try {
    const request = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    const result = lookupBalance_(request);
    return json_(result);
  } catch (err) {
    return json_({
      match: false,
      message: "Balance lookup is unavailable. Please enter the amount provided by 910CPR or text 910CPR.",
      text910cpr: TEXT_910CPR
    });
  }
}

function lookupBalance_(request) {
  const email = normalizeEmail_(request.email);
  const phone = digits_(request.phone);
  const name = normalizeText_(request.studentName);
  const classDate = normalizeDateText_(request.classDate);

  if (!email && !phone && !name) {
    return {
      match: false,
      message: "Enter email, phone, or student name to look up a possible balance."
    };
  }

  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) {
    return {
      match: false,
      message: "We could not find a matching registration balance. You can still enter the amount provided by 910CPR."
    };
  }

  const headers = values[0].map(function (value) {
    return String(value || "").trim();
  });
  const index = columnIndex_(headers);
  const matches = [];

  for (let rowIndex = 1; rowIndex < values.length; rowIndex += 1) {
    const row = values[rowIndex];
    const rowEmail = normalizeEmail_(row[index.email]);
    const rowPhone = digits_(row[index.phone]);
    const rowName = normalizeText_([row[index.firstName], row[index.lastName]].join(" "));
    const rowDate = normalizeDateText_(row[index.startTime]);

    let score = 0;
    if (email && rowEmail && email === rowEmail) score += 6;
    if (phone && rowPhone && phoneTail_(phone) === phoneTail_(rowPhone)) score += 4;
    if (name && rowName && namesMatch_(name, rowName)) score += 3;
    if (classDate && rowDate && rowDate.indexOf(classDate) !== -1) score += 3;

    const hasIdentityMatch = score >= 6 || (score >= 5 && classDate);
    if (!hasIdentityMatch) continue;

    matches.push({
      amount: amountString_(row[index.balanceDue]),
      course: safeText_(row[index.courseName]),
      classDate: safeDate_(row[index.startTime]),
      score: score
    });
  }

  if (!matches.length) {
    return {
      match: false,
      message: "We could not find a matching registration balance. You can still enter the amount provided by 910CPR."
    };
  }

  matches.sort(function (a, b) {
    return b.score - a.score;
  });

  const bestScore = matches[0].score;
  const bestMatches = matches.filter(function (match) {
    return match.score === bestScore;
  });

  if (bestMatches.length > 1 && !classDate) {
    return {
      match: false,
      multiple: true,
      message: "More than one possible registration was found. Please enter your class date or text 910CPR."
    };
  }

  const match = bestMatches[0];
  const amountNumber = Number(match.amount || "0");

  return {
    match: true,
    amount: match.amount,
    course: match.course,
    classDate: match.classDate,
    zeroBalance: amountNumber === 0,
    message: amountNumber === 0 ? "This registration lookup did not show a balance due. If 910CPR gave you a payment amount, you can still enter it below." : "Possible balance found."
  };
}

function columnIndex_(headers) {
  return {
    firstName: requiredIndex_(headers, "First Name"),
    lastName: requiredIndex_(headers, "Last Name"),
    email: requiredIndex_(headers, "Email Address"),
    phone: requiredIndex_(headers, "Phone Number"),
    startTime: requiredIndex_(headers, "Start Time"),
    courseName: requiredIndex_(headers, "Course Name"),
    balanceDue: requiredIndex_(headers, "Balance Due")
  };
}

function requiredIndex_(headers, name) {
  const index = headers.indexOf(name);
  if (index === -1) {
    throw new Error("Missing required column: " + name);
  }
  return index;
}

function json_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function normalizeEmail_(value) {
  return String(value || "").trim().toLowerCase();
}

function digits_(value) {
  return String(value || "").replace(/\D/g, "");
}

function phoneTail_(value) {
  return digits_(value).slice(-10);
}

function normalizeText_(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ");
}

function normalizeDateText_(value) {
  if (!value) return "";
  if (Object.prototype.toString.call(value) === "[object Date]") {
    return Utilities.formatDate(value, "America/New_York", "yyyy-MM-dd");
  }
  return normalizeText_(value);
}

function namesMatch_(requestName, rowName) {
  if (!requestName || !rowName) return false;
  const requestParts = requestName.split(" ").filter(Boolean);
  return requestParts.every(function (part) {
    return rowName.indexOf(part) !== -1;
  });
}

function amountString_(value) {
  const number = Number(String(value || "0").replace(/[^0-9.-]/g, ""));
  if (!isFinite(number)) return "0.00";
  return number.toFixed(2);
}

function safeText_(value) {
  return String(value || "").trim().slice(0, 120);
}

function safeDate_(value) {
  if (!value) return "";
  if (Object.prototype.toString.call(value) === "[object Date]") {
    return Utilities.formatDate(value, "America/New_York", "yyyy-MM-dd");
  }
  return String(value || "").trim().slice(0, 40);
}
