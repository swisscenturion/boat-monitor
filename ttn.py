import requests
import json
import pandas as pd
from datetime import datetime, timedelta


def get_current_timestamp_minus_one_hour():
    # Get the current UTC time
    current_time = datetime.utcnow()

    # Subtract 1 hour from the current time
    one_hour_ago = current_time - timedelta(hours=1)

    # Format the result as a string in the desired format
    timestamp = one_hour_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    return timestamp


def retrieve_stored_uplinks(api_key, application_id, timestamp):
    url = f"https://eu1.cloud.thethings.network/api/v3/as/applications/{application_id}/packages/storage/uplink_message"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "text/event-stream"}
    params = {"after": timestamp}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code}"


def get_ttn_data(TTN_KEY, timestamp=get_current_timestamp_minus_one_hour()):
    result = retrieve_stored_uplinks(TTN_KEY, "lora-test-sli1", timestamp)

    # Split the string by lines and filter out empty lines
    json_strings = [line for line in result.split("\n") if line.strip()]

    # Parse each JSON string into a dictionary
    dict_list = []
    for json_str in json_strings:
        try:
            dict_list.append(json.loads(json_str))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    # Extract data from the JSON and create a list of dictionaries
    extracted_data = []
    for entry in dict_list:
        # Start by extracting the common data that doesn't depend on the number of gateways
        extracted_entry = {
            "received_at": entry["result"]["received_at"],
            "batteryVoltage": entry["result"]["uplink_message"]["decoded_payload"]["batteryVoltage"],
            "humidity": entry["result"]["uplink_message"]["decoded_payload"]["humidity"],
            "latitude": entry["result"]["uplink_message"]["decoded_payload"]["latitude"],
            "longitude": entry["result"]["uplink_message"]["decoded_payload"]["longitude"],
            "reedSwitchStatus": entry["result"]["uplink_message"]["decoded_payload"]["reedSwitchStatus"],
            "satellites": entry["result"]["uplink_message"]["decoded_payload"]["satellites"],
            "temperature": entry["result"]["uplink_message"]["decoded_payload"]["temperature"],
            'count_gw': len(entry["result"]["uplink_message"]["rx_metadata"])
        }

        # Now iterate through each gateway in the rx_metadata to add the dynamic gateway information
        for index, gw_data in enumerate(entry["result"]["uplink_message"]["rx_metadata"], start=1):
            extracted_entry[f"id_gw_{index}"] = gw_data["gateway_ids"]["gateway_id"]
            extracted_entry[f"timestamp_gw_{index}"] = gw_data.get("timestamp", None)
            extracted_entry[f"latitude_gw_{index}"] = gw_data["location"]["latitude"] if "location" in gw_data else None
            extracted_entry[f"longitude_gw_{index}"] = gw_data["location"]["longitude"] if "location" in gw_data else None
            # extracted_entry[f"altitude_gw_{index}"] = gw_data["location"]["altitude"] if "location" in gw_data else None
            extracted_entry[f"snr_gw_{index}"] = gw_data.get("snr", None)
            extracted_entry[f"rssi_gw_{index}"] = gw_data.get("rssi", None)

        extracted_data.append(extracted_entry)
    # Create a DataFrame
    return pd.DataFrame(extracted_data)
