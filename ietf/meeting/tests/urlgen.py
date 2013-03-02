import base64
import sys
from django.test import TestCase, Client

from django.contrib.auth.models import User
from ietf.person.models import Person
from ietf.meeting.models  import Meeting, TimeSlot, Session, ScheduledSession
from ietf.meeting.models  import Constraint
from ietf.group.models    import Group


class UrlGenTestCase(TestCase):
    fixtures = [ 'names.xml',  # ietf/names/fixtures/names.xml for MeetingTypeName, and TimeSlotTypeName
                 'meeting83.json',
                 'constraint83.json',
                 'workinggroups.json',
                 'groupgroup.json',
                 'person.json', 'users.json' ]

    def test_meetingGeneratesUrl(self):
        mtg83 = Meeting.objects.get(pk=83)
        hostport = "http://datatracker.ietf.org"
        self.assertEqual(mtg83.url(hostport), "http://datatracker.ietf.org/meeting/83.json")

    def test_groupGeneratesUrl(self):
        group1 = Group.objects.get(pk=1730)
        hostport = "http://datatracker.ietf.org"
        self.assertEqual(group1.url(hostport), "http://datatracker.ietf.org/group/roll.json")

