"""Export optional post-study impressions without exposing personal data publicly."""
from __future__ import annotations
import csv
import sys
from pathlib import Path
import database


def main():
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('perceptions.csv')
    fields = ['participant_id', 'protocol_version', 'language', 'group_name',
              'perceived_difference', 'perceived_easiest', 'completed_at']
    with destination.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(database.export_perceptions())
    print(f'Exported optional perception responses to {destination}')


if __name__ == '__main__':
    main()
