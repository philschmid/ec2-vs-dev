# CLI: To easily start and stop ec2 instances for remote development. 



will start the ec2 instance with name `infinity-cpu` in the profile `hf-inf` and region `us-east-1`.

### Add new instance

```bash
ec2ssh add cpu --ssh_key_file path/to/file --user ubuntu --profile hf-inf --region us-east-1
```

### Start instance and connect with vs code

```bash
ec2ssh start infinity-cpu
```

### Start instance and connect with vs code to specific remote directory

```bash
ec2ssh start infinity-cpu -d /home/user/remote/directory
```


### Stop ec2 instance

```bash
ec2ssh stop infinity-cpu
```


### connect to running host with vscode

```bash
ec2ssh connect infinity-cpu
```


### List all hosts 

```bash
ec2ssh ls all
```

### List one host 

```bash
ec2ssh ls cpu
```

### Remove instance/host

```bash
ec2ssh remove cpu
```

### Edit instance/host

```bash
ec2ssh edit cpu
```



## TODOS

- [ ] Add AWS specific configurations to the `.ssh/config` file to create a "database", e.g. `aws-profile` and `aws-region`.
- [ ] 