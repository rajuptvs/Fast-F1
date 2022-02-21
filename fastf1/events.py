"""
:mod:`fastf1.events` - Events module
====================================
"""
import datetime
import pandas as pd
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message="Using slow pure-python SequenceMatcher")
    # suppress that warning, it's confusing at best here, we don't need fast sequence matching
    # and the installation (on windows) some effort
    from thefuzz import fuzz

from fastf1.api import Cache
from fastf1.core import Session


_SESSION_TYPE_ABBREVIATIONS = {
    'R': 'Race',
    'Q': 'Qualifying',
    'SQ': 'Sprint Qualifying',
    'FP1': 'Practice 1',
    'FP2': 'Practice 2',
    'FP3': 'Practice 3'
}


def get_session(year, gp, identifier=None, *, event=None):
    """Create a :class:`Session` object based on year, event name and session
    identifier.

    .. deprecated:: 2.2
        Creating :class:`Event` objects (previously
        :class:`fastf1.core.Weekend`) by not specifying an ``identifier`` has
        been deprecated. Use :func:`get_event` instead.

    .. deprecated:: 2.2
        The argument ``event`` has been replaced with ``identifier`` to adhere
        to new naming conventions.

    .. deprecated:: 2.2
        Testing sessions can no longer be created by specifying
        ``gp='testing'``. Use :func:`get_testing_session` instead. There is
        **no grace period** for this change. This will stop working immediately
        with the release of v2.2!


    Examples:

        Get the second free practice of the first race of 2021 by its session
        name abbreviation::

            >>> get_session(2021, 1, 'FP2')

        Get the qualifying of the 2020 Austrian Grand Prix by full session
        name::

            >>> get_session(2020, 'Austria', 'Qualifying')

        Get the 3rd session if the 5th Grand Prix in 2021::

            >>> get_session(2021, 5, 3)

    Args:
        year (int or str): Championship year
        gp (number or string): Name as str or round number as int. If gp is
            a string, a fuzzy match will be performed on the season rounds
            and the most likely will be selected.
            Fuzzy matching is performed on the country, location, name
            and officialName of each event.

            Some examples that will be correctly interpreted: 'bahrain',
            'australia', 'abudabi', 'monza'.

        event (str or int): may be one of

            - session name abbreviation: ``'FP1', 'FP2', 'FP3', 'Q',
              'SQ', 'R'``
            - full session name: ``'Practice 1', 'Practice 2', 'Practice 3',
              'Sprint Qualifying', 'Qualifying', 'Race'``
            - number of the session: ``1, 2, 3, 4, 5``

    Returns:
        :class:`~fastf1.core.Session`:
    """
    if identifier and event:
        raise ValueError("The arguments 'identifier' and 'event' are "
                         "mutually exclusive!")

    if gp == 'testing':
        raise DeprecationWarning('Accessing test sessions through '
                                 '`get_session` has been deprecated!\nUse '
                                 '`get_testing_session` instead.')

    if event is not None:
        warnings.warn("The keyword argument 'event' has been deprecated and "
                      "will be removed in a future version.\n"
                      "Use 'identifier' instead.")
        identifier = event

    event = get_event(year, gp, include_testing=False)

    if identifier is None:
        warnings.warn("Getting `Event` objects (previously `Session`) through "
                      "`get_session` has been deprecated.\n"
                      "Use `fastf1.events.get_event` instead.")
        return event  # TODO: remove in v2.3

    return event.get_session(identifier)


def get_testing_session(year, test_number, session_number):
    """Create a :class:`Session` object for testing sessions based on year,
    test number and session number
    identifier.

    Args:
        year (int or str): Championship year
        test_number (int): Number of the testing event (usually at most two)
        session_number (int): Number of the session withing a specific testing
            event. Each testing event usually has three sessions.

    Returns:
        :class:`~fastf1.core.Session`

    .. versionadded:: 2.2
    """
    schedule = get_event_schedule(year=year)
    schedule = schedule[schedule.is_testing()]

    try:
        event = schedule.iloc[test_number-1]
    except IndexError:
        raise ValueError(f"Test event number {test_number} does not exist")

    return event.get_session(session_number)


