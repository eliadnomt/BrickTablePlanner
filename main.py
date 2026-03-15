import argparse

from generator import generate_model
from topologies import get_topology_names


def main():
    parser = argparse.ArgumentParser(
        description="Generate a LEGO wedding seating chart"
    )
    parser.add_argument("--partner1", default="SOPHIE")
    parser.add_argument("--partner2", default="LAURENT")
    parser.add_argument("--guests", type=int, default=100)
    parser.add_argument(
        "--topology", choices=get_topology_names(), default="two_columns_center_names"
    )
    parser.add_argument("--output", default=None)
    parser.add_argument("--template", default=None)
    args = parser.parse_args()

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
