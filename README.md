# Rogers-Bank-OFX-Fix
2025 09 Rogers bank redid their website and broke OFX importing into MS Money.  This is a fix.

After Rogers Bank updated their website, OFX files are no longer valid imports for Microsoft Money.  This program converts the downloadable ofx files into a version compatible with Microsoft Money.

Additionally, Rogers Bank limited downloads to just complete monthly statements with no ability to select date ranges or "since last downloaded".  I added a feature to select all, select none or select specific sets of transactions.  Use a combination of Shift, CTRL and select to only convert and import the transactions you want.

Finally, even prior to this update, previous downloaded transaction dates were incorrectly set to 1 day earlier.  This program will correct that.

I have logged a ticket with Rogers Bank at 1-855-775-2265 to ask them address this issue.  I encourage you to do the same, as this program is designed to just be a temporary fix.

Here is a chrome extension that brings back the functionality to download current transactions.  It can be used in conjunction with the Rogers-Bank-OFX-fix program: https://github.com/mdanics/rogers-bank-current-transactions-extension

## Download
[![GitHub all releases](https://img.shields.io/github/downloads/kasmca/Rogers-Bank-OFX-Fix/total?label=Downloads&cacheSeconds=60)](https://github.com/kasmca/Rogers-Bank-OFX-Fix/releases/latest)

👉 [Download the latest version here](https://github.com/kasmca/Rogers-Bank-OFX-Fix/releases/latest)

Additional Details:

PURPOSE
- This program is designed to correct Rogers Bank OFX files so that they can be successfully imported into Microsoft Money. Rogers provides OFX files in a newer XML-style format (OFX 2.x), but Microsoft Money only supports the older SGML-based format (OFX 1.02).
- Without correction, Microsoft Money will reject or fail to read the file.

ISSUES WITH THE ORIGINAL ROGERS BANK OFX
- Wrong header format – Rogers uses an XML-style header, while Microsoft Money requires an SGML-style header (e.g., OFXHEADER:100, VERSION:102).
- Missing or inconsistent tags – Certain elements (like <DTEND>) were not properly closed, which breaks Money’s parser.
- FITID format – Transaction IDs provided by Rogers were not unique or consistent. Microsoft Money requires unique IDs to avoid duplicates.
- Transaction dates – The dates in Rogers’ OFX were off by one day compared to the actual statement.
- Format mismatch – Rogers exports OFX 2.x XML, while Microsoft Money only supports OFX 1.02 SGML.

FIXES APPLIED BY THIS PROGRAM
- Converts the header to OFX 1.02 SGML format.
- Ensures all tags are properly opened and closed.
- Reformats FITID values into a consistent, unique format.
- Adjusts all transaction dates by +1 day so they match correctly in Microsoft Money.
- Outputs a valid OFX file that Microsoft Money accepts.

HOW TO USE
- Run the program (convert_ofx_gui.exe).
- Click Browse to select your Rogers Bank OFX file.
- Review transactions (you can select/deselect which ones to include).
- Click Convert and Save.
- A new file will be created in the same folder with _fixed added to the filename.
- Import the _fixed.ofx file into Microsoft Money.

NOTES
- Highlight transactions to choose which ones to export. Use Ctrl and Shift for multi-selection.
- Select All and Select None buttons make it easy to manage selections.
- Dates are automatically corrected by +1 day.
