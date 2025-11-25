import csv

# Input and output file paths
txt_file = "UD.txt"
csv_file = "UD.csv"

with open(txt_file, "r", encoding="utf-8") as infile, \
     open(csv_file, "w", newline="", encoding="utf-8") as outfile:

    writer = csv.writer(outfile)

    for line in infile:
        # Split by whitespace OR comma — adjust if needed
        row = line.strip().split(",")

        writer.writerow(row)

print("Conversion complete: UD.csv created.")
