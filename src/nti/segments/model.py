#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import BTrees

from zope import component
from zope import interface

from zope.app.appsetup.bootstrap import ensureUtility

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.container.interfaces import INameChooser

from nti.containers.containers import AbstractNTIIDSafeNameChooser
from nti.containers.containers import CaseInsensitiveLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IX_IS_DEACTIVATED
from nti.coremetadata.interfaces import IX_TOPICS

from nti.dataserver.users import get_entity_catalog

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.segments.interfaces import IIntersectionUserFilterSet
from nti.segments.interfaces import IIntIdSet
from nti.segments.interfaces import IIsDeactivatedFilterSet
from nti.segments.interfaces import ISegmentsContainer
from nti.segments.interfaces import IUnionUserFilterSet
from nti.segments.interfaces import IUserSegment

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IUserSegment)
class UserSegment(PersistentCreatedModDateTrackingObject,
                  SchemaConfigured,
                  Contained):
    createDirectFieldProperties(IUserSegment)

    mimeType = mime_type = "application/vnd.nextthought.segments.usersegment"


@interface.implementer(ISegmentsContainer)
class SegmentsContainer(CaseInsensitiveLastModifiedBTreeContainer,
                        Contained):

    def add(self, segment):
        if not getattr(segment, 'id', None):
            segment.id = INameChooser(self).chooseName('', segment)
        self[segment.id] = segment
        return segment

    def remove(self, segment):
        key = getattr(segment, 'id', segment)
        try:
            del self[key]
            result = True
        except KeyError:
            result = False
        return result


def install_segments_container(site_manager_container):
    return ensureUtility(site_manager_container,
                         ISegmentsContainer,
                         'segments-container',
                         SegmentsContainer)


def _to_intids(result_set):
    if not hasattr(result_set, 'intids'):
        return result_set

    return result_set.intids()


@interface.implementer(IIntIdSet)
class IntIdSet(object):

    def __init__(self, intids, family=BTrees.family64):
        self.family = family
        self._intids = intids

    def intids(self):
        return self._intids

    def intersection(self, result_set):
        other_ids = _to_intids(result_set)
        return IntIdSet(self.family.IF.intersection(self._intids, other_ids))

    def union(self, result_set):
        other_ids = _to_intids(result_set)
        return IntIdSet(self.family.IF.union(self._intids, other_ids))

    def difference(self, result_set):
        other_ids = _to_intids(result_set)
        return IntIdSet(self.family.IF.difference(self._intids, other_ids))


@interface.implementer(IUnionUserFilterSet)
class UnionUserFilterSet(SchemaConfigured):

    createDirectFieldProperties(IUnionUserFilterSet)

    mimeType = mime_type = "application/vnd.nextthought.segments.UnionUserFilterSet"

    def apply(self, initial_set):
        result = self.filter_sets[0].apply(initial_set)
        for filter_set in self.filter_sets[1:]:
            result = result.union(filter_set.apply(initial_set))

        return result


@interface.implementer(IIntersectionUserFilterSet)
class IntersectionUserFilterSet(SchemaConfigured):

    createDirectFieldProperties(IIntersectionUserFilterSet)

    mimeType = mime_type = "application/vnd.nextthought.segments.IntersectionUserFilterSet"

    def apply(self, initial_set):
        result = self.filter_sets[0].apply(initial_set)
        for filter_set in self.filter_sets[1:]:
            result = result.intersection(filter_set.apply(result))

        return result


@interface.implementer(IIsDeactivatedFilterSet)
class IsDeactivatedFilterSet(SchemaConfigured):

    createDirectFieldProperties(IIsDeactivatedFilterSet)

    mimeType = mime_type = "application/vnd.nextthought.segments.isdeactivatedfilterset"

    def __init__(self, **kwargs):
        SchemaConfigured.__init__(self, **kwargs)

    @property
    def entity_catalog(self):
        return get_entity_catalog()

    @property
    def deactivated_intids(self):
        deactivated_idx = self.entity_catalog[IX_TOPICS][IX_IS_DEACTIVATED]
        deactivated_ids = self.entity_catalog.family.IF.Set(deactivated_idx.getIds() or ())

        return deactivated_ids

    def apply(self, initial_set):
        if self.Deactivated:
            return initial_set.intersection(self.deactivated_intids)
        return initial_set.difference(self.deactivated_intids)
