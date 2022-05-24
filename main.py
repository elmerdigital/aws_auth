#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import click
from rich import print
from aws_auth.context import Context
from aws_auth.auth import Auth

__version__ = '2.0.1'


def version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


@click.command()
@click.argument('username')
@click.option('-r', '--region', default='eu-central-1', help='Your AWS region')
@click.option('-d', '--duration-in-seconds', default=86400, help='Duration in seconds (expire)')
@click.option('-m', '--aws-meta-account-id', default=lambda: os.environ.get("AWS_AUTH_META_ACCOUNT_ID", ""), help='AWS Meta Account ID')
@click.option('-p', '--aws-target-profile', default="elmerdigital", help='AWS Target profile')
@click.option('-v', '--verbose', is_flag=True, help='Show debug output')
@click.option('--version', is_flag=True, callback=version, expose_value=False, is_eager=True)
def main(username: str, region: str, duration_in_seconds: int, aws_meta_account_id: int, aws_target_profile: str, verbose: bool):
    """
    AWS auth authenticates a user with temporary credentials for a specific amount of time with a MFA token
    :return:
    """

    Context.verbose = verbose

    if Context.verbose:
        print("""[blue]
_______ _  _  _ _______      _______ _     _ _______ _     _
|_____| |  |  | |______      |_____| |     |    |    |_____|
|     | |__|__| ______|      |     | |_____|    |    |     |[/]""")
        print(f"[blue]Initializing AWSAuth with version {__version__}[/]\n")

    auth = Auth(
        username=username,
        region=region,
        duration_in_seconds=duration_in_seconds,
        aws_meta_account_id=aws_meta_account_id,
        aws_target_profile=aws_target_profile,
    )

    auth.authenticate()


if __name__ == "__main__":
    main()
