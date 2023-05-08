from os import environ, stat, remove
from os.path import join, split
from uuid import uuid4
from json import loads
from csv import DictReader, DictWriter
from datetime import datetime
from glob import glob
from io import StringIO

from flask_login import UserMixin

from redis import StrictRedis
from redis.exceptions import ResponseError
from redis.commands.json.path import Path
from redis.commands.search.field import TextField
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

R = StrictRedis.from_url(environ.get('REDIS_URL', 'redis://localhost:6379'))
DISTRIBUTIONS_DIR = 'data/distributions'

_checkin_key = lambda id: f'checkin:{id}'
_day_checkin_file_headers = ['id', 'zip_code', 'dob', 'adults', 'minors', 'seniors', 'new']
_month_checkin_file_headers = ['date', 'id', 'zip_code', 'dob', 'adults', 'minors', 'seniors', 'new']
_client_key = lambda id: f'client:{id}'
_client_file_headers =  keys = ['id', 'first_name', 'last_name', 'dob', 'zip_code', 'phone_number', 'email_address', 'homelessness', 'adults', 'minors', 'seniors', 'date_added']

def reset_db():
    R.flushall()
    Client.batch_from_csv()

class Client:
    def __init__(self, first_name, last_name, dob, zip_code, adults, minors, seniors,
                 phone_number=None, email_address=None, homelessness='false', date_added=datetime.now().strftime('%Y-%m-%d'), **_) -> None:
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
        self.date_added = date_added
        

    @staticmethod
    def batch_from_csv():
        Client._client_index()

        clients = Client._read_clients_csv()
        print(clients)

        with R.pipeline(transaction=False) as pipe:
            for client in clients:
                client['id'] = client['id'].replace('-', '')
                pipe.json().set(_client_key(client['id']), Path.root_path(), client)
            
            pipe.execute()

    @staticmethod
    def batch_to_dict():        
        client_data = Client._read_clients_csv()
        clients = {}
        for client in client_data:
            clients[client['id'].replace('-', '')] = client
        return clients

    @staticmethod
    def find(query):
        idx = Client._client_index()
        query = Query(query)
        return _deserialize_results(idx.search(query))


    def save(self):
        clients = Client._read_clients_csv()

        clients.append(self.__dict__)
        R.json().set(_client_key(self.id), Path.root_path(), self.__dict__)

        with open('data/clients.csv', 'w') as f:
            dw = DictWriter(f, _client_file_headers)
            dw.writeheader()
            dw.writerows(clients)

    @staticmethod
    def _read_clients_csv():
        with open('data/clients.csv', 'r') as f:
            rows = DictReader(f)
            return [row for row in rows]

    @staticmethod
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

class CheckInBase:
    @staticmethod
    def _open_distribution_file(file):
        with open(file, 'r') as f:
            rows = DictReader(f)
            return [row for row in rows]

    @staticmethod
    def _save_distribution_file(file, checkins):
            with open(file, 'w+') as f:
                dw = DictWriter(f, _day_checkin_file_headers)
                dw.writeheader()
                dw.writerows(checkins)

    def _month_day_from_file(self, file):
            _file = split(file)[-1]
            _file = _file.split('.')[0]
            split_file = _file.split('-')
            return '-'.join(split_file[1:-1]), '-'.join(split_file[1:]) 

    def _stream_file(self, file):
        with open(file, 'r') as f:
            for row in f.read():
                yield row


