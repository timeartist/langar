import csv
import os
import glob
from datetime import datetime

def read_clients_csv(file_path):
    clients = {}
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            clients[row['id']] = row
    return clients

def find_first_appearance(client_id, distribution_files):
    first_appearance = None
    for file_path in distribution_files:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['id'] == client_id:
                    date_from_filename = os.path.basename(file_path).replace("distribution-", "").replace(".csv", "")
                    date_obj = datetime.strptime(date_from_filename, '%Y-%m-%d')
                    if first_appearance is None or date_obj < first_appearance:
                        first_appearance = date_obj
                    break
    return first_appearance

def write_clients_with_date_added(clients, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['id', 'first_name', 'last_name', 'dob', 'zip_code', 'phone_number', 'email_address', 'homelessness', 'adults', 'minors', 'seniors', 'date_added']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for client_id, client_data in clients.items():
            writer.writerow(client_data)

def main():
    clients_file = 'data/clients.csv'
    distribution_files = sorted(glob.glob('data/distributions/distribution-*.csv'))
    output_file = 'clients_with_date_added.csv'
    
    clients = read_clients_csv(clients_file)
    
    for client_id in clients:
        first_appearance = find_first_appearance(client_id, distribution_files)
        if first_appearance:
            clients[client_id]['date_added'] = first_appearance.strftime('%Y-%m-%d')
        else:
            clients[client_id]['date_added'] = 'N/A'

    write_clients_with_date_added(clients, output_file)

if __name__ == '__main__':
    main()
