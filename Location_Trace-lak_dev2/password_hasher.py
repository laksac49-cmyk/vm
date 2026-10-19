import bcrypt

def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def verify_password(password, hashed_password):
    # Check if the provided password matches the hashed password
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def main():
    # Get password input from user
    password = input("Enter a password to hash: ")
    
    # Hash the password
    hashed_password = hash_password(password)
    print(f"Hashed password: {hashed_password}")
    
    # Verify the password
    verify_pass = input("Enter the password again to verify: ")
    if verify_password(verify_pass, hashed_password):
        print("Password verification successful!")
    else:
        print("Password verification failed!")

if __name__ == "__main__":
    main()