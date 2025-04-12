# Import Hasher directly from its specific utility path
from streamlit_authenticator.utilities.hasher import Hasher

# Create a list of plain text passwords you want to hash
# Make sure these are the actual passwords you intend to use initially
passwords_to_hash = ["test"] # Use strong passwords!

# Generate the hashed passwords using the imported Hasher
# The usage pattern Hasher(list).generate() remains the same
hashed_passwords = Hasher(passwords_to_hash).generate()

# Print the hashed passwords
print("Hashed Passwords:")
for h in hashed_passwords:
    print(h)
