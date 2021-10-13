#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.annotation.interfaces import IAnnotatable

from zope.container.constraints import contains

from zope.container.interfaces import IContainer
from zope.container.interfaces import IContained

from zope.interface import Interface

from zope.schema import Object
from zope.schema import vocabulary

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified
from nti.base.interfaces import ITitled

from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.ntiids.schema import ValidNTIID

from nti.schema.field import Bool
from nti.schema.field import ValidChoice
from nti.schema.field import ValidTextLine

ENROLLED_IN = u"enrolled in"
NOT_ENROLLED_IN = u"not enrolled in"

ENROLLMENT_OPS = (ENROLLED_IN,
                  NOT_ENROLLED_IN)

ENROLLMENT_OP_VOCABULARY = vocabulary.SimpleVocabulary(
    tuple(vocabulary.SimpleTerm(x) for x in ENROLLMENT_OPS)
)


class IIntIdSet(Interface):

    def intids(self):
        """
        :return: A :mod:`BTrees` set of intids of entities that match.
        """

    def intersection(self, result_set):
        """
        Compute the result of the intersection between this and the given result
        set and return as a new :class:`IIntIdSet`
        """

    def union(self, result_set):
        """
        Compute the result of the union between this and the given result
        set and return as a new :class:`IIntIdSet`
        """

    def difference(self, result_set):
        """
        Compute the result of items in this result set for which there is no
        matching item in the given result set and return as a new
        :class:`IIntIdSet`
        """


class IFilterSet(Interface):
    """
    A filter set describes a set of objects through criteria defined by
    the implementations (e.g. all users enrolled in a course)
    """

    def apply(initial_set):
        """
        :param initial_set: An :class:`IIntIdSet` object providing the initial
        set of IDs in the population

        Given an initial set of object ids, return an :class:`IIntIdSet`
        consisting of the subset of these intids that meet the criteria of this
        filter set.
        """


class IUserFilterSet(IFilterSet):
    """
    A filter set applied and resolving to user objects.
    """


class IIsDeactivatedFilterSet(IUserFilterSet):
    """
    A filter set describing users with a given deactivation status.
    """

    Deactivated = Bool(title=u'Deactivated',
                       description=u'Whether to include only deactivated or activated users',
                       required=True,
                       default=False)


class ICourseMembershipFilterSet(IUserFilterSet):
    """
    A filter set describing users enrolled, or not enrolled, in the given
    course.
    """

    course_ntiid = ValidNTIID(title=u'Course NTIID',
                              description=u'NTIID of the course in which to check membership.',
                              required=True)

    operator = ValidChoice(title=u'Operator',
                           description=u'Whether to check for enrolled or not enrolled users.',
                           vocabulary=ENROLLMENT_OP_VOCABULARY,
                           required=True)


class ISegment(IContained,
               ICreated,
               ILastModified,
               ITitled,
               IShouldHaveTraversablePath):

    title = ValidTextLine(title=u"Segment Title",
                          description=u"Descriptive title for the segment.",
                          required=True)

    filter_set = Object(IFilterSet,
                        title=u"Filter set defining the set of objects.",
                        required=False)


class IUserSegment(ISegment):
    """
    Segment operating on user objects.
    """

    filter_set = Object(IUserFilterSet,
                        title=u"Filter set defining the set of objects.",
                        required=False)


class ISegmentsContainer(IContained,
                         IContainer,
                         IAnnotatable,
                         IShouldHaveTraversablePath):
    contains(ISegment)

    def add(segment):
        pass

    def remove(segment):
        pass


class ISiteSegmentsContainer(ISegmentsContainer):
    """
    Container for storing segments for the site
    """
