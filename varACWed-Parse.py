import sys
import re
import csv

if len(sys.argv) < 2:
    print("❌ Please provide the input file path as an argument.")
    print("Expected format")
    print("MM/DD/YYYY")
    print("")
    print("Callsign list")
    print(".")
    print(".")


    sys.exit(1)

input_path = sys.argv[1]

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
except FileNotFoundError:
    print(f"❌ File not found: {input_path}")
    sys.exit(1)

# Split text by date + callsigns chunks
entries = re.split(r'(\d{1,2}/\d{1,2}/\d{4})', raw_text)
entries = [e.strip() for e in entries if e.strip()]

# Extract and flatten
rows = []
for i in range(0, len(entries), 2):
    date = entries[i]
    callsigns = [c.strip() for c in entries[i+1].split(',') if c.strip()]
    for cs in callsigns:
        rows.append([date, cs])

# Output to CSV
with open('checkins.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Date', 'Callsign'])
    writer.writerows(rows)

print(f"✅ Saved {len(rows)} entries to checkins.csv")
