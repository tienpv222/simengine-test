"""Aggregate functionalities related to randomizing actions"""
import random
import functools
import itertools
import time
import sys
import types


class ChainedArgs:
    """Keeps track of previously calculated arguments for 
    random function arguments & passes it to the next argument
    (can be used when generation of a particular random value 
    passed to randomized method as an arg depends on previously generated values)
    
    Example:
        ChainedArgs(
            lambda self: generate_first_arg(),
            lambda self, first_arg: generate_seconds_arg(first_arg)
        )()
    """

    def __init__(self, arg_list):
        self._arg_gen = None
        if len(arg_list) < 2:
            raise ValueError("Cannot chain less than 2 arguments!")

        self._arg_list = arg_list

    def _generate_arg(self, instance: object):
        """Generate arguments in a sequential manner
        Args:
            instance: class or object to be passed to the args
        Yields:
            any: random function arguments (one by one) initialized at the ChainedArgs createion
        """

        prev_result = self._arg_list[0](instance)
        yield prev_result

        for calc_rand_arg in self._arg_list[1:-1]:
            prev_result = calc_rand_arg(instance, prev_result)
            yield prev_result

        # reset generator once went through the entire arg list
        self._arg_gen = None
        yield self._arg_list[-1](instance, prev_result)

    def _gen_arg_wrapper(self, instance: object):
        """Get next random argument value to be passed to a function
        Args:
            instance: class or object to be passed to the args
        Returns:
            next argument value
        """

        if not self._arg_gen:
            self._arg_gen = self._generate_arg(instance)

        return next(self._arg_gen)

    def __call__(self):
        """Get generated function arguments"""
        return tuple(map(lambda _: self._gen_arg_wrapper, self._arg_list))


class Randomizer:
    """Randomizer is a chaos generator that can perform random actions
    associated with a class/or its instance
    """

    # contains all the classes registered with Randomizer.register
    classes = {}

    # seed used for predictable randomization
    seed = None

    @classmethod
    def _rand_action(cls, rand_obj, nap):
        """Perform rand action associated with the passed object"""

        rand_func = random.choice(cls.classes[rand_obj.__class__])

        rand_args = list(map(lambda x: x(rand_obj), rand_func.arg_defaults))
        rand_func(rand_obj, *tuple(rand_args))

        # majestic nap
        if nap:
            nap()

    @classmethod
    def set_seed(cls, seed=random.randrange(sys.maxsize)):
        """Update randomizer seed"""
        random.seed(seed)
        # store in Randomizer since there's no seed getter in random
        cls.seed = seed

    @classmethod
    def get_seed(cls):
        """get randomizer seed"""
        return cls.seed

    @classmethod
    def randact(
        cls, instance, num_iter: int = 1, seconds: int = None, nap: callable = None
    ):
        """Perform random action(s) (one of the methods marked with @Randomizer.randomize_method) 
        on an object or a list of objects (instances marked with @Randomizer.register)

        Args:
            instance: either a list of objects whose methods will be randomized or a single object to be used
            num_iter: number of random actions to be performed
            seconds: perform actions for this number of seconds, alternative to num_iter
            nap: sleep function executed in-between the action, defaults to 0.5 seconds nap
        """

        if seconds and seconds < 0:
            raise ValueError("Argument 'seconds' must be positive")

        # received multiple objects
        if isinstance(instance, list):
            obj_classes = map(lambda x: x.__class__, instance)

            # Classes not registered in cls.classes
            if set(obj_classes).difference(set(cls.classes)) != set():
                raise ValueError("Unsupported/unregistered classes detected")
        elif instance.__class__ not in cls.classes:
            raise ValueError(
                "Unregistered class '{}'".format(instance.__class__.__name__)
            )

        # passed validation
        if not isinstance(instance, list):
            instance = [instance]

        if not nap:
            nap = functools.partial(time.sleep, 0.5)

        rand_obj = lambda: random.choice(instance)
        # either perform rand actions for 'n' seconds or for 'n' iterations
        if seconds:
            t_end = time.time() + seconds

            while time.time() < t_end:
                cls._rand_action(rand_obj(), nap)
        else:
            list(map(lambda _: cls._rand_action(rand_obj(), nap), range(num_iter)))

    @classmethod
    def biased_rand_obj(cls, supplied_objects):
        """Adds weights to classes based on number of randomized functions"""

        func_scores = list(map(lambda x: len(cls.classes[x]), cls.classes))
        rand_score = random.randrange(0, sum(func_scores))

        closest_score = min(func_scores, key=lambda x: abs(int(x) - rand_score))
        valid_indices = [i for i, x in enumerate(func_scores) if x == closest_score]
        return cls.classes[random.choice(valid_indices)]

    @classmethod
    def register(cls, new_reg_cls):
        """Register class as randomizable with @Randomizer.register decorator
        Randomizer will search for methods marked with @Randomizer.randomize_method & store them as randomly-replayable
        """
        cls_details = []

        # Find methods/classmethods with @Recorder()
        # decorator attached to them
        for attr_name in dir(new_reg_cls):
            attr = getattr(new_reg_cls, attr_name)

            # see https://stackoverflow.com/a/41696531
            if isinstance(attr, types.MethodType):
                attr = attr.__func__

            is_recordable = lambda a: a and hasattr(a, "recordable") and a.recordable

            if is_recordable(attr):
                cls_details.append(attr)

        cls.classes[new_reg_cls] = cls_details
        return new_reg_cls

    @classmethod
    def randomize_method(cls, arg_defaults=tuple()):
        """"""

        def decorator(work: callable):
            @functools.wraps(work)
            def func_wrapper(asset_self, *f_args, **f_kwargs):
                return work(asset_self, *f_args, **f_kwargs)

            func_wrapper.recordable = True
            func_wrapper.arg_defaults = arg_defaults
            return func_wrapper

        return decorator


Randomizer.set_seed()
