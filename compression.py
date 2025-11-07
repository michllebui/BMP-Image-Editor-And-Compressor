import struct 

def lzw_compression(uncompressed):
    # initialize dictionary
    dict_size = 256
    dictionary = {bytes([i]): i for i in range(dict_size)}
    
    w = b""
    compressed_data = []

    for byte in uncompressed:
        wb = w + bytes([byte])

        if wb in dictionary:
            w = wb

        else:
            compressed_data.append(dictionary[w])
            dictionary[wb] = dict_size
            dict_size += 1
            w = bytes([byte])
    
    if w:
        compressed_data.append(dictionary[w])
    
    return compressed_data

def lzw_decompression(compressed):
    dict_size = 256
    dictionary = {i: bytes([i]) for i in range(dict_size)}

    # in case of no bytes
    if not compressed:
        return b""

    output = b""
    w = dictionary[compressed[0]]
    output += w

    for c in compressed[1:]:
        if c in dictionary:
            data = dictionary[c]

        else:
            data = w + bytes([w[0]])

        output += data
        dictionary[dict_size] = w + bytes([data[0]])
        dict_size += 1
        w = data

    return output