class CheckIn(CheckInBase):
    def __init__(self, id=None, zip_code=None, dob=None, adults=None, minors=None, seniors=None, date_added=None, **_) -> None:
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.file = join(DISTRIBUTIONS_DIR, f'distribution-{self.date}.csv')
        self.id = id
        self.zip_code = zip_code
        self.dob = dob
        self.adults = adults
        self.minors = minors
        self.seniors = seniors
        self.new = int(date_added == self.date)
        self._checkins = []

        ## read any existing checkins
        if glob(self.file):
            self._checkins = CheckIn._open_distribution_file(self.file)

        ## if this is a new checkin, add it to redis and the data file
        if self.id is not None:
            # R.json().set(_checkin_key(self.id), Path.root_path(), self.__dict__)
            
            ## filter out any data we don't want in the file from the obj, and add this 
            data = self.__dict__.copy()
            data.pop('date')
            data.pop('file')
            data.pop('_checkins')
            self._checkins.append(data)

            CheckIn._save_distribution_file(self.file, self._checkins)


    def checkins_to_list(self):
        return self._checkins

    @staticmethod
    def delete(id):
        date = datetime.today().isoformat().split('T')[0]
        file = join(DISTRIBUTIONS_DIR, f'distribution-{date}.csv')
        checkins = CheckIn._open_distribution_file(file)
        for checkin in checkins:
            if checkin['id'] == id:
                print(checkin)
                break
        
        checkins.remove(checkin)

        CheckIn._save_distribution_file(file, checkins)

    @staticmethod
    def update_existing(id, adults, minors, seniors):
        date = datetime.today().isoformat().split('T')[0]
        file = join(DISTRIBUTIONS_DIR, f'distribution-{date}.csv')
        checkins = CheckIn._open_distribution_file(file)
        for checkin in checkins:
            if checkin['id'] == id:
                print(checkin)
                checkin['adults'] = adults
                checkin['minors'] = minors
                checkin['seniors'] = seniors

        CheckIn._save_distribution_file(file, checkins)

    def stream_file(self):
        self._stream_file(self.file)

class CheckIns(CheckInBase):
    def __init__(self) -> None:
        self.files = glob(join(DISTRIBUTIONS_DIR, '*.csv'))
        self.months = set()
        self.days = []
        
        for file in self.files:
            if stat(file).st_size > 0:
                month, day = self._month_day_from_file(file)
                self.months.add(month)
                self.days.append(day)
            else:
                remove(file)
                self.files.remove(file)


        self.months = list(self.months)
        self.months.sort(reverse=True)
        self.days.sort(reverse=True)

    def day_list(self, day:str):
        for file in self.files:
            if day in file:
                return self._open_distribution_file(file)

    def month_list(self, month:str):
        _checkins = {}
        for file in self.files:
            if month in file:
                _, day = self._month_day_from_file(file)
                _checkins[day] = self._open_distribution_file(file)

        checkins_final = []
        for date, checkins in _checkins.items():
            for checkin in checkins:
                checkin['date'] = date
                checkins_final.append(checkin)

        checkins_final.sort(key=lambda x: x['date'])

        return checkins_final

    def stream_day_file(self, day:str):
        for file in self.files:
            if day in file:
                return self._stream_file(file)

    def stream_month_file(self, month:str):
        month_list = self.month_list(month)
        stream = StringIO()
        
        dw = DictWriter(stream, _month_checkin_file_headers)
        dw.writeheader()
        dw.writerows(month_list)

        stream.seek(0)
        for i in stream:
            yield i
            

class UserNotFoundException(Exception):
    pass

class User(UserMixin):
    @staticmethod
    def _key(id):
        return f'user:{id}'

    def __init__(self, sub, name, email, picture, **_) -> None:
        self.sub = sub
        self.name = name
        self.email = email
        self.picture = picture
        
        self._create_user_if_not_exists()

    def _create_user_if_not_exists(self):
        existing_user = R.json().get(User._key(self.sub))
        if existing_user is None:
            R.json().set(User._key(self.sub), Path.root_path(), self.__dict__)

    @staticmethod
    def from_id(id):
        user_data = R.json().get(User._key(id))
        if user_data:
            return User(**user_data)
        else:
            raise UserNotFoundException

    def get_id(self):
        print('auth is getting id')
        return self.sub

        

def _deserialize_results(results) -> list:
    '''turn a list of json at results.docs into a list of dicts'''
    return [loads(result.json) for result in results.docs]
