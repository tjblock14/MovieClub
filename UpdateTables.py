import xlwings as xw
import os

FILENAME = r"C:\Users\trevo\OneDrive\Revamped Trev and Taylor Movie Club.xlsx"
CACHED_TITLES = "known_movie_titles.txt"

TNT_SHEET_NAME = "Movie Club - TnT"
MN_SHEET_NAME = "Movie Club - MN"
TNT_TABLE_NAME = "tnt_table"  # Update with actual Excel table name
MN_TABLE_NAME = "mn_table"    # Update with actual Excel table name

def load_known_titles():
    if os.path.exists(CACHED_TITLES):
        with open(CACHED_TITLES, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_known_titles(titles):
    with open(CACHED_TITLES, "w") as f:
        for title in sorted(titles):
            f.write(f"{title}\n")

def get_titles_from_table(table):
    titles = set()
    for row in table.DataBodyRange.Value:
        if row and row[0]:
            titles.add(row[0])
    return titles

def build_new_row(row, keep=4, total=9):
    return list(row[:keep]) + [""] * (total - keep)

def insert_into_first_empty_row(table, new_row):
    # Try to reuse a blank row
    for list_row in table.ListRows:
        title_cell = list_row.Range.Cells(1, 1)
        if not title_cell.Value:
            for i, val in enumerate(new_row):
                list_row.Range.Cells(1, i + 1).Value = val
            return
    # Otherwise add new row
    table.ListRows.Add()
    last_row = table.ListRows(table.ListRows.Count).Range
    for i, val in enumerate(new_row):
        last_row.Cells(1, i + 1).Value = val

def main():
    wb = xw.Book(FILENAME)
    tnt_sheet = wb.sheets[TNT_SHEET_NAME]
    mn_sheet = wb.sheets[MN_SHEET_NAME]

    tnt_table = tnt_sheet.api.ListObjects(TNT_TABLE_NAME)
    mn_table = mn_sheet.api.ListObjects(MN_TABLE_NAME)

    known_titles = load_known_titles()

    tnt_data = tnt_table.DataBodyRange.Value
    mn_data = mn_table.DataBodyRange.Value

    tnt_titles = get_titles_from_table(tnt_table)
    mn_titles = get_titles_from_table(mn_table)

    tnt_titles_added = tnt_titles - mn_titles - known_titles
    mn_titles_added = mn_titles - tnt_titles - known_titles

    for row in tnt_data:
        if row and row[0] in tnt_titles_added:
            new_row = build_new_row(row)
            insert_into_first_empty_row(mn_table, new_row)

    for row in mn_data:
        if row and row[0] in mn_titles_added:
            new_row = build_new_row(row)
            insert_into_first_empty_row(tnt_table, new_row)

    if tnt_titles_added or mn_titles_added:
        all_titles = tnt_titles.union(mn_titles)
        save_known_titles(all_titles)
        print("✅ Synced new titles between sheets:")
        if tnt_titles_added:
            print(" - From TnT to MN:", tnt_titles_added)
        if mn_titles_added:
            print(" - From MN to TnT:", mn_titles_added)
    else:
        print("✅ No new titles to sync.")

    wb.save()
    wb.close()

if __name__ == "__main__":
    main()
