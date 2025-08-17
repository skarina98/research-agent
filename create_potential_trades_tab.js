// Function to create POTENTIAL_TRADES tab
function createPotentialTradesTab() {
  const SHEET_ID = "1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q";

  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);

    // Check if POTENTIAL_TRADES tab already exists
    const existingSheet = ss.getSheetByName("POTENTIAL_TRADES");
    if (existingSheet) {
      Logger.log("POTENTIAL_TRADES tab already exists");
      return "POTENTIAL_TRADES tab already exists";
    }

    // Create new sheet
    const newSheet = ss.insertSheet("POTENTIAL_TRADES");

    // Define headers (same as AUCTIONS_MASTER plus added_to_potential_trades)
    const headers = [
      "auction_name",
      "auction_date",
      "address",
      "auction_sale",
      "lot_number",
      "postcode",
      "purchase_price",
      "sold_date",
      "owner",
      "guide_price",
      "auction_url",
      "source_url",
      "qa_status",
      "added_to_potential_trades",
      "ingested_at",
    ];

    // Set headers in first row
    newSheet.getRange(1, 1, 1, headers.length).setValues([headers]);

    // Format header row (make it bold)
    newSheet.getRange(1, 1, 1, headers.length).setFontWeight("bold");

    Logger.log("Successfully created POTENTIAL_TRADES tab with headers");
    return "Successfully created POTENTIAL_TRADES tab";
  } catch (error) {
    Logger.log("Error creating POTENTIAL_TRADES tab: " + error.toString());
    return "Error: " + error.toString();
  }
}

// Function to list all available sheets
function listAllSheets() {
  const SHEET_ID = "1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q";

  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const sheets = ss.getSheets();

    Logger.log("Available sheets:");
    for (let i = 0; i < sheets.length; i++) {
      const sheet = sheets[i];
      Logger.log(`${i + 1}. ${sheet.getName()}`);
    }

    return "Sheets listed in logs";
  } catch (error) {
    Logger.log("Error listing sheets: " + error.toString());
    return "Error: " + error.toString();
  }
}
