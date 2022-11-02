from formset.boundfield import ClassList


def test_add_class():
    class_list = ClassList()
    class_list.add('foo')
    assert str(class_list) == 'foo'
    class_list.add('bar')
    assert str(class_list) in ['foo bar', 'bar foo']
    class_list.add('foo')
    assert str(class_list) in ['foo bar', 'bar foo']


def test_remove_class():
    class_list = ClassList({'foo', 'bar'})
    assert str(class_list) in ['foo bar', 'bar foo']
    class_list.remove('foo')
    assert str(class_list) == 'bar'
    class_list.remove('bar')
    assert str(class_list) == ''


def test_toggle_class():
    class_list = ClassList({'foo', 'bar'})
    assert str(class_list) in ['foo bar', 'bar foo']
    class_list.toggle('foo')
    assert str(class_list) == 'bar'
    class_list.toggle('foo')
    assert str(class_list) in ['foo bar', 'bar foo']


def test_force_toggle_class():
    class_list = ClassList({'foo', 'bar'})
    assert str(class_list) in ['foo bar', 'bar foo']
    class_list.toggle('foo', True)
    assert str(class_list) in ['foo bar', 'bar foo']
    class_list.toggle('foo')
    assert str(class_list) == 'bar'
    class_list.toggle('foo', False)
    assert str(class_list) == 'bar'
