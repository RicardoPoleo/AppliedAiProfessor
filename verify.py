import os

def verify_file_exists(file_path):
    if os.path.exists(file_path):
        print(f"The file exists at: {file_path}")
    else:
        print(f"File not found: {file_path}")

def print_current_directory():
    current_directory = os.getcwd()
    print(f"Current working directory: {current_directory}")

# Example usage:
print_current_directory()

the_file = os.path.join(os.getcwd(), "verify.py")
print(f"File that I want {the_file}")

# Corrected file path construction
script_file_path = os.path.join("C:\\", "projects", "Sports-Buddy", "verify.py")
verify_file_exists(the_file)
