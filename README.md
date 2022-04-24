# Langar
*In Sikhism, a langar (Punjabi: ਲੰਗਰ, `kitchen`) is the community kitchen of a gurdwara, which serves meals to all free of charge, regardless of religion, caste, gender, economic status, or ethnicity. People sit on the floor and eat together, and the kitchen is maintained and serviced by Sikh community volunteers.* - [Wikipedia](https://en.wikipedia.org/wiki/Langar_(Sikhism))

Langar is an app for tracking food bank clients with minimal cost of ownership.

## Setup

Basic Dependancies:
- [Python3.8+ & Pip3](python.org/)
- [Poetry](pythonpoetry.org)
- [Redis](redis.io)

  Developed and Tested for Ubuntu 20.04 - Anything else, YMMV, you're welcome to contribute fixes to change that.
  
## Typical Install Script
  
 ```
 sudo apt update
 sudo apt install python-pip3 docker.io
 pip3 install poetry
 git clone https://github.com/timeartist/langar
 cd langar
 poetry install
 docker run redislabs/redisearch:2.4.3
 poetry shell
 langar
```

## Data
Data is created and maintained in CSV files.  This allows food banks to utilize a variety of formats and reporting methods (excel, google sheets, etc.).  It does limit this application to a single node in serving. It's possible that, in the future, we could make a distributed vs singular configuration for higher scale operations - should the need arise.

Redis and RediSearch are utilized to provide maximum searchability with minimial requirements from a code or operations perspective.  

## Questions, Derivative Works
Please reach out to adi@nederlandfoodpantry.org if you have any questions.  This work is officially **PUBLIC DOMAIN**. Please utilize it to help enable your operations. This is **VERY** basic software. There is no commercial advantage in deriving from it, probably the opposite.  But feel free if you so desire.

*"Everything comes by the Lord's Will, and everything goes by the Lord's Will." - Sri Guru Granth Sahib - Ang 556*
