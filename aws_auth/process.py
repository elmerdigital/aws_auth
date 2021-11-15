#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys

from rich.console import Console
from aws_auth.context import Context


class Process:

    @staticmethod
    def execute(command: str, timeout: int = 30):
        console = Console()
        if Context.verbose:
            console.print(f"Execute command: '{command}'")

        proc = subprocess.Popen(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, error = proc.communicate(timeout=timeout)
            if error:
                console.print(f"[red]{error}[/]")
                sys.exit(1)
            return output.rstrip()
        except subprocess.TimeoutExpired:
            proc.kill()
            console.print(f"[red]Timeout after {timeout} seconds. Please try again.[/]")
            sys.exit(1)
        except KeyboardInterrupt:
            proc.kill()
            console.print(f"\n[red]Canceled by user (KeyboardInterrupt)[/]")
            sys.exit(1)
