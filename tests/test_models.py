import copy
import unittest
import datetime

from schematics.models import Model
from schematics.serialize import whitelist
from schematics.models import ModelOptions

from schematics.types.base import StringType, IntType, DateTimeType
from schematics.types.compound import ListType, ModelType
from schematics.exceptions import ValidationError


class TestOptions(unittest.TestCase):
    """This test collection covers the `ModelOptions` class and related
    functions.
    """
    def setUp(self):
        self._class = ModelOptions

    def tearDown(self):
        pass

    def test_good_options_args(self):
        args = {
            'klass': None,
            'roles': None,
        }

        mo = self._class(**args)
        self.assertNotEqual(mo, None)

        # Test that a value for roles was generated
        self.assertEqual(mo.roles, None)

    def test_bad_options_args(self):
        args = {
            'klass': None,
            'roles': None,
            'badkw': None,
        }
        with self.assertRaises(TypeError):
            c = self._class(**args)

    def test_no_options_args(self):
        args = {}
        mo = self._class(None, **args)
        self.assertNotEqual(mo, None)

    def test_options_parsing_from_model(self):
        class Foo(Model):
            class Options:
                namespace = 'foo'
                roles = {}

        f = Foo()
        fo = f._options

        self.assertEqual(fo.__class__, ModelOptions)
        self.assertEqual(fo.namespace, 'foo')
        self.assertEqual(fo.roles, {})


class TestModels(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_with_kwargs(self):
        class Player(Model):
            id = IntType()
            display_name = StringType()

        player = Player(id=1, display="johann")

        self.assertEqual(player.id, 1)
        self.assertEqual(player.display_name, "johann")

    def test_equality(self):
        class TestModel(Model):
            some_int = IntType()

        tm1 = TestModel(some_int=4)
        self.assertEqual(tm1, copy.copy(tm1))

        tm2 = TestModel(some_int=4)
        self.assertEqual(tm1, tm2)

        tm3 = TestModel(some_int=5)

        self.assertTrue(tm1 == tm2)
        self.assertTrue(tm1 != tm3)

    def test_equality_with_submodels(self):
        class Location(Model):
            country_code = StringType()

        class Player(Model):
            id = IntType()
            location = ModelType(Location)

        p1 = Player(id=1, location={"country_code": "US"})
        p2 = Player(id=1, location={"country_code": "US"})

        self.assertTrue(p1.location == p2.location)
        self.assertFalse(p1.location != p2.location)
        self.assertEqual(p1.location, p2.location)

        self.assertTrue(p1 == p2)
        self.assertEqual(p1, p2)

    def test_model_field_list(self):
        it = IntType()

        class TestModel(Model):
            some_int = it

        self.assertEqual({'some_int': it}, TestModel.fields)

    def test_model_data(self):
        class TestModel(Model):
            some_int = IntType()

        self.assertRaises(AttributeError, lambda: TestModel.data)

    def test_instance_data(self):
        class TestModel(Model):
            some_int = IntType()

        tm = TestModel()
        tm.some_int = 5

        self.assertEqual({'some_int': 5}, tm._data)

    def test_dict_interface(self):
        class TestModel(Model):
            some_int = IntType()

        tm = TestModel()
        tm.some_int = 5

        self.assertEqual(True, 'some_int' in tm)
        self.assertEqual(5, tm['some_int'])
        self.assertEqual(True, 'fake_key' not in tm)


class TestModelInterface(unittest.TestCase):

    def setUp(self):
        pass

    def test_validate_input_partial(self):
        class TestModel(Model):
            name = StringType(required=True)
            bio = StringType()
        model = TestModel()
        self.assertEqual(model.validate({'bio': 'Genius'}, partial=True), True)
        self.assertEqual(model.bio, 'Genius')

    def test_raises_validation_error_on_init(self):
        class User(Model):
            name = StringType(required=True)
            bio = StringType(required=True)

        with self.assertRaises(ValidationError):
            User(name="Joe")

    def test_model_inheritance(self):
        class Parent(Model):
            name = StringType(required=True)

        class Child(Parent):
            bio = StringType()

        self.assertEqual(hasattr(Child(), '_options'), True)

        input_data = {'bio': u'Genius', 'name': u'Joey'}

        model = Child(name="Joey")
        self.assertEqual(model.validate(input_data), True)
        self.assertEqual(model.serialize(), input_data)

        child = Child(name="Baby Jane", bio="Always behaves")
        self.assertEqual(child.name, "Baby Jane")
        self.assertEqual(child.bio, "Always behaves")

        model = Child()

        self.assertEqual(hasattr(model, '_options'), True)

        input = {'bio': u'Genius', 'name': u'Joey'}
        self.assertEqual(model.validate(input), True)
        self.assertEqual(model.serialize(), input)

    def test_role_propagate(self):
        class Address(Model):
            city = StringType()
            class Options:
                roles = {'public': whitelist('city')}
        class User(Model):
            name = StringType(required=True)
            password = StringType()
            addresses = ListType(ModelType(Address))
            class Options:
                roles = {'public': whitelist('name')}
        model = User()
        self.assertEqual(model.validate({'name': 'a', 'addresses': [{'city': 'gotham'}]}), True)
        self.assertEqual(model.addresses[0].city, 'gotham')


class TestCompoundTypes(unittest.TestCase):
    """
    """

    def test_init(self):
        class User(Model):
            pass
        User()

    def test_field_default(self):
        class User(Model):
            name = StringType(default=u'Doggy')
        u = User()
        self.assertEqual(User.name.__class__, StringType)
        self.assertEqual(u.name, u'Doggy')

    def test_model_type(self):
        class User(Model):
            name = StringType()
        class Card(Model):
            user = ModelType(User)
        c = Card(user={'name': u'Doggy'})
        self.assertIsInstance(c.user, User)

    def test_as_field_validate(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        c = Card()
        c.validate(dict(user={'name': u'Doggy'}))
        self.assertEqual(c.user.name, u'Doggy')
        self.assertEqual(c.validate(dict(user=[1])), False)
        self.assertEqual(c.user.name, u'Doggy', u'Validation should not remove or modify existing data')

        c = Card()
        self.assertEqual(c.validate(dict(user=[1])), False)
        self.assertRaises(AttributeError, lambda: c.user.name)

    def test_model_field_validate_structure(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            user = ModelType(User)

        c = Card()
        c.validate({'user': [1, 2]})
        self.assertIn('user', c.errors)

    def test_list_field(self):
        class User(Model):
            ids = ListType(StringType)
        c = User()
        self.assertEqual(c.validate({'ids': []}), True)

    def test_list_field_required(self):
        class User(Model):
            ids = ListType(StringType, required=True)

        c = User(ids=[])

        self.assertEqual(c.validate({'ids': [None]}), False)
        self.assertIsInstance(c.errors, dict)

    def test_list_field_convert(self):
        class User(Model):
            ids = ListType(IntType)
            date = DateTimeType()

        c = User()
        self.assertEqual(c.validate({'ids': ["1", "2"]}), True)
        self.assertEqual(c.ids, [1, 2])
        now = datetime.datetime.now()
        self.assertEqual(c.validate({'date': now.isoformat()}), True)
        self.assertEqual(c.date, now)

    def test_list_model_field(self):
        class User(Model):
            name = StringType()

        class Card(Model):
            users = ListType(ModelType(User), min_size=1)

        data = {'users': [{'name': u'Doggy'}]}
        c = Card(**data)

        valid = c.validate({'users': None})
        self.assertFalse(valid)
        self.assertEqual(c.errors['users'], [u'This field is required.'])
        self.assertEqual(c.users[0].name, u'Doggy')
