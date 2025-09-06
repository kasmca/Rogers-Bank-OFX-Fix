import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import os

POST_TIME = "000000"
DEFAULT_TZ = ""

# ---------------------- OFX Parsing & Fixing ---------------------- #
def parse_transactions(ofx_path):
    with open(ofx_path, "r", encoding="utf-8") as f:
        data = f.read()

    if "<BANKTRANLIST>" in data:
        start = data.index("<BANKTRANLIST>")
        end = data.index("</BANKTRANLIST>") + len("</BANKTRANLIST>")
        trans_data = data[start:end]
    else:
        trans_data = data

    txns = []
    for stmnt in trans_data.split("<STMTTRN>")[1:]:
        txn = {}
        txn['type'] = extract_tag(stmnt, "TRNTYPE")
        dtposted = extract_tag(stmnt, "DTPOSTED")
        try:
            dt = datetime.strptime(dtposted[:8], "%Y%m%d") + timedelta(days=1)  # +1 day adjustment
        except Exception:
            dt = datetime.now()
        txn['date'] = dt
        txn['amount'] = float(extract_tag(stmnt, "TRNAMT"))
        txn['fitid'] = generate_fitid(dt, txn['amount'])
        txn['name'] = extract_tag(stmnt, "NAME").strip()
        txns.append(txn)
    return sorted(txns, key=lambda x: x["date"])

def extract_tag(text, tag):
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    if start_tag in text:
        start = text.index(start_tag) + len(start_tag)
        end = text.find(end_tag, start)
        return text[start:end].strip()
    return ""

def generate_fitid(date_obj, amt):
    rnd = int(abs(amt) * 1000) % 1000000
    d1 = date_obj.strftime("%Y-%m-%d")
    d2 = (date_obj + timedelta(days=0)).strftime("%Y-%m-%d")
    return f"{d1}~{d2}~{rnd}"

def sgml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_ofx_sgml(transactions, original_ofx_path):
    header = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:TYPE1
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

