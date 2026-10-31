"""Export study results locally without exposing an HTTP admin endpoint."""
import csv
import sys
from pathlib import Path
import database


def main():
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('study_results.csv')
    rows = database.export_rows()
    headers = ['participant_id','language','age_band','gender','protocol_version','group_name',
               'list_order','created_at','round_index','condition','list_id',
               'answers','score','max_score','recall_seconds','hidden_count',
               'submitted_late','completed_at']
    with destination.open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Saved {len(rows)} results to {destination}')


if __name__ == '__main__':
    main()
