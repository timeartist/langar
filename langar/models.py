import email


class Client:
    def __init__(self, first_name, last_name, dob, zip_code, adults, minors, seniors,
                 phone_number=None, email_address=None, homelessness='false') -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.zip_code = zip_code
        self.phone_number = phone_number
        self.email_address = email_address
        self.homelessness = homelessness == 'true'

