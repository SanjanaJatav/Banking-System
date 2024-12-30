import sqlite3
import random
import re
import hashlib
from datetime import datetime

conn = sqlite3.connect('banking_system.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        account_number TEXT UNIQUE NOT NULL,
        dob TEXT NOT NULL,
        city TEXT NOT NULL,
        password TEXT NOT NULL,
        balance REAL NOT NULL,
        contact_number TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        status TEXT DEFAULT 'active'
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS login (
        account_number TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        amount REAL NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email)

def is_valid_phone_number(phone):
    return re.match(r'^\+?1?\d{9,15}$', phone)

def generate_account_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def is_valid_account_number(account_number):
    return len(account_number) == 10 and account_number.isdigit()

def is_valid_password(password):
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password))

def add_user():
    print("----- Add New User -----")
    name = input("Enter Name: ")
    dob = input("Enter Date of Birth (YYYY-MM-DD): ")
    city = input("Enter City: ")
    
    while True:
        contact_number = input("Enter Contact Number (+CountryCodeNumber): ")
        if not is_valid_phone_number(contact_number):
            print("Invalid contact number. Please try again.")
        else:
            break

    while True:
        email = input("Enter Email ID: ")
        if not is_valid_email(email):
            print("Invalid email format. Please try again.")
        else:
            break
    
    while True:
        password = input("Create Password (min 8 characters, 1 uppercase, 1 number): ")
        if not is_valid_password(password):
            print("Password must have at least 8 characters, 1 uppercase, and 1 number. Try again.")
        else:
            break

    initial_balance = float(input("Enter Initial Balance (minimum 2000): "))
    if initial_balance < 2000:
        print("Initial balance must be at least 2000.")
        return

    address = input("Enter Address: ")

    account_number = generate_account_number()

    cursor.execute('''
        INSERT INTO users (name, account_number, dob, city, password, balance, contact_number, email, address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, account_number, dob, city, hash_password(password), initial_balance, contact_number, email, address))

    cursor.execute('''
        INSERT INTO login (account_number, password)
        VALUES (?, ?)
    ''', (account_number, hash_password(password)))

    conn.commit()

    print(f"User {name} added successfully with account number {account_number}.\n")

def show_users():
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    print("----- All Users -----")
    for user in users:
        print(f"Name: {user[1]}, Account Number: {user[2]}, Balance: {user[6]}")
    print("\n")

def login():
    print("----- Login -----")
    account_number = input("Enter Account Number: ")
    password = input("Enter Password: ")

    cursor.execute('SELECT * FROM login WHERE account_number = ? AND password = ?', (account_number, hash_password(password)))
    user = cursor.fetchone()

    if user:
        print(f"Login successful for account {account_number}.")
        account_menu(account_number)
    else:
        print("Invalid account number or password.")

def account_menu(account_number):
    while True:
        print("\n----- Account Menu -----")
        print("1. Show Balance")
        print("2. View Transactions")
        print("3. Credit Amount")
        print("4. Debit Amount")
        print("5. Transfer Amount")
        print("6. Change Password")
        print("7. Update Profile")
        print("8. Logout")
        
        choice = input("Enter your choice: ")

        if choice == '1':
            show_balance(account_number)
        elif choice == '2':
            view_transactions(account_number)
        elif choice == '3':
            credit_amount(account_number)
        elif choice == '4':
            debit_amount(account_number)
        elif choice == '5':
            transfer_amount(account_number)
        elif choice == '6':
            change_password(account_number)
        elif choice == '7':
            update_profile(account_number)
        elif choice == '8':
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


def show_balance(account_number):
    cursor.execute('SELECT balance FROM users WHERE account_number = ?', (account_number,))
    balance = cursor.fetchone()[0]
    print(f"Your balance is: {balance}")

def view_transactions(account_number):
    cursor.execute('SELECT * FROM transaction WHERE account_number = ? ORDER BY date DESC', (account_number,))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transactions found.")
    else:
        for txn in transactions:
            print(f"ID: {txn[0]}, Type: {txn[2]}, Amount: {txn[3]}, Date: {txn[4]}")


def credit_amount(account_number):
    amount = float(input("Enter amount to credit: "))
    if amount <= 0:
        print("Amount should be greater than zero.")
        return

    cursor.execute('UPDATE users SET balance = balance + ? WHERE account_number = ?', (amount, account_number))
    cursor.execute('INSERT INTO transaction (account_number, transaction_type, amount) VALUES (?, ?, ?)', 
                   (account_number, 'Credit', amount))
    conn.commit()

    print(f"Successfully credited {amount}. Updated balance is {get_balance(account_number)}.")

def debit_amount(account_number):
    amount = float(input("Enter amount to debit: "))
    if amount <= 0:
        print("Amount should be greater than zero.")
        return

    balance = get_balance(account_number)
    if amount > balance:
        print("Insufficient balance.")
        return

    cursor.execute('UPDATE users SET balance = balance - ? WHERE account_number = ?', (amount, account_number))
    cursor.execute('INSERT INTO transaction (account_number, transaction_type, amount) VALUES (?, ?, ?)', 
                   (account_number, 'Debit', amount))
    conn.commit()

    print(f"Successfully debited {amount}. Updated balance is {get_balance(account_number)}.")

def transfer_amount(account_number):
    target_account = input("Enter target account number: ")
    amount = float(input("Enter amount to transfer: "))

    if amount <= 0:
        print("Amount should be greater than zero.")
        return

    balance = get_balance(account_number)
    if amount > balance:
        print("Insufficient balance.")
        return

    cursor.execute('SELECT * FROM users WHERE account_number = ?', (target_account,))
    target_user = cursor.fetchone()
    if not target_user:
        print("Target account does not exist.")
        return

    cursor.execute('UPDATE users SET balance = balance - ? WHERE account_number = ?', (amount, account_number))
    cursor.execute('UPDATE users SET balance = balance + ? WHERE account_number = ?', (amount, target_account))
    cursor.execute('INSERT INTO transaction (account_number, transaction_type, amount) VALUES (?, ?, ?)', 
                   (account_number, 'Debit', amount))
    cursor.execute('INSERT INTO transaction (account_number, transaction_type, amount) VALUES (?, ?, ?)', 
                   (target_account, 'Credit', amount))
    conn.commit()

    print(f"Successfully transferred {amount} to account {target_account}. Updated balance is {get_balance(account_number)}.")

def get_balance(account_number):
    cursor.execute('SELECT balance FROM users WHERE account_number = ?', (account_number,))
    return cursor.fetchone()[0]

def change_password(account_number):
    current_password = input("Enter current password: ")
    cursor.execute('SELECT password FROM login WHERE account_number = ?', (account_number,))
    stored_password = cursor.fetchone()[0]

    if hash_password(current_password) != stored_password:
        print("Incorrect current password. Try again.")
        return

    new_password = input("Enter new password (min 8 characters, 1 uppercase, 1 number): ")
    if not is_valid_password(new_password):
        print("Invalid password format. Password must have at least 8 characters, 1 uppercase, and 1 number.")
        return

    cursor.execute('UPDATE login SET password = ? WHERE account_number = ?', 
                   (hash_password(new_password), account_number))
    cursor.execute('UPDATE users SET password = ? WHERE account_number = ?',
                   (hash_password(new_password), account_number))
    conn.commit()

    print("Password changed successfully.")

def update_profile(account_number):
    print("\n----- Update Profile -----")
    print("1. Change Address")
    print("2. Change City")
    print("3. Change Contact Number")
    print("4. Change Email")
    print("5. Back to Account Menu")

    choice = input("Enter your choice: ")

    if choice == '1':
        new_address = input("Enter new address: ")
        cursor.execute('UPDATE users SET address = ? WHERE account_number = ?', 
                       (new_address, account_number))
        conn.commit()
        print("Address updated successfully.")
    
    elif choice == '2':
        new_city = input("Enter new city: ")
        cursor.execute('UPDATE users SET city = ? WHERE account_number = ?', 
                       (new_city, account_number))
        conn.commit()
        print("City updated successfully.")
    
    elif choice == '3':
        while True:
            new_contact_number = input("Enter new contact number: ")
            if is_valid_phone_number(new_contact_number):
                cursor.execute('UPDATE users SET contact_number = ? WHERE account_number = ?',
                               (new_contact_number, account_number))
                conn.commit()
                print("Contact number updated successfully.")
                break
            else:
                print("Invalid contact number. Please try again.")
    
    elif choice == '4':
        while True:
            new_email = input("Enter new email: ")
            if is_valid_email(new_email):
                cursor.execute('UPDATE users SET email = ? WHERE account_number = ?', 
                               (new_email, account_number))
                conn.commit()
                print("Email updated successfully.")
                break
            else:
                print("Invalid email format. Please try again.")
    
    elif choice == '5':
        return
    else:
        print("Invalid choice. Please try again.")

def toggle_account_status(account_number):
    cursor.execute('SELECT status FROM users WHERE account_number = ?', (account_number,))
    current_status = cursor.fetchone()[0]

    if current_status == 'active':
        cursor.execute('UPDATE users SET status = ? WHERE account_number = ?', ('deactivated', account_number))
        print(f"Account {account_number} has been deactivated.")
    else:
        cursor.execute('UPDATE users SET status = ? WHERE account_number = ?', ('active', account_number))
        print(f"Account {account_number} has been reactivated.")

    conn.commit()

def show_menu():
    while True:
        print("\n----- Banking System -----")
        print("1. Add User")
        print("2. Show Users")
        print("3. Login")
        print("4. Exit")
        
        choice = input("Enter your choice: ")

        if choice == '1':
            add_user()
        elif choice == '2':
            show_users()
        elif choice == '3':
            login()
        elif choice == '4':
            print("Exiting the system. Goodbye!")
            conn.close()
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    show_menu()
