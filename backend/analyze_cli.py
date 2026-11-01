"""Descriptive summaries for the pilot. Not a substitute for preregistered analysis."""
from collections import Counter, defaultdict
from statistics import mean, stdev

import database


def main():
    all_rows = database.export_rows()
    rows = [row for row in all_rows if row["protocol_version"] == database.PROTOCOL_VERSION]
    if len(all_rows) > len(rows):
        print(f"Eldre pilotresultater er holdt utenfor: {len(all_rows) - len(rows)} runder.")
    if not rows:
        print('Ingen runder er fullført ennå.')
        return
    by_condition = defaultdict(list)
    by_person = defaultdict(dict)
    for row in rows:
        by_condition[row['condition']].append(row)
        by_person[row['participant_id']][row['condition']] = row['score']
    complete = sum(len(person) == 3 for person in by_person.values())
    print(f'Antall deltakere med minst én runde: {len(by_person)}')
    print(f'Antall med alle tre rundene: {complete}')
    print('')
    print(f'{"Betingelse":<14} {"Antall":>8} {"Gj.snitt":>10} {"Std.avvik":>12} {"For sent":>10}')
    for condition in database.CONDITIONS:
        entries = by_condition[condition]
        scores = [r['score'] for r in entries]
        print(f'{condition:<14} {len(scores):>8} {mean(scores) if scores else float("nan"):>10.2f} '
              f'{stdev(scores) if len(scores)>1 else 0:>12.2f} '
              f'{sum(int(r["submitted_late"]) for r in entries):>10}')
    complete_rows = [data for data in by_person.values() if len(data) == 3]
    if complete_rows:
        print('\nInnenpersonsforskjeller (bare fullførte deltakere):')
        for a, b in [('ORANGE','BLUE'), ('ORANGE','NEUTRAL'), ('BLUE','NEUTRAL')]:
            differences = [p[a] - p[b] for p in complete_rows]
            print(f'  {a} – {b}: {mean(differences):+.2f} poeng i snitt (n={len(differences)})')
    print('\nMerk: Deskriptiv pilotstatistikk, ikke hypotesetest eller kausalt bevis.')


if __name__ == '__main__':
    main()
