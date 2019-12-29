#!/usr/bin/env python3
"""Command-line interface to Skrate app."""
from typing import Optional

import click

from skrate import server


@click.group()
@click.option("--debug/--no-debug", default="False", help="Whether to enable debug mode")
def run_skrate(debug: bool) -> None:
    """Run Skrate application for skateboarding progression measurement."""
    server.init_app(debug)


@run_skrate.command()
def database_setup() -> None:
    """Create tables in skrate schema based on app models."""
    server.set_up_database()


@run_skrate.command()
@click.option("-p", "--port", help="Port to listen on", default=5000, type=int)
@click.option("-h", "--host", help="Use 0.0.0.0 for LAN, else localhost only")
def serve(port: int, host: Optional[str]) -> None:
    """Run the main server application."""
    server.app.logger.info("Running skrate web server.")
    server.app.run(port=port, host=host)


if __name__ == '__main__': 
    run_skrate()
