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

def update_distribution_file(file_path, clients):
    new_file_path = file_path.replace('.csv', '_updated.csv')
    with open(file_path, 'r') as input_file, open(new_file_path, 'w', newline='') as output_file:
        reader = csv.DictReader(input_file)
        # fieldnames = reader.fieldnames + ['new']
        writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames)
        
        writer.writeheader()
        for row in reader:
            client_id = row['id']
            date_from_filename = os.path.basename(file_path).replace("distribution-", "").replace(".csv", "")
            date_obj = datetime.strptime(date_from_filename, '%Y-%m-%d')
            
            if client_id in clients and clients[client_id]['date_added'] == date_obj.strftime('%Y-%m-%d'):
                row['new'] = '1'
            else:
                row['new'] = '0'
            
            writer.writerow(row)

def main():
    clients_file = 'data/clients.csv'
    distribution_files = sorted(glob.glob('data/distributions/distribution-*.csv'))
    
    clients = read_clients_csv(clients_file)

    for file_path in distribution_files:
        update_distribution_file(file_path, clients)

if __name__ == '__main__':
    main()
