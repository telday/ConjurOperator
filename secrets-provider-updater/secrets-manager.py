#!/usr/bin/env python3
import tempfile
import os
import subprocess

import kubernetes
import yaml
import kopf
import requests
from conjur_api.models import *
from conjur_api import *
from conjur_api.providers.simple_credentials_provider import SimpleCredentialsProvider

def get_conjur_client():
    conjur_url = 'https://localhost'
    account = 'default'
    username = 'admin'
    password = '3p3585mf8t0b32qxfgy422eecsq15afyz71pqgzr52b21j051be2tm6'

    connection_info = ConjurConnectionInfo(conjur_url, account, None)
    creds = CredentialsData(username=username, password=password, machine=conjur_url)

    provider = SimpleCredentialsProvider()
    provider.save(creds)

    return Client(connection_info, credentials_provider=provider, ssl_verification_mode=SslVerificationMode.INSECURE, async_mode=False)

def setup_helm_file(secret_name):
    # Get the helm template
    with open('secrets-provider.yaml') as helm_file:
        data = yaml.load(helm_file, Loader=yaml.Loader)

    # Read in the cert file
    with open('conjur-cert.pem') as cert_file:
        cert = cert_file.read()

    data['environment']['conjur']['sslCertificate']['value'] = cert
    data['environment']['k8sSecrets'] = [secret_name]

    file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    # Could easily add more to this policy file but just keep it simple for this example
    file.write(yaml.dump(data))
    file.close()

    return file.name

@kopf.on.create('secrets')
def create_fn(body, **kwargs):
    secret_name = kwargs['meta']['name']

    k8s_config = kubernetes.config.load_kube_config()
    k8s_client = kubernetes.client.ApiClient()

    # Ensure that we have a conjur managed secret before running secrets provider
    if 'conjur-map' in body['data']:
        #sp_config_file = setup_helm_file(secret_name)
        #subprocess.run(['helm', 'upgrade', 'secrets-provider', 'secrets-provider', '--repo', 'https://cyberark.github.io/helm-charts', '-f', sp_config_file, '--reuse-values'])
        #os.unlink(sp_config_file)
        ret = kubernetes.utils.create_from_yaml(k8s_client, "secrets-provider-k8s.yaml", verbose=False)
        print(type(ret[0]))
