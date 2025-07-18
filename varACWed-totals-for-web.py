import sys
import csv

if len(sys.argv) < 2:
    print("❌ Usage: python callsign_formatter.py input.csv")
    sys.exit(1)

input_file = sys.argv[1]
output_file = 'callsignSummary.txt'

entries = []

with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if len(row) >= 2:
            callsign = row[0].strip().upper()
            count = row[1].strip()
            if callsign and count.isdigit():
                entries.append(f"{callsign} ({count})")

# Join entries with comma and space
formatted_output = ', '.join(entries)

# Write to text file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(formatted_output)

print(f"✅ Output saved to {output_file}")