def get_event_schedule(year='current', include_testing=True):
    """Create an :class:`EventSchedule` object for a specific season.

    The event schedule currently supports the 2018 season and later.

    Args:
        year (int or str): Year (YYYY) or the string 'current' to get
            the event schedule for the current season.
        include_testing (bool): Include or exclude testing sessions from the
            event schedule.

    Returns:
        :class:`EventSchedule`

    .. versionadded:: 2.2
    """
    if year == 'current':
        year = datetime.datetime.now().year
    else:
        year = int(year)
        if year not in range(2018, datetime.datetime.now().year+1):
            raise NotImplementedError

    response = Cache.requests_get(
        f"https://raw.githubusercontent.com/theOehrly/f1schedule/master/"
        f"schedule_{year}.json")

    df = pd.read_json(response.text)
    schedule = EventSchedule(df, year=year)
    if not include_testing:
        schedule = schedule[~schedule.is_testing()]
    return schedule


def get_event(year, gp, include_testing=True):
    """Create an :class:`EventSchedule` object for a specific season and gp.

    The event schedule currently supports the 2018 season and later.

    Args:
        year (int or str): Year (YYYY) or the string 'current' to get
            the event schedule for the current season.
        gp (int or str): Name as string or round number as int. If gp is a
            string, a fuzzy match will be performed on the season rounds
            and the most likely will be selected.
        include_testing (bool): Include or exclude testing sessions from the
            event schedule. (May change the result in case of fuzzy matching
            the gp name)

    Returns:
        :class:`Event`

    .. versionadded:: 2.2
    """
    schedule = get_event_schedule(year=year, include_testing=include_testing)

    if type(gp) is str:
        event = schedule.get_event_by_name(gp)
    else:
        event = schedule.get_event_by_round(gp)

    return event


