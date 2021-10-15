#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from zope.schema import Int

from nti.schema.field import IndexedIterable

from nti.segments.interfaces import IUserFilterSet


class ITestUserFilterSet(IUserFilterSet):

    ids = IndexedIterable(title=u'Static matching IDs',
                          value_type=Int())
