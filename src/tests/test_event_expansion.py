"""Test suite for the event queue"""
import unittest
import src.events
from src.events import _EventDefinition as _EDef
import pygame

_DUMMY = object()
pygame.init()


class TestEventExpansion(unittest.TestCase):

    def test_no_attributes(self):
        test_event_type = src.events.create_custom_event_type("TestEventType")
        edef = src.events.get_event_def(test_event_type)
        self.assertDictEqual(edef.attrs, {})

    def test_post_evt_no_attributes(self):
        test_event_type = src.events.create_custom_event_type("TestEventType")
        src.events.post_event(test_event_type)
        edef = src.events.get_event_def(test_event_type)
        result_event = edef()
        self.assertDictEqual(result_event.dict, {})
        event_queue = pygame.event.get()
        self.assertIn(result_event, event_queue, "event was not posted")

    def test_evt_type_no_attrs_posted_with_attrs(self):
        evt_noattrs = src.events.create_custom_event_type("EventNoAttrs")
        self.assertRaises(
            TypeError,
            src.events.post_event,
            evt_noattrs,
            some_unexpected_attribute=_DUMMY
        )

    def test_one_attribute(self):
        expected_dict = {
            "attr1": int
        }
        test_event_type = src.events.create_custom_event_type("TestEventType", attr1=int)
        edef = src.events.get_event_def(test_event_type)
        self.assertDictEqual(edef.attrs, expected_dict)

    def test_post_evt_one_attribute_correct_value(self):
        test_event_type = src.events.create_custom_event_type("TestEventType", attr1=int)
        edef = src.events.get_event_def(test_event_type)
        src.events.post_event(test_event_type, attr1=5)
        result_event = edef(attr1=5)
        self.assertEqual(5, result_event.attr1)
        self.assertIn(result_event, pygame.event.get(), "event was not posted")

    def test_evt_type_one_attr_wrong_type(self):
        evt_one_attr = src.events.create_custom_event_type("EvtOneAttr", attr1=float)
        self.assertRaises(
            TypeError,
            src.events.post_event,
            evt_one_attr,
            attr1="wrong type"
        )

    def test_evt_type_one_attr_arg_missing(self):
        evt_one_attr = src.events.create_custom_event_type("EvtOneAttr", attr1=int)
        self.assertRaises(
            TypeError,
            src.events.post_event,
            evt_one_attr
        )

    def test_evt_type_one_attr_arg_missing_default_set(self):
        evt_one_attr = src.events.create_custom_event_type("EvtOneAttr", attr1=int)
        edef = src.events.get_event_def(evt_one_attr)
        edef.set_default_for_attr("attr1", 1)
        self.assertEqual(edef.default_values_for_attrs["attr1"], 1)
        evt_with_default = edef()
        self.assertEqual(evt_with_default.attr1, 1)
        evt_custom_val = edef(attr1=6)
        self.assertEqual(evt_custom_val.attr1, 6)

    def test_evt_type_one_attr_union_type(self):
        IntOrStr = int | str
        evt_one_attr = src.events.create_custom_event_type("EvtOneAttr", attr1=IntOrStr)
        edef = src.events.get_event_def(evt_one_attr)
        self.assertIs(edef.attrs["attr1"], IntOrStr)
        event_with_type_a_value = edef(attr1=50)
        self.assertEquals(event_with_type_a_value.attr1, 50)


