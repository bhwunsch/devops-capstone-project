"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_read(self):
        """It should read an account"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], account.name)

    def test_bad_read(self):
        """It should fail to read a bad account id"""
        account = self._create_accounts(1)[0]
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        #check for it to fail finding an account, use a bad id
        bad_id = 2222
        resp = self.client.get(
            f"{BASE_URL}/{bad_id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update(self):
        """It should change update an account"""
        #create an account
        account = self._create_accounts(1)[0]
        #find the account
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            print('test_update, account not found')
        else:
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #get data from found account
        found_account = resp.get_json()
        
        #check found data is same as created data
        self.assertEqual(account.id, found_account["id"])
        self.assertEqual(account.name, found_account["name"])
        
        #make modification to found data
        found_account["name"] = "Cyrano"

        #update()
        resp = self.client.put(
            f'{BASE_URL}/{found_account["id"]}', 
            content_type="application/json",
            json = found_account
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        #find the updated account - same id
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            print('test_update, updated account not found')
        
        updated_account = resp.get_json()

        #check that updated account = modified found data
        self.assertEqual(account.id, updated_account["id"])
        self.assertEqual(found_account["id"], updated_account["id"])
        self.assertEqual(found_account["name"], updated_account["name"])

        #check that updated account != created data
        self.assertNotEqual(account.name, updated_account["name"])
        
    def test_bad_update(self):
        """It should fail to update an account using a bogus id"""
        #create an account
        account = self._create_accounts(1)[0]
        #find the account
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            print('test_update, account not found')
        else:
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #get data from found account
        found_account = resp.get_json()
        
        #check found data is same as created data
        self.assertEqual(account.id, found_account["id"])
        self.assertEqual(account.name, found_account["name"])
        
        #make modification to found data
        found_account["name"] = "Cyrano"

        #give bogus id
        found_account["id"] = account.id + 9999

        #update()
        resp = self.client.put(
            f'{BASE_URL}/{found_account["id"]}', 
            content_type="application/json",
            json = found_account
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete(self):
        """It should delete an account"""
        #create an account
        account = self._create_accounts(1)[0]
        #check that it does exist
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            print('test_update, account not found')
        else:
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
        
        #delete account
        resp = self.client.delete(
            f"{BASE_URL}/{account.id}", content_type = "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        #check that it doesn't exist
        resp = self.client.get(
            f"{BASE_URL}/{account.id}", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self):
        """It should return all accounts in database"""
        #create an array of accounts
        accounts = self._create_accounts(3)
        accounts_size = len(accounts)

        #get list of all arrays in database
        resp = self.client.get(
            BASE_URL, content_type = "application/json"
        )
        data = resp.get_json()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), accounts_size)

        #out of curiosity, is the data returned the same order as when accounts created?
        for i in range(len(data)):
            self.assertEqual(data[i]["name"], accounts[i].name)
    
    def test_method_not_allowed(self):
        """It should show method not allowed"""
        resp = self.client.put(
            BASE_URL, content_type = "application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)