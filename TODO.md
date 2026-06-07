1. Добавить создание VLAN интерфейсов
    ```
    /interface vlan
    add comment=Management interface=bridge name=VLAN10 vlan-id=10
    ```
    Например так:
    ```
    - name: Build list of VLAN definitions for api_modify
      ansible.builtin.set_fact:
        bridge_vlan_data: >-
          {{
            bridge_vlan | map('combine', {
              'name': 'VLAN' + (item.vlanid | string),
              'interface': bridge.name,
              'vlan_id': item.vlanid,
              'comment': item.comment
            }) | list
          }}
      when: bridge_vlan is defined and bridge_vlan

    - name: Create/modify VLAN interfaces in one API call      
      community.routeros.api_modify:
        hostname: "{{ address }}"
        password: "{{ ros_api_password }}"
        username: "{{ ros_api_user }}"
        path: interface vlan
        data: "{{ bridge_vlan_data }}"
      when: bridge_vlan_data is defined and bridge_vlan_data
    ```
2. Добавить назначение IP адресов на интерфейсы
    ```
    /ip address
    add address=10.20.0.1/16 interface=VLAN20 network=10.20.0.0
    ```
3. *Возвращать настройки limit-unknown-multicasts, limit-unknown-unicasts и storm-rate к значениям по умолчанию для портов, не включенных в bridge.* - **Сделано. Тестируется.**
4. Добавлять в firewall правила для fast-track и established