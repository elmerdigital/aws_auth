#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import boto3
import boto3.session
from aws_auth.context import Context
from aws_auth.process import Process
from rich.console import Console
from rich.table import Table, box


class Auth:
    pass

    username: str
    region: str
    duration_in_seconds: int
    aws_meta_account_id: int
    aws_target_profile: str

    device_token_arn: str
    console: Console

    def __init__(
            self,
            username: str,
            region: str,
            duration_in_seconds: int,
            aws_meta_account_id: int,
            aws_target_profile: str,
    ):
        self.username = username
        self.region = region
        self.duration_in_seconds = duration_in_seconds
        self.aws_meta_account_id = aws_meta_account_id
        self.aws_target_profile = aws_target_profile

        self.device_token_arn = f"arn:aws:iam::{self.aws_meta_account_id}:mfa/{self.username}"
        self.console = Console()

        self.debug_used_variables()

    def debug_used_variables(self):
        if not Context.verbose:
            return

        table = Table(box=box.MINIMAL)
        table.add_column("Key", style="", no_wrap=True, min_width=25)
        table.add_column("Value", no_wrap=False, style="")
        table.add_row("Username", self.username)
        table.add_row("Region", self.region)
        table.add_row("Duration in seconds", f"{self.duration_in_seconds}")
        table.add_row("AWS meta account ID", f"{self.aws_meta_account_id}")
        table.add_row("AWS target profile", f"{self.aws_target_profile}")
        table.add_row("Device token ARN", f"{self.device_token_arn}")
        if "OTP_1PASSWORD_ITEM_UUID" in os.environ:
            table.add_row("OTP 1pass item UUID", f"{os.getenv('OTP_1PASSWORD_ITEM_UUID')}")
        self.console.print(table)

    def get_mfa_token(self):
        if "OTP_1PASSWORD_ITEM_UUID" not in os.environ:
            return input("Enter MFA token: ")

        process = Process()
        session_token = process.execute('op signin elmerdigital -r')
        if Context.verbose:
            self.console.print(f"OP Session token: {session_token}")
        otp = process.execute(f'op --session {session_token} get totp {os.getenv("OTP_1PASSWORD_ITEM_UUID")} otp')
        if otp == '':
            self.console.print(f"[red]Get OP otp failed[/]")
            sys.exit(1)
        if Context.verbose:
            self.console.print(f"OP mfa: {otp}")
        return otp

    def get_aws_session_token(self, mfa_token: str):
        session = boto3.session.Session(profile_name='elmerdigital-meta')
        sts_client = session.client('sts')
        try:
            session_token = sts_client.get_session_token(DurationSeconds=self.duration_in_seconds, SerialNumber=self.device_token_arn, TokenCode=mfa_token)
        except Exception as error:
            self.console.print(f"[red]ERROR: {error}[/]")
            sys.exit(1)
        # or instead in a service environment
        # session_token = sts_client.get_session_token(DurationSeconds=args.durationInSeconds)
        if session_token == '':
            self.console.print(f"[red]Get AWS session token failed[/]")
            sys.exit(1)
        return session_token

    def debug_caller(self, session_token: str):
        if not Context.verbose:
            return

        session = boto3.session.Session(profile_name=self.aws_target_profile)
        sts_client = session.client('sts')
        caller_identity = sts_client.get_caller_identity()

        username = caller_identity['Arn'].split('/')[-1]
        table = Table(box=box.MINIMAL)
        table.add_column("AWS Caller Identity", style="", no_wrap=True, min_width=25)
        table.add_column("", no_wrap=False, style="")
        table.add_row("User", f"{username}")
        table.add_row("UserId", f"{caller_identity['UserId']}")
        table.add_row("Profile", f"{self.aws_target_profile}")
        table.add_row("Account", f"{caller_identity['Account']}")
        table.add_row("Identity", f"{caller_identity['Arn']}")
        self.console.print(table)

        self.console.print(f'[green]\nSuccessfully logged in as user {username}[/]')
        self.console.print(f'[yellow]Session token will expire at {session_token["Credentials"]["Expiration"]}[/]')

    def authenticate(self):
        mfa_token = self.get_mfa_token()
        session_token = self.get_aws_session_token(mfa_token)

        os.system(f'aws --profile "{self.aws_target_profile}" configure set region "{self.region}"')
        os.system(f'aws --profile "{self.aws_target_profile}" configure set aws_access_key_id "{session_token["Credentials"]["AccessKeyId"]}"')
        os.system(f'aws --profile "{self.aws_target_profile}" configure set aws_secret_access_key "{session_token["Credentials"]["SecretAccessKey"]}"')
        os.system(f'aws --profile "{self.aws_target_profile}" configure set aws_session_token "{session_token["Credentials"]["SessionToken"]}"')

        self.debug_caller(session_token)
