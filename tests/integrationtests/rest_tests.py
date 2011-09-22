import json
from unittest2 import TestCase
from paste.fixture import TestApp
from nose.tools import *
from lib import web
from mock import Mock

import mixins
from   mixins import AppSetupMixin

from framework.config import Config
from framework.session_holder import SessionHolder
import main

from controllers.rest import ForbiddenError
from controllers.rest import NeedInstance
from controllers.rest import NotFoundError
from controllers.rest import NonProjectMemberReadOnly
from controllers.rest import NeedVolunteerList
from controllers.rest import RestController
from controllers.rest import Serializer

class Test_RestController_instanceToDict (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_return_user_object_dict_with_mapper_names_instead_of_table_names(self):
        from giveaminute.models import *
        cont = RestController()
        user = cont.orm.query(User).get(1)

        result = cont.instance_to_dict(user)

        assert_in('id', result)
        assert_not_in('user_id', result)


class Test_Needs_REST_endpoint (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_not_allow_anonymous_user_to_create_needs(self):
        # Check out http://webpy.org/cookbook/testing_with_paste_and_nose for
        # more about testing with Paste.
        from giveaminute.models import Need
        from framework.orm_holder import OrmHolder

        orm = OrmHolder().orm
        orig_needs = len(orm.query(Need).all())

        response = self.app.post('/rest/v1/needs/',
            params={
                'type': 'volunteer',
                'request': 'basketball players',
                'quantity': '5',
                'description': 'Play on my basketball team',
                'project_id': 1,
            },
            status=403)

        final_needs = len(orm.query(Need).all())
        assert_equal(orig_needs, final_needs)

    @istest
    def should_allow_admin_user_to_update_needs(self):
        self.login(user_id=3)

        response = self.app.post('/rest/v1/needs/1/',
            params={
                '_method': 'PUT',
                'type': 'volunteer',
                'request': 'basketball players',
                'quantity': '5',
                'description': 'Play on my basketball team',
                'address': 'Code for America, 85 2nd St., San Francisco, CA 94105',
                'date': 'August 10, 2011',
                'time': 'early afternoon',
                'duration': 'a couple hours',
                'project_id': 1,
            },
            status=200)

        assert '"quantity": "5"' in response
        assert '"id": "1"' in response

    @istest
    def should_allow_admin_user_to_create_needs(self):
        self.login(user_id=3)

        response = self.app.post('/rest/v1/needs/',
            params={
                'type': 'volunteer',
                'request': 'basketball players',
                'quantity': '5',
                'description': 'Play on my basketball team',
                'address': 'Code for America, 85 2nd St., San Francisco, CA 94105',
                'date': 'August 10, 2011',
                'time': 'early afternoon',
                'duration': 'a couple hours',
                'project_id': 1,
            },
            status=200)

        assert '"quantity": "5"' in response

class Test_NeedsRestEndpoint_GET (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_return_a_reasonable_representation_of_a_need(self):
        response = self.app.get('/rest/v1/needs/1/', status=200)

        response_dict = json.loads(response.body)
        assert_equal(response_dict["request"], "gardeners")

    @istest
    def should_include_the_address_object_in_the_return_value(self):
        response = self.app.get('/rest/v1/needs/2/', status=200)

        response_dict = json.loads(response.body)
        assert_equal(response_dict["address"], "Frugal 4 House, 563 46th St., Oakland, CA 94609")

    @istest
    def should_include_a_pretty_date_in_the_list(self):
        response = self.app.get('/rest/v1/needs/', status=200)

        response_list = json.loads(response.body)
        for need_dict in response_list:
            print need_dict["display_date"]
            if need_dict["display_date"] == "August 26th":
                ok_(True)
                return
        ok_(False)

    @istest
    def should_include_a_pretty_date_in_the_return_value(self):
        response = self.app.get('/rest/v1/needs/2/', status=200)

        response_dict = json.loads(response.body)
        assert_equal(response_dict["display_date"], "August 26th")

    @istest
    def should_include_the_volunteers_in_the_return_value(self):
        response = self.app.get('/rest/v1/needs/1/', status=200)

        response_dict = json.loads(response.body)
        assert_in("volunteers", response_dict)
        assert_equal(len(response_dict['volunteers']), 2)

    @istest
    def should_include_the_volunteer_avatars_in_the_return_value(self):
        response = self.app.get('/rest/v1/needs/1/', status=200)

        response_dict = json.loads(response.body)
        for volunteer_dict in response_dict['volunteers']:
            assert_in("avatar_path", volunteer_dict)

    @istest
    def should_not_include_the_volunteer_passwords_in_the_return_value(self):
        response = self.app.get('/rest/v1/needs/1/', status=200)

        response_dict = json.loads(response.body)
        for volunteer_dict in response_dict['volunteers']:
            assert_not_in("password", volunteer_dict)
            assert_not_in("salt", volunteer_dict)

    @istest
    def should_include_a_display_name_for_each_user_in_the_return_value(self):
        response = self.app.get('/rest/v1/needs/1/', status=200)

        response_dict = json.loads(response.body)
        for volunteer_dict in response_dict['volunteers']:
            assert_in("display_name", volunteer_dict)


class Test_NeedInstance_REST_READ (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_return_a_dictionary(self):
        controller = NeedInstance()
        response = controller.REST_READ(1)

        assert_equal(response.__class__.__name__, 'dict')

    @istest
    def should_not_raise_NotFoundError(self):
        controller = NeedInstance()

        try:
            response = controller.REST_READ(1)
        except NotFoundError:
            ok_(False)


class Test_NeedVolunteersRestEndpoint_POST (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_return_forbidden_when_no_user_is_logged_in(self):
        response = self.app.post('/rest/v1/needs/2/volunteers/',
            params={
                'member_id':u'1'
            }, status=403)

#    @istest
#    def should_(self):
#        self.login(user_id=3)
#        response = self.app.post('/rest/v1/needs/',
#            params={
#                'type': 'volunteer',
#                'request': 'basketball players',
#                'quantity': '5',
#                'description': 'Play on my basketball team',
#                'address[name]': 'Code for America',
#                'address[street]': '85 2nd St.',
#                'address[city]': 'San Francisco, CA 94105',
#                'date': 'August 10, 2011',
#                'time': 'early afternoon',
#                'duration': 'a couple hours',
#                'project_id': 0,
#            },
#            status=200)


class Test_NeedVolunteersList_REST_CREATE (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_create_a_new_volunteer_when_user_is_member_of_needs_project(self):
        from giveaminute.models import User
        cont = NeedVolunteerList()
        cont.user = cont.orm.query(User).get(1)

        web.ctx.env['REQUEST_METHOD'] = 'GET'
        web.ctx.env['SCRIPT_NAME'] = ''
        obj = cont.REST_CREATE(u'2', member_id=u'1')
        assert isinstance(obj, dict)

    @istest
    def should_not_allow_anonymous_user_to_create_volunteers(self):
        from giveaminute.models import User, Volunteer
        cont = NeedVolunteerList()
        orig_needs = len(cont.orm.query(Volunteer).all())

        web.ctx.env['REQUEST_METHOD'] = 'GET'
        web.ctx.env['SCRIPT_NAME'] = ''

        try:
            obj = cont.REST_CREATE(u'2', member_id=u'1')
        except ForbiddenError:
            final_needs = len(cont.orm.query(Volunteer).all())
            assert_equal(orig_needs, final_needs)
        else:
            ok_(False)


class Test_RestController__BASE_METHOD_HANDLER (AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    def test_that_it_sets_the_user_to_an_sqlalchemy_object_if_its_a_gam_object(self):
        import giveaminute.models
        import giveaminute.user

        self.login(user_id=1)

        cont = RestController()
        cont.REST_FAKE = lambda: None

        cont._BASE_METHOD_HANDLER(['REST_FAKE'])

        assert_is_instance(cont.user, giveaminute.models.User)


class Test_NonProjectMemberReadOnly_IsMember(AppSetupMixin, TestCase):
    fixtures = ['aarons_db_20110826.sql']

    @istest
    def should_return_true_if_user_is_member(self):
        from framework.orm_holder import OrmHolder
        from giveaminute.models import Project, User

        orm = OrmHolder().orm
        user = orm.query(User).get(1)
        project = orm.query(Project).get(1)
        rules = NonProjectMemberReadOnly()

        assert rules.is_member(user, project)


class Test_Serializer_serialize (AppSetupMixin, TestCase):

    @istest
    def dates_are_converted_to_iso_strings(self):
        import datetime

        serializer = Serializer()
        serialized = serializer.serialize(datetime.date(2011,8,2))

        assert_equal(serialized, '2011-08-02')