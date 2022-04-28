from uuid import uuid4
from json import loads, dumps
from csv import DictReader, DictWriter
from datetime import datetime
from glob import glob


from redis import StrictRedis
from redis.exceptions import ResponseError
from redis.commands.json.path import Path
from redis.commands.search.field import TextField
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

R = StrictRedis()

_checkin_key = lambda id: f'checkin:{id}'
_checkin_file_headers = ['id', 'zip_code', 'dob', 'adults', 'minors', 'seniors']
_client_key = lambda id: f'client:{id}'
_client_file_headers =  keys = ['id', 'first_name', 'last_name', 'dob', 'zip_code', 'phone_number', 'email_address', 'homelessness', 'adults', 'minors', 'seniors']

def _client_index():
    idx = R.ft(_client_key('idx'))
    try:
        idx.info()
        return idx
    except ResponseError:
        pass

    idx.create_index((
        TextField('$.id', as_name='id'),
        TextField('$.first_name', as_name='first'),
        TextField('$.last_name', as_name='last')
    ), definition=IndexDefinition(prefix=[_client_key('')], index_type=IndexType.JSON))

    return idx

def _read_clients_csv():
    with open('data/clients.csv', 'r') as f:
        rows = DictReader(f)
        return [row for row in rows]

class Client:
    def __init__(self, first_name, last_name, dob, zip_code, adults, minors, seniors,
                 phone_number=None, email_address=None, homelessness='false', **_) -> None:
        self.id = str(uuid4()).replace('-', '')
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.zip_code = zip_code
        self.phone_number = phone_number
        self.email_address = email_address
        self.homelessness = homelessness == 'true'
        self.adults = int(adults)
        self.minors = int(minors)
        self.seniors = int(seniors)
        

    @staticmethod
    def batch_from_csv():
        _client_index()

        clients = _read_clients_csv()
        print(clients)

        with R.pipeline(transaction=False) as pipe:
            for client in clients:
                client['id'] = client['id'].replace('-', '')
                pipe.json().set(_client_key(client['id']), Path.root_path(), client)
            
            pipe.execute()

    @staticmethod
    def batch_to_dict():        
        client_data = _read_clients_csv()
        clients = {}
        for client in client_data:
            clients[client['id'].replace('-', '')] = client
        return clients

    @staticmethod
    def find(query):
        idx = _client_index()
        query = Query(query)
        return _deserialize_results(idx.search(query))


    def save(self):
        clients = _read_clients_csv()

        clients.append(self.__dict__)
        R.json().set(_client_key(self.id), Path.root_path(), self.__dict__)

        with open('data/clients.csv', 'w') as f:
            dw = DictWriter(f, _client_file_headers)
            dw.writeheader()
            dw.writerows(clients)

class CheckIn:
    def __init__(self, id=None, zip_code=None, dob=None, adults=None, minors=None, seniors=None, **_) -> None:
        self.date = datetime.today().isoformat().split('T')[0]
        self.file = f'data/distributions/distribution-{self.date}.csv'
        self.id = id
        self.zip_code = zip_code
        self.dob = dob
        self.adults = adults
        self.minors = minors
        self.seniors = seniors
        self._checkins = []

        ## create checkin file if it doesn't exist already
        if not glob(self.file):
            open(self.file, 'w+') 
        ## otherwise open and read it
        else:
            with open(self.file, 'r') as f:
                rows = DictReader(f)
                self._checkins = [row for row in rows]

        ## if this is a new checkin, add it to redis and the data file
        if self.id is not None:
            R.json().set(_checkin_key(self.id), Path.root_path(), self.__dict__)
            
            ## filter out any data we don't want in the file from the obj, and add this 
            data = self.__dict__.copy()
            data.pop('date')
            data.pop('file')
            data.pop('_checkins')
            self._checkins.append(data)

            with open(self.file, 'w') as f:
                dw = DictWriter(f, _checkin_file_headers)
                dw.writeheader()
                dw.writerows(self._checkins)

    def checkins_to_list(self):
        return self._checkins


def _deserialize_results(results) -> list:
    '''turn a list of json at results.docs into a list of dicts'''
    return [loads(result.json) for result in results.docs]
