from django.utils import simplejson as json
from dajaxice.core import dajaxice_functions
from dajaxice.decorators import dajaxice_register
from django.views.decorators.cache import cache_page
from django.core import serializers
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from ietf.ietfauth.decorators import group_required, has_role
from ietf.name.models import TimeSlotTypeName
from django.http import HttpResponseRedirect, HttpResponse, Http404, QueryDict, Http403

from ietf.meeting.helpers import get_meeting, get_schedule, get_schedule_by_id, agenda_permissions
from ietf.meeting.views   import edit_timeslots, edit_agenda


# New models
from ietf.meeting.models import Meeting, TimeSlot, Session
from ietf.meeting.models import Schedule, ScheduledSession, Room
from ietf.group.models import Group
import datetime

import logging
import sys
from ietf.settings import LOG_DIR

log = logging.getLogger(__name__)

@dajaxice_register
def readonly(request, meeting_num, schedule_id):
    meeting = get_meeting(meeting_num)
    schedule = get_schedule_by_id(meeting, schedule_id)

    secretariat = False
    write_perm  = False

    cansee,canedit = agenda_permissions(meeting, schedule, request.user)
    read_only = not canedit

    user = request.user
    if has_role(user, "Secretariat"):
        secretariat = True
        write_perm  = True

    if has_role(user, "Area Director"):
        write_perm  = True

    try:
        person = user.get_profile()
        if person is not None and schedule.owner == user.person:
            read_only = False
    except:
        # specific error if user has no profile...
        pass

    return json.dumps(
        {'secretariat': secretariat,
         'write_perm':  write_perm,
         'owner_href':  schedule.owner.url(request.get_host_protocol()),
         'read_only':   read_only})

@group_required('Area Director','Secretariat')
@dajaxice_register
def update_timeslot(request, schedule_id, session_id, scheduledsession_id=None, extended_from_id=None, duplicate=False):
    schedule = get_object_or_404(Schedule, pk = int(schedule_id))
    meeting  = schedule.meeting
    ss_id = 0
    ess_id = 0
    ess = None
    ss = None

    print "duplicate: %s schedule.owner: %s user: %s" % (duplicate, schedule.owner, request.user.get_profile())
    cansee,canedit = agenda_permissions(meeting, schedule, request.user)

    if not canedit:
        raise Http403
        return json.dumps({'error':'no permission'})

    session_id = int(session_id)
    session = get_object_or_404(meeting.session_set, pk=session_id)

    if scheduledsession_id is not None:
        ss_id = int(scheduledsession_id)

    if extended_from_id is not None:
        ess_id = int(extended_from_id)

    if ss_id != 0:
        ss = get_object_or_404(schedule.scheduledsession_set, pk=ss_id)

    # need a way to clean up a two sessions in one slot situation, the
    # extra scheduledsessions need to be cleaned up.

    if ess_id == 0:
        # if this is None, then we must be moving.
        for ssO in schedule.scheduledsession_set.filter(session = session):
            print "sched(%s): removing session %s from slot %u" % ( schedule, session, ssO.pk )
            #if ssO.extendedfrom is not None:
            #    ssO.extendedfrom.session = None
            #    ssO.extendedfrom.save()
            ssO.session = None
            ssO.extendedfrom = None
            ssO.save()
    else:
        ess = get_object_or_404(schedule.scheduledsession_set, pk = ess_id)
        ss.extendedfrom = ess

    try:
        # find the scheduledsession, assign the Session to it.
        if ss:
            print "ss.session: %s session:%s duplicate=%s"%(ss, session, duplicate)
            ss.session = session
            if(duplicate):
                ss.id = None
            ss.save()
    except Exception as e:
        return json.dumps({'error':'invalid scheduledsession'})

    return json.dumps({'message':'valid'})

@group_required('Secretariat')
@dajaxice_register
def update_timeslot_purpose(request, timeslot_id=None, purpose=None):
    ts_id = int(timeslot_id)
    try:
       timeslot = TimeSlot.objects.get(pk=ts_id)
    except:
        return json.dumps({'error':'invalid timeslot'})

    try:
        timeslottypename = TimeSlotTypeName.objects.get(pk = purpose)
    except:
        return json.dumps({'error':'invalid timeslot type',
                           'extra': purpose})

    timeslot.type = timeslottypename
    timeslot.save()

    return json.dumps(timeslot.json_dict(request.get_host_protocol))

