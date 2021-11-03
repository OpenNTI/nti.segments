#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from numbers import Number

from unittest import TestCase

import BTrees

from hamcrest import all_of
from hamcrest import assert_that
from hamcrest import calling
from hamcrest import contains
from hamcrest import contains_inanyorder
from hamcrest import has_entries
from hamcrest import has_entry
from hamcrest import has_key
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import is_
from hamcrest import is_not
from hamcrest import none
from hamcrest import not_none
from hamcrest import raises

from z3c.baseregistry.baseregistry import BaseComponents

from zope import interface

from zope.component import globalSiteManager as BASE

from zope.container.interfaces import InvalidItemType

from nti.externalization import update_from_external_object

from nti.externalization.internalization import find_factory_for

from nti.externalization.tests import externalizes

from nti.segments.interfaces import IIntersectionUserFilterSet
from nti.segments.interfaces import ISegmentsContainer
from nti.segments.interfaces import IUnionUserFilterSet
from nti.segments.interfaces import IUserSegment

from nti.segments.model import install_segments_container
from nti.segments.model import IntIdSet
from nti.segments.model import IntersectionUserFilterSet
from nti.segments.model import UnionUserFilterSet
from nti.segments.model import UserSegment
from nti.segments.model import SegmentsContainer

from nti.segments.tests import SharedConfiguringTestLayer

from nti.segments.tests.interfaces import ITestUserFilterSet

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


@interface.implementer(ITestUserFilterSet)
class TestFilterSet(object):
    mimeType = mime_type = "application/vnd.nextthought.segments.test.testfilterset"

    def __init__(self, ids=None):
        self.ids = tuple(ids or ())

    def apply(self, _unused_filter_set):
        return IntIdSet(BTrees.family64.IF.Set(self.ids))


class TestModel(TestCase):

    layer = SharedConfiguringTestLayer

    def test_container(self):
        filter_set_a = UnionUserFilterSet(filter_sets=(TestFilterSet([1, 2, 3]),))
        filter_set_b = UnionUserFilterSet(filter_sets=(TestFilterSet([2, 3, 4]),))
        filter_set = IntersectionUserFilterSet(filter_sets=(filter_set_a,
                                                            filter_set_b))
        container = SegmentsContainer()

        # Can only add segments
        assert_that(calling(container.add).with_args(filter_set),
                    raises(InvalidItemType))

        segment = UserSegment(title=u'All Users',
                              filter_set=filter_set)
        container.add(segment)
        assert_that(container, has_length(is_(1)))

        segment_two = UserSegment(title=u'All Users Two')
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


class TestUnionUserFilterSet(TestCase):

    layer = SharedConfiguringTestLayer

    def test_valid_interface(self):
        assert_that(UnionUserFilterSet(filter_sets=(TestFilterSet(),)),
                    verifiably_provides(IUnionUserFilterSet))

    def _internalize(self, external):
        factory = find_factory_for(external)
        assert_that(factory, is_(not_none()))
        new_io = factory()
        if new_io is not None:
            update_from_external_object(new_io, external)
        return new_io

    def test_internalize(self):
        ext_obj = {
            "MimeType": UnionUserFilterSet.mime_type,
            "filter_sets": [
                {
                    "MimeType": TestFilterSet.mime_type,
                    "ids": [3, 4, 5]
                },
                {
                    "MimeType": TestFilterSet.mime_type,
                    "ids": [7, 8, 9]
                },
            ]
        }
        filter_set = self._internalize(ext_obj)
        assert_that(filter_set, has_properties(
            mime_type=UnionUserFilterSet.mime_type,
            filter_sets=contains(
                has_properties(
                    mime_type=TestFilterSet.mime_type,
                    ids=[3, 4, 5]
                ),
                has_properties(
                    mime_type=TestFilterSet.mime_type,
                    ids=[7, 8, 9]
                ),
            )
        ))

    def test_externalize(self):
        filter_set = UnionUserFilterSet(filter_sets=(TestFilterSet([1, 2, 3]),
                                                     TestFilterSet([2, 3, 4])))
        assert_that(filter_set,
                    externalizes(all_of(has_entries({
                        'MimeType': UnionUserFilterSet.mime_type,
                        'filter_sets': contains(
                            has_entries(
                                MimeType=TestFilterSet.mime_type,
                                ids=[1, 2, 3]
                            ),
                            has_entries(
                                MimeType=TestFilterSet.mime_type,
                                ids=[2, 3, 4]
                            ),
                        ),
                    }))))

    def test_apply(self):
        filter_set_a = UnionUserFilterSet(filter_sets=(TestFilterSet([1, 2, 3]),))
        filter_set_b = UnionUserFilterSet(filter_sets=(TestFilterSet([2, 3, 4]),))
        filter_set = UnionUserFilterSet(filter_sets=(TestFilterSet([1, 2, 3]),
                                                     TestFilterSet([2, 3, 4])))
        initial = IntIdSet(BTrees.family64.IF.Set([1, 2, 3, 4, 5]))

        result = filter_set_a.apply(initial)
        assert_that(result.intids(), contains_inanyorder(1, 2, 3))

        result = filter_set_b.apply(initial)
        assert_that(result.intids(), contains_inanyorder(2, 3, 4))

        result = filter_set.apply(initial)
        assert_that(result.intids(), contains_inanyorder(1, 2, 3, 4))


