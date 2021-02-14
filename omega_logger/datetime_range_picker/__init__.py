from dash.development.base_component import (
    _explicitize_args,
    Component,
)

# Avoid getting:
#   AttributeError: module 'datetime_range_picker' has no attribute '__version__'
from omega_logger import __version__


_js_dist = [{
    'relative_package_path': 'boilerplate/datetime_range_picker/datetime_range_picker.min.js',
    'namespace': __name__,
}]

_css_dist = [{
    'relative_package_path': 'boilerplate/datetime_range_picker/datetime_range_picker.css',
    'namespace': __name__,
}]


class DatetimeRangePicker(Component):
    """A DatetimeRangePicker component.

    Select a range of dates to within millisecond resolution.

    Based off of https://github.com/SebastianRehfeldt/dash-datepicker

    Parameters
    ----------
    id : :class:`str`, optional
        The ID used to identify this component in Dash callbacks.
    start : :class:`str` or :class:`datetime.datetime`, optional
        The start date and time of the range picker. Use the ISO 8601 format
        ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` for a string. A Dash
        callback is triggered when the range picker closes. The default
        date and time is yesterday at 8:00 am.
    end : :class:`str` or :class:`datetime.datetime`, optional
        The end date and time of the range picker. Use the ISO 8601 format
        ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` for a string. A Dash
        callback is triggered when the range picker closes. The default
        value is the current date and time.
    min_date : :class:`str` or :class:`datetime.datetime`, optional
        The minimum date that can be picked.
    max_date : :class:`str` or :class:`datetime.datetime`, optional
        The maximum date that can be picked.
    date_format : :class:`str`, optional
        The format to use to display the date that was picked.
        See :ref:`https://www.tutorialspoint.com/momentjs/momentjs_format.htm`
        for supported formats.
    time_format : :class:`str`, optional
        The format to use to display the time that was picked.
        See :ref:`https://www.tutorialspoint.com/momentjs/momentjs_format.htm`
        for supported formats.
    date_style : :class:`dict`, optional
        The style to use to render the date that was picked.
        See :ref:`https://www.w3schools.com/jsref/dom_obj_style.asp` for
        supported options.
    time_style : :class:`dict`, optional
        The style to use to render the time that was picked.
        See :ref:`https://www.w3schools.com/jsref/dom_obj_style.asp` for
        supported options.
    arrow : :class:`dict`, optional
        The SVG properties of the arrow. Default is
        ``{width: '30px', height: '30px', color: 'black'}``
    class_name : :class:`str`, optional
        A class name in the ``datetime_range_picker.css`` file.
        Default is ``datetime-range-center``
    text : :class:`str`, optional
        The text to display to the user to update the end date to the
        current date and time. Use the ``<br/>`` tag to insert a line break.
    """

    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, start=Component.UNDEFINED, end=Component.UNDEFINED,
                 min_date=Component.UNDEFINED, max_date=Component.UNDEFINED,
                 date_format=Component.UNDEFINED, time_format=Component.UNDEFINED,
                 date_style=Component.UNDEFINED, time_style=Component.UNDEFINED,
                 arrow=Component.UNDEFINED, class_name=Component.UNDEFINED,
                 text=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'start', 'end', 'min_date', 'max_date',
                            'date_format', 'time_format', 'date_style',
                            'time_style', 'arrow', 'class_name', 'text']
        self._type = 'DatetimeRangePicker'
        self._namespace = 'datetime_range_picker'
        self._valid_wildcard_attributes = []
        self.available_properties = ['id', 'start', 'end', 'min_date',
                                     'max_date', 'date_format', 'time_format',
                                     'date_style', 'time_style', 'arrow',
                                     'class_name', 'text']
        self.available_wildcard_properties = []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        super(DatetimeRangePicker, self).__init__(**args)
