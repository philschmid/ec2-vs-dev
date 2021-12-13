import sys
import os
import argparse
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
from sshconf import read_ssh_config
from os.path import expanduser
import subprocess
import json


EC2SSH_PATH = Path.home().joinpath(".ec2ssh")


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


def start_stop_or_connect_ec2_instance(action, instance_id):
    ec2 = boto3.resource("ec2")
    instance = ec2.Instance(id=instance_id)
    if action == "start":
        print("starting instance " + instance_id)
        instance.start()
        instance.wait_until_running()
        print(f"Instance is UP & accessible on port 22, the IP address is:  {instance.public_dns_name}")
        return instance.public_dns_name
    elif action == "stop":
        instance.stop()
        return None
    elif action == "connect" and instance.state["Name"] == "running":
        print(f"Instance is UP & accessible on port 22, the IP address is:  { instance.public_dns_name}")
        return instance.public_dns_name


def start_vs_code(remote_name=None, folder=None):
    print(f"starting vs code with remote: {remote_name} in folder {folder}")
    subprocess.run(f"code --remote ssh-remote+{remote_name} {folder}".split(" "))


def read_json_file_if_exists(path):
    if Path(path).is_file():
        with open(path) as f:
            try:
                data = json.load(f)
                return data
            except json.decoder.JSONDecodeError:
                print(f"{path} is not a valid json file")
                return None
    else:
        return None


def read_aws_configuration(host=None):
    ec2ssh_config = read_json_file_if_exists(str(EC2SSH_PATH))
    if ec2ssh_config:
        if host in list(ec2ssh_config.keys()):
            return ec2ssh_config[host]
        else:
            print(f"Host {host} not found in {str(ec2ssh_config)}")
            print("falling back to defaults: `aws region=us-east-1`; `profile=default`")
            return {"region": "us-east-1", "profile": "default"}
    else:
        print(f"{str(ec2ssh_config)} not found")
        print("falling back to defaults: `aws region=us-east-1`; `profile=default`")
        return {"region": "us-east-1", "profile": "default"}


def write_aws_configuration(host=None, region=None, profile=None):
    ec2ssh_config = read_json_file_if_exists(str(EC2SSH_PATH))
    if ec2ssh_config:
        ec2ssh_config[host] = {"region": region, "profile": profile}
        with open(str(EC2SSH_PATH), "w+") as f:
            json.dump(ec2ssh_config, f)
    else:
        with open(str(EC2SSH_PATH), "w+") as f:
            all_hosts = {}
            all_hosts[host] = {"region": region, "profile": profile}
            json.dump(all_hosts, f)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", action="store", choices=["ls", "start", "add", "stop", "connect", "remove", "edit"], type=str
    )
    parser.add_argument(
        "host", type=str, help="hostname of the ec2 instance; When you want to list all hosts, use 'all'"
    )
    parser.add_argument("--config-file", type=str, default=str(Path.home().joinpath(".ssh/config")))
    parser.add_argument("-d", "--target_dir", type=str, default="/home/ubuntu")

    # arguments for adding new config
    parser.add_argument("--profile", type=str, default=None)
    parser.add_argument("--region", type=str, default=None)
    parser.add_argument("--ssh_key_file", type=str, default=str(Path.home().joinpath(".ssh/")))
    parser.add_argument("--hostname", type=str, default="placeholder")
    parser.add_argument("--user", type=str, default="ubuntu")

    args, _ = parser.parse_known_args()
    return args


def main():
    # parse args
    args = parse_args()
    # read config file
    ssh_config = read_ssh_config(args.config_file)
    # print all hosts hosts or only one host
    if args.action == "ls" and args.host == "all":
        for host in ssh_config.hosts():
            print(host)
            print({**ssh_config.host(host), **read_aws_configuration(host)})
        return
    elif args.action == "ls" and args.host != "all":
        print({**ssh_config.host(args.host), **read_aws_configuration(args.host)})

    # writes new ec2ssh config for aws on action add
    if args.action == "add":
        if args.host in list(ssh_config.hosts()):
            raise ValueError(f"Host {args.host} already exists in {args.config_file}")
        ssh_config.add(
            args.host,
            HostName=args.hostname,
            IdentityFile=args.ssh_key_file,
            User=args.user,
            Port=22,
        )
        ssh_config.save()
        write_aws_configuration(host=args.host, region=args.region, profile=args.profile)
        print(f"Added new host {args.host} to {args.config_file}")
        return

    # check if host exists
    remote_host = ssh_config.host(args.host)
    if not remote_host:
        raise ValueError(f'host "{args.host}" not found in config file {args.config_file}')

    remote_host = {**remote_host, **read_aws_configuration(args.host)}

    args.target_dir = Path(args.target_dir)
    if len(str(args.target_dir).split("/")) <= 1:
        args.target_dir = Path("home").joinpath(remote_host["user"]).joinpath(args.target_dir)
    # set target_dir
    if str(args.target_dir).split("/")[1] != remote_host["user"]:
        args.target_dir = Path("home").joinpath(remote_host["user"])

    # check if aws config exists and override defaults
    if remote_host["profile"] and remote_host["region"]:
        os.environ["AWS_DEFAULT_REGION"] = remote_host["region"]
        os.environ["AWS_PROFILE"] = remote_host["profile"]

    #######################
    # start/stop/connect #
    ######################

    if args.action == "start":
        instance_id = get_instance_id(args.host, args.action)
        public_dns_name = start_stop_or_connect_ec2_instance(args.action, instance_id)
        if public_dns_name:
            ssh_config.set(args.host, Hostname=public_dns_name)
            ssh_config.save()
        start_vs_code(args.host, args.target_dir)
        return

    elif args.action == "stop":
        instance_id = get_instance_id(args.host, args.action)
        public_dns_name = start_stop_or_connect_ec2_instance(args.action, instance_id)
        return

    elif args.action == "connect":
        instance_id = get_instance_id(args.host, args.action)
        public_dns_name = start_stop_or_connect_ec2_instance(args.action, instance_id)
        if public_dns_name:
            ssh_config.set(args.host, Hostname=public_dns_name)
            ssh_config.save()
        start_vs_code(args.host, args.target_dir)
        return


if __name__ == "__main__":
    main()
