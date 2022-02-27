import pytest

import warnings

import fastf1.core
import fastf1.events


def test_get_session_deprecations():
    # deprecated kwarg 'event'
    with warnings.catch_warnings(record=True) as cap_warn:
        session = fastf1.events.get_session(2021, 1, event='Q')
    assert 'deprecated' in str(cap_warn[0].message)
    assert isinstance(session, fastf1.core.Session)
    assert session.name == 'Qualifying'

    # cannot supply kwargs 'identifier' and 'event' simultaneously
    with pytest.raises(ValueError):
        fastf1.events.get_session(2021, 1, 'Q', event='Q')

    # cannot get testing anymore
    with pytest.raises(DeprecationWarning):
        fastf1.get_session(2021, 'testing', 1)

    # getting a Weekend/Event object through get session is deprecated
    with warnings.catch_warnings(record=True) as cap_warn:
        event = fastf1.events.get_session(2021, 1)
    assert 'deprecated' in str(cap_warn[0].message)
    assert isinstance(event, fastf1.events.Event)


@pytest.mark.parametrize("gp", ['Bahrain', 'Bharain', 'Sakhir', 1])
@pytest.mark.parametrize("identifier", ['Q', 4, 'Qualifying'])
def test_get_session(gp, identifier):
    session = fastf1.events.get_session(2021, gp, identifier)
    assert session.event.event_name == 'Bahrain Grand Prix'
    assert session.name == 'Qualifying'


@pytest.mark.parametrize("test_n, pass_1", [(0, False), (1, True), (2, False)])
@pytest.mark.parametrize(
    "session_n, pass_2",
    [(0, False), (1, True), (2, True), (3, True), (4, False)]
)
def test_get_testing_session(test_n, session_n, pass_1, pass_2):
    if pass_1 and pass_2:
        session = fastf1.events.get_testing_session(2021, test_n, session_n)
        assert isinstance(session, fastf1.core.Session)
        assert session.name == f"Practice {session_n}"
    else:
        with pytest.raises(ValueError):
            fastf1.events.get_testing_session(2021, test_n, session_n)


@pytest.mark.parametrize("gp", ['Bahrain', 'Bharain', 'Sakhir', 1])
def test_get_event(gp):
    event = fastf1.events.get_event(2021, gp)
    assert event.event_name == 'Bahrain Grand Prix'


def test_get_testing_event():
    # 0 is not a valid number for a testing event
    with pytest.raises(ValueError):
        fastf1.events.get_testing_event(2021, 0)

    session = fastf1.events.get_testing_event(2021, 1)
    assert isinstance(session, fastf1.events.Event)

    # only one testing event in 2021
    with pytest.raises(ValueError):
        fastf1.events.get_testing_event(2021, 2)
