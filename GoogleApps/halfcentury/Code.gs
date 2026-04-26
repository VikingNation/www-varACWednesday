/**
 * MAIN ROUTER — Serves different HTML pages based on ?mode=
 *
 *   /exec?mode=search        → search.html
 *   /exec?mode=halfcentury   → halfcentury.html
 */
function doGet(e) {
  const mode = (e && e.parameter.mode)
    ? e.parameter.mode.toLowerCase()
    : "search";

  if (mode === "halfcentury") {
    return HtmlService.createHtmlOutputFromFile("halfcentury")
      .setTitle("VarAC Wednesday – Half‑Century Awards")
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }

  // Default = search page
  return HtmlService.createHtmlOutputFromFile("search")
    .setTitle("VarAC Wednesday – Callsign Lookup")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Helper: Return JSON to HTML pages
 */
function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ============================================================
   SEARCH MODE (Existing Feature)
   ============================================================ */

function searchSpreadsheet(callsign) {
  const ssId = "1Nzt-s2HG2D1iUImuDXN9ATlLVS4XU3rIccK3xFlDr8k";
  const sheetName = "Weekly Checkins";

  try {
    const ss = SpreadsheetApp.getActive();
    const sheet = ss.getSheetByName(sheetName);
    const data = sheet.getDataRange().getValues();

    const headers = data[0].map(String);
    const searchKey = callsign ? callsign.toString().trim().toUpperCase() : "";

    const matches = data.slice(1).filter(row => {
      const cellValue = row[2] ? row[2].toString().trim().toUpperCase() : "";
      return cellValue === searchKey;
    });

    if (matches.length === 0) {
      return { noResults: true, callsign: callsign };
    }

    const cleanRows = matches.map(row => {
      return row.map(cell => {
        if (cell instanceof Date) return cell.toLocaleDateString();
        return (cell === null || cell === undefined) ? "" : String(cell);
      });
    });

    return {
      headers: headers,
      rows: cleanRows
    };

  } catch (e) {
    return { error: "Server Error: " + e.toString() };
  }
}

/* ============================================================
   HALF‑CENTURY MODE (≥ 50 check‑ins)
   ============================================================ */

function runHalfCentury() {
  const SHEET_ID = "1Nzt-s2HG2D1iUImuDXN9ATlLVS4XU3rIccK3xFlDr8k";
  const SHEET_NAME = "Weekly Checkins";

  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(SHEET_NAME);
  const data = sheet.getDataRange().getValues();

  data.shift(); // remove headers

  // Sort by date (column index 1)
  data.sort((a, b) => new Date(a[1]) - new Date(b[1]));

  const counts = {};
  const winners = [];

  data.forEach(row => {
    const week = row[0];
    const date = row[1];
    const callsign = String(row[2]).toUpperCase().trim();

    if (!callsign) return;

    counts[callsign] = (counts[callsign] || 0) + 1;

    if (counts[callsign] === 50) {
      const formattedDate = (date instanceof Date)
        ? date.toLocaleDateString()
        : date;

      winners.push({
        week: week,
        date: formattedDate,
        callsign: callsign
      });
    }
  });

  return {
    winners: winners.reverse(),
    totalWinners: winners.length
  };
}

/**
 * Expose backend functions to HTML pages
 */
function getHalfCenturyData() {
  return runHalfCentury();
}

function getSearchData(callsign) {
  return searchSpreadsheet(callsign);
}

