from main import settings_manager


def send_announce_response(server_ip: str, server_port: str):
    try:
        dev_ip = settings_manager.device_environ.get("DEVICE_IP", "None")
        dev_name = settings_manager.device_environ.get("DEVICE_NAME", "None")
        dev_status = settings_manager.device_environ.get("DEVICE_STATUS", "None")
        
        data = {
            "device_name": dev_name,
            "device_ip": dev_ip,
            "device_status": dev_status
        }
        # print(data)
        
        import ujson
        json_data = ujson.dumps(data)

        print(json_data)
        try:
            import urequests
            # Use the 'data' parameter instead of 'json_data'
            url = f"http://{server_ip}:{server_port}/annoncement_resp"
            # print(url)
            response = urequests.post(url,
                                       data=json_data,  # Pass the JSON string here
                                       headers={"Content-Type": "application/json"})  # Set the content type
            print(response.json())  # Call .json() on the response object
        except Exception as e:
            print("Exc2 in send_announce_response ", e)
    except Exception as e:
        print("Exc in send_announce_response ", e)


def send_task_response(server_ip: str, server_port: str):
    try:
        dev_ip = settings_manager.device_environ.get("DEVICE_IP", "None")
        dev_name = settings_manager.device_environ.get("DEVICE_NAME", "None")
        dev_status = settings_manager.device_environ.get("DEVICE_STATUS", "None")
        
        data = {
            "device_name": dev_name,
            "device_ip": dev_ip,
            "device_status": dev_status
        }
        # print(data)
        
        import ujson
        json_data = ujson.dumps(data)

        print(json_data)
        try:
            import urequests
            # Use the 'data' parameter instead of 'json_data'
            url = f"http://{server_ip}:{server_port}/annoncement_resp"
            # print(url)
            response = urequests.post(url,
                                       data=json_data,  # Pass the JSON string here
                                       headers={"Content-Type": "application/json"})  # Set the content type
            print(response.json())  # Call .json() on the response object
        except Exception as e:
            print("Exc2 in send_task_response ", e)
    except Exception as e:
        print("Exc in send_task_response ", e)