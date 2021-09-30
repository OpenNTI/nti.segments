#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from zope import component
from zope import interface

from zope.app.appsetup.bootstrap import ensureUtility

from zope.container.contained import Contained

from zope.container.interfaces import INameChooser

from nti.containers.containers import AbstractNTIIDSafeNameChooser
from nti.containers.containers import CaseInsensitiveLastModifiedBTreeContainer

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.segments.interfaces import ISegment
from nti.segments.interfaces import ISegmentsContainer

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ISegment)
class Segment(PersistentCreatedModDateTrackingObject,
              SchemaConfigured,
              Contained):

    createDirectFieldProperties(ISegment)

    mimeType = mime_type = "application/vnd.nextthought.segments.segment"


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
