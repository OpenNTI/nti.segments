#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import BTrees
from nti.contenttypes.courses.index import IX_USERNAME

from zope import component
from zope import interface

from zope.intid import IIntIds

from zope.app.appsetup.bootstrap import ensureUtility

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.container.interfaces import INameChooser

from nti.containers.containers import AbstractNTIIDSafeNameChooser
from nti.containers.containers import CaseInsensitiveLastModifiedBTreeContainer

from nti.contenttypes.courses import get_enrollment_catalog

from nti.contenttypes.courses.index import IX_COURSE
from nti.contenttypes.courses.index import IX_SITE

from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseInstanceEnrollmentRecord

from nti.coremetadata.interfaces import IUser
from nti.coremetadata.interfaces import IX_IS_DEACTIVATED
from nti.coremetadata.interfaces import IX_TOPICS

from nti.dataserver.users import get_entity_catalog

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.segments.interfaces import ENROLLED_IN
from nti.segments.interfaces import ICourseMembershipFilterSet
from nti.segments.interfaces import IIsDeactivatedFilterSet
from nti.segments.interfaces import IIntIdSet
from nti.segments.interfaces import ISegmentsContainer
from nti.segments.interfaces import IUserSegment

from nti.site.site import get_component_hierarchy_names

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
            segment.id = INameChooser(self).chooseName(segment.title, segment)
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


@component.adapter(ISegmentsContainer)
@interface.implementer(INameChooser)
class _SegmentsNameChooser(AbstractNTIIDSafeNameChooser):
    """
    Handles NTIID-safe name choosing for a stored segment.
    """
    leaf_iface = ISegmentsContainer


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


@interface.implementer(IIsDeactivatedFilterSet)
class IsDeactivatedFilterSet(SchemaConfigured):

    createDirectFieldProperties(IIsDeactivatedFilterSet)

    mimeType = mime_type = "application/vnd.nextthought.segments.isdeactivatedfilterset"

    def __init__(self, **kwargs):
        SchemaConfigured.__init__(self, **kwargs)

    @Lazy
    def entity_catalog(self):
        return get_entity_catalog()

    @Lazy
    def deactivated_intids(self):
        deactivated_idx = self.entity_catalog[IX_TOPICS][IX_IS_DEACTIVATED]
        deactivated_ids = self.entity_catalog.family.IF.Set(deactivated_idx.getIds() or ())

        return deactivated_ids

    def apply(self, initial_set):
        if self.Deactivated:
            return initial_set.intersection(self.deactivated_intids)
        return initial_set.difference(self.deactivated_intids)


@interface.implementer(ICourseMembershipFilterSet)
class CourseMembershipFilterSet(SchemaConfigured,
                                Contained):

    createDirectFieldProperties(IIsDeactivatedFilterSet)

    mimeType = mime_type = "application/vnd.nextthought.segments.coursemembershipfilterset"

    def __init__(self, **kwargs):
        SchemaConfigured.__init__(self, **kwargs)

    @Lazy
    def enrollment_catalog(self):
        return get_enrollment_catalog()

    @Lazy
    def enrolled_intids(self):
        course = find_object_with_ntiid(self.course_ntiid)
        catalog_entry = ICourseCatalogEntry(course, None)

        # TODO: Do we want to be more restrictive than this?  E.g. only
        #  operate on the current site, or the site the "parent" segment is
        #  stored in (filter sets are not currently Contained objects).  Should
        #  this be a part of the definition?  To some
        #  degree this is currently already enforced at the view level.
        site_names = get_component_hierarchy_names()
        query = {
            IX_SITE: {'any_of': site_names},
            IX_COURSE: {'any_of': (catalog_entry.ntiid,)},
        }

        # Seems unfortunate that we have to reify all the enrollment records
        # to get what we're after.  While there is an IX_USERNAME index, getting
        # the value for this document would require accessing the _rev_index
        # private field, and would still require reifying all the user objects,
        # though I suppose we could make another query against the entity index
        # with the list of users?
        result = self.enrollment_catalog.family.IF.Set()
        intids = component.getUtility(IIntIds)
        for intid in self.enrollment_catalog.apply(query):
            record = intids.queryObject(intid)
            if not ICourseInstanceEnrollmentRecord.providedBy(record):
                continue

            user = IUser(record, None)
            if user is None:
                continue

            self.enrollment_catalog[IX_USERNAME]

            user_intid = intids.getId(user)
            result.add(user_intid)

        return result

    def apply(self, initial_set):
        if self.operator == ENROLLED_IN:
            return initial_set.intersection(self.enrolled_intids)
        return initial_set.difference(self.enrolled_intids)
