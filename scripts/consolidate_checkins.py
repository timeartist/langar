import csv
import os
import glob
from datetime import datetime

def consolidate_distribution_files(distribution_files, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['date', 'id', 'zip_code', 'dob', 'adults', 'minors', 'seniors', 'new']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for file_path in distribution_files:
            with open(file_path, 'r') as input_file:
                reader = csv.DictReader(input_file)
                
                date_from_filename = os.path.basename(file_path).replace("distribution-", "").replace(".csv", "")
                date_obj = datetime.strptime(date_from_filename, '%Y-%m-%d')
                
                for row in reader:
                    row['date'] = date_obj.strftime('%Y-%m-%d')
                    writer.writerow(row)

def main():
    distribution_files = sorted(glob.glob('data/distributions/distribution-*.csv'))
    output_file = 'distributions.csv'

    consolidate_distribution_files(distribution_files, output_file)

if __name__ == '__main__':
    main()