#############################################################################
## ROOM API
#############################################################################
from django.forms.models import modelform_factory
AddRoomForm = modelform_factory(Room, exclude=('meeting',))

# no authorization required
def timeslot_roomlist(request, mtg):
    rooms = mtg.room_set.all()
    json_array=[]
    for room in rooms:
        json_array.append(room.json_dict(request.get_host_protocol))
    return HttpResponse(json.dumps(json_array),
                        mimetype="application/json")

@group_required('Secretariat')
def timeslot_addroom(request, meeting):
    # authorization was enforced by the @group_require decorator above.

    newroomform = AddRoomForm(request.POST)
    if not newroomform.is_valid():
        return HttpResponse(status=404)

    newroom = newroomform.save(commit=False)
    newroom.meeting = meeting
    newroom.save()
    newroom.create_timeslots()

    if "HTTP_ACCEPT" in request.META and "application/json" in request.META['HTTP_ACCEPT']:
        url = reverse(timeslot_roomurl, args=[meeting.number, newroom.pk])
        #log.debug("Returning timeslot_roomurl: %s " % (url))
        return HttpResponseRedirect(url)
    else:
        return HttpResponseRedirect(
            reverse(edit_timeslots, args=[meeting.number]))

@group_required('Secretariat')
def timeslot_delroom(request, meeting, roomid):
    # authorization was enforced by the @group_require decorator above.
    room = get_object_or_404(meeting.room_set, pk=roomid)

    room.delete_timeslots()
    room.delete()
    return HttpResponse('{"error":"none"}', status = 200)

def timeslot_roomsurl(request, num=None):
    meeting = get_meeting(num)

    if request.method == 'GET':
        return timeslot_roomlist(request, meeting)
    elif request.method == 'POST':
        return timeslot_addroom(request, meeting)

    # unacceptable reply
    return HttpResponse(status=406)

def timeslot_roomurl(request, num=None, roomid=None):
    meeting = get_meeting(num)

    if request.method == 'GET':
        room = get_object_or_404(meeting.room_set, pk=roomid)
        return HttpResponse(json.dumps(room.json_dict(request.get_host_protocol())),
                            mimetype="application/json")
    elif request.method == 'PUT':
        return timeslot_updroom(request, meeting)
    elif request.method == 'DELETE':
        return timeslot_delroom(request, meeting, roomid)

#############################################################################
## DAY/SLOT API
#############################################################################
AddSlotForm = modelform_factory(TimeSlot, exclude=('meeting','name','location','sessions', 'modified'))

# no authorization required to list.
def timeslot_slotlist(request, mtg):
    slots = mtg.timeslot_set.all()
    json_array=[]
    for slot in slots:
        json_array.append(slot.json_dict(request.get_host_protocol()))
    return HttpResponse(json.dumps(json_array),
                        mimetype="application/json")

@group_required('Secretariat')
def timeslot_addslot(request, meeting):

    # authorization was enforced by the @group_require decorator above.
    addslotform = AddSlotForm(request.POST)
    #log.debug("newslot: %u" % ( addslotform.is_valid() ))
    if not addslotform.is_valid():
        return HttpResponse(status=404)

    newslot = addslotform.save(commit=False)
    newslot.meeting = meeting
    newslot.save()

    newslot.create_concurrent_timeslots()

    if "HTTP_ACCEPT" in request.META and "application/json" in request.META['HTTP_ACCEPT']:
        return HttpResponseRedirect(
            reverse(timeslot_dayurl, args=[meeting.number, newroom.pk]))
    else:
        return HttpResponseRedirect(
            reverse(edit_timeslots, args=[meeting.number]))

@group_required('Secretariat')
def timeslot_delslot(request, meeting, slotid):
    # authorization was enforced by the @group_require decorator above.
    slot = get_object_or_404(meeting.timeslot_set, pk=slotid)

    # this will delete self as well.
    slot.delete_concurrent_timeslots()
    return HttpResponse('{"error":"none"}', status = 200)

def timeslot_slotsurl(request, num=None):
    meeting = get_meeting(num)

    if request.method == 'GET':
        return timeslot_slotlist(request, meeting)
    elif request.method == 'POST':
        return timeslot_addslot(request, meeting)

    # unacceptable reply
    return HttpResponse(status=406)

