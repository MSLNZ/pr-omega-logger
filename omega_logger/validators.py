"""
A Validator validates the data from an OMEGA iServer before the data is
inserted into a database. All custom-written validators should inherit
from the :class:`.Validator` class and override the
:meth:`~.Validator.validate` method.
"""
from abc import ABC
from abc import abstractmethod


class Validator(ABC):
    """Base class for all OMEGA iServer validators."""

    @abstractmethod
    def validate(self, data, ithx):
        """The callback that is used to validate the data from an OMEGA iServer.

        Parameters
        ----------
        data : :class:`tuple`
            The temperature, humidity and dew point values for each iServer probe.

            If a 1-probe iServer then::
               (temperature, humidity, dewpoint)

            If a 2-probe iServer then::
               (temperature1, humidity1, dewpoint1, temperature2, humidity2, dewpoint2)

        ithx
            An instance of the :class:`~msl.equipment.resources.omega.ithx.iTHX` class.

        Returns
        -------
        :class:`bool`
            Whether the `data` should be inserted into the database.
        """


class SimpleRange(Validator):

    def __init__(self, tmin=10, tmax=30, hmin=10, hmax=90, dmin=0, dmax=20, **kwargs):
        """Validates the data by verifying that it is within a certain range.

        The term "Simple" refers to the fact that nothing special is done if a
        value is outside of the allowed range except for writing a message to
        stdout. A more complex range validator could, for example, send an
        email to notify people.

        Parameters
        ----------
        tmin : :class:`float`, optional
            The minimum temperature value allowed.
        tmax : :class:`float`, optional
            The maximum temperature value allowed.
        hmin : :class:`float`, optional
            The minimum humidity value allowed.
        hmax : :class:`float`, optional
            The maximum humidity value allowed.
        dmin : :class:`float`, optional
            The minimum dew point value allowed.
        dmax : :class:`float`, optional
            The maximum dew point value allowed.
        kwargs
            Anything else is ignored.
        """
        self.tmin = float(tmin)
        self.tmax = float(tmax)
        self.hmin = float(hmin)
        self.hmax = float(hmax)
        self.dmin = float(dmin)
        self.dmax = float(dmax)

    def validate(self, data, ithx):
        if len(data) == 3:
            t1, h1, d1 = data
            temperatures = [t1]
            humidities = [h1]
            dewpoints = [d1]
        else:
            t1, h1, d1, t2, h2, d2 = data
            temperatures = [t1, t2]
            humidities = [h1, h2]
            dewpoints = [d1, d2]

        for t in temperatures:
            if not (self.tmin <= t <= self.tmax):
                ithx.log_warning(
                    f'Temperature value of {t} is out of range [{self.tmin}, {self.tmax}]'
                )
                return False

        for h in humidities:
            if not (self.hmin <= h <= self.hmax):
                ithx.log_warning(
                    f'Humidity value of {h} is out of range [{self.hmin}, {self.hmax}]'
                )
                return False

        for d in dewpoints:
            if not (self.dmin <= d <= self.dmax):
                ithx.log_warning(
                    f'Dewpoint value of {d} is out of range [{self.dmin}, {self.dmax}]'
                )
                return False

        # the data is okay, return True to insert the data into the database
        return True


class WithReset(Validator):

    def __init__(self, reset_criterion=5, **kwargs):
        """Reset the iServer after a certain number of invalid data values.

        Parameters
        ----------
        reset_criterion : :class:`int`, optional
            The maximum number of times that the data can fall outside of
            the specified range before resetting the iServer.
        kwargs
            All additional keyword arguments are passed to
            :class:`.SimpleRange`.
        """
        self.counter = 0
        self.reset_criterion = int(reset_criterion)

        self.simplerange = SimpleRange(**kwargs)

    def validate(self, data, ithx):

        if self.simplerange.validate(data, ithx):
            return True

        self.counter += 1

        if self.counter >= self.reset_criterion:
            ithx.log_warning(
                f'The Omega iServer will reset due to {self.reset_criterion} bad readings.'
            )
            ithx.reset(wait=True, password=None, port=2002, timeout=10)
            self.counter = 0

        return False


# A mapping between a name and the validator to use.
# The name is specified in a configuration file as the text of an XML element
# and the attributes of the element are used as keyword arguments for the
# Validator. For example, to use the SimpleRange validator you could include
# the following in your config.xml file:
#
#   <validator tmax="40" dmax="15">simple-range</validator>
#
# to change the default values to use for the maximum temperature and the
# maximum dew point.
validator_map = {
    'simple-range': SimpleRange,
    'with-reset': WithReset,
}
