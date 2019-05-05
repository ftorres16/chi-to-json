import json
import re

import click


SIM_HEADERS = {
    "TRANSIENT ANALYSIS": "tran",
    "DC TRANSFER CURVES": "dc",
    "AC ANALYSIS": "ac",
}


@click.command()
@click.argument("input", type=click.File("r"))
@click.argument("output", type=click.File("w"))
def cli(input, output):
    """
    This command takes an ELDO simulation output (a .chi file) and saves the data to a JSON file.
    """

    sim_flag = False
    sim_results = {
        "tran": {"V": {"unit": "V", "plots": []}, "I": {"unit": "A", "plots": []}},
        "dc": {"V": {"unit": "V", "plots": []}, "I": {"unit": "A", "plots": []}},
        "ac": {"Mag": {"unit": "db", "plots": []}, "Phase": {"unit": "°", "plots": []}},
    }

    all_lines = input.readlines()

    for index, line in enumerate(all_lines):
        if any(sim_header in line for sim_header in SIM_HEADERS):
            sim_flag = True
            sim_type = [
                sim_type
                for sim_header, sim_type in SIM_HEADERS.items()
                if sim_header in line
            ][0]
            data_flag = False
            print_legends = {}
            continue

        if sim_flag:
            if line.startswith("Print_Legend"):
                # Gather all the print legends
                legend_regex = r"Print_Legend (\d+): (\w+\(\w+(?:\.\w+)?\))"
                header_name, legend = re.findall(legend_regex, line)[0]
                print_legends[header_name] = legend

            elif "X" in line:
                headers = [
                    print_legends.get(header, header)
                    for header in all_lines[index - 1].split()
                ]
                traces = {header: [] for header in headers}
                data_flag = True

            elif data_flag and "Y" not in line:
                values = line.split()
                for header, value in zip(headers, values):
                    traces[header].append(float(value))

            elif data_flag:
                sim_flag = False
                data_flag = False
                if sim_type == "ac":
                    trace_type = headers[-1].split("(")[0][1:]
                    if trace_type == "DB":
                        trace_type = "Mag"
                    elif trace_type == "P":
                        trace_type = "Phase"
                else:
                    trace_type = headers[-1][0]  # tran
                sim_results[sim_type][trace_type]["plots"].append({"traces": traces})

    json.dump(sim_results, output)


if __name__ == "__main__":
    cli()
