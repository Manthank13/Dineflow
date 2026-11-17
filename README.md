# DINEFLOW
### Restaurant Billing Management System

DINEFLOW is a local desktop point-of-sale and billing project built with Python and Tkinter. It helps a restaurant operator browse a sample menu, assemble an order, calculate GST and discounts, and produce a readable text receipt.

## Features

- Premium light dashboard with a live clock and order number.
- Searchable menu and seven working category filters.
- Add, edit, and delete menu dishes in the built-in menu manager.
- Attach local food photos to menu items; images are copied into `assets/` and menu changes persist in `menu.json`.
- Add dishes to an order; repeated additions increase quantity.
- Select an order row to increase, decrease, or remove it.
- Live subtotal, 5% GST, percentage discount, and grand total.
- Bill preview window and `.txt` receipt export.
- About window with the project team details.
- Graceful operation without food image assets; menu cards use emoji illustrations.

## Technologies

Python 3, Tkinter, ttk, `datetime`, `pathlib`, JSON, and standard-library `messagebox` and `filedialog`. Pillow is optional and enables JPEG/WebP resizing; without it, Tkinter can display PNG and GIF, with emoji placeholders for unsupported or missing images.

## Installation and execution

1. Install Python 3 with Tk support (Tkinter is included with most standard Python desktop installations).
2. Open a terminal in this folder.
3. Run:

   ```bash
   python main.py
   ```

Receipt exports default to the `receipts/` folder. The Save Receipt dialog opens there; choose a path and filename to save.

## Team

- Srishti — Registration Number: RA2511030010319
- Radhika — Registration Number: RA2511030010348
- Manthan — Registration Number: RA2511030010333

## Project layout

- `main.py` — complete runnable application.
- `assets/` — reserved for optional local images.
- `menu.json` — created on first menu change to store custom dishes and edits.
- `receipts/` — default destination for receipt exports.
- `VIVA_PREPARATION.md` — code walkthrough and practice questions.
