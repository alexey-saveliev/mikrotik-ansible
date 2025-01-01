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
1. Create bridge named `bridge`
    ```
    /interface bridge
    add name=bridge priority=0x2000 pvid=100
    /interface/bridge/port
    add bridge=bridge interface=sfp-sfpplus3
    add bridge=bridge interface=sfp-sfpplus4

    ```
1. Create VLAN
    ```
    /interface bridge vlan
    add bridge=bridge comment=Management tagged=sfp-sfpplus3,sfp-sfpplus4 vlan-ids=100
    /interface vlan
    add comment=Management interface=bridge name=VLAN100 vlan-id=100
    /ip address
    add address=192.168.100.4/24 interface=VLAN100 network=192.168.100.0
    ```