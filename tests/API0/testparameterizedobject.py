"""
Unit test for Parameterized.
"""

import unittest
import param
import numbergen

# CEBALERT: not anything like a complete test of Parameterized!

from param.parameterized import ParamOverrides, shared_parameters

from tests.API1.utils import SomeRandomNumbers


class MyTestPO(param.Parameterized):
    inst = param.Parameter(default=[1,2,3],instantiate=True)
    notinst = param.Parameter(default=[1,2,3],instantiate=False)
    const = param.Parameter(default=1,constant=True)
    ro = param.Parameter(default="Hello",readonly=True)
    ro2 = param.Parameter(default=object(),readonly=True,instantiate=True)

    dyn = param.Dynamic(default=1)


class MyAnotherTestPO(param.Parameterized):
    instPO = param.Parameter(default=MyTestPO(), instantiate=True)
    notinstPO = param.Parameter(default=MyTestPO(), instantiate=False)


class MyTestAbstractPO(param.Parameterized):
    __abstract = True


class MyTestParamInstantiation(MyAnotherTestPO):
    instPO = param.Parameter(default=MyAnotherTestPO(), instantiate=False)


class TestParameterized(unittest.TestCase):

    def test_constant_parameter(self):
        """Test that you can't set a constant parameter after construction."""
        testpo = MyTestPO(const=17)
        self.assertEqual(testpo.const,17)
        self.assertRaises(TypeError,setattr,testpo,'const',10)

        # check you can set on class
        MyTestPO.const=9
        testpo = MyTestPO()
        self.assertEqual(testpo.const,9)

    def test_readonly_parameter(self):
        """Test that you can't set a read-only parameter on construction or as an attribute."""
        testpo = MyTestPO()
        self.assertEqual(testpo.ro,"Hello")

        with self.assertRaises(TypeError):
            t = MyTestPO(ro=20)

        t=MyTestPO()
        self.assertRaises(TypeError,setattr,t,'ro',10)

        # check you cannot set on class
        self.assertRaises(TypeError,setattr,MyTestPO,'ro',5)

        self.assertEqual(testpo.params()['ro'].constant,True)

        # check that instantiate was ignored for readonly
        self.assertEqual(testpo.params()['ro2'].instantiate,False)



    def test_basic_instantiation(self):
        """Check that instantiated parameters are copied into objects."""

        testpo = MyTestPO()

        self.assertEqual(testpo.inst,MyTestPO.inst)
        self.assertEqual(testpo.notinst,MyTestPO.notinst)

        MyTestPO.inst[1]=7
        MyTestPO.notinst[1]=7

        self.assertEqual(testpo.notinst,[1,7,3])
        self.assertEqual(testpo.inst,[1,2,3])


    def test_more_instantiation(self):
        """Show that objects in instantiated Parameters can still share data."""
        anothertestpo = MyAnotherTestPO()

        ### CB: _AnotherTestPO.instPO is instantiated, but
        ### _TestPO.notinst is not instantiated - so notinst is still
        ### shared, even by instantiated parameters of _AnotherTestPO.
        ### Seems like this behavior of Parameterized could be
        ### confusing, so maybe mention it in documentation somewhere.
        MyTestPO.notinst[1]=7
        # (if you thought your instPO was completely an independent object, you
        # might be expecting [1,2,3] here)
        self.assertEqual(anothertestpo.instPO.notinst,[1,7,3])


    def test_instantiation_inheritance(self):
        """Check that instantiate=True is always inherited (SF.net #2483932)."""
        t = MyTestParamInstantiation()
        assert t.params('instPO').instantiate is True
        assert isinstance(t.instPO,MyAnotherTestPO)


    def test_abstract_class(self):
        """Check that a class declared abstract actually shows up as abstract."""
        self.assertEqual(MyTestAbstractPO.abstract,True)
        self.assertEqual(MyTestPO.abstract,False)


    def test_params(self):
        """Basic tests of params() method."""


        # CB: test not so good because it requires changes if params
        # of PO are changed
        assert 'name' in param.Parameterized.params()
        assert len(param.Parameterized.params()) in [1,2]

        ## check for bug where subclass Parameters were not showing up
        ## if params() already called on a super class.
        assert 'inst' in MyTestPO.params()
        assert 'notinst' in MyTestPO.params()

        ## check caching
        assert param.Parameterized.params() is param.Parameterized().params(), "Results of params() should be cached." # just for performance reasons


    def test_state_saving(self):
        t = MyTestPO(dyn=SomeRandomNumbers())
        g = t.get_value_generator('dyn')
        g._Dynamic_time_fn=None
        assert t.dyn!=t.dyn
        orig = t.dyn
        t.state_push()
        t.dyn
        assert t.inspect_value('dyn')!=orig
        t.state_pop()
        assert t.inspect_value('dyn')==orig



