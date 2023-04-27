from algosdk import encoding

import base64


def unpack_data(data: str, format: dict):
    decoded_data = base64.b64decode(data)
    result = {}
    index = 0
    for name, type in format.items():
        if index >= len(decoded_data):
            return result

        if type["type"] == 'address':
            result[name] = encoding.encode_address(
                decoded_data[index:index + 32])
            index += 32
        elif type["type"] == 'bytes':
            pass
        elif type["type"] == 'uint':
            result[name] = int.from_bytes(
                decoded_data[index:index + 8], byteorder='big')
            index += 8
        elif type["type"] == 'string':
            pass

    return result
