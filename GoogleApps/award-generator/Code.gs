/**
 * Serves the HTML form and passes the award list to the template
 */
function doGet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const listSheet = ss.getSheetByName("awardList");
  const awards = listSheet.getRange("A2:A" + listSheet.getLastRow()).getValues().flat();
  
  const template = HtmlService.createTemplateFromFile('Index');
  template.awardNames = awards.filter(String); // Pass award names to HTML
  
  return template.evaluate()
    .setTitle('Award Download Portal')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Validates callsign against the specific award sheet
 */
function verifyCallsign(callsign, awardName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const listSheet = ss.getSheetByName("awardList");
  const data = listSheet.getDataRange().getValues();
  
  // Find the row for the selected award
  const awardRow = data.find(row => row[0] === awardName);
  if (!awardRow) return { success: false, message: "Award configuration not found." };
  
  const attendeeSheetName = awardRow[3]; // Column D: workSheetAwardees
  const attendeeSheet = ss.getSheetByName(attendeeSheetName);
  
  if (!attendeeSheet) return { success: false, message: "Awardee list is missing for this category." };
  
  const callsigns = attendeeSheet.getRange("A2:A" + attendeeSheet.getLastRow()).getValues().flat();
  const isValid = callsigns.map(c => String(c).toUpperCase().trim()).includes(callsign.toUpperCase().trim());

  if (!isValid) {
    return {
      success: false, 
      message: "I checked our records and you are not eligible for this award. Please see the website for details for qualifications on this award."
    };
  }
  return { success: true };
}

/**
 * Generates PDF using metadata from awardList
 * Updated to handle <SCORE> replacement for "Superstation Betta Test"
 */
function generateAward(callsign, awardName) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const listSheet = ss.getSheetByName("awardList");
    const data = listSheet.getDataRange().getValues();
    const awardRow = data.find(row => row[0] === awardName);

    const TEMPLATE_ID = awardRow[1]; // Column B: linkAwardTemplate
    const FOLDER_ID = awardRow[2];   // Column C: linkUploadDirectory
    const attendeeSheetName = awardRow[3]; // Column D: workSheetAwardees
    
    const targetFolder = DriveApp.getFolderById(FOLDER_ID);
    const fileName = `${callsign.toUpperCase()}_${awardName}.pdf`;

    // Clean up old versions
    const existingFiles = targetFolder.getFilesByName(fileName);
    while (existingFiles.hasNext()) { existingFiles.next().setTrashed(true); }

    // Generate new PDF
    const templateFile = DriveApp.getFileById(TEMPLATE_ID);
    const newCopy = templateFile.makeCopy(`${awardName}_${callsign}`, targetFolder);
    const doc = DocumentApp.openById(newCopy.getId());
    const body = doc.getBody();

    // Standard Replacement
    body.replaceText("<CALL_SIGN>", callsign.toUpperCase());

    // --- NEW SPECIAL CASE LOGIC ---
    if (awardName === "Superstation Betta Test") {
      const attendeeSheet = ss.getSheetByName(attendeeSheetName);
      const attendeeData = attendeeSheet.getDataRange().getValues();
      
      // Find row where Column A matches callsign
      const userRow = attendeeData.find(row => String(row[0]).toUpperCase().trim() === callsign.toUpperCase().trim());
      
      if (userRow) {
        const score = userRow[1]; // Column B (Index 1)
        body.replaceText("<SCORE>", String(score));
      }
    }
    // ------------------------------

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