"""
    ofx_content = [header, "<OFX>"]

    with open(original_ofx_path, "r", encoding="utf-8") as f:
        raw = f.read()
    signon = extract_section(raw, "<SIGNONMSGSRSV1>", "</SIGNONMSGSRSV1>")
    acct = extract_section(raw, "<CCACCTFROM>", "</CCACCTFROM>")
    curdef = extract_tag(raw, "CURDEF") or "CAD"
    ofx_content.append(f"<SIGNONMSGSRSV1>{signon}</SIGNONMSGSRSV1>")
    ofx_content.append("<CREDITCARDMSGSRSV1>")
    ofx_content.append("<CCSTMTTRNRS>")
    ofx_content.append("<TRNUID>0</TRNUID>")
    ofx_content.append("<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>")
    ofx_content.append("<CCSTMTRS>")
    ofx_content.append(f"<CURDEF>{curdef}</CURDEF>")
    ofx_content.append(f"<CCACCTFROM>{acct}</CCACCTFROM>")
    ofx_content.append("<BANKTRANLIST>")
    if transactions:
        dtstart = min(t["date"] for t in transactions).strftime("%Y%m%d")
        dtend = max(t["date"] for t in transactions).strftime("%Y%m%d")
    else:
        dtstart = dtend = datetime.now().strftime("%Y%m%d")
    ofx_content.append(f"<DTSTART>{dtstart}</DTSTART>")
    ofx_content.append(f"<DTEND>{dtend}</DTEND>")

    for t in transactions:
        name = sgml_escape(t["name"])
        dtp  = t["date"].strftime("%Y%m%d") + POST_TIME + DEFAULT_TZ
        amt  = f"{t['amount']:.2f}"
        ofx_content.append("<STMTTRN>")
        ofx_content.append(f"<TRNTYPE>{t['type']}")
        ofx_content.append(f"<DTPOSTED>{dtp}")
        ofx_content.append(f"<TRNAMT>{amt}")
        ofx_content.append(f"<FITID>{t['fitid']}")
        ofx_content.append(f"<NAME>{name}")
        ofx_content.append("</STMTTRN>")

    ofx_content.append("</BANKTRANLIST>")
    balamt = extract_tag(raw, "BALAMT") or "0.00"
    dta = extract_tag(raw, "DTASOF") or datetime.now().strftime("%Y%m%d%H%M%S")
    ofx_content.append("<LEDGERBAL>")
    ofx_content.append(f"<BALAMT>{balamt}")
    ofx_content.append(f"<DTASOF>{dta}")
    ofx_content.append("</LEDGERBAL>")

    ofx_content.append("</CCSTMTRS>")
    ofx_content.append("</CCSTMTTRNRS>")
    ofx_content.append("</CREDITCARDMSGSRSV1>")
    ofx_content.append("</OFX>")
    return "\r\n".join(ofx_content)

def extract_section(text, start_tag, end_tag):
    if start_tag in text and end_tag in text:
        start = text.index(start_tag) + len(start_tag)
        end = text.index(end_tag)
        return text[start:end]
    return ""

# ---------------------- GUI ---------------------- #
class OFXConverterGUI:
    def __init__(self, root):
        self.root = root
        root.title("OFX Fixer & Converter")
        root.geometry("950x600")

        self.transactions = []

        self.file_frame = tk.Frame(root)
        self.file_frame.pack(pady=10, fill="x")
        tk.Label(self.file_frame, text="OFX File:").pack(side="left", padx=5)
        self.file_entry = tk.Entry(self.file_frame, width=70)
        self.file_entry.pack(side="left", padx=5)
        tk.Button(self.file_frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)
        tk.Button(self.file_frame, text="Help", command=self.show_help).pack(side="left", padx=5)

        # Treeview with scrollbar
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.tree_scroll = tk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("Date", "Name", "Amount", "Type"),
            show="headings",
            yscrollcommand=self.tree_scroll.set,
            selectmode="extended"
        )
        self.tree_scroll.config(command=self.tree.yview)

        self.tree.heading("Date", text="Date")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Type", text="Type")
        self.tree.column("Date", width=100)
        self.tree.column("Name", width=500)
        self.tree.column("Amount", width=100, anchor="e")
        self.tree.column("Type", width=80)
        self.tree.pack(fill="both", expand=True)

        # Alternate row colors
        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f0f0f0')

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=5, fill="x")
        tk.Button(self.button_frame, text="Select All", command=self.select_all).pack(side="left", padx=10)
        tk.Button(self.button_frame, text="Select None", command=self.select_none).pack(side="left", padx=10)
        tk.Button(self.button_frame, text="Convert and Save", command=self.convert_and_save).pack(side="right", padx=10)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("OFX Files", "*.ofx")])
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)
            self.load_transactions(path)

    def load_transactions(self, path):
        self.transactions = parse_transactions(path)
        self.tree.delete(*self.tree.get_children())
        for idx, txn in enumerate(self.transactions):
            amt_display = f"${abs(txn['amount']):,.2f}"
            if txn['amount'] < 0:
                amt_display = f"-{amt_display}"
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            self.tree.insert(
                "",
                "end",
                values=(txn['date'].strftime("%Y-%m-%d"), txn['name'], amt_display, txn['type']),
                tags=(tag,)
            )

        # Auto-adjust Name column width
        self.tree.update_idletasks()
        max_width = max([self.tree.column("Name", width=None)] +
                        [self.tree.bbox(iid, column=1)[2] for iid in self.tree.get_children() if self.tree.bbox(iid, column=1)])
        self.tree.column("Name", width=min(max_width + 20, 600))  # cap width at 600

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def select_none(self):
        self.tree.selection_remove(self.tree.get_children())

    def convert_and_save(self):
        if not self.transactions:
            messagebox.showwarning("No Transactions", "No transactions to convert!")
            return
        path = self.file_entry.get()
        selected_indices = [self.tree.index(iid) for iid in self.tree.selection()]
        selected_txns = [self.transactions[i] for i in selected_indices]
        if not selected_txns:
            messagebox.showwarning("No Selection", "No transactions selected!")
            return
        output_path = os.path.splitext(path)[0] + "_fixed.ofx"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(build_ofx_sgml(selected_txns, path))
        messagebox.showinfo("Success", f"OFX saved to:\n{output_path}")

    def show_help(self):
        msg = (
            "This program is designed to allow users to download OFX files from Roger's Bank "
            "and correct the format so that it can be imported into Microsoft Money.\n\n"
            "The transaction dates are corrected by adding 1 day.\n\n"
            "This program allows the user to select which transactions they want imported. "
            "Use combinations of Shift, CTRL, and select.\n\n"
            "Provide feedback at https://github.com/kasmca/Rogers-Bank-OFX-Fix"
        )
        messagebox.showinfo("Help", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = OFXConverterGUI(root)
    root.mainloop()
