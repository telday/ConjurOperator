#!/usr/bin/env python3
import tempfile
import os
import subprocess
import functools

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

@functools.lru_cache
def get_k8s_client():
    k8s_config = kubernetes.config.load_kube_config()
    return kubernetes.client.ApiClient()

@kopf.on.startup()
def prep_namespace(*args, **kwargs):
    print(args)
    print(kwargs)

@kopf.on.cleanup()
def cleanup_namespace(*args, **kwargs):
    print('cleanup')
    print(args, kwargs)

@kopf.on.create('secrets')
def create_fn(body, **kwargs):
    secret_name = kwargs['meta']['name']

    k8s_client = get_k8s_client()

    # Ensure that we have a conjur managed secret before running secrets provider
    if 'conjur-map' in body['data']:
        kubernetes.utils.create_from_yaml(k8s_client, "secrets-provider-job.yaml", verbose=False)

@kopf.on.field('jobs', field='spec.completions')
def cleanup_job(body, **kwargs):
    job_name = body['metadata']['name']
    # TODO should check to make sure job ran successfully here
    if job_name == "secrets-provider":
        k8s_client = get_k8s_client()
        batch_api = kubernetes.client.BatchV1Api(k8s_client)

        res = batch_api.delete_namespaced_job(
            name=job_name,
            namespace="default",
            body=kubernetes.client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5
            ))
        print(res)
