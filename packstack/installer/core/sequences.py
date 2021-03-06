# -*- coding: utf-8 -*-

"""
Base class for steps & sequences
"""
import re
import sys
import logging
import traceback

from .. import utils
from ..exceptions import SequenceError


class Step(object):
    """
    Wrapper for function representing single setup step.
    """
    def __init__(self, name, function, title=None):
        self.name = name
        self.title = title or ('Step: %s' % name)

        # process step function
        if function and not callable(function):
            raise SequenceError("Function object have to be callable. "
                                "Object %s is not callable." % function)
        self.function = function

    def run(self, config=None):
        config = config or {}
        # TO-DO: complete logger name when logging will be setup correctly
        logger = logging.getLogger()
        logger.debug('Running step %s.' % self.name)
        sys.stdout.write('%s...' % self.title)
        sys.stdout.flush()

        # count space needed for title print
        title = self.title
        for color in utils.COLORS.itervalues():
            title = re.sub(re.escape(color), '', title)
        space = 70 - len(title)

        # execute and report state
        state_fmt = '[ %s ]\n'
        try:
            self.function(config)
        except Exception, ex:
            logger.debug(traceback.format_exc())
            state = state_fmt % utils.color_text('ERROR', 'red')
            sys.stdout.write(state.rjust(space))
            sys.stdout.flush()
            raise SequenceError(str(ex))
        else:
            state = state_fmt % utils.color_text('DONE', 'green')
            sys.stdout.write(state.rjust(space))
            sys.stdout.flush()



class Sequence(object):
    """
    Wrapper for sequence of setup steps.
    """
    def __init__(self, name, steps, title=None, condition=None,
                 cond_match=None):
        self.name = name
        self.title = title
        self.condition = condition
        self.cond_match = cond_match

        # process sequence steps
        self.steps = utils.SortedDict()
        for step in steps:
            name, func = step['name'], step['function']
            self.steps[name] = Step(name, func, title=step.get('title'))

    def validate_condition(self, config):
        """
        Returns True if config option condition has value given
        in cond_match. Otherwise returns False.
        """
        if not self.condition:
            return True
        result = config.get(self.condition)
        return result == self.cond_match

    def run(self, config=None, step=None):
        """
        Runs sequence of steps. Runs only specific step if step's name
        is given via 'step' parameter.
        """
        config = config or {}
        if not self.validate_condition(config):
            return
        if step:
            self.steps[step].run(config=config)
            return

        logger = logging.getLogger()
        logger.debug('Running sequence %s.' % self.name)
        if self.title:
            sys.stdout.write('%s\n' % self.title)
            sys.stdout.flush()
        for step in self.steps.itervalues():
            step.run(config=config)
