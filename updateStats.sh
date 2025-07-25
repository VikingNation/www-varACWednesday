
echo "Now updating stats for website"

python ./varACWed-Parse.py check-in-history/results.txt
python ./varACWed-totals.py checkins.csv
python ./varACWed-totals-for-web.py checkinTotals.csv
