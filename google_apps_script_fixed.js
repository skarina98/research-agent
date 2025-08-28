/**
 * Google Apps Script for Property Data Management
 * Fixed version with working update_row functionality
 */

// Configuration
const SHEET_ID = "1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q";
const SHARED_TOKEN =
  "3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb";

// Sheet names
const SHEET_NAMES = {
  AUCTIONS_MASTER: "AUCTIONS_MASTER",
  POTENTIAL_TRADES: "POTENTIAL_TRADES",
};

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    // Validate token
    if (data.token !== SHARED_TOKEN) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: "Invalid token",
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const action = data.action;

    switch (action) {
      case "add":
        return handleAdd(data);
      case "update":
        return handleUpdate(data);
      case "read":
        return handleRead(data);
      case "update_row":
        return handleUpdateRow(data);
      case "delete_row":
        return handleDeleteRow(data);
      default:
        return ContentService.createTextOutput(
          JSON.stringify({
            ok: false,
            error: "Unknown action: " + action,
          })
        ).setMimeType(ContentService.MimeType.JSON);
    }
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: "Error processing request: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleAdd(data) {
  try {
    const sheet = SpreadsheetApp.openById(SHEET_ID);
    const rows = data.rows || [];

    let totalAdded = 0;
    let totalSkipped = 0;
    let totalUpdated = 0;

    for (const row of rows) {
      try {
        // Determine which sheet to use based on transaction type and purchase price
        const transactionType =
          row.transaction_type || "estate agent to auction";
        const hasPurchasePrice =
          row.purchase_price && row.purchase_price.trim() !== "";

        // Route to AUCTIONS_MASTER if:
        // 1. Transaction type is "auction to auction" (has relevant auction entries), OR
        // 2. Has purchase price (property prices found)
        const targetSheetName =
          transactionType === "auction to auction" || hasPurchasePrice
            ? SHEET_NAMES.AUCTIONS_MASTER
            : SHEET_NAMES.POTENTIAL_TRADES;
        const targetSheet = sheet.getSheetByName(targetSheetName);

        if (!targetSheet) {
          console.log(`Sheet ${targetSheetName} not found, skipping row`);
          totalSkipped++;
          continue;
        }

        // Get headers and row data for the specific sheet
        const headers = getHeadersForSheet(targetSheetName);
        const rowData = getRowDataForSheet(row, targetSheetName);

        // Check if this property already exists (by lot number, auction name, and auction date)
        const existingRow = findExistingRow(targetSheet, row);

        if (existingRow) {
          console.log(
            `Property already exists in ${targetSheetName}: ${row.address} - Updating existing row`
          );
          try {
            // Update the existing row instead of skipping
            const fieldsToUpdate = getFieldsToUpdate(row, targetSheetName);
            updateRow(
              targetSheet,
              existingRow,
              fieldsToUpdate,
              targetSheetName
            );
            totalUpdated++;
            console.log(
              `Successfully updated row ${existingRow} in ${targetSheetName}`
            );
          } catch (updateError) {
            console.log(`Error updating row: ${updateError.message}`);
            totalSkipped++;
          }
          continue;
        }

        // Add the new row
        targetSheet.appendRow(rowData);
        totalAdded++;
        console.log(`Added to ${targetSheetName}: ${row.address}`);
        // Note: Both "estate agent to auction" and "auction opportunity" go to POTENTIAL_TRADES
      } catch (error) {
        console.log(`Error processing row: ${error.message}`);
        totalSkipped++;
      }
    }

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        message: `Added ${totalAdded} properties, updated ${totalUpdated}, skipped ${totalSkipped}`,
        added: totalAdded,
        updated: totalUpdated,
        skipped: totalSkipped,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: "Error adding data: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleUpdate(data) {
  try {
    const sheet = SpreadsheetApp.openById(SHEET_ID);
    const rows = data.rows || [];

    let totalUpdated = 0;
    let totalSkipped = 0;

    for (const row of rows) {
      try {
        // Determine which sheet to use based on transaction type and purchase price
        const transactionType =
          row.transaction_type || "estate agent to auction";
        const hasPurchasePrice =
          row.purchase_price && row.purchase_price.trim() !== "";

        // Route to AUCTIONS_MASTER if:
        // 1. Transaction type is "auction to auction" (has relevant auction entries), OR
        // 2. Has purchase price (property prices found)
        const targetSheetName =
          transactionType === "auction to auction" || hasPurchasePrice
            ? SHEET_NAMES.AUCTIONS_MASTER
            : SHEET_NAMES.POTENTIAL_TRADES;
        const targetSheet = sheet.getSheetByName(targetSheetName);

        if (!targetSheet) {
          console.log(`Sheet ${targetSheetName} not found, skipping row`);
          totalSkipped++;
          continue;
        }

        // Find existing row
        const existingRow = findExistingRow(targetSheet, row);

        if (!existingRow) {
          console.log(
            `Property not found in ${targetSheetName}: ${row.address}`
          );
          totalSkipped++;
          continue;
        }

        // Update the row
        const fieldsToUpdate = getFieldsToUpdate(row, targetSheetName);
        updateRow(targetSheet, existingRow, fieldsToUpdate, targetSheetName);

        totalUpdated++;
        console.log(`Updated in ${targetSheetName}: ${row.address}`);
        // Note: Properties with purchase prices go to AUCTIONS_MASTER, others go to POTENTIAL_TRADES
      } catch (error) {
        console.log(`Error processing row: ${error.message}`);
        totalSkipped++;
      }
    }

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        message: `Updated ${totalUpdated} properties, skipped ${totalSkipped}`,
        updated: totalUpdated,
        skipped: totalSkipped,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: "Error updating data: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleRead(data) {
  try {
    // Determine which sheet to read from
    const sheetName = data.sheet_name || SHEET_NAMES.AUCTIONS_MASTER;
    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(sheetName);

    if (!sheet) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: `Sheet ${sheetName} not found`,
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const dataRange = sheet.getDataRange();
    const values = dataRange.getValues();

    if (values.length <= 1) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: true,
          rows: [],
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const headers = values[0];
    const rows = [];

    for (let i = 1; i < values.length; i++) {
      const row = {};
      for (let j = 0; j < headers.length; j++) {
        row[headers[j]] = values[i][j];
      }
      rows.push(row);
    }

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        rows: rows,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: "Error reading data: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleUpdateRow(data) {
  try {
    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(
      SHEET_NAMES.AUCTIONS_MASTER
    );

    if (!sheet) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: "Sheet not found",
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const rowIndex = data.row_index;
    const rowData = data.row_data;

    if (rowIndex === undefined || rowIndex === null) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: "row_index is required",
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    if (!rowData) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: "row_data is required",
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Calculate the actual row number in the sheet (rowIndex is 0-based, sheet rows are 1-based)
    // Add 2 because: +1 for 1-based indexing, +1 for header row
    const actualRowNumber = rowIndex + 2;

    // Check if the row exists
    const lastRow = sheet.getLastRow();
    if (actualRowNumber > lastRow) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: `Row not found: row_index ${rowIndex} (sheet row ${actualRowNumber}) exceeds last row ${lastRow}`,
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Get the headers to map the data correctly
    const headers = sheet
      .getRange(1, 1, 1, sheet.getLastColumn())
      .getValues()[0];

    // Create the row data array in the correct order
    const rowArray = [];
    for (const header of headers) {
      rowArray.push(rowData[header] || "");
    }

    // Update the row
    const range = sheet.getRange(actualRowNumber, 1, 1, rowArray.length);
    range.setValues([rowArray]);

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        message: `Updated row ${actualRowNumber} (index ${rowIndex})`,
        updated_row: actualRowNumber,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: "Error updating row: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function handleDeleteRow(data) {
  try {
    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(
      SHEET_NAMES.AUCTIONS_MASTER
    );

    if (!sheet) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: "Sheet not found",
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const rowIndex = data.row_index;

    if (rowIndex === undefined || rowIndex === null) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: "row_index is required",
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Calculate the actual row number in the sheet (rowIndex is 0-based, sheet rows are 1-based)
    // Add 2 because: +1 for 1-based indexing, +1 for header row
    const actualRowToDelete = rowIndex + 2;

    // Check if the row exists
    const lastRow = sheet.getLastRow();
    if (actualRowToDelete > lastRow) {
      return ContentService.createTextOutput(
        JSON.stringify({
          ok: false,
          error: `Row not found: row_index ${rowIndex} (sheet row ${actualRowToDelete}) exceeds last row ${lastRow}`,
        })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    // Delete the row
    sheet.deleteRow(actualRowToDelete);

    return ContentService.createTextOutput(
      JSON.stringify({
        ok: true,
        message: `Deleted row ${actualRowToDelete} (index ${rowIndex})`,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        ok: false,
        error: "Error deleting row: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

// Helper function for case-insensitive string comparison
function normalizeString(str) {
  if (typeof str !== "string") return "";
  return str.toLowerCase().trim();
}

function getHeadersForSheet(sheetName) {
  // Define headers for each sheet in the correct order
  if (sheetName === SHEET_NAMES.AUCTIONS_MASTER) {
    return [
      "auction_name",
      "auction_date",
      "address",
      "auction_sale",
      "profit", // NEW FIELD: Calculated profit
      "lot_number",
      "postcode",
      "purchase_price",
      "sold_date",
      "transaction_type",
      "eig_street_history_url",
      "guide_price",
      "source_url",
      "auction_url",
      "qa_status",
      "ingested_at",
    ];
  } else if (sheetName === SHEET_NAMES.POTENTIAL_TRADES) {
    return [
      "auction_name",
      "auction_date",
      "address",
      "auction_sale",
      "profit", // NEW FIELD: Calculated profit
      "lot_number",
      "postcode",
      "purchase_price",
      "sold_date",
      "transaction_type",
      "eig_street_history_url",
      "guide_price",
      "source_url",
      "auction_url",
      "added_to_potential_trades",
      "qa_status",
      "ingested_at",
    ];
  }
  return [];
}

function getRowDataForSheet(row, sheetName) {
  const headers = getHeadersForSheet(sheetName);
  const rowData = [];

  for (const header of headers) {
    if (
      header === "added_to_potential_trades" &&
      sheetName === SHEET_NAMES.POTENTIAL_TRADES
    ) {
      rowData.push("Yes"); // Default value for new entries
    } else {
      rowData.push(row[header] || "");
    }
  }

  return rowData;
}

function findExistingRow(sheet, row) {
  const data = sheet.getDataRange().getValues();
  const headers = data[0];

  const lotNumberCol = headers.indexOf("lot_number");
  const auctionNameCol = headers.indexOf("auction_name");
  const auctionDateCol = headers.indexOf("auction_date");

  if (lotNumberCol === -1 || auctionNameCol === -1 || auctionDateCol === -1) {
    return null;
  }

  const lotNumber = row.lot_number;
  const auctionName = row.auction_name;
  const auctionDate = row.auction_date;

  for (let i = 1; i < data.length; i++) {
    if (
      data[i][lotNumberCol] === lotNumber &&
      data[i][auctionNameCol] === auctionName &&
      data[i][auctionDateCol] === auctionDate
    ) {
      return i + 1; // Return 1-based row number
    }
  }

  return null;
}

function getFieldsToUpdate(row, sheetName) {
  const headers = getHeadersForSheet(sheetName);
  const fieldsToUpdate = {};

  for (const header of headers) {
    if (row.hasOwnProperty(header)) {
      fieldsToUpdate[header] = row[header];
    }
  }

  return fieldsToUpdate;
}

function updateRow(sheet, rowNum, fieldsToUpdate, sheetName) {
  const headers = getHeadersForSheet(sheetName);

  for (const [field, value] of Object.entries(fieldsToUpdate)) {
    const colIndex = headers.indexOf(field);
    if (colIndex !== -1) {
      sheet.getRange(rowNum, colIndex + 1).setValue(value);
    }
  }
}
