from algosdk import encoding

import base64


def unpack_data(data: str, format: dict):
    decoded_data = base64.b64decode(data)
    result = {}
    index = 0
    for name, type in format.items():
        if index >= len(decoded_data):
            return result

        if type["type"] == "address":
            result[name] = encoding.encode_address(decoded_data[index: index + 32])
            index += 32
        elif type["type"] == "bytes":
            pass
        elif type["type"] == "uint":
            result[name] = int.from_bytes(
                decoded_data[index: index + 8], byteorder="big"
            )
            index += 8
        elif type["type"] == "string":
            pass

    return result


def decode_state(app_info):
    state = {}
    gl_state = app_info["params"]["global-state"]
    for i in range(len(gl_state)):
        key = base64.b64decode(gl_state[i]["key"]).decode()

        value = gl_state[i]["value"]
        value_type = value["type"]

        if value_type == 2:
            value = value.get("uint", {})

        if value_type == 1:
            try:
                value = value["bytes"].decode()
            except Exception:
                value = value["bytes"]

        if key == "gov":
            state["gov"] = encoding.encode_address(value)
        else:
            state[key] = value

    return state
