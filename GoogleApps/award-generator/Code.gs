function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('Award Download Portal')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);
}


// FUNCTION 1: Just checks the whitelist
function verifyCallsign(callsign) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const whitelistSheet = ss.getSheetByName("Whitelist"); 
  const data = whitelistSheet.getRange("A2:A" + whitelistSheet.getLastRow()).getValues();
  const validCallsigns = data.flat().map(c => String(c).toUpperCase().trim());

  if (validCallsigns.indexOf(callsign.toUpperCase().trim()) === -1) {
    return {
      success: false, 
      message: "I checked our records and you are not eligible for this award. Please see the website for details for qualifications on this award."
    };
  }
  return { success: true };
}

// FUNCTION 2: Handles the heavy lifting
function generateAward(callsign) {
  try {
    const TEMPLATE_ID = '1flxSgr7GaUqngtiwe1BXZIqnDhLS7aT2Ax-XUtpZ5x0';
    const FOLDER_ID = '1U8bw-GY8vmjjJmdF0idkL9MEiwFND6N2';
    const targetFolder = DriveApp.getFolderById(FOLDER_ID);
    const fileName = callsign.toUpperCase() + "_Award.pdf";

    // Delete old version
    const existingFiles = targetFolder.getFilesByName(fileName);
    while (existingFiles.hasNext()) { existingFiles.next().setTrashed(true); }

    // Create PDF
    const templateFile = DriveApp.getFileById(TEMPLATE_ID);
    const newCopy = templateFile.makeCopy(`Temp_${callsign}`, targetFolder);
    const doc = DocumentApp.openById(newCopy.getId());
    doc.getBody().replaceText("<CALL_SIGN>", callsign.toUpperCase());
    doc.saveAndClose();

    const pdfBlob = newCopy.getAs(MimeType.PDF);
    const finalPdf = targetFolder.createFile(pdfBlob);
    finalPdf.setName(fileName);
    finalPdf.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    
    newCopy.setTrashed(true);

    return { success: true, downloadUrl: finalPdf.getDownloadUrl().replace("?usp=drivesdk", "") };
  } catch (err) {
    return { success: false, message: "Generation Error: " + err.toString() };
  }
}


