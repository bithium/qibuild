## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

import qisys.interact
import mock

class FakeInteract:
    """ A class to tests code depending on qisys.interact

    """
    def __init__(self, answers):
        self.answers_type = None
        self.answer_index = -1
        if type(answers) == type(dict()):
            self.answers_type = "dict"
        elif type(answers) == type(list()):
            self.answers_type = "list"
        else:
            raise Exception("Unknow answer type: " + type(answers))
        self.answers = answers

    def find_answer(self, message, choices=None, default=None):
        keys = self.answers.keys()
        for key in keys:
            if key in message.lower():
                if not choices:
                    return self.answers[key]
                answer = self.answers[key]
                if answer in choices:
                    return answer
                else:
                    mess  = "Would answer %s\n" % answer
                    mess += "But choices are: %s\n" % choices
                    raise Exception(mess)
        if default is not None:
            return default
        mess  = "Could not find answer for\n  :: %s\n" % message
        mess += "Known keys are: %s" % ", ".join(keys)
        raise Exception(mess)

    def ask_choice(self, choices, message):
        print "::", message
        for choice in choices:
            print "* ", choice
        answer = self._get_answer(message, choices)
        print ">", answer
        return answer

    def ask_yes_no(self, message, default=False):
        print "::", message,
        if default:
            print "(Y/n)"
        else:
            print "(y/N)"
        answer = self._get_answer(message, default=default)
        print ">", answer
        return answer

    def ask_path(self, message):
        print "::", message
        answer = self._get_answer(message)
        print ">", answer
        return answer

    def ask_string(self, message):
        print "::", message
        answer = self._get_answer(message)
        print ">", answer
        return answer

    def ask_program(self, message):
        print "::", message
        answer =  self._get_answer(message)
        print ">", answer
        return answer

    def _get_answer(self, message, choices=None, default=None):
        if self.answers_type == "dict":
            return self.find_answer(message, choices=choices, default=default)
        else:
            self.answer_index += 1
            return self.answers[self.answer_index]


def test_fake_interat_list():
    fake_interact = FakeInteract([False, "coffee!"])
    with mock.patch('qisys.interact', fake_interact):
        assert qisys.interact.ask_yes_no("tea?") is False
        assert qisys.interact.ask_string("then what?") == "coffee!"

def test_fake_interat_dict():
    fake_interact = FakeInteract({"coffee" : "y", "tea" : "n"})
    with mock.patch('qisys.interact', fake_interact):
        assert qisys.interact.ask_yes_no("Do you like tea?") == "n"
        assert qisys.interact.ask_yes_no("Do you like coffee?") == "y"


def test_ask_yes_no():
    """ Test that you can answer with several types of common answers """
    with mock.patch('__builtin__.raw_input') as m:
        m.side_effect = ["y", "yes", "Yes", "n", "no", "No"]
        expected_res  = [True, True, True, False, False, False]
        for res in expected_res:
            actual = qisys.interact.ask_yes_no("coffee?")
            assert actual == res

def test_ask_yes_no_default():
    """ Test that just pressing enter returns the default value """
    with mock.patch('__builtin__.raw_input') as m:
        m.side_effect = ["", ""]
        assert qisys.interact.ask_yes_no("coffee?", default=True)  is True
        assert qisys.interact.ask_yes_no("coffee?", default=False) is False

def test_ask_yes_no_wrong_input():
    """ Test that we keep asking when answer does not make sense """
    with mock.patch('__builtin__.raw_input') as m:
        m.side_effect = ["coffee!", "n"]
        assert qisys.interact.ask_yes_no("tea?") is False
        assert m.call_count == 2
