const SHEET_ID = "1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q"; // your actual Google Sheet ID
const SHARED_TOKEN =
  "3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb"; // your shared secret
const DEFAULT_TAB_NAME = "AUCTIONS_MASTER";

function doPost(e) {
  try {
    const requestData = JSON.parse(e.postData.contents);
    const { token, action, rows, row_data, sheet_id, sheet_name } = requestData;

    if (token !== SHARED_TOKEN) {
      return ContentService.createTextOutput(
        JSON.stringify({ ok: false, error: "Invalid token" })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const sheetId = sheet_id || SHEET_ID;
    const tabName = sheet_name || DEFAULT_TAB_NAME;

    // Debug logging
    Logger.log(`Requested sheet_name: ${sheet_name}`);
    Logger.log(`Using tabName: ${tabName}`);

    const sheet = SpreadsheetApp.openById(sheetId).getSheetByName(tabName);

    if (!sheet) {
      Logger.log(`Sheet '${tabName}' not found`);
      return ContentService.createTextOutput(
        JSON.stringify({ ok: false, error: `Sheet '${tabName}' not found` })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    Logger.log(`Successfully found sheet: ${sheet.getName()}`);

    switch (action) {
      case "add":
        return handleAdd(sheet, rows, tabName);
      case "read":
        return handleRead(sheet, tabName);
      case "update_row":
        return handleUpdateRow(sheet, row_data, tabName);
      case "delete_row":
        return handleDeleteRow(sheet, row_data, tabName);
      default:
        return ContentService.createTextOutput(
          JSON.stringify({ ok: false, error: "Invalid action" })
        ).setMimeType(ContentService.MimeType.JSON);
    }
  } catch (error) {
    Logger.log(`Error in doPost: ${error.toString()}`);
    return ContentService.createTextOutput(
      JSON.stringify({ ok: false, error: error.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleAdd(sheet, rows, tabName) {
  try {
    Logger.log(`Adding ${rows.length} rows to sheet: ${tabName}`);

    let addedCount = 0;
    const headers = sheet.getDataRange().getValues()[0];

    Logger.log(`Headers in ${tabName}: ${headers.join(", ")}`);

    for (const rowData of rows) {
      // Logger.log(JSON.stringify(rowData)); // For debugging
      const row = headers.map((header) => {
        switch (header) {
          case "auction_name":
            return rowData.auction_name || "";
          case "auction_date":
            return rowData.auction_date || "";
          case "address":
            return rowData.address || "";
          case "auction_sale":
            return rowData.auction_sale || "";
          case "lot_number":
            return rowData.lot_number || "";
          case "postcode":
            return rowData.postcode || "";
          case "purchase_price":
            return rowData.purchase_price || "";
          case "sold_date":
            return rowData.sold_date || "";
          case "owner":
            return rowData.owner || "";
          case "guide_price":
            return rowData.guide_price || "";
          case "auction_url":
            return rowData.auction_url || "";
          case "source_url":
            return rowData.source_url || "";
          case "qa_status":
            return rowData.qa_status || "imported";
          case "added_to_potential_trades":
            return rowData.added_to_potential_trades || "";
          case "ingested_at":
            return rowData.ingested_at || new Date().toISOString();
          default:
            return "";
        }
      });

      sheet.appendRow(row);
      addedCount++;
    }

    Logger.log(`Successfully added ${addedCount} rows to ${tabName}`);

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        count: addedCount,
        message: `Added ${addedCount} rows to ${tabName}`,
        sheet_name: tabName,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    Logger.log(`Error in handleAdd: ${error.toString()}`);
    return ContentService.createTextOutput(
      JSON.stringify({ ok: false, error: error.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleRead(sheet, tabName) {
  try {
    Logger.log(`Reading from sheet: ${tabName}`);

    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const rows = data.slice(1).map((row) => {
      const obj = {};
      headers.forEach((header, i) => (obj[header] = row[i] || ""));
      return obj;
    });

    Logger.log(`Read ${rows.length} rows from ${tabName}`);

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        rows: rows,
        count: rows.length,
        sheet_name: tabName,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    Logger.log(`Error in handleRead: ${error.toString()}`);
    return ContentService.createTextOutput(
      JSON.stringify({ ok: false, error: error.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleUpdateRow(sheet, rowData, tabName) {
  try {
    Logger.log(`Updating row in sheet: ${tabName}`);

    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const rows = data.slice(1);

    const addressIndex = headers.indexOf("address");
    const auctionNameIndex = headers.indexOf("auction_name");
    const auctionDateIndex = headers.indexOf("auction_date");

    let rowIndex = -1;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      if (
        row[addressIndex] === rowData.address &&
        row[auctionNameIndex] === rowData.auction_name &&
        row[auctionDateIndex] === rowData.auction_date
      ) {
        rowIndex = i + 1; // Adjust for header
        break;
      }
    }

    if (rowIndex === -1) {
      return ContentService.createTextOutput(
        JSON.stringify({ ok: false, error: "Row not found" })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const currentRow = rows[rowIndex - 1];
    const updatedRow = headers.map((header, i) => {
      switch (header) {
        case "auction_name":
          return rowData.auction_name || "";
        case "auction_date":
          return rowData.auction_date || "";
        case "address":
          return rowData.address || "";
        case "auction_sale":
          return rowData.auction_sale || "";
        case "lot_number":
          return rowData.lot_number || "";
        case "postcode":
          return rowData.postcode || "";
        case "purchase_price":
          return rowData.purchase_price || "";
        case "sold_date":
          return rowData.sold_date || "";
        case "owner":
          return rowData.owner || "";
        case "guide_price":
          return rowData.guide_price || "";
        case "auction_url":
          return rowData.auction_url || "";
        case "source_url":
          return rowData.source_url || "";
        case "qa_status":
          return rowData.qa_status || "enriched";
        case "added_to_potential_trades":
          return rowData.added_to_potential_trades || "";
        case "ingested_at":
          return rowData.ingested_at || new Date().toISOString();
        default:
          return currentRow[i] || "";
      }
    });

    const range = sheet.getRange(rowIndex + 1, 1, 1, updatedRow.length);
    range.setValues([updatedRow]);

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        message: "Row updated successfully",
        rowIndex: rowIndex,
        sheet_name: tabName,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    Logger.log(`Error in handleUpdateRow: ${error.toString()}`);
    return ContentService.createTextOutput(
      JSON.stringify({ ok: false, error: error.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleDeleteRow(sheet, rowData, tabName) {
  try {
    Logger.log(`Deleting row from sheet: ${tabName}`);

    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const rows = data.slice(1);

    const addressIndex = headers.indexOf("address");
    const auctionNameIndex = headers.indexOf("auction_name");
    const auctionDateIndex = headers.indexOf("auction_date");

    let rowIndex = -1;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      if (
        row[addressIndex] === rowData.address &&
        row[auctionNameIndex] === rowData.auction_name &&
        row[auctionDateIndex] === rowData.auction_date
      ) {
        rowIndex = i + 1; // Adjust for header
        break;
      }
    }

    if (rowIndex === -1) {
      return ContentService.createTextOutput(
        JSON.stringify({ ok: false, error: "Row not found" })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Delete the row
    sheet.deleteRow(rowIndex + 1); // +1 because rowIndex is 0-based but deleteRow is 1-based

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        message: "Row deleted successfully",
        rowIndex: rowIndex,
        sheet_name: tabName,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    Logger.log(`Error in handleDeleteRow: ${error.toString()}`);
    return ContentService.createTextOutput(
      JSON.stringify({ ok: false, error: error.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const tabName = e.parameter.sheet_name || DEFAULT_TAB_NAME;
    const sheet = ss.getSheetByName(tabName);

    if (!sheet) {
      return ContentService.createTextOutput(
        JSON.stringify({ ok: false, error: `Sheet '${tabName}' not found` })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const data = sheet.getDataRange().getValues();
    const headers = data[0];
    const allRows = data.slice(1);

    const offset = parseInt(e.parameter.offset || "0", 10);
    const limit = parseInt(e.parameter.limit || "100", 10);

    const fromDate = e.parameter.fromDate; // ISO string expected
    const toDate = e.parameter.toDate;

    const dateColumnIndex = headers.indexOf("auction_date"); // or use ingested_at

    let filteredRows = allRows;

    // Filter by date range if provided
    if (fromDate || toDate) {
      filteredRows = filteredRows.filter((row) => {
        const cellDate = new Date(row[dateColumnIndex]);
        if (fromDate && new Date(fromDate) > cellDate) return false;
        if (toDate && new Date(toDate) < cellDate) return false;
        return true;
      });
    }

    const paginatedRows = filteredRows.slice(offset, offset + limit);

    const result = paginatedRows.map((row) => {
      const obj = {};
      headers.forEach((header, i) => {
        obj[header] = row[i] || "";
      });
      return obj;
    });

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        rows: result,
        total: filteredRows.length,
        offset: offset,
        limit: limit,
        returned: result.length,
        sheet_name: tabName,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

// Function to create POTENTIAL_TRADES tab
function createPotentialTradesTab() {
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

// Test function to verify sheet names
function testSheetNames() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheets = ss.getSheets();

  Logger.log("Available sheets:");
  for (let i = 0; i < sheets.length; i++) {
    const sheet = sheets[i];
    Logger.log(`${i + 1}. ${sheet.getName()}`);
  }
}

// Optional test function for POTENTIAL_TRADES
function testPotentialTrades() {
  const testData = {
    auction_name: "Test Auction",
    auction_date: "2025-01-15",
    address: "123 Test Street, London",
    auction_sale: "£500,000",
    lot_number: "123",
    postcode: "SW1A 1AA",
    purchase_price: "",
    sold_date: "",
    owner: "",
    guide_price: "",
    auction_url: "https://example.com/auction/123",
    source_url: "",
    qa_status: "pending_enrichment",
    added_to_potential_trades: new Date().toISOString(),
    ingested_at: new Date().toISOString(),
  };

  const sheet =
    SpreadsheetApp.openById(SHEET_ID).getSheetByName("POTENTIAL_TRADES");
  if (sheet) {
    const result = handleAdd(sheet, [testData], "POTENTIAL_TRADES");
    Logger.log(result.getContent());
  } else {
    Logger.log("POTENTIAL_TRADES sheet not found");
  }
}
