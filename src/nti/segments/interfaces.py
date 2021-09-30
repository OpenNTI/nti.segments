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

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified
from nti.base.interfaces import ITitled

from nti.coremetadata.interfaces import IShouldHaveTraversablePath

from nti.schema.field import ValidTextLine


class IFilterSet(Interface):
    """
    A filter set describes a set of objects through criteria defined by
    the implementations (e.g. all users enrolled in a course)
    """


class IUserFilterSet(IFilterSet):
    """
    A filter set applied to user objects.
    """


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
