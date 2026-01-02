"""Contain fixtures to fill application db"""
import factory
from factory import Faker as FactoryFaker
import random
from models.application import Users

class UserFactory(factory.Factory):
    class Meta:
        model = Users

    userid = factory.Sequence(lambda n: 'user_%d' % n)
    passwd = FactoryFaker('password')
    surname = FactoryFaker('last_name')
    forename = FactoryFaker('first_name')
    telno = FactoryFaker('phone_number')
    addr1 = FactoryFaker('street_address')
    addr2 = FactoryFaker('secondary_address')
    city = FactoryFaker('city')
    state = FactoryFaker('state')
    postcode = FactoryFaker('postcode')
    active = factory.LazyFunction(lambda: random.choice(['Y', 'N']))
    admin = factory.LazyFunction(lambda: 'Y' if random.random() > 0.95 else 'N')