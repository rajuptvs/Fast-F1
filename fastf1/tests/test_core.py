import warnings

import fastf1.core
import fastf1.events


def test_get_session_deprecated():
    with warnings.catch_warnings(record=True) as cap_warn:
        session = fastf1.core.get_session(2021, 1, 'FP1')
    assert isinstance(session, fastf1.core.Session)
    assert session.weekend.year == 2021
    assert session.weekend.roundNumber == 1
    assert 'deprecated' in str(cap_warn[0].message)


def test_get_round_deprecated():
    with warnings.catch_warnings(record=True) as cap_warn:
        round_number = fastf1.core.get_round(2021, 'Bahrain')
    assert round_number == 1
    assert 'deprecated' in str(cap_warn[0].message)


def test_weekend_deprecated():
    with warnings.catch_warnings(record=True) as cap_warn:
        weekend = fastf1.core.Weekend(2021, 1)
    assert isinstance(weekend, fastf1.events.Event)
    assert weekend.year == 2021
    assert weekend.roundNumber == 1
    assert 'deprecated' in str(cap_warn[0].message)
