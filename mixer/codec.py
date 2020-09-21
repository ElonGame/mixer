"""
Helper function fo encode and decode BLENDER_DATA_* messages
"""
import dataclasses
import importlib
from typing import List, Mapping, Optional

from mixer.broadcaster import common


class Message:
    # Base class for encodable/decodable messages
    pass


class Matrix:
    pass


class Color:
    pass


MessageTypes = Mapping[common.MessageType, Message]

# The message types registered by "components" (VRtist, Blender protocol)
registered_message_types: MessageTypes = {}


# TODO extend
codec_functions = {
    float: (common.encode_float, common.decode_float),
    int: (common.encode_int, common.decode_int),
    str: (common.encode_string, common.decode_string),
    Color: (common.encode_color, common.decode_color),
    Matrix: (common.encode_matrix, common.decode_matrix),
}


def decode_as(message_type: common.MessageType, buffer: bytes) -> Optional[Message]:
    """
    Decode buffer as message_type. Returns None is mesage_type is not registered
    """
    index = 0
    args = []
    message_class = registered_message_types.get(message_type)
    if message_class is None:
        raise NotImplementedError(f"No encode/decode function for {message_type}")
    fields = (f.type for f in dataclasses.fields(message_class))
    for type_ in fields:
        if type_ not in codec_functions:
            raise NotImplementedError(f"No codec_func for {type_}")
        decode = codec_functions[type_][1]
        decoded, index = decode(buffer, index)
        args.append(decoded)
    return message_class(*args)


def decode(command: common.Command) -> Optional[Message]:
    return decode_as(command.type, command.data)


def encode(message: Message) -> bytes:
    # not tested, actually
    raise NotImplementedError("encode")
    buffer = b""
    fields = ((f.name, f.type) for f in dataclasses.fields(message))
    for (
        name,
        type_,
    ) in fields:
        if type_ not in codec_functions:
            raise NotImplementedError(f"No codec_func for {type_}")
        encode = codec_functions[type_][0]

        attr = getattr(message, name)
        # TODO need something smarter that multiple reallocations ?
        buffer += encode(type_)(attr)
    return buffer


def is_registered(message_type: common.MessageType) -> bool:
    return message_type in registered_message_types.keys()


def register_message_types(types_dict: MessageTypes):
    registered_message_types.update(types_dict)


def unregister_message_types(command_types: List[common.Command]):
    for t in command_types:
        if t in registered_message_types:
            del registered_message_types[t]


# works around a circular dependency problem, a a tiny step towards  splitting VRtist and Blender protocols
_packages = ["mixer.blender_client", "mixer.blender_data"]


def register():
    for p in _packages:
        mod_name = p + ".codec"
        mod = importlib.import_module(mod_name)
        mod.register()


def unregister():
    for p in _packages:
        mod_name = p + ".codec"
        mod = importlib.import_module(mod_name)
        mod.unregister()
