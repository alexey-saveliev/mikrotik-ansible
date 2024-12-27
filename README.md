# Mikrotik configuration with ansible
## Prepare Ansible host
1. Install Ansible
1. Install  `librouteros`
    ```
    apt install python3-librouteros
    ```
## Prepare Mikrotik device
1. Create group for API access
    ```
    /user group
    add name=ansible policy=\
        read,write,api,!local,!telnet,!ssh,!ftp,!reboot,!policy,!test,!winbox,!password,!web,!sniff,!sensitive,!romon,!rest-api
    ```
1. Create user for API access
    ```
    /user
    add group=ansible name=ansible
    ```
