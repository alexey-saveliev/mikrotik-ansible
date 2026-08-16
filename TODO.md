1. *Добавить создание VLAN интерфейсов* - **Done**
2. *Добавить назначение IP адресов на интерфейсы* - **Done**
3. *Возвращать настройки limit-unknown-multicasts, limit-unknown-unicasts и storm-rate к значениям по умолчанию для портов, не включенных в bridge.* - **Сделано. Тестируется.**
4. Добавлять в firewall правила для fast-track и established
5. Добавить отключение IPv6
6. Добавить создание interface list
7. Добавить создание address list
8. Добавить настройку DHCP Snooping ** Testing **
    # 1. Enable DHCP Snooping on the bridge
    /interface bridge set [find name=bridge] dhcp-snooping=yes

    # 2. Set your uplink port as TRUSTED (Allows DHCP Offers/Replies)
    /interface bridge port set [find interface=ether1 bridge=bridge] trusted=yes

    # 3. Enable DHCP Snooping for your specific VLAN IDs (e.g., VLAN 10 and 20)
    /interface bridge vlan set [find vlan-ids=10 bridge=bridge] dhcp-snooping=yes
    /interface bridge vlan set [find vlan-ids=20 bridge=bridge] dhcp-snooping=yes

    Critical CRS326 Architecture NotesHardware Offloading:
        1. The CRS326 supports hardware-accelerated DHCP Snooping. According to the MikroTik Layer 2 Misconfiguration Guide, you must enable snooping on both the bridge level and individual VLAN entries for the rule to apply properly.
        2. Option 82: If your DHCP server requires circuit ID tracking, you can safely enable add-dhcp-option82=yes on the bridge settings. The CRS326 switch chip will process this in hardware.    
9. Добавить параметр enable: true/false для порта