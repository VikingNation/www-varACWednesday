import sys
import csv
from collections import Counter

if len(sys.argv) < 2:
    print("❌ Usage: python checkin_totals.py input.csv")
    sys.exit(1)

input_file = sys.argv[1]
callsign_counter = Counter()

# Read and count callsigns
with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if len(row) >= 2:
            callsign = row[1].strip().upper()
            if callsign:
                callsign_counter[callsign] += 1

# Sort alphabetically
sorted_callsigns = sorted(callsign_counter.items(), key=lambda x: x[0])

# Write to CSV
with open('checkinTotals.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Callsign', 'Total Check-ins'])
    writer.writerows(sorted_callsigns)

print(f"✅ Output sorted alphabetically to checkinTotals.csv")