class EventSchedule(pd.DataFrame):
    """This class implements a per-season event schedule.

    This class is usually not instantiated directly. You should use
    :func:`get_event_schedule` to get an event schedule for a specific
    season.

    Args:
        *args: passed on to :class:`pandas.DataFrame` superclass
        year (int): Championship year
        **kwargs: passed on to :class:`pandas.DataFrame` superclass

    .. versionadded:: 2.2
    """

    _TYPES = {
        'roundNumber': 'int64',
        'country': 'object',
        'location': 'object',
        'officialEventName': 'object',
        'eventDate': 'datetime64[ns]',
        'eventName': 'object',
        'eventFormat': 'object',
        'session1': 'object',
        'session1Date': 'datetime64[ns]',
        'session2': 'object',
        'session2Date': 'datetime64[ns]',
        'session3': 'object',
        'session3Date': 'datetime64[ns]',
        'session4': 'object',
        'session4Date': 'datetime64[ns]',
        'session5': 'object',
        'session5Date': 'datetime64[ns]',
    }

    _metadata = ['year']

    _internal_names = ['base_class_view']

    def __init__(self, *args, year=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year

        # apply column specific dtypes
        for col, _type in self._TYPES.items():
            self[col] = self[col].astype(_type)

    def __repr__(self):
        return self.base_class_view.__repr__()

    @property
    def _constructor(self):
        return EventSchedule

    @property
    def _constructor_sliced(self):
        def new(*args, **kwargs):
            # with warnings.catch_warnings():
            #     warnings.simplefilter('ignore')
            event = Event(*args, **kwargs)
            event.__finalize__(self)
            return event
        return new

    @property
    def base_class_view(self):
        """For a nicer debugging experience; can view DataFrame through
        this property in various IDEs"""
        return pd.DataFrame(self)

    def is_testing(self):
        """Return `True` or `False`, depending on whether each event is a
        testing event."""
        return self['eventFormat'] == 'testing'

    def get_event_by_round(self, round):
        """Get an :class:`Event` by its round number.

        Args:
            round (int): The round number
        Returns:
            :class:`Event`
        Raises:
            ValueError: The round does not exist in the event schedule
        """
        mask = self['roundNumber'] == round
        if not mask.any():
            raise ValueError(f"Invalid round: {round}")
        return self[mask].iloc[0]

    def get_event_by_name(self, name):
        """Get an :class:`Event` by its name.

        A fuzzy match is performed to find the event that best matches the
        given name. Fuzzy matching is performed using the country, location,
        name and officialName of each event.

        Args:
            name (str): The name of the event. For example,
                ``.get_event_by_name("british")`` and
                ``.get_event_by_name("silverstone")`` will both return the
                event for the British Grand Prix.
        Returns:
            :class:`Event`
        """
        def _matcher_strings(ev):
            strings = list()
            strings.append(ev['location'])
            strings.append(ev['country'])
            strings.append(ev['eventName'].replace("Grand Prix", ""))
            strings.append(ev['officialEventName']
                           .replace("FORMULA 1", "")
                           .replace(str(self.year), ""))
            return strings

        max_ratio = 0
        index = 0
        for i, event in self.iterrows():
            ratio = max(
                [fuzz.ratio(val.casefold(), name.casefold())
                 for val in _matcher_strings(event)]
            )
            if ratio > max_ratio:
                max_ratio = ratio
                index = i
        return self.loc[index]


class Event(pd.Series):

    _metadata = ['year']

    _internal_names = ['date', 'gp']

    def __init__(self, *args, year=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.year = year
        self._getattr_override = True  # TODO: remove in v2.3

    @property
    def _constructor(self):
        return Event

    def __getattribute__(self, name):
        # TODO: remove in v2.3
        if name == 'name' and getattr(self, '_getattr_override', False):
            if 'eventName' in self:
                warnings.warn(
                    "The `Weekend.name` property is deprecated and will be"
                    "removed in a future version.\n"
                    "Use `Event['eventName']` or `Event.eventName` instead.")
                # name may be accessed by pandas internals to, when data
                # does not exist yet
                return self['eventName']
        return super().__getattribute__(name)

    @property
    def date(self):
        """Weekend race date (YYYY-MM-DD)"""
        # TODO: remove in v2.3
        warnings.warn("The `Weekend.date` property is deprecated and will be"
                      "removed in a future version.\n"
                      "Use `Event['eventDate']` or `Event.eventDate` instead.")
        return self['eventDate'].strftime('%Y-%m-%d')

    @property
    def gp(self):
        """Weekend round number"""
        # TODO: remove in v2.3
        warnings.warn("The `Weekend.gp` property is deprecated and will be"
                      "removed in a future version.\n"
                      "Use `Event['roundNumber']` or `Event.roundNumber` "
                      "instead.")
        return self['roundNumber']

    def is_testing(self):
        """Return `True` or `False`, depending on whether this event is a
        testing event."""
        return self['eventFormat'] == 'testing'

    def _get_session_name(self, session_type):
        if session_type in _SESSION_TYPE_ABBREVIATIONS.values():
            return session_type
        else:
            try:
                return _SESSION_TYPE_ABBREVIATIONS[session_type.upper()]
            except KeyError:
                raise ValueError(f"Invalid session type '{session_type}'")

    def get_session_date(self, session_type):
        session_name = self._get_session_name(session_type)
        relevant_columns = self.loc[['session1', 'session2', 'session3',
                                     'session4', 'session5']]
        mask = (relevant_columns == session_name)
        if not mask.any():
            raise ValueError(f"Session type '{session_type}' does not exist "
                             f"for this event")
        else:
            _name = mask.idxmax()
            return self[f"{_name}Date"]

    def get_session(self, identifier):
        """Return the a from this weekend.

        Args:
            identifier (str, int): One of 'R', 'SQ', 'Q', 'FP3', 'FP2', 'FP1'
                or an integer between 1 and 5

        Returns:
            :class:`Session` instance
        """
        try:
            num = float(identifier)
        except ValueError:
            # by name or abbreviation
            session_name = self._get_session_name(identifier)
            if session_name not in self.values:
                raise ValueError(f"No session of type '{identifier}' for "
                                 f"this event")
        else:
            # by number
            if (float(num).is_integer()
                    and (num := int(num)) in (1, 2, 3, 4, 5)):
                session_name = self[f'session{num}']
            else:
                raise ValueError(f"Invalid session type '{num}'")
            if not session_name:
                raise ValueError(f"Session number {num} does not "
                                 f"exist for this event")

        return Session(event=self, session_name=session_name)

    def get_race(self):
        """Return the race session.

        Returns:
            :class:`Session` instance
        """
        return self.get_session('R')

    def get_quali(self):
        """Return the qualifying session.

        Returns:
            :class:`Session` instance
        """
        return self.get_session('Q')

    def get_sprint(self):
        """Return the sprint session.

        Returns:
            :class:`Session` instance
        """
        return self.get_session('SQ')

    def get_practice(self, number):
        """Return the specified practice session.
        Args:
            number: 1, 2 or 3 - Free practice session number
        Returns:
            :class:`Session` instance
        """
        return self.get_session(f'FP{number}')
