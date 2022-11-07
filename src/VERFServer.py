# VERFServer - v1.0
# Written by vlOd (vlodiscord@gmail.com)

# OS: Operating System related utilities
import os
# SHUTIL: Shell related utilities
import shutil
# THREADING: Thread related utilities
import threading
# SOCKET: Network related utilities
import socket

db_licenses = {}
db_trial_licenses = {}

# TODO: Clean-up
# File format: KEY:VALUE
def load_db():
    print("Loading databases...")
    # Clears existing entries
    db_licenses.clear()
    db_trial_licenses.clear()

    try:
        # Check if the file exists
        if not os.path.exists("licenses.properties"):
            # If not, create it
            db_licenses_file = open("licenses.properties", "w")
            db_licenses_file.close()
        else:
            # If yes, load it
            db_licenses_file = open("licenses.properties", "r")
            # Go thru each line
            for line in db_licenses_file.readlines():
                # Split the line at the first :
                line_splitted = line.split(":", 2)
                
                # If the line does not have a key and a value, continue
                if len(line_splitted) < 2:
                    print("licenses.properties: Skipping " + line)
                    continue
                
                # Get the key
                key = line_splitted[0].strip()
                # Get the value
                value = line_splitted[1].strip()
                
                # Add the value to the database
                db_licenses[key] = value
            # Close the file (to restore access to other programs and prevent memory leaks)
            db_licenses_file.close()
    except Exception as ex:
        print("Failed to load licenses.properties: " + str(ex))
    
    # Check other database loading producedure for information
    try:
        if not os.path.exists("trial_licenses.properties"):
            db_trial_licenses_file = open("trial_licenses.properties", "w")
            db_trial_licenses_file.close()
        else:
            db_trial_licenses_file = open("trial_licenses.properties", "r")
            for line in db_trial_licenses_file.readlines():
                line_splitted = line.split(":", 2)
                
                if len(line_splitted) < 2:
                    print("trial_licenses.properties: Skipping " + line)
                    continue
                
                key = line_splitted[0].strip()
                value = line_splitted[1].strip()
                
                db_trial_licenses[key] = value
            db_trial_licenses_file.close()
    except Exception as ex:
        print("Failed to load trial_licenses.properties: " + str(ex))
    
    print("Loaded databases")

is_running = True
# Create a TCP (checked and stream based protocol) socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients = {}

def get_ip_str(client_addr):
    # IP:PORT
    return client_addr[0] + ":" + str(client_addr[1])

def disconnect_client(client_addr, client):
    # Close the client
    client.close()
    # Delete the client's entry
    del clients[client_addr]
    print(get_ip_str(client_addr) + " disconnected")

def handle_clients():
    # Mark variables as global so they are updated
    global db_licenses
    global db_trial_licenses
    global is_running
    global server
    global clients
    
    while is_running:
        # Go thru each client
        for client_addr, client in clients.copy().items():
            try:
                # Receive at most 1024 bytes
                data = client.recv(1024).decode().strip()
                # If the data is invalid, asume the client disconnected
                if not data:
                    disconnect_client(client_addr, client)
                    continue
                    
                # Parse the client's data
                parsed_data = data.split(":", 3)
                # Get the client's action (max 2 parameters)
                action = parsed_data[0]
                    
                # Check if the action is VERF and there are atleast 2 parameters
                if action.upper() == "VERF" and len(parsed_data) >= 3:
                    # Get the license key
                    key = parsed_data[1].lower()
                    # Get the license verify ID
                    verify_id = parsed_data[2].lower()
                    
                    print(get_ip_str(client_addr) + " requested verification:")
                    print("- Key: " + key)
                    print("- Verify ID: " + verify_id)
                    
                    # Check if the key is in any either the trial or normal database
                    if key in db_licenses or key in db_trial_licenses:
                        # Declare validation variables
                        correct_verify_id = None
                        trial_license = False
                    
                        # Check if the key is a trial key
                        if key in db_licenses:
                            # If not, grab the regular verify ID
                            correct_verify_id = db_licenses[key]
                        else:
                            # If yes, grab the trial verify ID
                            correct_verify_id = db_trial_licenses[key]
                            # Mark the key as trial
                            trial_license = True
                            
                        # Check if the client verify ID matches the correct one
                        if verify_id == correct_verify_id.lower():
                            print(get_ip_str(client_addr) + " passed verification (trial: " + str(trial_license) + ")")
                            if trial_license:
                                # Pass the client as a trial one
                                client.send("TRAL".encode("UTF-8"))
                            else:
                                # Pass the client
                                client.send("PASS".encode("UTF-8"))
                        else:
                            # Fail the client for sending an verify ID
                            print(get_ip_str(client_addr) + " failed verification (invalid verify ID)")
                            client.send("FAIL".encode("UTF-8"))
                    else:
                        # Fail the client for sending an invalid key
                        print(get_ip_str(client_addr) + " failed verification (invalid key)")
                        client.send("FAIL".encode("UTF-8"))
                    
                    # Disconnect the client
                    disconnect_client(client_addr, client)
                else:
                    # Kick the client for a protocol violation
                    print(get_ip_str(client_addr) + " performed a protocol violation")
                    disconnect_client(client_addr, client)
                    continue
            except Exception as ex:
                # Check if the error occured during a shutdown
                if is_running:
                    print("Unable to handle client " + get_ip_str(client_addr) + ": " + str(ex))
                    disconnect_client(client_addr, client)
                else:
                    return

def accept_clients():
    # Mark variables as global so they are updated
    global is_running
    global server
    global clients
    
    while is_running:
        try:
            # Accept a client
            client, client_addr = server.accept()
            print(get_ip_str(client_addr) + " connected")
            # Add the client to the list of to handle clients
            clients[client_addr] = client
        except Exception as ex:
            # Check if the error occured during a shutdown
            if is_running:
                print("Unable to accept a client: " + str(ex))
            else:
                return

print("VERFServer - v1.0")
print("".ljust(shutil.get_terminal_size().lines, "-"))
print("Administration: To close the server, press CTRL+C, to reload the databases, press enter")
print("".ljust(shutil.get_terminal_size().lines, "-"))

# Load database
load_db()

# Start TCP server on 6859
server.bind(("0.0.0.0", 6859))
server.listen()
print("Listening on 0.0.0.0:6859...")

# Start server threads
handle_clients_thread = threading.Thread(target=handle_clients)
handle_clients_thread.start()
accept_clients_thread = threading.Thread(target=accept_clients)
accept_clients_thread.start()

try:
    while is_running:
        # Wait for user to press enter
        input()
        # Load database
        load_db()
except KeyboardInterrupt:
    print("Closing server...")
    # Mark server as not running (prevents threads from continuing execution)
    is_running = False
    # Stop the server (also kills the accept thread)
    server.close()
    # Disconnect all clients (also kills the handle thread)
    for client_addr, client in clients.copy().items():
        disconnect_client(client_addr, client)