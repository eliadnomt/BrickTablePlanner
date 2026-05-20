import argparse
import sys

from generator import generate_model
from guests import GuestListError, load_guest_list
from seating import optimize_seating
from topologies import get_topology_max_tables, get_topology_names


def _format_guest(guest):
    return f"{guest.name} [{'/'.join(guest.languages)}]"


def _run_with_guest_list(args):
    try:
        guests = load_guest_list(args.guest_list)
    except GuestListError as exc:
        print(f"Error reading guest list: {exc}", file=sys.stderr)
        return 1

    max_tables = get_topology_max_tables(args.topology)
    seating = optimize_seating(guests, max_tables=max_tables)

    if not seating.feasible:
        print(
            "Cannot produce a valid seating chart for this guest list. "
            "The following placements violate the seating constraints:",
            file=sys.stderr,
        )
        for violation in seating.violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    table_count = max(seating.table_count, 1)
    guest_count = table_count * 10  # the LEGO model uses 10 seats per table

    result = generate_model(
        partner1=args.partner1,
        partner2=args.partner2,
        guest_count=guest_count,
        topology_key=args.topology,
        output_path=args.output,
        template_path=args.template,
    )

    print(f"Generated: {result['output_path']}")
    print(f"Guests: {len(guests)}")
    print(f"Tables: {result['table_count']}")
    print(f"Grid: {result['grid_cols']} x {result['grid_rows']} baseplates")
    print("Optimised seating plan:")
    for index, table in enumerate(seating.tables, start=1):
        print(f"  Table {index}: " + ", ".join(_format_guest(g) for g in table))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate a LEGO wedding seating chart"
    )
    parser.add_argument("--partner1", default="SOPHIE")
    parser.add_argument("--partner2", default="LAURENT")
    parser.add_argument("--guests", type=int, default=100)
    parser.add_argument(
        "--guest-list",
        default=None,
        help=(
            "Path to a guest list spreadsheet (.csv or .xlsx) with columns "
            "first_name, languages, related_guests. When given, the seating "
            "optimiser decides the table count and arrangement and --guests is "
            "ignored."
        ),
    )
    parser.add_argument(
        "--topology", choices=get_topology_names(), default="two_columns_center_names"
    )
    parser.add_argument("--output", default=None)
    parser.add_argument("--template", default=None)
    args = parser.parse_args()

    if args.guest_list:
        sys.exit(_run_with_guest_list(args))

    result = generate_model(
        partner1=args.partner1,
        partner2=args.partner2,
        guest_count=args.guests,
        topology_key=args.topology,
        output_path=args.output,
        template_path=args.template,
    )

    print(f"Generated: {result['output_path']}")
    print(f"Tables: {result['table_count']}")
    print(f"Grid: {result['grid_cols']} x {result['grid_rows']} baseplates")


if __name__ == "__main__":
    main()
