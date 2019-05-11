import json
import re
import os

import click
import jsonschema


SIM_HEADERS = {
    "TRANSIENT ANALYSIS": "tran",
    "DC TRANSFER CURVES": "dc",
    "AC ANALYSIS": "ac",
}

JSON_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "jsonschema.json")


@click.command()
@click.argument("input", type=click.File("r"))
@click.argument("output", type=click.File("w"))
def cli(input, output):
    """
    This command takes an ELDO simulation output (a .chi file) and saves the data to a JSON file.

    Example:
        [
            {
                "sim_type": "tran",
                "name": "RC circuit simulation",
                "plots": [
                    [
                        {
                            "name": "time",
                            "unit": "s",
                            "data": [1,2,3,4]
                        },
                        {
                            "name": "N_1",
                            "unit": "V",
                            "data": [1.0,2.0,3.0,4.0]
                        }
                    ]
                ]
            }
        ]
    """

    sim_flag = False
    sim_results = []

    all_lines = input.readlines()

    for index, line in enumerate(all_lines):
        if any(sim_header in line for sim_header in SIM_HEADERS):
            sim_flag = True
            sim_type = next(
                sim_type
                for sim_header, sim_type in SIM_HEADERS.items()
                if sim_header in line
            )
            data_flag = False
            print_legends = {}

            try:
                all_sim_types = [sim_result["sim_type"] for sim_result in sim_results]
                sim_index = all_sim_types.index(sim_type)
            except ValueError:
                sim_results.append({"sim_type": sim_type, "plots": []})
                sim_index = -1

        elif sim_flag:
            if line.startswith("Print_Legend"):
                # Gather all the print legends
                legend_regex = re.compile(r"Print_Legend (\d+): (\w+\(\w+(?:\.\w+)?\))")
                header_name, legend = legend_regex.findall(line)[0]
                print_legends[header_name] = legend

            elif "X" in line:
                headers_line = all_lines[index - 1]
                plot = []

                for header in headers_line.split():
                    header = print_legends.get(header, header).lower()
                    trace = {"data": []}

                    headers_regex = re.compile(r"(\w+)\(([\w\.]+)\)")

                    if headers_regex.match(header):
                        trace_type, name = headers_regex.findall(header)[0]
                        trace["name"] = name

                        if trace_type.endswith("db"):
                            trace["unit"] = "db"
                        elif trace_type.endswith("p"):
                            trace["unit"] = "°"
                        elif trace_type.startswith("v"):
                            trace["unit"] = "V"
                        elif trace_type.startswith("i"):
                            trace["unit"] = "A"
                    else:
                        trace["name"] = header

                        if header == "time":
                            trace["unit"] = "s"
                        elif header == "hertz":
                            trace["unit"] = "Hz"

                    plot.append(trace)

                data_flag = True

            elif data_flag and "Y" not in line:
                for index, value in enumerate(line.split()):
                    plot[index]["data"].append(float(value))

            elif data_flag and "Y" in line:
                sim_flag = False
                data_flag = False
                sim_results[sim_index]["plots"].append(plot)

    with open(JSON_SCHEMA_PATH) as f:
        schema = json.load(f)

    try:
        jsonschema.validate(sim_results, schema)
    except jsonschema.ValidationError:
        click.echo("Could not walidate JSON schema", err=True)

    json.dump(sim_results, output)


if __name__ == "__main__":
    cli()