def timeslot_sloturl(request, num=None, slotid=None):
    meeting = get_meeting(num)

    if request.method == 'GET':
        slot = get_object_or_404(meeting.timeslot_set, pk=slotid)
        return HttpResponse(json.dumps(slot.json_dict(request.get_host_protocol())),
                            mimetype="application/json")
    elif request.method == 'PUT':
        # not yet implemented!
        return timeslot_updslot(request, meeting)
    elif request.method == 'DELETE':
        return timeslot_delslot(request, meeting, slotid)

#############################################################################
## Agenda List API
#############################################################################
AgendaEntryForm = modelform_factory(Schedule, exclude=('meeting','owner'))
EditAgendaEntryForm = modelform_factory(Schedule, exclude=('meeting','owner', 'name'))

@group_required('Area Director','Secretariat')
def agenda_list(request, mtg):
    agendas = mtg.schedule_set.all()
    json_array=[]
    for agenda in agendas:
        json_array.append(agenda.json_dict(request.get_host_protocol))
    return HttpResponse(json.dumps(json_array),
                        mimetype="application/json")

# duplicates save-as functionality below.
@group_required('Area Director','Secretariat')
def agenda_add(request, meeting):
    # authorization was enforced by the @group_require decorator above.

    newagendaform = AgendaEntryForm(request.POST)
    if not newagendaform.is_valid():
        return HttpResponse(status=404)

    newagenda = newagendaform.save(commit=False)
    newagenda.meeting = meeting
    newagenda.owner   = request.user.get_profile()
    newagenda.save()

    if "HTTP_ACCEPT" in request.META and "application/json" in request.META['HTTP_ACCEPT']:
        url =  reverse(agenda_infourl, args=[meeting.number, newagenda.name])
        #log.debug("Returning agenda_infourl: %s " % (url))
        return HttpResponseRedirect(url)
    else:
        return HttpResponseRedirect(
            reverse(edit_agenda, args=[meeting.number, newagenda.name]))

@group_required('Area Director','Secretariat')
def agenda_update(request, meeting, schedule):
    # authorization was enforced by the @group_require decorator above.

    # forms are completely useless for update actions that want to
    # accept a subset of values.
    update_dict = QueryDict(request.raw_post_data, encoding=request._encoding)

    #log.debug("99 meeting.agenda: %s / %s / %s" %
    #          (schedule, update_dict, request.raw_post_data))

    user = request.user
    if has_role(user, "Secretariat"):
        if "public" in update_dict:
            value1 = True
            value = update_dict["public"]
            if value == "0" or value == 0 or value=="false":
                value1 = False
            log.debug("setting public for %s to %s" % (schedule, value1))
            schedule.public = value1

    if "visible" in update_dict:
        value1 = True
        value = update_dict["visible"]
        if value == "0" or value == 0 or value=="false":
            value1 = False
        log.debug("setting visible for %s to %s" % (schedule, value1))
        schedule.visible = value1

    if "name" in update_dict:
        value = update_dict["name"]
        log.debug("setting name for %s to %s" % (schedule, value))
        schedule.name = value

    schedule.save()

    # enforce that a non-public schedule can not be the public one.
    if meeting.agenda == schedule and not schedule.public:
        meeting.agenda = None
        meeting.save()

    if "HTTP_ACCEPT" in request.META and "application/json" in request.META['HTTP_ACCEPT']:
        return HttpResponse(json.dumps(schedule.json_dict(request.get_host_protocol())),
                            mimetype="application/json")
    else:
        return HttpResponseRedirect(
            reverse(edit_agenda, args=[meeting.number, schedule.name]))

@group_required('Secretariat')
def agenda_del(request, meeting, schedule):
    schedule.delete_scheduledsessions()
    #log.debug("deleting meeting: %s agenda: %s" % (meeting, meeting.agenda))
    if meeting.agenda == schedule:
        meeting.agenda = None
        meeting.save()
    schedule.delete()
    return HttpResponse('{"error":"none"}', status = 200)

def agenda_infosurl(request, num=None):
    meeting = get_meeting(num)

    if request.method == 'GET':
        return agenda_list(request, meeting)
    elif request.method == 'POST':
        return agenda_add(request, meeting)

    # unacceptable action
    return HttpResponse(status=406)

