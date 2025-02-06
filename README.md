# Mikrotik configuration with ansible
## Prepare Ansible host
1. Install Ansible
1. Install  `librouteros`
    ```
    apt install python3-librouteros
    ```
## Prepare Mikrotik device
1. Build and apply new Mikrotik config with [Mikrotik basic config generator](https://alexey-saveliev.github.io/mikrotik-ansible/)    
1. Create user for API access
    ```
    /user add group=ansible name=ansible
    ```