from param import parameterized

class some_fn(param.ParameterizedFunction):
   num_phase = param.Number(18)
   frequencies = param.List([99])
   scale = param.Number(0.3)

   def __call__(self,**params_to_override):
       params = parameterized.ParamOverrides(self,params_to_override)
       num_phase = params['num_phase']
       frequencies = params['frequencies']
       scale = params['scale']
       return scale,num_phase,frequencies

instance = some_fn.instance()

class TestParameterizedFunction(unittest.TestCase):

    def _basic_tests(self,fn):
        self.assertEqual(fn(),(0.3,18,[99]))
        self.assertEqual(fn(frequencies=[1,2,3]),(0.3,18,[1,2,3]))
        self.assertEqual(fn(),(0.3,18,[99]))

        fn.frequencies=[10,20,30]
        self.assertEqual(fn(frequencies=[1,2,3]),(0.3,18,[1,2,3]))
        self.assertEqual(fn(),(0.3,18,[10,20,30]))

    def test_parameterized_function(self):
        self._basic_tests(some_fn)

    def test_parameterized_function_instance(self):
        self._basic_tests(instance)

    def test_pickle_instance(self):
        import pickle
        s = pickle.dumps(instance)
        instance.scale=0.8
        i = pickle.loads(s)
        self.assertEqual(i(),(0.3,18,[10,20,30]))


class MyTestPO1(param.Parameterized):
    x = param.Number(default=numbergen.UniformRandom(lbound=-1,ubound=1,seed=1),bounds=(-1,1))
    y = param.Number(default=1,bounds=(-1,1))

class TestNumberParameter(unittest.TestCase):

    def test_outside_bounds(self):
        t1 = MyTestPO1()
        # Test bounds (non-dynamic number)
        try:
            t1.y = 10
        except ValueError:
            pass
        else:
            assert False, "Should raise ValueError."

    def test_outside_bounds_numbergen(self):
        t1 = MyTestPO1()
        # Test bounds (dynamic number)
        t1.x = numbergen.UniformRandom(lbound=2,ubound=3)  # bounds not checked on set
        try:
            t1.x
        except ValueError:
            pass
        else:
            assert False, "Should raise ValueError."


class TestStringParameter(unittest.TestCase):

    def setUp(self):
        super(TestStringParameter, self).setUp()

        class TestString(param.Parameterized):
            a = param.String()
            b = param.String(default='',allow_None=True)
            c = param.String(default=None)

        self._TestString = TestString

    def test_handling_of_None(self):
        t = self._TestString()

        with self.assertRaises(ValueError):
            t.a = None

        t.b = None

        assert t.c is None



class TestParamOverrides(unittest.TestCase):

    def setUp(self):
        super(TestParamOverrides, self).setUp()
        self.po = param.Parameterized(name='A',print_level=0)

    def test_init_name(self):
        self.assertEqual(self.po.name, 'A')

    def test_simple_override(self):
        overrides = ParamOverrides(self.po,{'name':'B'})
        self.assertEqual(overrides['name'], 'B')
        self.assertEqual(overrides['print_level'], 0)

    # CEBALERT: missing test for allow_extra_keywords (e.g. getting a
    # warning on attempting to override non-existent parameter when
    # allow_extra_keywords is False)

    def test_missing_key(self):
        overrides = ParamOverrides(self.po,{'name':'B'})
        with self.assertRaises(AttributeError):
            overrides['doesnotexist']


class TestSharedParameters(unittest.TestCase):

    def setUp(self):
        with shared_parameters():
            self.p1 = MyTestPO(name='A', print_level=0)
            self.p2 = MyTestPO(name='B', print_level=0)
            self.ap1 = MyAnotherTestPO(name='A', print_level=0)
            self.ap2 = MyAnotherTestPO(name='B', print_level=0)

    def test_shared_object(self):
        self.assertTrue(self.ap1.instPO is self.ap2.instPO)
        self.assertTrue(self.ap1.params('instPO').default is not self.ap2.instPO)

    def test_shared_list(self):
        self.assertTrue(self.p1.inst is self.p2.inst)
        self.assertTrue(self.p1.params('inst').default is not self.p2.inst)
