from collections import defaultdict
from datetime import datetime

# Input and output paths
input_file = "./check-in-history/results.txt"
csv_output = "metrics_new_users.csv"
txt_output = "new_users_by_date.txt"

# Step 1: Parse file into date -> callsigns dictionary
date_to_callsigns = {}
with open(input_file, "r") as f:
    lines = [line.strip() for line in f if line.strip()]  # Remove blank lines

i = 0
while i < len(lines) - 1:
    date_line = lines[i]
    calls_line = lines[i + 1]
    i += 2

    try:
        # Validate date format
        parsed_date = datetime.strptime(date_line, "%m/%d/%Y")
        callsigns = [call.strip() for call in calls_line.split(",") if call.strip()]
        date_to_callsigns[date_line] = callsigns
    except ValueError:
        print(f"Skipping invalid date line: {date_line}")
        continue

# Step 2: Sort dates chronologically
sorted_dates = sorted(date_to_callsigns.keys(), key=lambda d: datetime.strptime(d, "%m/%d/%Y"))

# Step 3: Track first-time callsigns
seen_callsigns = set()
new_users_by_date = {}

for date in sorted_dates:
    new_callsigns = []
    for call in date_to_callsigns[date]:
        if call not in seen_callsigns:
            seen_callsigns.add(call)
            new_callsigns.append(call)
    new_users_by_date[date] = new_callsigns

# Step 4: Write CSV output
with open(csv_output, "w") as f_csv:
    f_csv.write("date,count\n")
    for date in sorted_dates:
        f_csv.write(f"{date},{len(new_users_by_date[date])}\n")

# Step 5: Write TXT output
with open(txt_output, "w") as f_txt:
    for date in sorted_dates:
        f_txt.write(f"{date}\n")
        f_txt.write(", ".join(new_users_by_date[date]) + "\n\n")

