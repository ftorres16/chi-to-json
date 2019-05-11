from setuptools import setup

setup(
    name="chi_to_json",
    version="0.1",
    py_modules=["chi_to_json"],
    include_package_data=True,
    install_requires=["click", "jsonschema"],
    entry_points="""
        [console_scripts]
        chi_to_json=chi_to_json.cli:cli
    """,
)
