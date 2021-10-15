#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class
# pylint: disable=no-self-argument

from zope.annotation.interfaces import IAnnotatable

from zope.container.constraints import contains

from zope.container.interfaces import IContainer
from zope.container.interfaces import IContained

from zope.interface import Interface

from zope.schema import Object

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified
from nti.base.interfaces import ITitled

from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.schema.field import Bool
from nti.schema.field import IndexedIterable
from nti.schema.field import ValidTextLine


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


def simple_filter_set(filter_set):
    return (not IUnionUserFilterSet.providedBy(filter_set)
            and not IIntersectionUserFilterSet.providedBy(filter_set))


class IUnionUserFilterSet(IUserFilterSet):
    """
    A filter set containing a list of other filter sets whose result is the
    union of results from the contained filter sets.
    """

    filter_sets = IndexedIterable(title=u'Filter Sets',
                                  description=u'Filter sets whose results will be unioned.',
                                  value_type=Object(IUserFilterSet,
                                                    constraint=simple_filter_set),
                                  min_length=1)


class IIntersectionUserFilterSet(IUserFilterSet):
    """
    A filter set containing a list of other filter sets whose result is the
    intersection of results from the contained filter sets.
    """

    filter_sets = IndexedIterable(title=u'Filter Sets',
                                  description=u'Filter sets whose results will be unioned.',
                                  value_type=Object(IUnionUserFilterSet),
                                  min_length=1)


class IIsDeactivatedFilterSet(IUserFilterSet):
    """
    A filter set describing users with a given deactivation status.
    """

    Deactivated = Bool(title=u'Deactivated',
                       description=u'Whether to include only deactivated or activated users',
                       required=True,
                       default=False)


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

    filter_set = Object(IIntersectionUserFilterSet,
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
