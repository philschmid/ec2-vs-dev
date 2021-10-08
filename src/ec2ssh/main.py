import sys
import os
import argparse
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
from sshconf import read_ssh_config
from os.path import expanduser


def get_instance_id(name, action):
    # Connect to EC2
    ec2 = boto3.resource("ec2")

    target_instance = list(ec2.instances.filter(Filters=[{"Name": "tag:Name", "Values": [name]}]))[0]
    if action == "stop":
        assert (
            target_instance.state["Name"] == "running"
        ), f"Instance is not running, can't be stopped, current state is {target_instance.state['Name']}"
    if action == "start":
        assert (
            target_instance.state["Name"] == "stopped"
        ), f"Instance is not stopped, can't be started, current state is {target_instance.state['Name']}"
    return target_instance.instance_id


def start_or_stop_ec2_instance(action, instance_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(id=instance_id)

    if action == "start":
        print("starting instance " + instance_id)
        instance.start()
        instance.wait_until_running()
        print(f"Instance is UP & accessible on port 22, the IP address is:  {instance.public_dns_name}")
        return instance.public_dns_name
    else:
        instance.stop()
        return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", action="store", choices=["ls", "start", "add", "stop"], type=str)
    parser.add_argument("--ec2-name", type=str, default="infinity-gpu-cuda-11.4")
    parser.add_argument("--config-file", type=str, default=str(Path.home().joinpath(".ssh/config")))
    parser.add_argument("--profile", type=str, default="hf-sm")
    parser.add_argument("--region", type=str, default="eu-west-1")

    # arguments for adding new config
    parser.add_argument("--ssh_key_file", type=str, default=str(Path.home().joinpath(".ssh/")))
    parser.add_argument("--hostname", type=str, default="placeholder")
    parser.add_argument("--user", type=str, default="ubuntu")

    args, _ = parser.parse_known_args()
    return args


def main():
    args = parse_args()
    os.environ["AWS_DEFAULT_REGION"] = args.region
    os.environ["AWS_PROFILE"] = args.profile
    ssh_config = read_ssh_config(args.config_file)

    print(list(ssh_config.hosts()))
    print(args.ec2_name in list(ssh_config.hosts()))

    if args.action == "ls":
        print("hosts", ssh_config.hosts())

    elif args.action == "add":
        if args.ec2_name in list(ssh_config.hosts()):
            raise ValueError(f"Host {args.ec2_name} already exists in {args.config_file}")
        ssh_config.add(args.ec2_name, HostName=args.hostname, IdentityFile=args.ssh_key_file, User=args.user, Port=22)
        ssh_config.save()
        print(f"Added new host {args.ec2_name} to {args.config_file}")

    elif args.action == "start":
        instance_id = get_instance_id(args.ec2_name, args.action)
        public_dns_name = start_or_stop_ec2_instance(args.action, instance_id)
        if public_dns_name:
            ssh_config.set(args.ec2_name, Hostname=public_dns_name)
            ssh_config.save()

    elif args.action == "stop":
        instance_id = get_instance_id(args.ec2_name, args.action)
        public_dns_name = start_or_stop_ec2_instance(args.action, instance_id)


if __name__ == "__main__":
    main()
