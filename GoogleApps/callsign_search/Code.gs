function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
      .setTitle('Callsign Lookup')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function processSearch(callsign) {
  return callsign ? "Showing results for [" + callsign + "]" : "Showing all records";
}

function searchSpreadsheet(callsign) {
  const ssId = "1Nzt-s2HG2D1iUImuDXN9ATlLVS4XU3rIccK3xFlDr8k"; 
  const sheetName = "Weekly Checkins";
  
  try {
    const ss = SpreadsheetApp.openById(ssId);
    const sheet = ss.getSheetByName(sheetName);
    const data = sheet.getDataRange().getValues();
    
    const headers = data[0].map(String);
    const searchKey = callsign ? callsign.toString().trim().toUpperCase() : "";

    // Filter rows where Column 2 (Index 2) matches the searchKey
    const matches = data.slice(1).filter(row => {
      const cellValue = row[2] ? row[2].toString().trim().toUpperCase() : "";
      return cellValue === searchKey;
    });

    // If no matches, return a specific flag so HTML can show your message
    if (matches.length === 0) {
      return { noResults: true, callsign: callsign };
    }

    // Sanitize the matching rows for transport
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
