#!/usr/bin/env python3
import tempfile
import os

import kopf
import requests
from conjur_api.models import *
from conjur_api import *
from conjur_api.providers.simple_credentials_provider import SimpleCredentialsProvider

def get_conjur_client():
    conjur_url = 'http://localhost:3000'
    account = 'cucumber'
    username = 'admin'
    password = '3p3585mf8t0b32qxfgy422eecsq15afyz71pqgzr52b21j051be2tm6'

    connection_info = ConjurConnectionInfo(conjur_url, account, None)
    creds = CredentialsData(username=username, password=password, machine=conjur_url)

    provider = SimpleCredentialsProvider()
    provider.save(creds)

    return Client(connection_info, credentials_provider=provider, ssl_verification_mode=SslVerificationMode.INSECURE, async_mode=False)

def get_policy_file(host_name):
    # For some reason the conjur python API doesn't provide faculties for passing a string
    # as policy text so we need to create a tempfile and populate with our policy yaml

    file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    # Could easily add more to this policy file but just keep it simple for this example
    file.write(f'- !host {host_name}\n')
    file.close()
    return file.name

@kopf.on.create('namespaces')
def create_fn(body, **kwargs):
    # Gets the name of the new namespace we just added from the body of the k8s api request
    name = body['metadata']['name']

    # If this isn't a conjur attached namespace quit
    if name[:5] != "conj-":
        return

    client = get_conjur_client()
    policy_file = get_policy_file(name)
    client.login()
    # Just load the policy into root for now
    print(client.load_policy_file('root', policy_file))
    os.unlink(policy_file)