class TestIntersectionUserFilterSet(TestCase):

    layer = SharedConfiguringTestLayer

    def test_valid_interface(self):
        filter_set_u = UnionUserFilterSet(filter_sets=(TestFilterSet(),))
        assert_that(IntersectionUserFilterSet(filter_sets=(filter_set_u,)),
                    verifiably_provides(IIntersectionUserFilterSet))

    def _internalize(self, external):
        factory = find_factory_for(external)
        assert_that(factory, is_(not_none()))
        new_io = factory()
        if new_io is not None:
            update_from_external_object(new_io, external)
        return new_io

    def test_internalize(self):
        ext_obj = {
            "MimeType": IntersectionUserFilterSet.mime_type,
            "filter_sets": [
                {
                    "MimeType": UnionUserFilterSet.mime_type,
                    "filter_sets": [
                        {
                            "MimeType": TestFilterSet.mime_type,
                            "ids": [1, 2, 3]
                        },
                    ]
                },
                {
                    "MimeType": UnionUserFilterSet.mime_type,
                    "filter_sets": [
                        {
                            "MimeType": TestFilterSet.mime_type,
                            "ids": [2, 3, 4]
                        },
                    ]
                }
            ]
        }
        filter_set = self._internalize(ext_obj)
        assert_that(filter_set, has_properties(
            mime_type=IntersectionUserFilterSet.mime_type,
            filter_sets=contains(
                has_properties(
                    mime_type=UnionUserFilterSet.mime_type,
                    filter_sets=contains(
                        has_properties(
                            mime_type=TestFilterSet.mime_type,
                            ids=[1, 2, 3]
                        ),
                    )
                ),
                has_properties(
                    mime_type=UnionUserFilterSet.mime_type,
                    filter_sets=contains(
                        has_properties(
                            mime_type=TestFilterSet.mime_type,
                            ids=[2, 3, 4]
                        ),
                    )
                ),
            )
        ))

    def test_externalize(self):
        filter_set_a = UnionUserFilterSet(filter_sets=(TestFilterSet([1, 2, 3]),))
        filter_set_b = UnionUserFilterSet(filter_sets=(TestFilterSet([2, 3, 4]),))
        filter_set = IntersectionUserFilterSet(filter_sets=(filter_set_a,
                                                            filter_set_b))
        assert_that(filter_set,
                    externalizes(all_of(has_entries({
                        'MimeType': IntersectionUserFilterSet.mime_type,
                        'filter_sets': contains(
                            has_entries({
                                'MimeType': UnionUserFilterSet.mime_type,
                                'filter_sets': contains(
                                    has_entries(
                                        MimeType=TestFilterSet.mime_type,
                                        ids=[1, 2, 3]
                                    ),
                                ),
                            }),
                            has_entries({
                                'MimeType': UnionUserFilterSet.mime_type,
                                'filter_sets': contains(
                                    has_entries(
                                        MimeType=TestFilterSet.mime_type,
                                        ids=[2, 3, 4]
                                    ),
                                ),
                            }),
                        ),
                    }))))

    def test_apply(self):
        filter_set_u1 = UnionUserFilterSet(filter_sets=(TestFilterSet([0, 1, 2]),
                                                        TestFilterSet([1, 2, 3]),))
        filter_set_u2 = UnionUserFilterSet(filter_sets=(TestFilterSet([2, 3, 4]),))
        filter_set_a = IntersectionUserFilterSet(
            filter_sets=(filter_set_u1,)
        )
        filter_set_b = IntersectionUserFilterSet(
            filter_sets=(filter_set_u2,)
        )
        filter_set = IntersectionUserFilterSet(filter_sets=(filter_set_u1,
                                                            filter_set_u2))
        initial = IntIdSet(BTrees.family64.IF.Set([1, 2, 3, 4, 5]))

        result = filter_set_a.apply(initial)
        assert_that(result.intids(), contains_inanyorder(0, 1, 2, 3))

        result = filter_set_b.apply(initial)
        assert_that(result.intids(), contains_inanyorder(2, 3, 4))

        result = filter_set.apply(initial)
        assert_that(result.intids(), contains_inanyorder(2, 3))