def agenda_infourl(request, num=None, schedule_name=None):
    meeting = get_meeting(num)
    #log.debug("agenda: %s / %s" % (meeting, schedule_name))

    schedule = get_schedule(meeting, schedule_name)
    #log.debug("results in agenda: %u / %s" % (schedule.id, request.method))

    if request.method == 'GET':
        return HttpResponse(json.dumps(schedule.json_dict(request.get_host_protocol())),
                            mimetype="application/json")
    elif request.method == 'PUT':
        return agenda_update(request, meeting, schedule)
    elif request.method == 'DELETE':
        return agenda_del(request, meeting, schedule)
    else:
        return HttpResponse(status=406)

#############################################################################
## Meeting API  (very limited)
#############################################################################

def meeting_get(request, meeting):
    return HttpResponse(json.dumps(meeting.json_dict(request.get_host_protocol()),
                                sort_keys=True, indent=2),
                        mimetype="application/json")

@group_required('Secretariat')
def meeting_update(request, meeting):
    # authorization was enforced by the @group_require decorator above.

    # at present, only the official agenda can be updated from this interface.
    update_dict = QueryDict(request.raw_post_data, encoding=request._encoding)

    #log.debug("1 meeting.agenda: %s / %s / %s" % (meeting.agenda, update_dict, request.raw_post_data))
    if "agenda" in update_dict:
        value = update_dict["agenda"]
        #log.debug("4 meeting.agenda: %s" % (value))
        if value is None or value == "None":
            meeting.agenda = None
        else:
            schedule = get_schedule(meeting, value)
            if not schedule.public:
                return HttpResponse(status = 406)
            #log.debug("3 meeting.agenda: %s" % (schedule))
            meeting.agenda = schedule

    #log.debug("2 meeting.agenda: %s" % (meeting.agenda))
    meeting.save()
    return meeting_get(request, meeting)

def meeting_json(request, meeting_num):
    meeting = get_meeting(meeting_num)

    if request.method == 'GET':
        return meeting_get(request, meeting)
    elif request.method == 'PUT':
        return meeting_update(request, meeting)
    elif request.method == 'POST':
        return meeting_update(request, meeting)

    else:
        return HttpResponse(status=406)


#############################################################################
## Agenda Editing API functions
#############################################################################

# this get_info needs to be replaced once we figure out how to get rid of silly
# ajax state we are passing through.
# XXX believed to be obsolete now?
@dajaxice_register
def get_info(request, scheduledsession_id=None, active_slot_id=None, timeslot_id=None, session_id=None):#, event):

    try:
        session = Session.objects.get(pk=int(session_id))
    except Session.DoesNotExist:
        log.debug("No ScheduledSession was found for id:%s" % (session_id))
        # in this case we want to return empty the session information and perhaps indicate to the user there is a issue.
        return


    sess1 = session.json_dict(request.get_host_protocol())
    sess1['active_slot_id'] = str(active_slot_id)
    sess1['ss_id']          = str(scheduledsession_id)
    sess1['timeslot_id']    = str(timeslot_id)

    return json.dumps(sess1, sort_keys=True, indent=2)

def session_json(request, num, sessionid):
    meeting = get_meeting(num)

    try:
        session = meeting.session_set.get(pk=int(sessionid))
    except Session.DoesNotExist:
        return json.dumps({'error':"no such session %s" % sessionid})

    sess1 = session.json_dict(request.get_host_protocol())
    return HttpResponse(json.dumps(sess1, sort_keys=True, indent=2),
                        mimetype="application/json")

# current dajaxice does not support GET, only POST.
# it has almost no value for GET, particularly if the results are going to be
# public anyway.   Cache for 1 day.
@cache_page(86400)
def session_constraints(request, num=None, sessionid=None):
    meeting = get_meeting(num)

    #print "Getting meeting=%s session contraints for %s" % (num, sessionid)
    try:
        session = meeting.session_set.get(pk=int(sessionid))
    except Session.DoesNotExist:
        return json.dumps({"error":"no such session"})

    constraint_list = session.constraints_dict(request.get_host_protocol())

    json_str = json.dumps(constraint_list,
                          sort_keys=True, indent=2),
    #print "  gives: %s" % (json_str)

    return HttpResponse(json_str, mimetype="application/json")



