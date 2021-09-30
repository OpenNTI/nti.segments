#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from numbers import Number

from unittest import TestCase

from hamcrest import all_of
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_entry
from hamcrest import has_key
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import is_
from hamcrest import is_not
from hamcrest import none
from hamcrest import not_none

from z3c.baseregistry.baseregistry import BaseComponents

from zope import interface

from zope.component import globalSiteManager as BASE

from nti.externalization import update_from_external_object

from nti.externalization.internalization import find_factory_for

from nti.externalization.tests import externalizes

from nti.segments.interfaces import ISegmentsContainer
from nti.segments.interfaces import IUserFilterSet
from nti.segments.interfaces import IUserSegment

from nti.segments.model import UserSegment
from nti.segments.model import SegmentsContainer
from nti.segments.model import install_segments_container

from nti.segments.tests import SharedConfiguringTestLayer

from nti.site.folder import HostPolicyFolder
from nti.site.folder import HostPolicySiteManager

from nti.testing.matchers import verifiably_provides


class MockSite(object):

    __name__ = None
    __parent__ = None

    def __init__(self, site_man=None):
        self.site_man = site_man

    def getSiteManager(self):
        return self.site_man


@interface.implementer(IUserFilterSet)
class TestFilterSet(object):
    pass


class TestModel(TestCase):

    layer = SharedConfiguringTestLayer

    def test_valid_interface(self):
        assert_that(UserSegment(title=u'All Users'), verifiably_provides(IUserSegment))

    def _internalize(self, external):
        factory = find_factory_for(external)
        assert_that(factory, is_(not_none()))
        new_io = factory()
        if new_io is not None:
            update_from_external_object(new_io, external)
        return new_io

    def test_internalize(self):
        ext_obj = {
            "MimeType": UserSegment.mime_type,
            "title": u"my segment",
        }
        segment = self._internalize(ext_obj)
        assert_that(segment, has_properties(
            title=u"my segment"
        ))

    def test_externalize(self):
        segment = UserSegment(title=u'All Users',
                              filter_set=TestFilterSet())
        assert_that(segment,
                    externalizes(all_of(has_entries({
                        'MimeType': UserSegment.mime_type,
                        'title': 'All Users',
                        'filter_set': not_none(),
                        'CreatedTime': is_(Number),
                        'Last Modified': is_(Number),
                    }))))

    def test_container(self):
        segment = UserSegment(title=u'All Users',
                              filter_set=TestFilterSet())
        container = SegmentsContainer()
        container.add(segment)
        assert_that(container, has_length(is_(1)))

        segment_two = UserSegment(title=u'All Users Two',
                                  filter_set=TestFilterSet())
        container.add(segment_two)
        assert_that(container, has_length(is_(2)))

        container.remove(segment)
        assert_that(container, has_length(is_(1)))

        # can also remove by id
        container.remove(segment_two.id)
        assert_that(container, has_length(is_(0)))

    def test_install_container(self):
        pers_comps = BaseComponents(BASE, 'persistent', (BASE,))
        host_comps = BaseComponents(BASE, 'example.com', (BASE,))

        site = HostPolicyFolder()
        site_policy = HostPolicySiteManager(site)
        site_policy.__bases__ = (host_comps, pers_comps)
        site.setSiteManager(site_policy)

        container = install_segments_container(site)
        assert_that(container, is_not(none()))
        assert_that(site_policy, has_key('default'))
        assert_that(site_policy['default'],
                    has_entry('segments-container', not_none()))
        assert_that(site_policy['default']['segments-container'],
                    is_(container))
        assert_that(site_policy.getUtility(ISegmentsContainer),
                    is_(container))

        site_policy.unregisterUtility(container, ISegmentsContainer)
        del site_policy['default']['segments-container']