class TestUserSegment(TestCase):

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
            "filter_set": {
                "MimeType": IntersectionUserFilterSet.mime_type,
                "filter_sets": [
                    {
                        "MimeType": UnionUserFilterSet.mime_type,
                        "filter_sets": [
                            {
                                "MimeType": TestFilterSet.mime_type,
                                "ids": [0, 1, 2]
                            },
                        ]
                    },
                    {
                        "MimeType": UnionUserFilterSet.mime_type,
                        "filter_sets": [
                            {
                                "MimeType": TestFilterSet.mime_type,
                                "ids": [1, 2, 3]
                            },
                        ]
                    }
                ]
            }
        }
        segment = self._internalize(ext_obj)
        assert_that(segment, has_properties(
            title=u"my segment",
            filter_set=has_properties(
                mime_type=IntersectionUserFilterSet.mime_type,
                filter_sets=contains(
                    has_properties(
                        mime_type=UnionUserFilterSet.mime_type,
                        filter_sets=contains(
                            has_properties(
                                mime_type=TestFilterSet.mime_type,
                                ids=[0, 1, 2]
                            ),
                        )
                    ),
                    has_properties(
                        mime_type=UnionUserFilterSet.mime_type,
                        filter_sets=contains(
                            has_properties(
                                mime_type=TestFilterSet.mime_type,
                                ids=[1, 2, 3]
                            ),
                        )
                    ),
                )
            )
        ))

    def test_externalize(self):
        filter_set_a = UnionUserFilterSet(filter_sets=(TestFilterSet([0, 1, 2]),
                                                       TestFilterSet([1, 2, 3]),))
        filter_set_b = UnionUserFilterSet(filter_sets=(TestFilterSet([2, 3, 4]),))
        filter_set = IntersectionUserFilterSet(filter_sets=(filter_set_a,
                                                            filter_set_b))
        segment = UserSegment(title=u'All Users',
                              filter_set=filter_set)
        assert_that(segment,
                    externalizes(all_of(has_entries({
                        'MimeType': UserSegment.mime_type,
                        'title': 'All Users',
                        'filter_set': has_entries({
                            'MimeType': IntersectionUserFilterSet.mime_type,
                            'filter_sets': contains(
                                has_entries({
                                    'MimeType': UnionUserFilterSet.mime_type,
                                    'filter_sets': contains(
                                        has_entries(
                                            MimeType=TestFilterSet.mime_type,
                                            ids=[0, 1, 2]
                                        ),
                                        has_entries(
                                            MimeType=TestFilterSet.mime_type,
                                            ids=[1, 2, 3]
                                        ),
                                    ),
                                }),
                                has_entries({
                                    'MimeType': UnionUserFilterSet.mime_type,
                                    'filter_sets': contains(
                                        has_entries(
                                            MimeType=TestFilterSet.mime_type,
                                            ids=[2, 3, 4]
                                        ),
                                    ),
                                }),
                            ),
                        }),
                        'CreatedTime': is_(Number),
                        'Last Modified': is_(Number),
                    }))))
