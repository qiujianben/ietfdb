# Copyright (C) 2009 Nokia Corporation and/or its subsidiary(-ies).
# All rights reserved. Contact: Pasi Eronen <pasi.eronen@nokia.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#
#  * Neither the name of the Nokia Corporation and/or its
#    subsidiary(-ies) nor the names of its contributors may be used
#    to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.conf.urls.defaults import patterns, url, include
from ietf.idrfc import views_search, views_edit, views_ballot, views
from ietf.doc.models import State
from ietf.doc import views_status_change
from ietf.doc import views_doc

urlpatterns = patterns('',
    (r'^/?$', views_search.search),
    url(r'^search/$', views_search.search, name="doc_search"),
    url(r'^in-last-call/$', views_search.drafts_in_last_call, name="drafts_in_last_call"),
    url(r'^ad/(?P<name>[A-Za-z0-9.-]+)/$', views_search.drafts_for_ad, name="drafts_for_ad"),
#    url(r'^ad2/(?P<name>[A-Za-z0-9.-]+)/$', views_search.docs_for_ad, name="docs_for_ad"),
    url(r'^ad2/(?P<name>[A-Za-z0-9.-]+)/$', views_search.docs_for_ad, name="docs_for_ad"),

#    (r'^all/$', views_search.all), # XXX CHECK MERGE
#    (r'^active/$', views_search.active), # XXX CHECK MERGE
    url(r'^rfc-status-changes/$', views_status_change.rfc_status_changes, name='rfc_status_changes'), 
    url(r'^start-rfc-status-change/(?P<name>[A-Za-z0-9._+-]*)$', views_status_change.start_rfc_status_change, name='start_rfc_status_change'), 
    url(r'^iesg/(?P<last_call_only>[A-Za-z0-9.-]+/)?$', views_search.drafts_in_iesg_process, name="drafts_in_iesg_process"),

    url(r'^all/$', views_search.index_all_drafts, name="index_all_drafts"),
    url(r'^active/$', views_search.index_active_drafts, name="index_active_drafts"),

    url(r'^(?P<name>[A-Za-z0-9._+-]+)/((?P<rev>[0-9-]+)/)?$', views_doc.document_main, name="doc_view"),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/history/$', views_doc.document_history, name="doc_history"),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/writeup/$', views_doc.document_writeup, name="doc_writeup"),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/shepherdwriteup/$', views_doc.document_shepherd_writeup, name="doc_shepherd_writeup"),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/ballot/(?P<ballot_id>[0-9]+)/position/$', views_ballot.edit_position),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/ballot/(?P<ballot_id>[0-9]+)/emailposition/$', views_ballot.send_ballot_comment, name='doc_send_ballot_comment'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/ballot/(?P<ballot_id>[0-9]+)/$', views_doc.document_ballot, name="doc_ballot"),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/ballot/$', views_doc.document_ballot, name="doc_ballot"),
    (r'^(?P<name>[A-Za-z0-9._+-]+)/doc.json$', views_doc.document_json),
    (r'^(?P<name>[A-Za-z0-9._+-]+)/ballotpopup/(?P<ballot_id>[0-9]+)/$', views_doc.ballot_popup),
    #(r'^(?P<name>[A-Za-z0-9._+-]+)/ballot.json$', views_doc.ballot_json), # legacy view

    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/state/$', views_edit.change_state, name='doc_change_state'), # IESG state
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/state/(?P<state_type>iana-action|iana-review)/$', views_edit.change_iana_state, name='doc_change_iana_state'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/info/$', views_edit.edit_info, name='doc_edit_info'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/requestresurrect/$', views_edit.request_resurrect, name='doc_request_resurrect'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/resurrect/$', views_edit.resurrect, name='doc_resurrect'),                       
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/addcomment/$', views_edit.add_comment, name='doc_add_comment'),

    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/stream/$', views_edit.change_stream, name='doc_change_stream'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/notify/$', views_edit.edit_notices, name='doc_change_notify'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/status/$', views_edit.change_intention, name='doc_change_intended_status'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/telechat/$', views_edit.telechat_date, name='doc_change_telechat_date'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/iesgnote/$', views_edit.edit_iesg_note, name='doc_change_iesg_note'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/ad/$', views_edit.edit_ad, name='doc_change_ad'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/consensus/$', views_edit.edit_consensus, name='doc_edit_consensus'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/shepherd/$', views_edit.edit_shepherd, name='doc_edit_shepherd'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/shepherdwriteup/$', views_edit.edit_shepherd_writeup, name='doc_edit_shepherd_writeup'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/requestpublication/$', views_edit.request_publication, name='doc_request_publication'),

    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/clearballot/$', views_ballot.clear_ballot, name='doc_clear_ballot'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/deferballot/$', views_ballot.defer_ballot, name='doc_defer_ballot'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/undeferballot/$', views_ballot.undefer_ballot, name='doc_undefer_ballot'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/lastcalltext/$', views_ballot.lastcalltext, name='doc_ballot_lastcall'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/ballotwriteupnotes/$', views_ballot.ballot_writeupnotes, name='doc_ballot_writeupnotes'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/approvaltext/$', views_ballot.ballot_approvaltext, name='doc_ballot_approvaltext'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/approveballot/$', views_ballot.approve_ballot, name='doc_approve_ballot'),
    url(r'^(?P<name>[A-Za-z0-9._+-]+)/edit/makelastcall/$', views_ballot.make_last_call, name='doc_make_last_call'),

    url(r'^help/state/(?P<type>[\w-]+)/$', 'ietf.doc.views_help.state_help', name="state_help"),

    (r'^(?P<name>charter-[A-Za-z0-9._+-]+)/', include('ietf.wgcharter.urls')),
    (r'^(?P<name>[A-Za-z0-9._+-]+)/conflict-review/', include('ietf.doc.urls_conflict_review')),
    (r'^(?P<name>[A-Za-z0-9._+-]+)/status-change/', include('ietf.doc.urls_status_change')),
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^help/state/charter/$', 'direct_to_template', { 'template': 'doc/states.html', 'extra_context': { 'states': State.objects.filter(used=True, type="charter"),'title':"Charter" } }, name='help_charter_states'),
    url(r'^help/state/conflict-review/$', 'direct_to_template', { 'template': 'doc/states.html', 'extra_context': { 'states': State.objects.filter(used=True, type="conflrev").order_by("order"),'title':"Conflict Review" } }, name='help_conflict_review_states'),
    url(r'^help/state/status-change/$', 'direct_to_template', { 'template': 'doc/states.html', 'extra_context': { 'states': State.objects.filter(type="statchg").order_by("order"),'title':"RFC Status Change" } }, name='help_status_change_states'),
)

