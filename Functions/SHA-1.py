import hashlib

# Example input (string)
data = "Hello, World!"

# Create a SHA-1 hash object
sha1_hash = hashlib.sha1()

# Update the hash object with the data (must be bytes)
sha1_hash.update(data.encode('utf-8'))

# Get the binary digest (20 bytes)
binary_digest = sha1_hash.digest()

# Get the hexadecimal digest (readable format)
hex_digest = sha1_hash.hexdigest()

print("Binary Digest:", binary_digest)
print("Hex Digest:", hex_digest)
